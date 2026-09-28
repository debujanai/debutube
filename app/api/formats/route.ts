import { NextRequest, NextResponse } from 'next/server'
import { listFormats } from '@/lib/ytdlp'

export const maxDuration = 60
export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const url = body?.url
    if (!url || typeof url !== 'string') {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 })
    }
    const data = await listFormats(url, typeof body.cookies === 'string' ? body.cookies : undefined)
    return NextResponse.json(data, { headers: { 'Access-Control-Allow-Origin': '*' } })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to get video info'
    console.error('formats error:', message)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}
