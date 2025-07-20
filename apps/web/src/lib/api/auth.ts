/**
 * Authentication API client for NeuroSync
 * Handles user registration, login, profile management
 */

import { AuthTokens, User } from '../auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface RegisterRequest {
  email: string
  password: string
  subscription_tier?: 'starter' | 'professional' | 'enterprise'
  metadata?: Record<string, any>
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface ResetPasswordRequest {
  email: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface UpdateProfileRequest {
  name?: string
  email?: string
}

export interface ApiError {
  detail: string
  code?: string
}

export interface AuthResponse {
  status: string
  user_id: string
  email: string
  subscription_tier: string
  access_token: string
  refresh_token: string
  token_type: string
  expires_in?: number
}

class AuthApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'AuthApiError'
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    let errorCode: string | undefined

    try {
      const errorData: ApiError = await response.json()
      errorMessage = errorData.detail || errorMessage
      errorCode = errorData.code
    } catch {
      // If we can't parse error JSON, use status text
      errorMessage = response.statusText || errorMessage
    }

    throw new AuthApiError(errorMessage, response.status, errorCode)
  }

  return response.json()
}

export class AuthApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result: AuthResponse = await handleApiResponse(response)
    
    return {
      user: {
        id: result.user_id,
        email: result.email,
        subscription_tier: result.subscription_tier as any,
        created_at: new Date().toISOString(),
        is_active: true
      },
      tokens: {
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        token_type: result.token_type,
        expires_in: result.expires_in || 1800
      }
    }
  }

  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result: AuthResponse = await handleApiResponse(response)
    
    return {
      user: {
        id: result.user_id,
        email: result.email,
        subscription_tier: result.subscription_tier as any,
        created_at: new Date().toISOString(),
        is_active: true
      },
      tokens: {
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        token_type: result.token_type,
        expires_in: result.expires_in || 1800
      }
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    const result = await handleApiResponse<{ access_token: string; token_type: string }>(response)
    
    return {
      access_token: result.access_token,
      refresh_token: refreshToken, // Keep the same refresh token
      token_type: result.token_type,
      expires_in: 1800
    }
  }

  /**
   * Get user profile
   */
  async getProfile(accessToken: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    })

    const result = await handleApiResponse<any>(response)
    
    return {
      id: result.user_id,
      email: result.email,
      subscription_tier: result.subscription_tier,
      created_at: result.created_at,
      is_active: result.is_active
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(
    accessToken: string,
    data: UpdateProfileRequest
  ): Promise<User> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: ResetPasswordRequest): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Change password
   */
  async changePassword(
    accessToken: string,
    data: ChangePasswordRequest
  ): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/change-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Get token usage information
   */
  async getTokenUsage(accessToken: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/tokens/usage`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }
}

// Export singleton instance
export const authApi = new AuthApi()
