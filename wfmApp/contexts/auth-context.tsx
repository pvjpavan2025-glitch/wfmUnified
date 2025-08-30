'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { authService, type User, type LoginCredentials } from '../lib/auth-service'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already authenticated on app startup
    const checkAuth = async () => {
      try {
        const token = authService.getToken();
        if (token) {
          try {
            const isValid = await authService.verifyToken();
            if (isValid) {
              // Token is valid, set a mock user for development
              const mockUser: User = {
                id: 'authenticated-user',
                username: 'testuser',
                email: 'test@wfm.local',
                first_name: 'Test',
                last_name: 'User',
                roles: ['SuperAdmin']
              };
              setUser(mockUser);
              setIsLoading(false);
            } else {
              authService.logout();
              setIsLoading(false);
            }
          } catch (verifyError) {
            console.error('Token verification failed:', verifyError);
            // If token verification fails, clear the token and continue
            authService.logout();
            setIsLoading(false);
          }
        } else {
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        authService.logout();
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const getDefaultRoute = (roles: string[]): string => {
    if (roles.includes('SuperAdmin') || roles.includes('Admin')) {
      return '/dashboard';
    } else if (roles.includes('Vendor')) {
      return '/dashboard';
    } else if (roles.includes('Technician')) {
      return '/dashboard';
    } else if (roles.includes('Demo')) {
      return '/dashboard';
    }
    return '/dashboard';
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    
    try {
      console.log('AuthContext: Attempting login...');
      const response = await authService.login({ username, password });
      console.log('AuthContext: Login successful, user:', response.user);
      console.log('AuthContext: Token stored:', !!authService.getToken());
      console.log('AuthContext: Token value from authService:', authService.getToken());
      
      setUser(response.user);
      
      // Redirect to the appropriate dashboard
      const defaultRoute = getDefaultRoute(response.user.roles);
      console.log('AuthContext: Redirecting to:', defaultRoute);
      router.push(defaultRoute);
      
      return true;
    } catch (error: any) {
      console.error('AuthContext: Login failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }

  const logout = () => {
    authService.logout();
    setUser(null);
    router.push('/login');
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
