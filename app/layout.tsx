import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DebuTube by Debu',
  description: 'Simple YouTube downloader. Just paste a link and download your video.',
  keywords: ['youtube', 'downloader', 'video', 'debutube'],
  authors: [{ name: 'Debu' }],
  icons: {
    icon: '/logo1.png',
    shortcut: '/logo1.png',
    apple: '/logo1.png',
  },
  openGraph: {
    title: 'DebuTube by Debu',
    description: 'Simple YouTube downloader. Just paste a link and download your video.',
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