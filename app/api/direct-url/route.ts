import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const { url, formatId } = await request.json()

    if (!url || !formatId) {
      return NextResponse.json({ error: 'URL and format ID are required' }, { status: 400 })
    }

    // Validate YouTube URL
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/
    if (!youtubeRegex.test(url)) {
      return NextResponse.json({ error: 'Please provide a valid YouTube URL' }, { status: 400 })
    }

    const directUrl = await getDirectUrl(url, formatId)
    return NextResponse.json({ directUrl })
  } catch (error) {
    console.error('Error getting direct URL:', error)
    return NextResponse.json(
      { error: 'Failed to get direct download URL. Please try again.' },
      { status: 500 }
    )
  }
}

function getDirectUrl(url: string, formatId: string): Promise<string> {
  return new Promise((resolve, reject) => {
    // Use your original working yt-dlp command to get direct URL
    const child = spawn('python', ['-m', 'yt_dlp', '-g', '-f', formatId, url], {
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
        const directUrl = stdout.trim()
        if (directUrl) {
          resolve(directUrl)
        } else {
          reject(new Error('No direct URL found'))
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