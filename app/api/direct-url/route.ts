import { NextRequest, NextResponse } from 'next/server'
import { directUrl } from '@/lib/ytdlp'

export const maxDuration = 60
export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const url = body?.url
    const formatId = body?.formatId
    if (!url || !formatId) {
      return NextResponse.json({ error: 'URL and formatId are required' }, { status: 400 })
    }
    const link = await directUrl(url, String(formatId), typeof body.cookies === 'string' ? body.cookies : undefined)
    return NextResponse.json({ directUrl: link }, { headers: { 'Access-Control-Allow-Origin': '*' } })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to get direct URL'
    console.error('direct-url error:', message)
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
