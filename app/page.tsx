'use client'

import { useState, useEffect } from 'react'
import { Download, Youtube, AlertCircle, Loader2, Film, Music, FileVideo, FileAudio, Play, Moon, Sun, Eye, ThumbsUp, Clock, Calendar, User } from 'lucide-react'

interface Format {
  format_id: string
  ext: string
  resolution?: string
  format_note?: string
  filesize?: number
  vcodec?: string
  acodec?: string
  fps?: number
}

interface VideoInfo {
  title: string
  description: string
  duration: number
  uploader: string
  upload_date: string
  view_count: number
  like_count: number
  thumbnail: string
  channel: string
  channel_id: string
  webpage_url: string
  id: string
  fulltitle: string
}

export default function Home() {
  const [url, setUrl] = useState('')
  const [formats, setFormats] = useState<Format[]>([])
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('video')
  const [activeVideoFormat, setActiveVideoFormat] = useState('mp4')
  const [activeAudioFormat, setActiveAudioFormat] = useState('m4a')
  const [downloadingFormats, setDownloadingFormats] = useState<Set<string>>(new Set())
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Load theme preference on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('debutube-theme')
    if (savedTheme === 'dark') {
      setIsDarkMode(true)
    }
  }, [])

  // Save theme preference
  const toggleTheme = () => {
    const newMode = !isDarkMode
    setIsDarkMode(newMode)
    localStorage.setItem('debutube-theme', newMode ? 'dark' : 'light')
  }

  const handleGetFormats = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL')
      return
    }

    setLoading(true)
    setError('')
    setFormats([])
    setVideoInfo(null)

    try {
      const response = await fetch('/api/formats', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch formats')
      }

      setVideoInfo(data.videoInfo)
      setFormats(data.formats)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (formatId: string, resolution: string, ext: string) => {
    setDownloadingFormats(prev => new Set(prev).add(formatId))
    
    try {
      const response = await fetch('/api/direct-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, formatId }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to get direct URL')
      }

      // Get video title for better filename
      const videoTitle = videoInfo?.title || await getVideoTitle(url)
      const cleanTitle = videoTitle.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 50)
      
      // Create filename
      const filename = `${cleanTitle}_${resolution || formatId}.${ext}`
      
      // Use our proxy download API to bypass CORS
      const downloadUrl = `/api/download?url=${encodeURIComponent(data.directUrl)}&filename=${encodeURIComponent(filename)}`
      
      // Create download link using our proxy
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      link.style.display = 'none'
      
      // Add to DOM, click, and remove
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download')
    } finally {
      setDownloadingFormats(prev => {
        const newSet = new Set(prev)
        newSet.delete(formatId)
        return newSet
      })
    }
  }

  const getVideoTitle = async (videoUrl: string): Promise<string> => {
    try {
      const videoId = videoUrl.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/)?.[1]
      if (!videoId) return 'video'
      return `video_${videoId}`
    } catch {
      return 'video'
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Size unknown'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDuration = (seconds: number) => {
    if (!seconds) return 'Unknown'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'Unknown'
    try {
      // yt-dlp returns dates in YYYYMMDD format
      const year = dateStr.slice(0, 4)
      const month = dateStr.slice(4, 6)
      const day = dateStr.slice(6, 8)
      const date = new Date(`${year}-${month}-${day}`)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
    } catch {
      return dateStr
    }
  }

  // Filter and organize formats
  const videoFormats = formats.filter(f => 
    f.vcodec && f.vcodec !== 'none' && 
    !f.format_note?.includes('storyboard') &&
    f.resolution && f.resolution !== 'audio only'
  )

  const audioFormats = formats.filter(f => 
    f.acodec && f.acodec !== 'none' && 
    (f.resolution === 'audio only' || !f.vcodec || f.vcodec === 'none')
  )

  // Group video formats by extension and resolution
  const groupedVideoFormats = videoFormats.reduce((acc, format) => {
    const ext = format.ext.toLowerCase()
    const resolution = format.resolution || 'Unknown'
    
    if (!acc[ext]) {
      acc[ext] = {}
    }
    if (!acc[ext][resolution]) {
      acc[ext][resolution] = []
    }
    acc[ext][resolution].push(format)
    return acc
  }, {} as Record<string, Record<string, Format[]>>)

  // Group audio formats by extension
  const groupedAudioFormats = audioFormats.reduce((acc, format) => {
    const ext = format.ext.toLowerCase()
    if (!acc[ext]) {
      acc[ext] = []
    }
    acc[ext].push(format)
    return acc
  }, {} as Record<string, Format[]>)

  // Get available video formats
  const availableVideoFormats = Object.keys(groupedVideoFormats).sort()
  const availableAudioFormats = Object.keys(groupedAudioFormats).sort()

  // Sort resolutions by quality (descending)
  const sortResolutions = (resolutions: string[]) => {
    return resolutions.sort((a, b) => {
      const getResolutionValue = (res: string) => {
        if (res.includes('2160')) return 2160
        if (res.includes('1440')) return 1440
        if (res.includes('1080')) return 1080
        if (res.includes('720')) return 720
        if (res.includes('480')) return 480
        if (res.includes('360')) return 360
        if (res.includes('240')) return 240
        if (res.includes('144')) return 144
        return 0
      }
      return getResolutionValue(b) - getResolutionValue(a)
    })
  }

  const getFormatIcon = (ext: string) => {
    const extension = ext.toLowerCase()
    if (['mp4', 'avi', 'mkv', 'webm'].includes(extension)) {
      return <FileVideo className="w-4 h-4" />
    }
    if (['mp3', 'm4a', 'webm', 'opus', 'aac'].includes(extension)) {
      return <FileAudio className="w-4 h-4" />
    }
    return <Play className="w-4 h-4" />
  }

  // Theme-aware colors
  const getThemeColors = () => {
    if (isDarkMode) {
      return {
        bg: '#1a1a1a',
        text: '#e2e8f0',
        textSecondary: '#94a3b8',
        textMuted: '#64748b',
        cardBg: '#0f172a',
        cardBorder: '#334155',
        cardBorderHover: '#475569',
        cardHoverBg: '#1e293b',
        uploadAreaBg: '#0f172a',
        uploadAreaBorder: '#334155',
        uploadAreaBorderHover: '#475569',
        uploadAreaHoverBg: '#1e293b',
        inputBg: '#1e293b',
        inputBorder: '#334155',
        inputFocus: '#cbd5e1',
        errorBg: '#1f2937',
        errorBorder: '#ef4444',
        errorText: '#fca5a5'
      }
    }
    return {
      bg: '#ffffff',
      text: '#2c3e50',
      textSecondary: '#5a6c7d',
      textMuted: '#64748b',
      cardBg: '#f8fafc',
      cardBorder: '#bdc9d7',
      cardBorderHover: '#8fa3b3',
      cardHoverBg: '#f1f5f9',
      uploadAreaBg: '#f8fafc',
      uploadAreaBorder: '#bdc9d7',
      uploadAreaBorderHover: '#8fa3b3',
      uploadAreaHoverBg: '#f1f5f9',
      inputBg: '#ffffff',
      inputBorder: '#bdc9d7',
      inputFocus: '#334155',
      errorBg: '#fef2f2',
      errorBorder: '#fca5a5',
      errorText: '#dc2626'
    }
  }

  const colors = getThemeColors()

  const FormatCard = ({ format }: { format: Format }) => {
    const isDownloading = downloadingFormats.has(format.format_id)
    
    return (
      <div 
        className="border-2 rounded-2xl p-8 text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(44,62,80,0.12)] shadow-[0_4px_20px_rgba(44,62,80,0.08)]"
        style={{
          backgroundColor: colors.cardBg,
          borderColor: colors.cardBorder,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = colors.cardBorderHover
          e.currentTarget.style.backgroundColor = colors.cardHoverBg
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = colors.cardBorder
          e.currentTarget.style.backgroundColor = colors.cardBg
        }}
      >
        {/* Format Type and ID */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="flex items-center gap-2">
            {getFormatIcon(format.ext)}
            <span className="font-semibold text-lg" style={{ color: colors.text }}>
              {format.ext?.toUpperCase()}
            </span>
          </div>
          <span 
            className="text-xs px-3 py-1 rounded-full font-mono"
            style={{ 
              backgroundColor: isDarkMode ? '#374151' : '#e2e8f0',
              color: colors.textMuted 
            }}
          >
            {format.format_id}
          </span>
        </div>

        {/* Quality Badge */}
        {format.resolution && format.resolution !== 'audio only' && (
          <div className="mb-6">
            <span className="inline-block bg-[#334155] text-white px-4 py-2 rounded-2xl text-sm font-medium">
              {format.resolution}
            </span>
          </div>
        )}

        {/* Details */}
        <div className="space-y-3 mb-8" style={{ color: colors.textSecondary }}>
          {format.filesize && (
            <div className="flex justify-between items-center">
              <span className="text-sm">Size:</span>
              <span className="font-medium" style={{ color: colors.text }}>{formatFileSize(format.filesize)}</span>
            </div>
          )}
          
          {format.fps && (
            <div className="flex justify-between items-center">
              <span className="text-sm">FPS:</span>
              <span className="font-medium" style={{ color: colors.text }}>{format.fps}</span>
            </div>
          )}

          {format.vcodec && format.vcodec !== 'none' && (
            <div className="flex justify-between items-center">
              <span className="text-sm">Video:</span>
              <span className="font-medium text-xs" style={{ color: colors.text }}>{format.vcodec}</span>
            </div>
          )}

          {format.acodec && format.acodec !== 'none' && (
            <div className="flex justify-between items-center">
              <span className="text-sm">Audio:</span>
              <span className="font-medium text-xs" style={{ color: colors.text }}>{format.acodec}</span>
            </div>
          )}

          {format.format_note && (
            <div className="text-xs mt-4 opacity-80" style={{ color: colors.textMuted }}>
              {format.format_note}
            </div>
          )}
        </div>

        {/* Download Button */}
        <button
          onClick={() => handleDownload(format.format_id, format.resolution || '', format.ext)}
          disabled={isDownloading}
          className={`
            w-full py-4 px-6 rounded-2xl font-bold text-lg tracking-wide transition-all duration-300 relative overflow-hidden
            ${isDownloading 
              ? 'cursor-not-allowed' 
              : 'hover:-translate-y-1 hover:shadow-[0_15px_35px_rgba(51,65,85,0.35)] shadow-[0_8px_25px_rgba(51,65,85,0.25)]'
            }
          `}
          style={{ 
            fontFamily: 'Bangers, cursive',
            backgroundColor: isDownloading ? (isDarkMode ? '#374151' : '#cbd5e1') : '#334155',
            color: isDownloading ? (isDarkMode ? '#6b7280' : '#94a3b8') : 'white'
          }}
          onMouseEnter={(e) => {
            if (!isDownloading) {
              e.currentTarget.style.backgroundColor = '#1e293b'
            }
          }}
          onMouseLeave={(e) => {
            if (!isDownloading) {
              e.currentTarget.style.backgroundColor = '#334155'
            }
          }}
        >
          <span className="relative z-10 flex items-center justify-center gap-2">
            {isDownloading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                DOWNLOADING...
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                DOWNLOAD
              </>
            )}
          </span>
          {!isDownloading && (
            <div className="absolute top-0 left-[-100%] w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-left duration-500 hover:left-[100%]"></div>
          )}
        </button>
      </div>
    )
  }

  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link href="https://fonts.googleapis.com/css2?family=Bangers&family=Lato:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      
      <div 
        className="min-h-screen overflow-x-hidden transition-colors duration-300" 
        style={{ 
          fontFamily: 'Lato, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', 
          lineHeight: '1.6',
          backgroundColor: colors.bg,
          color: colors.text
        }}
      >
        {/* Theme Toggle */}
        <div className="fixed top-6 right-6 z-50">
          <button
            onClick={toggleTheme}
            className="p-3 rounded-full transition-all duration-300 hover:scale-110 shadow-lg"
            style={{
              backgroundColor: colors.cardBg,
              borderColor: colors.cardBorder,
              color: colors.text
            }}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
          </button>
        </div>

        <div className="max-w-[1000px] mx-auto px-10 py-15 min-h-screen flex flex-col justify-center">
          
          {/* Header */}
          <div className="text-center mb-20 opacity-0 animate-[fadeInUp_1s_ease_0.2s_forwards]">
            <div className="flex items-center justify-center gap-4 mb-8">
              <Youtube className="w-12 h-12 text-red-600 opacity-0 animate-[fadeInUp_1s_ease_0.1s_forwards] hover:-translate-y-0.5 hover:scale-105 transition-all duration-300 filter drop-shadow-[0_4px_20px_rgba(44,62,80,0.15)]" />
            </div>
            <h1 className="text-[4.5rem] mb-5 tracking-[3px] relative" style={{ fontFamily: 'Bangers, cursive', color: colors.text }}>
              DEBU TUBE
            </h1>
            <p className="text-xl font-normal mb-0" style={{ color: colors.textSecondary }}>
              Download any YouTube video in the format you want
            </p>
          </div>

          {/* URL Input Section */}
          <div className="mb-15 opacity-0 animate-[fadeInUp_1s_ease_0.4s_forwards]">
            <div 
              className="border-2 border-dashed rounded-2xl p-15 text-center transition-all duration-300 cursor-pointer w-full mb-10 relative shadow-[0_4px_20px_rgba(44,62,80,0.08)] hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(44,62,80,0.12)]"
              style={{
                backgroundColor: colors.uploadAreaBg,
                borderColor: colors.uploadAreaBorder,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = colors.uploadAreaBorderHover
                e.currentTarget.style.backgroundColor = colors.uploadAreaHoverBg
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = colors.uploadAreaBorder
                e.currentTarget.style.backgroundColor = colors.uploadAreaBg
              }}
            >
              <div className="text-6xl mb-6 transition-all duration-300 hover:scale-110" style={{ color: isDarkMode ? '#64748b' : '#8fa3b3' }}>
                🎥
              </div>
              <div className="text-2xl mb-3 font-medium transition-colors duration-300" style={{ color: colors.text }}>
                {url ? `URL: ${url.substring(0, 50)}${url.length > 50 ? '...' : ''}` : 'Paste your YouTube URL here'}
              </div>
              <div className="text-base font-normal" style={{ color: colors.textMuted }}>
                Supports all YouTube video URLs • Get all available formats
              </div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full mt-6 px-4 py-4 border rounded-xl text-lg focus:outline-none transition-all duration-300"
                style={{
                  backgroundColor: colors.inputBg,
                  borderColor: colors.inputBorder,
                  color: colors.text
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = colors.inputFocus
                  e.currentTarget.style.boxShadow = `0 0 0 3px rgba(51, 65, 85, 0.3)`
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = colors.inputBorder
                  e.currentTarget.style.boxShadow = 'none'
                }}
                onKeyPress={(e) => e.key === 'Enter' && handleGetFormats()}
              />
            </div>

            <button
              onClick={handleGetFormats}
              disabled={loading}
              className={`
                block mx-auto mb-12 py-5 px-12 rounded-2xl text-2xl tracking-wide cursor-pointer transition-all duration-300 min-w-[220px] relative overflow-hidden border-none
                ${loading 
                  ? 'cursor-not-allowed shadow-[0_4px_15px_rgba(203,213,225,0.3)]' 
                  : 'hover:-translate-y-1 hover:shadow-[0_15px_35px_rgba(51,65,85,0.35)] shadow-[0_8px_25px_rgba(51,65,85,0.25)]'
                }
              `}
              style={{ 
                fontFamily: 'Bangers, cursive',
                backgroundColor: loading ? (isDarkMode ? '#374151' : '#cbd5e1') : '#334155',
                color: loading ? (isDarkMode ? '#6b7280' : '#94a3b8') : 'white'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = '#1e293b'
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = '#334155'
                }
              }}
            >
              <span className="relative z-10 flex items-center justify-center gap-3">
                {loading ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    FETCHING FORMATS...
                  </>
                ) : (
                  <>
                    <Download className="w-6 h-6" />
                    GET FORMATS
                  </>
                )}
              </span>
              {!loading && (
                <div className="absolute top-0 left-[-100%] w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-left duration-500 hover:left-[100%]"></div>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div 
              className="mx-auto mb-12 p-8 rounded-2xl text-center opacity-0 animate-[fadeInUp_0.5s_ease_forwards] border"
              style={{
                backgroundColor: colors.errorBg,
                borderColor: colors.errorBorder,
                color: colors.errorText
              }}
            >
              <div className="flex items-center justify-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <span><strong>Error:</strong> {error}</span>
              </div>
            </div>
          )}

          {/* Video Information Section */}
          {videoInfo && (
            <div 
              className="mb-16 opacity-0 animate-[fadeInUp_0.5s_ease_forwards] rounded-3xl overflow-hidden shadow-[0_8px_32px_rgba(44,62,80,0.15)]"
              style={{
                backgroundColor: colors.cardBg,
                borderColor: colors.cardBorder,
              }}
            >
              <div className="relative">
                {/* Thumbnail */}
                {videoInfo.thumbnail && (
                  <div className="relative h-64 overflow-hidden">
                    <img 
                      src={videoInfo.thumbnail} 
                      alt={videoInfo.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                  </div>
                )}
                
                {/* Video Info Content */}
                <div className="p-8">
                  {/* Title */}
                  <h2 className="text-3xl font-bold mb-4 leading-tight" style={{ color: colors.text }}>
                    {videoInfo.title}
                  </h2>

                  {/* Stats Row */}
                  <div className="flex flex-wrap gap-6 mb-6 text-sm" style={{ color: colors.textSecondary }}>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      <span>{videoInfo.channel}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      <span>{formatNumber(videoInfo.view_count)} views</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{formatNumber(videoInfo.like_count)} likes</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>{formatDuration(videoInfo.duration)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(videoInfo.upload_date)}</span>
                    </div>
                  </div>

                  {/* Description */}
                  {videoInfo.description && (
                    <div 
                      className="text-sm leading-relaxed max-h-32 overflow-hidden"
                      style={{ color: colors.textMuted }}
                    >
                      {videoInfo.description.slice(0, 300)}
                      {videoInfo.description.length > 300 && '...'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Formats Section */}
          {formats.length > 0 && (
            <div className="mb-12 opacity-0 animate-[fadeInUp_0.5s_ease_forwards]">
              {/* Tab Navigation */}
              <div className="flex justify-center mb-12 gap-4">
                <button
                  onClick={() => setActiveTab('video')}
                  className={`
                    flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-lg tracking-wide transition-all duration-300
                    ${activeTab === 'video'
                      ? 'bg-[#334155] text-white shadow-[0_8px_25px_rgba(51,65,85,0.25)]'
                      : 'border-2 hover:-translate-y-0.5'
                    }
                  `}
                  style={{ 
                    fontFamily: 'Bangers, cursive',
                    ...(activeTab !== 'video' && {
                      backgroundColor: colors.cardBg,
                      color: colors.text,
                      borderColor: colors.cardBorder
                    })
                  }}
                  onMouseEnter={(e) => {
                    if (activeTab !== 'video') {
                      e.currentTarget.style.borderColor = colors.cardBorderHover
                      e.currentTarget.style.backgroundColor = colors.cardHoverBg
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeTab !== 'video') {
                      e.currentTarget.style.borderColor = colors.cardBorder
                      e.currentTarget.style.backgroundColor = colors.cardBg
                    }
                  }}
                >
                  <Film className="w-5 h-5" />
                  VIDEO FORMATS
                  <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                    {videoFormats.length}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('audio')}
                  className={`
                    flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-lg tracking-wide transition-all duration-300
                    ${activeTab === 'audio'
                      ? 'bg-[#059669] text-white shadow-[0_8px_25px_rgba(5,150,105,0.25)]'
                      : 'border-2 hover:-translate-y-0.5'
                    }
                  `}
                  style={{ 
                    fontFamily: 'Bangers, cursive',
                    ...(activeTab !== 'audio' && {
                      backgroundColor: colors.cardBg,
                      color: colors.text,
                      borderColor: colors.cardBorder
                    })
                  }}
                  onMouseEnter={(e) => {
                    if (activeTab !== 'audio') {
                      e.currentTarget.style.borderColor = colors.cardBorderHover
                      e.currentTarget.style.backgroundColor = colors.cardHoverBg
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeTab !== 'audio') {
                      e.currentTarget.style.borderColor = colors.cardBorder
                      e.currentTarget.style.backgroundColor = colors.cardBg
                    }
                  }}
                >
                  <Music className="w-5 h-5" />
                  AUDIO ONLY
                  <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                    {audioFormats.length}
                  </span>
                </button>
              </div>

              {/* Format Type Selectors */}
              {activeTab === 'video' && availableVideoFormats.length > 0 && (
                <div className="mb-12">
                  <h3 className="text-2xl font-semibold mb-6 text-center" style={{ color: colors.text }}>Select Format Type:</h3>
                  <div className="flex justify-center gap-4 flex-wrap">
                    {availableVideoFormats.map(format => (
                      <button
                        key={format}
                        onClick={() => setActiveVideoFormat(format)}
                        className={`
                          flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-300 border
                          ${activeVideoFormat === format
                            ? 'bg-[#334155] text-white shadow-lg'
                            : ''
                          }
                        `}
                        style={{
                          ...(activeVideoFormat !== format && {
                            backgroundColor: colors.cardBg,
                            color: colors.text,
                            borderColor: colors.cardBorder
                          })
                        }}
                        onMouseEnter={(e) => {
                          if (activeVideoFormat !== format) {
                            e.currentTarget.style.borderColor = colors.cardBorderHover
                            e.currentTarget.style.backgroundColor = colors.cardHoverBg
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (activeVideoFormat !== format) {
                            e.currentTarget.style.borderColor = colors.cardBorder
                            e.currentTarget.style.backgroundColor = colors.cardBg
                          }
                        }}
                      >
                        {getFormatIcon(format)}
                        {format.toUpperCase()}
                        <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                          {Object.keys(groupedVideoFormats[format]).length}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'audio' && availableAudioFormats.length > 0 && (
                <div className="mb-12">
                  <h3 className="text-2xl font-semibold mb-6 text-center" style={{ color: colors.text }}>Select Audio Format:</h3>
                  <div className="flex justify-center gap-4 flex-wrap">
                    {availableAudioFormats.map(format => (
                      <button
                        key={format}
                        onClick={() => setActiveAudioFormat(format)}
                        className={`
                          flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-300 border
                          ${activeAudioFormat === format
                            ? 'bg-[#059669] text-white shadow-lg'
                            : ''
                          }
                        `}
                        style={{
                          ...(activeAudioFormat !== format && {
                            backgroundColor: colors.cardBg,
                            color: colors.text,
                            borderColor: colors.cardBorder
                          })
                        }}
                        onMouseEnter={(e) => {
                          if (activeAudioFormat !== format) {
                            e.currentTarget.style.borderColor = colors.cardBorderHover
                            e.currentTarget.style.backgroundColor = colors.cardHoverBg
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (activeAudioFormat !== format) {
                            e.currentTarget.style.borderColor = colors.cardBorder
                            e.currentTarget.style.backgroundColor = colors.cardBg
                          }
                        }}
                      >
                        {getFormatIcon(format)}
                        {format.toUpperCase()}
                        <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm">
                          {groupedAudioFormats[format].length}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Content */}
              {activeTab === 'video' && activeVideoFormat && groupedVideoFormats[activeVideoFormat] && (
                <div className="space-y-16">
                  {sortResolutions(Object.keys(groupedVideoFormats[activeVideoFormat])).map(resolution => (
                    <div key={resolution}>
                      <h4 className="text-3xl font-bold mb-8 text-center" style={{ fontFamily: 'Bangers, cursive', color: colors.text }}>
                        {resolution} - {activeVideoFormat.toUpperCase()}
                      </h4>
                      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                        {groupedVideoFormats[activeVideoFormat][resolution].map(format => (
                          <FormatCard key={format.format_id} format={format} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'audio' && activeAudioFormat && groupedAudioFormats[activeAudioFormat] && (
                <div>
                  <h4 className="text-3xl font-bold mb-8 text-center" style={{ fontFamily: 'Bangers, cursive', color: colors.text }}>
                    {activeAudioFormat.toUpperCase()} AUDIO FILES
                  </h4>
                  <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                    {groupedAudioFormats[activeAudioFormat].map(format => (
                      <FormatCard key={format.format_id} format={format} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="text-center mt-16">
            <p className="text-sm opacity-80" style={{ color: colors.textMuted }}>
              DebuTube - Debu
            </p>
          </div>
        </div>

        <style jsx>{`
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(30px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}</style>
      </div>
    </>
  )
} 