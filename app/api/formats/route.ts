import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // In development, we can try to call Python directly
    // In production, this will be handled by the Python serverless function
    if (process.env.NODE_ENV === 'development') {
      const { url } = body
      
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
    }
    
    // In production, this should not be called as the Python function handles it
    return NextResponse.json({ error: 'This endpoint should be handled by Python function in production' }, { status: 500 })
    
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
    // Try different Python executables for better compatibility
    const pythonCommands = ['python3', 'python', '/usr/bin/python3', '/usr/bin/python']
    
    const tryPythonCommand = (commandIndex: number) => {
      if (commandIndex >= pythonCommands.length) {
        reject(new Error('Python not found. Please ensure Python and yt-dlp are installed.'))
        return
      }

      const pythonCmd = pythonCommands[commandIndex]
      console.log(`Trying Python command: ${pythonCmd}`)
      
      const child = spawn(pythonCmd, ['-m', 'yt_dlp', '--dump-json', '--no-download', url], {
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
            console.error('Parse error:', parseError)
            reject(new Error('Failed to parse video information'))
          }
        } else {
          console.error(`${pythonCmd} failed with code ${code}, stderr: ${stderr}`)
          // Try next Python command
          tryPythonCommand(commandIndex + 1)
        }
      })

      child.on('error', (error: Error) => {
        console.error(`Failed to start ${pythonCmd}:`, error.message)
        // Try next Python command
        tryPythonCommand(commandIndex + 1)
      })
    }

    // Start with the first Python command
    tryPythonCommand(0)

    // Set timeout
    setTimeout(() => {
      reject(new Error('Request timeout - yt-dlp took too long to respond'))
    }, 30000)
  })
} 