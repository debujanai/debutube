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
  language?: string | null
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
  language?: string | null
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

function forceEnglishPrefs(raw: string) {
  return raw
    .split(/\r?\n/)
    .map((line) => {
      if (!line || line.startsWith('#')) return line
      const parts = line.split('\t')
      if (parts.length < 7 || parts[5] !== 'PREF') return line
      let value = parts.slice(6).join('\t')
      value = value.replace(/(^|&)hl=[^&]*/g, '$1hl=en')
      if (!/(^|&)hl=/.test(value)) value = value ? `${value}&hl=en` : 'hl=en'
      parts.splice(6, parts.length - 6, value)
      return parts.join('\t')
    })
    .join('\n')
}

function withCookies(cookies?: string) {
  const source = cookieSource(cookies)
  if (!source) return { options: {} as { cookies?: string }, cleanup: () => {} }
  const raw = !source.includes('\n') && fs.existsSync(source) ? fs.readFileSync(source, 'utf8') : source
  const body = forceEnglishPrefs(
    raw.includes('# Netscape HTTP Cookie File') ? raw : `# Netscape HTTP Cookie File\n${raw}`
  )
  const file = path.join(os.tmpdir(), `debutube-${process.pid}-${Date.now()}.txt`)
  fs.writeFileSync(file, body)
  return { options: { cookies: file }, cleanup: () => fs.rmSync(file, { force: true }) }
}

function isEnglishTrack(format: { language?: string | null; format_note?: string; format?: string }) {
  const lang = (format.language || '').toLowerCase()
  if (lang && !lang.startsWith('en')) return false
  const note = `${format.format_note || ''} ${format.format || ''}`
  if (/[\u0600-\u06FF]/.test(note)) return false
  if (/\barabic\b/i.test(note)) return false
  return true
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
    language: format.language,
    type: hasVideo && !hasAudio ? 'video' : hasAudio && !hasVideo ? 'audio' : 'combined',
  }
}

async function info(url: string, cookies?: string) {
  const jar = withCookies(cookies)
  try {
    return await ytdlp.getInfoAsync<'video'>(url, Object.assign(
      { ...jar.options, flatPlaylist: false },
      { forceIpv4: true, noCacheDir: true, extractorArgs: { youtube: ['lang=en'] } }
    ))
  } finally {
    jar.cleanup()
  }
}

export async function listFormats(url: string, cookies?: string) {
  const video = await info(url, cookies)
  const listed = ((video.formats || []) as RawFormat[])
    .map(toListed)
    .filter((format): format is ListedFormat => !!format)
  const english = listed.filter(isEnglishTrack)
  const formats = (english.length ? english : listed).sort((a, b) => (b.quality || 0) - (a.quality || 0))

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

export const PLAYBACK_CLIENTS = ['tv_embedded', 'web_safari', 'ios'] as const

export async function extractPlaybackUrl(url: string, formatId: string, client: string) {
  // No cookies here. Cookie-backed links 403 after the first range, and a URL
  // minted on one Vercel instance is rejected when another instance fetches it.
  const jsRuntime = process.platform === 'win32' ? `node:${process.execPath}` : 'node'
  let stdout = ''
  try {
    const result = await execFileAsync(
      fs.existsSync(binary) ? binary : 'yt-dlp',
      [
        '--no-warnings',
        '--no-config',
        '--no-cache-dir',
        '--no-playlist',
        '--force-ipv4',
        '--js-runtimes',
        jsRuntime,
        '-g',
        '-f',
        formatId,
        '--extractor-args',
        `youtube:player_client=${client};lang=en`,
        url,
      ],
      {
        windowsHide: true,
        timeout: 20000,
        maxBuffer: 1024 * 1024,
        env: {
          ...process.env,
          PATH: process.env.PATH,
          PATHEXT: process.env.PATHEXT,
          SystemRoot: process.env.SystemRoot,
          HOME: process.platform === 'win32' ? process.env.USERPROFILE : '/tmp',
          XDG_CACHE_HOME: process.platform === 'win32' ? undefined : '/tmp',
        },
      }
    )
    stdout = result.stdout
  } catch (err) {
    const failure = err as { stderr?: string; message?: string }
    const detail = (failure.stderr || failure.message || 'extract failed').trim().slice(0, 300)
    throw new Error(detail)
  }
  const link = stdout.split(/\r?\n/).find((line) => line.startsWith('https'))
  if (!link) throw new Error(`Format ${formatId} is not available for this video`)
  return link.trim()
}

export async function directUrl(url: string, formatId: string, cookies?: string) {
  const video = await info(url, cookies)
  const match = ((video.formats || []) as RawFormat[]).find((format) => format.format_id === formatId)
  if (!match) throw new Error(`Format ${formatId} is not available for this video`)

  const failures: string[] = []
  for (const client of PLAYBACK_CLIENTS) {
    try {
      return await extractPlaybackUrl(url, formatId, client)
    } catch (err) {
      failures.push(`${client}: ${err instanceof Error ? err.message : err}`)
    }
  }
  if (match.url) return match.url
  throw new Error(failures.join(' | ').slice(0, 500) || `Format ${formatId} is not available for this video`)
}
