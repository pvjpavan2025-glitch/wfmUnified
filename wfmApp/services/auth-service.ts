export interface User {
  id: string
  username: string
  email: string
  roles: string[]
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  user: User
  token: string
}

class AuthService {
  private readonly API_BASE_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000'

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await fetch(`${this.API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    const data = await response.json()
    
    // Store the token
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token)
    }

    return {
      user: {
        id: data.user_id || '1',
        username: credentials.username,
        email: data.email || `${credentials.username}@example.com`,
        roles: data.roles || ['User']
      },
      token: data.access_token
    }
  }

  async verifyToken(): Promise<boolean> {
    const token = this.getToken()
    if (!token) return false

    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/verify`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      return response.ok
    } catch {
      return false
    }
  }

  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
  }
}

export const authService = new AuthService()
