import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const requestData = JSON.parse(body)
    
    console.log('📥 Received request for URL:', requestData.url)
    
    // Determine backend URL based on environment
    const backendUrl = process.env.FLASK_BACKEND_URL || 'http://localhost:5000'
    const apiUrl = `${backendUrl}/api/formats`
    
    console.log('🔗 Proxying to Flask backend:', apiUrl)
    
    try {
      const flaskResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: body,
        // Add timeout
        signal: AbortSignal.timeout(60000) // 60 seconds
      })
      
      const responseText = await flaskResponse.text()
      console.log('📤 Flask response status:', flaskResponse.status)
      console.log('📤 Flask response preview:', responseText.substring(0, 200))
      
      // Try to parse as JSON to validate
      let responseData
      try {
        responseData = JSON.parse(responseText)
      } catch (parseError) {
        console.error('❌ Failed to parse Flask response as JSON:', parseError)
        return NextResponse.json({ 
          error: 'Invalid response from backend',
          details: responseText.substring(0, 500)
        }, { status: 500 })
      }
      
      // Check if response has the expected structure
      if (!responseData.videoInfo && !responseData.error) {
        console.error('⚠️ Unexpected response structure:', Object.keys(responseData))
      }
      
      return NextResponse.json(responseData, {
        status: flaskResponse.status,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
      
    } catch (fetchError: any) {
      console.error('❌ Error connecting to Flask backend:', fetchError)
      
      // Check if it's a connection error
      if (fetchError.code === 'ECONNREFUSED' || fetchError.message?.includes('fetch failed')) {
        return NextResponse.json({ 
          error: 'Backend server is not running',
          details: 'Make sure Flask server is running on port 5000',
          hint: 'Run: python api/app.py'
        }, { status: 503 })
      }
      
      // Check if it's a timeout
      if (fetchError.name === 'AbortError' || fetchError.message?.includes('timeout')) {
        return NextResponse.json({ 
          error: 'Request timeout',
          details: 'The backend took too long to respond'
        }, { status: 504 })
      }
      
      return NextResponse.json({ 
        error: 'Failed to connect to backend',
        details: fetchError.message || 'Unknown error'
      }, { status: 500 })
    }
    
  } catch (error: any) {
    console.error('❌ Proxy error:', error)
    return NextResponse.json({ 
      error: 'Failed to process request',
      details: error.message || 'Unknown error'
    }, { status: 500 })
  }
}

export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }
  })
} 