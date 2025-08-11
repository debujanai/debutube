import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // In development, we can try to call Python directly
    if (process.env.NODE_ENV === 'development') {
      const { url, formatId } = body
      
      if (!url || !formatId) {
        return NextResponse.json({ error: 'URL and formatId are required' }, { status: 400 })
      }

      const result = await getDirectUrl(url, formatId)
      return NextResponse.json(result)
    }
    
    // In production, this should not be called as the Python function handles it
    return NextResponse.json({ error: 'This endpoint should be handled by Python function in production' }, { status: 500 })
    
  } catch (error) {
    console.error('Error getting direct URL:', error)
    return NextResponse.json(
      { error: 'Failed to get direct URL. Please try again.' },
      { status: 500 }
    )
  }
}

function getDirectUrl(url: string, formatId: string): Promise<any> {
  return new Promise((resolve, reject) => {
    // Try different Python executables
    const pythonCommands = ['python3', 'python', '/usr/bin/python3', '/usr/bin/python']
    
    const tryPythonCommand = (commandIndex: number) => {
      if (commandIndex >= pythonCommands.length) {
        reject(new Error('Python not found. Please ensure Python and yt-dlp are installed.'))
        return
      }

      const pythonCmd = pythonCommands[commandIndex]
      console.log(`Trying Python command: ${pythonCmd}`)
      
      const child = spawn(pythonCmd, ['-m', 'yt_dlp', '-g', '-f', formatId, url], {
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
          if (!directUrl) {
            reject(new Error('No direct URL found'))
            return
          }
          resolve({ directUrl })
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
      reject(new Error('Request timeout'))
    }, 30000)
  })
} 