/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@chainsync/core'],
  experimental: {
    serverComponentsExternalPackages: [],
  },
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig