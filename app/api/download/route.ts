import { NextRequest, NextResponse } from 'next/server'

export const maxDuration = 60

const UPSTREAM_UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

// googlevideo throttles long single requests to playback speed; small ranged requests stay at full speed.
const CHUNK_SIZE = 8 * 1024 * 1024

const upstreamHeaders = (range: string) => ({
  'User-Agent': UPSTREAM_UA,
  Accept: '*/*',
  'Accept-Encoding': 'identity',
  Referer: 'https://www.youtube.com/',
  Range: range,
})

async function fetchChunk(url: string, start: number, end: number) {
  const res = await fetch(url, {
    headers: upstreamHeaders(`bytes=${start}-${end}`),
    redirect: 'follow',
  })
  if (!res.ok && res.status !== 206) {
    throw new Error(`Upstream chunk ${start}-${end} failed: ${res.status}`)
  }
  return res
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const videoUrl = searchParams.get('url')
    const filename = searchParams.get('filename') || 'video.mp4'

    if (!videoUrl) {
      return NextResponse.json({ error: 'Video URL is required' }, { status: 400 })
    }

    const knownTotal = Number(new URL(videoUrl).searchParams.get('clen')) || 0
    // YouTube returns 403 for audio when a range runs past the end of the file.
    const clampEnd = (start: number, end: number) =>
      knownTotal ? Math.min(end, knownTotal - 1) : end

    const range = request.headers.get('range')?.match(/bytes=(\d+)-(\d*)/)
    if (range) {
      const start = Number(range[1])
      const requestedEnd = range[2] ? Number(range[2]) : start + CHUNK_SIZE - 1
      const end = clampEnd(start, requestedEnd)
      if (knownTotal && start >= knownTotal) {
        return new NextResponse(null, {
          status: 416,
          headers: { 'Content-Range': `bytes */${knownTotal}` },
        })
      }
      const piece = await fetchChunk(videoUrl, start, end)
      const pieceHeaders = new Headers()
      pieceHeaders.set('Content-Type', 'application/octet-stream')
      pieceHeaders.set('Cache-Control', 'no-store')
      for (const h of ['content-length', 'content-range']) {
        const v = piece.headers.get(h)
        if (v) pieceHeaders.set(h, v)
      }
      return new NextResponse(piece.body, { status: 206, headers: pieceHeaders })
    }

    const first = await fetchChunk(videoUrl, 0, clampEnd(0, CHUNK_SIZE - 1))
    const contentType = first.headers.get('content-type') || 'application/octet-stream'

    let total = Number(new URL(videoUrl).searchParams.get('clen')) || 0
    const contentRange = first.headers.get('content-range')
    if (!total && contentRange) {
      total = Number(contentRange.split('/')[1]) || 0
    }

    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          const pipe = async (res: Response) => {
            const reader = res.body!.getReader()
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
              await pipe(await fetchChunk(videoUrl, start, end))
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
