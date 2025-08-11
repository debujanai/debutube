/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['yt-dlp-wrap']
  },
  env: {
    CUSTOM_KEY: 'my-value',
  },
}

module.exports = nextConfig 