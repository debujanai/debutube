import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const videoUrl = new URL(request.url).searchParams.get('url')
  if (!videoUrl) {
    return NextResponse.json({ error: 'Video URL is required' }, { status: 400 })
  }

  let target: URL
  try {
    target = new URL(videoUrl)
  } catch {
    return NextResponse.json({ error: 'Invalid video URL' }, { status: 400 })
  }

  const host = target.hostname
  const allowed = host === 'googlevideo.com' || host.endsWith('.googlevideo.com')
  if (!allowed) {
    return NextResponse.json({ error: 'Only YouTube media links can be downloaded' }, { status: 400 })
  }

  // Vercel’s IP is rejected by googlevideo. The browser must request the file itself.
  return NextResponse.redirect(target, 302)
}
