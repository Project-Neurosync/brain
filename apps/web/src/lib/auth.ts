/**
 * Authentication utilities for NeuroSync frontend
 * Handles JWT tokens, user sessions, and API authentication
 */

import { jwtDecode } from 'jwt-decode'

export interface User {
  id: string
  email: string
  name?: string
  current_project_id?: string
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
  private readonly USER_KEY = 'neurosync_user'
  private readonly TOKEN_KEY = 'neurosync_tokens' // For temp storage during login/logout processes

  /**
   * Store token data in memory temporarily
   * Note: Real JWT tokens are now handled by HTTP-only cookies set by the server
   */
  setTokens(tokens: AuthTokens): void {
    // With HTTP-only cookies, we don't need to store tokens in localStorage
    // But we'll keep this method for backwards compatibility
    if (typeof window === 'undefined') return
    // Store tokens temporarily in memory for the current session only
    this.tempTokens = tokens
  }

  // Temporary in-memory storage for tokens during login/logout
  private tempTokens: AuthTokens | null = null

  /**
   * Get access token (for backwards compatibility)
   * Note: With HTTP-only cookies, this is only used during the login process
   */
  getAccessToken(): string | null {
    // With HTTP-only cookies, we can't access the token directly
    // This is just for compatibility with existing code
    return this.tempTokens?.access_token || null
  }

  /**
   * Get refresh token (for backwards compatibility)
   * Note: With HTTP-only cookies, this is only used during the login process
   */
  getRefreshToken(): string | null {
    // With HTTP-only cookies, we can't access the token directly
    // This is just for compatibility with existing code
    return this.tempTokens?.refresh_token || null
  }

  /**
   * Store user data in localStorage
   * Note: JWT tokens are now handled by HTTP-only cookies set by the server
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
   * Remove all authentication data
   * Note: To clear HTTP-only cookies, we need to call the logout endpoint
   */
  clearAuth(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(this.USER_KEY)
    this.tempTokens = null
  }

  /**
   * Check if token is valid and not expired
   */
  isTokenValid(): boolean {
    try {
      // Since we're using HTTP-only cookies, we can't check token directly
      // Instead, we rely on user data existence and expiry checking via API
      const user = this.getUser()
      return !!user?.is_active
    } catch {
      return false
    }
  }

  /**
   * Get user from access token
   * Note: This is now a helper method for initial auth state
   * Real authentication is managed by HTTP-only cookies
   */
  getUserFromToken(): User | null {
    // Return stored user data
    return this.getUser()
  }
}

// Export singleton instance
export const authService = new AuthService()

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return authService.isTokenValid()
}

/**
 * Get current user
 */
export function getUser(): User | null {
  return authService.getUser()
}

/**
 * Logout user
 */
export function logout(): void {
  // Call logout API to clear HTTP-only cookies
  fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include',
  }).finally(() => {
    authService.clearAuth()
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  })
}

/**
 * Get auth headers for API requests
 * Note: No longer needed for endpoints that use HTTP-only cookies
 * Only needed for external API calls that require token in header
 */
export function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  }
}
