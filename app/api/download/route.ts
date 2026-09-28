import { NextRequest, NextResponse } from 'next/server'
import https from 'node:https'
import type { IncomingHttpHeaders, IncomingMessage } from 'node:http'
import { Readable } from 'node:stream'
import { extractPlaybackUrl, PLAYBACK_CLIENTS } from '@/lib/ytdlp'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 60

const UPSTREAM_UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

// googlevideo throttles long single requests to playback speed; small ranged requests stay at full speed.
const CHUNK_SIZE = 8 * 1024 * 1024

const upstreamHeaders = (range: string) => ({
  'User-Agent': UPSTREAM_UA,
  Accept: '*/*',
  'Accept-Encoding': 'identity',
  Origin: 'https://www.youtube.com',
  Referer: 'https://www.youtube.com/',
  Range: range,
})

type ChunkResponse = {
  status: number
  headers: Headers
  body: ReadableStream<Uint8Array>
}

function headerValue(headers: IncomingHttpHeaders, name: string) {
  const value = headers[name]
  return Array.isArray(value) ? value[0] : value
}

function requestOnce(target: string, range: string) {
  return new Promise<{ status: number; headers: IncomingHttpHeaders; stream: IncomingMessage }>(
    (resolve, reject) => {
      const parsed = new URL(target)
      const req = https.request(
        {
          hostname: parsed.hostname,
          path: `${parsed.pathname}${parsed.search}`,
          method: 'GET',
          family: 4,
          timeout: 25000,
          headers: upstreamHeaders(range),
        },
        (res) => resolve({ status: res.statusCode || 0, headers: res.headers, stream: res })
      )
      req.on('error', reject)
      req.on('timeout', () => req.destroy(new Error('Upstream timed out')))
      req.end()
    }
  )
}

async function fetchChunk(url: string, start: number, end: number): Promise<ChunkResponse> {
  let current = url
  const range = `bytes=${start}-${end}`
  for (let hop = 0; hop < 5; hop++) {
    const res = await requestOnce(current, range)
    const location = headerValue(res.headers, 'location')
    if (res.status >= 300 && res.status < 400 && location) {
      res.stream.resume()
      current = new URL(location, current).href
      continue
    }
    if (res.status !== 200 && res.status !== 206) {
      res.stream.resume()
      throw new Error(`Upstream chunk ${start}-${end} failed: ${res.status}`)
    }
    const headers = new Headers()
    for (const name of ['content-type', 'content-length', 'content-range']) {
      const value = headerValue(res.headers, name)
      if (value) headers.set(name, value)
    }
    return {
      status: res.status,
      headers,
      body: Readable.toWeb(res.stream) as ReadableStream<Uint8Array>,
    }
  }
  throw new Error(`Upstream chunk ${start}-${end} failed: too many redirects`)
}

async function openPlayable(watch: string, formatId: string, cookies?: string) {
  const failures: string[] = []
  for (const client of PLAYBACK_CLIENTS) {
    let link = ''
    try {
      link = await extractPlaybackUrl(watch, formatId, client, cookies)
      const knownTotal = Number(new URL(link).searchParams.get('clen')) || 0
      const end = knownTotal ? Math.min(CHUNK_SIZE - 1, knownTotal - 1) : CHUNK_SIZE - 1
      const first = await fetchChunk(link, 0, end)
      console.log(`playback client ${client}`)
      return { link, knownTotal, first }
    } catch (err) {
      failures.push(`${client}: ${err instanceof Error ? err.message : err}`)
    }
  }
  throw new Error(failures.join(' | ').slice(0, 700))
}

export async function GET(request: NextRequest) {
  return serve(new URL(request.url).searchParams)
}

// The page submits a form POST so pasted cookies can travel without bloating the URL.
export async function POST(request: NextRequest) {
  const form = await request.formData()
  const params = new URLSearchParams()
  form.forEach((value, key) => {
    if (typeof value === 'string') params.set(key, value)
  })
  return serve(params)
}

async function serve(searchParams: URLSearchParams) {
  try {
    const watch = searchParams.get('watch')
    const formatId = searchParams.get('format')
    const filename = searchParams.get('filename') || 'video.mp4'
    const cookies = searchParams.get('cookies') || undefined

    if (!watch || !formatId) {
      return NextResponse.json({ error: 'Video URL and format are required' }, { status: 400 })
    }

    const opened = await openPlayable(watch, formatId, cookies)
    const { link, first } = opened
    let total = opened.knownTotal
    const contentType = first.headers.get('content-type') || 'application/octet-stream'
    const contentRange = first.headers.get('content-range')
    if (!total && contentRange) {
      total = Number(contentRange.split('/')[1]) || 0
    }

    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          const pipe = async (res: ChunkResponse) => {
            const reader = res.body.getReader()
            for (;;) {
              const { done, value } = await reader.read()
              if (done) break
              controller.enqueue(value)
            }
          }

          await pipe(first)
          if (first.status === 206 && total) {
            for (let start = CHUNK_SIZE; start < total; start += CHUNK_SIZE) {
              const end = Math.min(start + CHUNK_SIZE, total) - 1
              await pipe(await fetchChunk(link, start, end))
            }
          }
          controller.close()
        } catch (err) {
          console.error('Download stream error:', err)
          controller.error(err)
        }
      },
    })

    const headers = new Headers()
    headers.set('Content-Type', contentType)
    headers.set(
      'Content-Disposition',
      `attachment; filename="${filename.replace(/"/g, '')}"; filename*=UTF-8''${encodeURIComponent(filename)}`
    )
    headers.set('Access-Control-Allow-Origin', '*')
    headers.set('Cache-Control', 'no-store')
    if (first.status === 206 && total) {
      headers.set('Content-Length', String(total))
    } else if (first.headers.get('content-length')) {
      headers.set('Content-Length', first.headers.get('content-length')!)
    }

    return new NextResponse(body, { status: 200, headers })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download video'
    console.error('Download error:', message)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
