import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DebuTube - Professional YouTube Downloader',
  description: 'Download any YouTube video in the format you want with beautiful interface and professional features',
  keywords: ['youtube', 'downloader', 'video', 'formats', 'professional', 'debutube'],
  authors: [{ name: 'DebuTube Team' }],
  icons: {
    icon: '/logo1.png',
    shortcut: '/logo1.png',
    apple: '/logo1.png',
  },
  openGraph: {
    title: 'DebuTube - Professional YouTube Downloader',
    description: 'Download any YouTube video in the format you want with beautiful interface and professional features',
    type: 'website',
    images: ['/logo.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/logo1.png" type="image/png" />
        <link rel="shortcut icon" href="/logo1.png" type="image/png" />
        <link rel="apple-touch-icon" href="/logo1.png" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
} 