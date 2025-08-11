import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DebuTube - YouTube Format Downloader',
  description: 'Get direct download links for any YouTube video format',
  keywords: ['youtube', 'downloader', 'video', 'formats', 'direct link'],
  authors: [{ name: 'DebuTube' }],
  openGraph: {
    title: 'DebuTube - YouTube Format Downloader',
    description: 'Get direct download links for any YouTube video format',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
} 