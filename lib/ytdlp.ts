import { YtDlp } from 'ytdlp-nodejs'
import { execFile } from 'child_process'
import { promisify } from 'util'
import fs from 'fs'
import os from 'os'
import path from 'path'

const execFileAsync = promisify(execFile)

const binary = path.join(process.cwd(), 'node_modules', 'ytdlp-nodejs', 'bin', process.platform === 'win32' ? 'yt-dlp.exe' : 'yt-dlp')

const ytdlp = new YtDlp({
  binaryPath: fs.existsSync(binary) ? binary : undefined,
})

type RawFormat = {
  format_id?: string
  ext?: string
  resolution?: string
  format_note?: string
  filesize?: number | null
  filesize_approx?: number | null
  vcodec?: string
  acodec?: string
  fps?: number
  quality?: number
  width?: number
  height?: number
  tbr?: number
  abr?: number
  vbr?: number
  protocol?: string
  format?: string
  url?: string
}

export type ListedFormat = {
  format_id: string
  ext?: string
  resolution?: string
  format_note?: string
  filesize?: number | null
  filesize_approx?: number | null
  vcodec?: string
  acodec?: string
  fps?: number
  quality?: number
  width?: number
  height?: number
  tbr?: number
  abr?: number
  vbr?: number
  protocol?: string
  format?: string
  url?: string
  type: 'video' | 'audio' | 'combined'
}

function cookieSource(cookies?: string) {
  const trimmed = cookies?.trim()
  if (trimmed) return trimmed
  const fromEnv = process.env.YTDLP_COOKIES?.trim()
  if (fromEnv) return fromEnv
  const local = path.join(process.cwd(), 'youtube_cookies.txt')
  if (fs.existsSync(local)) return local
  return ''
}

function withCookies(cookies?: string) {
  const source = cookieSource(cookies)
  if (!source) return { options: {} as { cookies?: string }, cleanup: () => {} }
  if (!source.includes('\n') && fs.existsSync(source)) {
    return { options: { cookies: source }, cleanup: () => {} }
  }
  const file = path.join(os.tmpdir(), `debutube-${process.pid}-${Date.now()}.txt`)
  const body = source.includes('# Netscape HTTP Cookie File') ? source : `# Netscape HTTP Cookie File\n${source}`
  fs.writeFileSync(file, body)
  return { options: { cookies: file }, cleanup: () => fs.rmSync(file, { force: true }) }
}

function isStoryboard(format: RawFormat) {
  const protocol = (format.protocol || '').toLowerCase()
  return (
    String(format.format_id || '').startsWith('sb') ||
    (format.ext || '').toLowerCase() === 'mhtml' ||
    protocol.includes('m3u8') ||
    (protocol !== '' && protocol !== 'https')
  )
}

function toListed(format: RawFormat): ListedFormat | null {
  if (!format.format_id || isStoryboard(format)) return null
  const hasVideo = !!format.vcodec && format.vcodec !== 'none'
  const hasAudio = !!format.acodec && format.acodec !== 'none'
  return {
    format_id: format.format_id,
    ext: format.ext,
    resolution: format.resolution,
    format_note: format.format_note,
    filesize: format.filesize || format.filesize_approx,
    filesize_approx: format.filesize_approx,
    vcodec: format.vcodec,
    acodec: format.acodec,
    fps: format.fps,
    quality: format.quality,
    width: format.width,
    height: format.height,
    tbr: format.tbr,
    abr: format.abr,
    vbr: format.vbr,
    protocol: format.protocol,
    format: format.format,
    url: format.url,
    type: hasVideo && !hasAudio ? 'video' : hasAudio && !hasVideo ? 'audio' : 'combined',
  }
}

async function info(url: string, cookies?: string) {
  const jar = withCookies(cookies)
  try {
    return await ytdlp.getInfoAsync<'video'>(url, { ...jar.options, flatPlaylist: false })
  } finally {
    jar.cleanup()
  }
}

export async function listFormats(url: string, cookies?: string) {
  const video = await info(url, cookies)
  const formats = ((video.formats || []) as RawFormat[])
    .map(toListed)
    .filter((format): format is ListedFormat => !!format)
    .sort((a, b) => (b.quality || 0) - (a.quality || 0))

  const videoFormats = formats
    .filter((format) => format.type !== 'audio')
    .sort((a, b) => (b.height || 0) - (a.height || 0) || (b.quality || 0) - (a.quality || 0))
  const audioFormats = formats
    .filter((format) => format.type !== 'video')
    .sort((a, b) => (b.abr || 0) - (a.abr || 0) || (b.quality || 0) - (a.quality || 0))

  return {
    videoInfo: {
      title: video.title || 'Unknown Title',
      description: video.description || '',
      duration: video.duration || 0,
      uploader: video.uploader || video.channel || 'Unknown',
      upload_date: video.upload_date || '',
      view_count: video.view_count || 0,
      like_count: video.like_count || 0,
      thumbnail: video.thumbnail || '',
      channel: video.channel || video.uploader || 'Unknown',
      channel_id: video.channel_id || '',
      webpage_url: video.webpage_url || url,
      id: video.id || '',
      fulltitle: video.fulltitle || video.title,
      age_limit: video.age_limit || 0,
      is_live: !!video.is_live,
      availability: video.availability || 'public',
    },
    formats,
    videoFormats,
    audioFormats,
  }
}

function ytdlpError(error: unknown) {
  if (error && typeof error === 'object' && 'stderr' in error) {
    const stderr = String((error as { stderr?: string }).stderr || '').trim()
    if (stderr) return stderr.split('\n').slice(-4).join(' ').slice(0, 500)
  }
  return error instanceof Error ? error.message : 'yt-dlp failed'
}

async function printMediaUrl(url: string, formatId: string, client: string) {
  // No cookies. Cookie-backed web links are IP-locked and return 403 on download.
  const { stdout } = await execFileAsync(
    fs.existsSync(binary) ? binary : 'yt-dlp',
    [
      '--no-warnings',
      '--no-playlist',
      '--no-cache-dir',
      '--no-cookies',
      '--js-runtimes',
      `node:${process.execPath}`,
      '-g',
      '-f',
      formatId,
      '--extractor-args',
      `youtube:player_client=${client}`,
      url,
    ],
    { windowsHide: true, timeout: 50000, maxBuffer: 2 * 1024 * 1024 }
  )
  const link = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => line.startsWith('https'))
  if (!link) throw new Error(`Format ${formatId} is not available for this video`)
  return link
}

export async function directUrl(url: string, formatId: string, _cookies?: string) {
  const clients = ['tv_embedded', 'tv', 'ios']
  const errors: string[] = []
  for (const client of clients) {
    try {
      const link = await printMediaUrl(url, formatId, client)
      const player = new URL(link).searchParams.get('c') || ''
      if (player.startsWith('WEB')) {
        errors.push(`${client}: refused web player link`)
        continue
      }
      return link
    } catch (error) {
      errors.push(`${client}: ${ytdlpError(error)}`)
    }
  }
  throw new Error(errors.join(' | ') || `Format ${formatId} is not available for this video`)
}
