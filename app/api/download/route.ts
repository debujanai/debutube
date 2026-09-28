import { NextRequest, NextResponse } from 'next/server'
import { mediaSource } from '@/lib/ytdlp'

export const maxDuration = 60
export const dynamic = 'force-dynamic'

function attachmentName(filename: string) {
  const clean = (filename || 'video.mp4').replace(/[\r\n"]/g, '')
  return `attachment; filename="${clean}"; filename*=UTF-8''${encodeURIComponent(clean)}`
}

async function readPayload(request: NextRequest) {
  const type = request.headers.get('content-type') || ''
  if (type.includes('application/json')) {
    return (await request.json()) as { url?: string; formatId?: string; filename?: string; cookies?: string }
  }
  const form = await request.formData()
  return {
    url: String(form.get('url') || ''),
    formatId: String(form.get('formatId') || ''),
    filename: String(form.get('filename') || ''),
    cookies: String(form.get('cookies') || ''),
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await readPayload(request)
    if (!body.url || !body.formatId) {
      return NextResponse.json({ error: 'URL and format are required' }, { status: 400 })
    }

    const source = await mediaSource(body.url, String(body.formatId), body.cookies || undefined)
    const upstream = await fetch(source.url, {
      headers: {
        ...source.headers,
        Accept: '*/*',
        'Accept-Encoding': 'identity',
        Referer: 'https://www.youtube.com/',
      },
      redirect: 'follow',
    })

    if (!upstream.ok || !upstream.body) {
      return NextResponse.json({ error: `YouTube rejected the file (${upstream.status})` }, { status: 502 })
    }

    const headers = new Headers()
    headers.set('Content-Type', upstream.headers.get('content-type') || 'application/octet-stream')
    headers.set('Content-Disposition', attachmentName(body.filename || 'video.mp4'))
    headers.set('Cache-Control', 'no-store')
    const length = upstream.headers.get('content-length')
    if (length) headers.set('Content-Length', length)

    return new NextResponse(upstream.body, { status: 200, headers })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to download'
    console.error('Download error:', message)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
