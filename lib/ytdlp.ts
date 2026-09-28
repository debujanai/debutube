import { YtDlp } from 'ytdlp-nodejs'
import { execFile } from 'child_process'
import { promisify } from 'util'
import fs from 'fs'
import os from 'os'
import path from 'path'

const execFileAsync = promisify(execFile)

function bundledBinary() {
  // ytdlp-nodejs saves the GitHub asset name, not "yt-dlp". On Vercel that file is yt-dlp_linux.
  const dirs = [path.join(process.cwd(), 'node_modules', 'ytdlp-nodejs', 'bin')]
  try {
    dirs.unshift(path.resolve(path.dirname(require.resolve('ytdlp-nodejs')), '..', 'bin'))
  } catch {
    // package resolution failed; keep the cwd path
  }
  const names =
    process.platform === 'win32'
      ? ['yt-dlp.exe']
      : process.platform === 'darwin'
        ? ['yt-dlp_macos', 'yt-dlp']
        : ['yt-dlp_linux', 'yt-dlp_musllinux', 'yt-dlp_linux_aarch64', 'yt-dlp']
  const found = dirs
    .flatMap((binDir) => names.map((name) => path.join(binDir, name)))
    .find((candidate) => fs.existsSync(candidate))
  if (!found) {
    throw new Error(`yt-dlp binary is missing. Looked in ${dirs.join(', ')}`)
  }
  if (process.platform === 'win32') return found
  try {
    fs.accessSync(found, fs.constants.X_OK)
    return found
  } catch {
    const dest = path.join(os.tmpdir(), path.basename(found))
    if (!fs.existsSync(dest)) fs.copyFileSync(found, dest)
    fs.chmodSync(dest, 0o755)
    return dest
  }
}

const ytdlp = new YtDlp()

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
  language?: string
  language_preference?: number
  http_headers?: Record<string, string>
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
  language?: string
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
    language: format.language,
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
  const raw =
    error && typeof error === 'object' && 'stderr' in error
      ? String((error as { stderr?: string }).stderr || '').trim()
      : error instanceof Error
        ? error.message
        : 'yt-dlp failed'
  if (/not a bot/i.test(raw)) return 'YouTube asked for sign-in'
  const line = raw.split('\n').filter(Boolean).pop() || raw
  return line.slice(0, 240)
}

async function printMediaUrl(url: string, formatId: string, client: string, cookieFile?: string) {
  const args = [
    '--no-warnings',
    '--no-playlist',
    '--no-cache-dir',
    '--js-runtimes',
    `node:${process.execPath}`,
    '-g',
    '-f',
    formatId,
  ]
  if (client) {
    args.push('--extractor-args', `youtube:player_client=${client}`)
  }
  if (cookieFile) args.push('--cookies', cookieFile)
  else args.push('--no-cookies')
  args.push(url)

  const { stdout } = await execFileAsync(bundledBinary(), args, {
    windowsHide: true,
    timeout: 50000,
    maxBuffer: 2 * 1024 * 1024,
  })
  const link = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => line.startsWith('https'))
  if (!link) throw new Error(`Format ${formatId} is not available for this video`)
  return link
}

export async function mediaSource(url: string, formatId: string, cookies?: string) {
  // Use the same format entry the user clicked. TV player links swap in dubbed audio and a stream Chrome misreads.
  const video = await info(url, cookies)
  const match = ((video.formats || []) as RawFormat[]).find((format) => format.format_id === formatId && format.url)
  if (match?.url) {
    return { url: match.url, headers: match.http_headers || {} }
  }

  const jar = withCookies(cookies)
  try {
    const link = await printMediaUrl(url, formatId, '', jar.options.cookies)
    return { url: link, headers: {} as Record<string, string> }
  } catch (error) {
    if (!jar.options.cookies) {
      throw new Error('YouTube blocked the server. Turn on cookies — the same ones that loaded the formats — and try the download again.')
    }
    throw new Error(ytdlpError(error))
  } finally {
    jar.cleanup()
  }
}

export async function directUrl(url: string, formatId: string, cookies?: string) {
  const source = await mediaSource(url, formatId, cookies)
  return source.url
}
