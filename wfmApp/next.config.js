/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Load environment variables based on NODE_ENV
    NEXT_PUBLIC_API_GATEWAY_URL: process.env.NODE_ENV === 'production' 
      ? 'https://wfm-unified-apim.azure-api.net/api/v1'
      : process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000',
    NEXT_PUBLIC_PROCESS_ENGINE_URL: process.env.NODE_ENV === 'production'
      ? 'https://wfm-unified-apim.azure-api.net/process/v1' 
      : process.env.NEXT_PUBLIC_PROCESS_ENGINE_URL || 'http://localhost:8100'
  },
  experimental: {
    serverComponentsExternalPackages: ['bpmn-js']
  }
}

module.exports = nextConfig
