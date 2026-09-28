/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['ytdlp-nodejs'],
    outputFileTracingIncludes: {
      '/api/formats': ['./node_modules/ytdlp-nodejs/bin/**/*'],
      '/api/direct-url': ['./node_modules/ytdlp-nodejs/bin/**/*'],
      '/api/download': ['./node_modules/ytdlp-nodejs/bin/**/*'],
    },
  },
  env: {
    CUSTOM_KEY: 'my-value',
  },
}

module.exports = nextConfig 