// API Configuration for Next.js
export const API_CONFIG = {
  // Backend service URLs
  AUTH_SERVICE: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8001',
  API_GATEWAY: process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000',
  
  // Service endpoints
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      VERIFY: '/auth/verify',
      REFRESH: '/auth/refresh',
    },
    USERS: {
      LIST: '/users',
      CREATE: '/users',
      GET: (id: string) => `/users/${id}`,
      UPDATE: (id: string) => `/users/${id}`,
      DELETE: (id: string) => `/users/${id}`,
    },
    ROLES: {
      LIST: '/roles',
      CREATE: '/roles',
      GET: (id: string) => `/roles/${id}`,
      UPDATE: (id: string) => `/roles/${id}`,
      DELETE: (id: string) => `/roles/${id}`,
    },
    TENANTS: {
      LIST: '/tenants',
      CREATE: '/tenants',
      GET: (id: string) => `/tenants/${id}`,
      UPDATE: (id: string) => `/tenants/${id}`,
      DELETE: (id: string) => `/tenants/${id}`,
    },
  },
  
  // HTTP headers
  HEADERS: {
    CONTENT_TYPE: 'application/json',
    AUTHORIZATION: 'Bearer',
  },
  
  // Timeouts
  TIMEOUTS: {
    REQUEST: 30000, // 30 seconds
    AUTH_REFRESH: 5000, // 5 seconds
  },
};

// Environment-specific configuration
export const ENV_CONFIG = {
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',
};
