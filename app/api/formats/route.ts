import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const { url } = await request.json()

    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 })
    }

    // Validate YouTube URL
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/
    if (!youtubeRegex.test(url)) {
      return NextResponse.json({ error: 'Please provide a valid YouTube URL' }, { status: 400 })
    }

    const result = await getVideoInfo(url)
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error fetching formats:', error)
    return NextResponse.json(
      { error: 'Failed to fetch video information. Please try again.' },
      { status: 500 }
    )
  }
}

function getVideoInfo(url: string): Promise<any> {
  return new Promise((resolve, reject) => {
    // Use your original working yt-dlp command to get formats
    const child = spawn('python', ['-m', 'yt_dlp', '--dump-json', '--no-download', url], {
      stdio: ['ignore', 'pipe', 'pipe']
    })

    let stdout = ''
    let stderr = ''

    child.stdout.on('data', (data: Buffer) => {
      stdout += data.toString()
    })

    child.stderr.on('data', (data: Buffer) => {
      stderr += data.toString()
    })

    child.on('close', (code: number) => {
      if (code === 0) {
        try {
          const videoInfo = JSON.parse(stdout.trim())
          const formats = videoInfo.formats || []
          
          // Filter and sort formats just like your original script
          const filteredFormats = formats
            .filter((format: any) => format.url && format.format_id)
            .map((format: any) => ({
              format_id: format.format_id,
              ext: format.ext,
              resolution: format.resolution,
              format_note: format.format_note,
              filesize: format.filesize,
              vcodec: format.vcodec,
              acodec: format.acodec,
              fps: format.fps,
              quality: format.quality
            }))
            .sort((a: any, b: any) => {
              // Sort by quality/resolution
              if (a.quality && b.quality) {
                return b.quality - a.quality
              }
              return 0
            })

          // Extract video metadata
          const videoMetadata = {
            title: videoInfo.title || 'Unknown Title',
            description: videoInfo.description || '',
            duration: videoInfo.duration || 0,
            uploader: videoInfo.uploader || videoInfo.channel || 'Unknown',
            upload_date: videoInfo.upload_date || '',
            view_count: videoInfo.view_count || 0,
            like_count: videoInfo.like_count || 0,
            thumbnail: videoInfo.thumbnail || '',
            channel: videoInfo.channel || videoInfo.uploader || 'Unknown',
            channel_id: videoInfo.channel_id || videoInfo.uploader_id || '',
            webpage_url: videoInfo.webpage_url || url,
            id: videoInfo.id || '',
            fulltitle: videoInfo.fulltitle || videoInfo.title || 'Unknown Title'
          }

          resolve({
            videoInfo: videoMetadata,
            formats: filteredFormats
          })
        } catch (parseError) {
          reject(new Error('Failed to parse video information'))
        }
      } else {
        reject(new Error(`yt-dlp failed: ${stderr || 'Unknown error'}`))
      }
    })

    child.on('error', (error: Error) => {
      reject(new Error(`Failed to start yt-dlp: ${error.message}`))
    })

    // Set timeout
    setTimeout(() => {
      child.kill()
      reject(new Error('Request timeout'))
    }, 30000)
  })
} 