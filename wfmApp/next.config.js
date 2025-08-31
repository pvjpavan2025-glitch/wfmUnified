/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Load environment variables based on NODE_ENV
    NEXT_PUBLIC_API_GATEWAY_URL: process.env.NODE_ENV === 'production' 
      ? 'http://localhost:8000'
      : process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000',
    NEXT_PUBLIC_PROCESS_ENGINE_URL: process.env.NODE_ENV === 'production'
      ? 'http://localhost:8100' 
      : process.env.NEXT_PUBLIC_PROCESS_ENGINE_URL || 'http://localhost:8100'
  },
  // Next.js 15+: use top-level serverExternalPackages instead of deprecated experimental.serverComponentsExternalPackages
  serverExternalPackages: ['bpmn-js']
}

module.exports = nextConfig
