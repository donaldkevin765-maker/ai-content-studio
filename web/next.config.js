/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://sistema-video-ai.vercel.app/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
