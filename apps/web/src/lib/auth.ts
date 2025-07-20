/**
 * Authentication utilities for NeuroSync frontend
 * Handles JWT tokens, user sessions, and API authentication
 */

import { jwtDecode } from 'jwt-decode'

export interface User {
  id: string
  email: string
  name?: string
  subscription_tier: 'starter' | 'professional' | 'enterprise'
  tokens_remaining?: number
  tokens_total?: number
  created_at: string
  is_active: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface JWTPayload {
  sub: string // user_id
  email: string
  name: string
  subscription_tier: string
  exp: number
  iat: number
}

class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'neurosync_access_token'
  private readonly REFRESH_TOKEN_KEY = 'neurosync_refresh_token'
  private readonly USER_KEY = 'neurosync_user'

  /**
   * Store authentication tokens in localStorage
   */
  setTokens(tokens: AuthTokens): void {
    if (typeof window === 'undefined') return
    
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh_token)
  }

  /**
   * Get access token from localStorage
   */
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.ACCESS_TOKEN_KEY)
  }

  /**
   * Get refresh token from localStorage
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  /**
   * Remove all authentication data
   */
  clearAuth(): void {
    if (typeof window === 'undefined') return
    
    localStorage.removeItem(this.ACCESS_TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
    localStorage.removeItem(this.USER_KEY)
  }

  /**
   * Store user data in localStorage
   */
  setUser(user: User): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(this.USER_KEY, JSON.stringify(user))
  }

  /**
   * Get user data from localStorage
   */
  getUser(): User | null {
    if (typeof window === 'undefined') return null
    
    const userData = localStorage.getItem(this.USER_KEY)
    if (!userData) return null
    
    try {
      return JSON.parse(userData)
    } catch {
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getAccessToken()
    if (!token) return false

    try {
      const payload = jwtDecode<JWTPayload>(token)
      const now = Date.now() / 1000
      return payload.exp > now
    } catch {
      return false
    }
  }

  /**
   * Get user data from JWT token
   */
  getUserFromToken(): User | null {
    const token = this.getAccessToken()
    if (!token) return null

    try {
      const payload = jwtDecode<JWTPayload>(token)
      const now = Date.now() / 1000
      
      if (payload.exp <= now) {
        this.clearAuth()
        return null
      }

      return {
        id: payload.sub,
        email: payload.email,
        name: payload.name,
        subscription_tier: payload.subscription_tier as User['subscription_tier'],
        tokens_remaining: 0, // Will be fetched from API
        tokens_total: 0, // Will be fetched from API
        created_at: new Date(payload.iat * 1000).toISOString(),
        is_active: true
      }
    } catch {
      this.clearAuth()
      return null
    }
  }

  /**
   * Get authorization header for API requests
   */
  getAuthHeader(): Record<string, string> {
    const token = this.getAccessToken()
    if (!token) return {}
    
    return {
      'Authorization': `Bearer ${token}`
    }
  }

  /**
   * Check if token needs refresh (expires in less than 5 minutes)
   */
  needsRefresh(): boolean {
    const token = this.getAccessToken()
    if (!token) return false

    try {
      const payload = jwtDecode<JWTPayload>(token)
      const now = Date.now() / 1000
      const fiveMinutes = 5 * 60
      
      return payload.exp - now < fiveMinutes
    } catch {
      return true
    }
  }
}

// Export singleton instance
export const authService = new AuthService()

// Helper functions for common operations
export const isAuthenticated = () => authService.isAuthenticated()
export const getUser = () => authService.getUser() || authService.getUserFromToken()
export const logout = () => {
  authService.clearAuth()
  // Redirect to login page
  if (typeof window !== 'undefined') {
    window.location.href = '/login'
  }
}

export const getAuthHeaders = () => authService.getAuthHeader()
