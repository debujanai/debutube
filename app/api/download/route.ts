import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const videoUrl = searchParams.get('url')
    const filename = searchParams.get('filename')

    if (!videoUrl) {
      return NextResponse.json({ error: 'Video URL is required' }, { status: 400 })
    }

    // Fetch the video from the direct URL
    const response = await fetch(videoUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Range': 'bytes=0-',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch video: ${response.status}`)
    }

    // Get content info
    const contentLength = response.headers.get('content-length')
    const contentType = response.headers.get('content-type') || 'video/mp4'

    // Create response headers for download
    const headers = new Headers()
    headers.set('Content-Type', contentType)
    headers.set('Content-Disposition', `attachment; filename="${filename || 'video.mp4'}"`)
    headers.set('Access-Control-Allow-Origin', '*')
    
    if (contentLength) {
      headers.set('Content-Length', contentLength)
    }

    // Return the video stream with download headers
    return new NextResponse(response.body, {
      status: 200,
      headers,
    })

  } catch (error) {
    console.error('Download error:', error)
    return NextResponse.json(
      { error: 'Failed to download video' },
      { status: 500 }
    )
  }
} 