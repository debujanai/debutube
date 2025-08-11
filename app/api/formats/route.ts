import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // In development, we need to proxy to our Flask backend
    // In production, Vercel routes handle this automatically
    if (process.env.NODE_ENV === 'development') {
      // Forward the request to Flask backend running on different port
      const body = await request.text()
      
      const flaskResponse = await fetch('http://localhost:5000/api/formats', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: body
      })
      
      const data = await flaskResponse.text()
      
      return new Response(data, {
        status: flaskResponse.status,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      })
    }
    
    // In production, this should not be reached
    return NextResponse.json({ error: 'Use Flask backend in production' }, { status: 500 })
    
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json({ 
      error: 'Failed to connect to backend. Make sure Flask server is running on port 5000.' 
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