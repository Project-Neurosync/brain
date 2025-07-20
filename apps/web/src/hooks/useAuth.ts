/**
 * Authentication hooks for NeuroSync
 * Provides React hooks for authentication state and operations
 */

import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { 
  authService, 
  User, 
  AuthTokens,
  isAuthenticated,
  getUser,
  logout as logoutHelper
} from '../lib/auth'
import { 
  authApi, 
  RegisterRequest, 
  LoginRequest, 
  UpdateProfileRequest,
  ChangePasswordRequest,
  ResetPasswordRequest
} from '../lib/api/auth'

// Simple error interface for API errors
interface ApiError {
  message?: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

/**
 * Main authentication hook
 * Provides current auth state and operations
 */
export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true
  })

  const queryClient = useQueryClient()

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = () => {
      const authenticated = isAuthenticated()
      const user = getUser()
      
      setAuthState({
        user,
        isAuthenticated: authenticated,
        isLoading: false
      })
    }

    initAuth()
  }, [])

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: ({ user, tokens }) => {
      authService.setTokens(tokens)
      authService.setUser(user)
      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false
      })
      toast.success('Account created successfully!')
      
      // Redirect to dashboard
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard'
      }
    },
    onError: (error: ApiError) => {
      toast.error(error.message || 'Registration failed')
    }
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: ({ user, tokens }) => {
      authService.setTokens(tokens)
      authService.setUser(user)
      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false
      })
      toast.success('Welcome back!')
      
      // Redirect to dashboard
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard'
      }
    },
    onError: (error: ApiError) => {
      toast.error(error.message || 'Login failed')
    }
  })

  // Logout function
  const logout = useCallback(async () => {
    try {
      // Clear tokens and user data
      // Note: logout API call removed as method may not exist
    } catch (error) {
      console.error('Logout API error:', error)
    } finally {
      authService.clearAuth()
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false
      })
      queryClient.clear()
      toast.success('Logged out successfully')
      logoutHelper()
    }
  }, [queryClient])

  // Token refresh function
  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = authService.getRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const tokens = await authApi.refreshToken(refreshToken)
      authService.setTokens(tokens)
      
      return tokens.access_token
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      throw error
    }
  }, [logout])

  return {
    ...authState,
    register: registerMutation.mutate,
    login: loginMutation.mutate,
    logout,
    refreshToken,
    isRegistering: registerMutation.isPending,
    isLoggingIn: loginMutation.isPending
  }
}

/**
 * Hook for user profile management
 */
export function useProfile() {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()

  // Get user profile query
  const profileQuery = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const token = authService.getAccessToken()
      if (!token) throw new Error('No access token')
      return authApi.getProfile(token)
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: UpdateProfileRequest) => {
      const token = authService.getAccessToken()
      if (!token) throw new Error('No access token')
      return authApi.updateProfile(token, data)
    },
    onSuccess: (updatedUser) => {
      authService.setUser(updatedUser)
      queryClient.setQueryData(['profile'], updatedUser)
      toast.success('Profile updated successfully!')
    },
    onError: (error: ApiError) => {
      toast.error(error.message || 'Failed to update profile')
    }
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: ChangePasswordRequest) => {
      const token = authService.getAccessToken()
      if (!token) throw new Error('No access token')
      return authApi.changePassword(token, data)
    },
    onSuccess: () => {
      toast.success('Password changed successfully!')
    },
    onError: (error: ApiError) => {
      toast.error(error.message || 'Failed to change password')
    }
  })

  return {
    user: profileQuery.data || user,
    isLoading: profileQuery.isLoading,
    error: profileQuery.error,
    updateProfile: updateProfileMutation.mutate,
    changePassword: changePasswordMutation.mutate,
    isUpdatingProfile: updateProfileMutation.isPending,
    isChangingPassword: changePasswordMutation.isPending,
    refetch: profileQuery.refetch
  }
}

/**
 * Hook for token usage tracking
 */
export function useTokenUsage() {
  const { isAuthenticated } = useAuth()

  const tokenUsageQuery = useQuery({
    queryKey: ['tokenUsage'],
    queryFn: async () => {
      const token = authService.getAccessToken()
      if (!token) throw new Error('No access token')
      return authApi.getTokenUsage(token)
    },
    enabled: isAuthenticated,
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
    staleTime: 10 * 1000, // Consider stale after 10 seconds
  })

  return {
    tokenUsage: tokenUsageQuery.data,
    isLoading: tokenUsageQuery.isLoading,
    error: tokenUsageQuery.error,
    refetch: tokenUsageQuery.refetch
  }
}

/**
 * Hook for protected routes
 * Redirects to login if not authenticated
 */
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
  }, [isAuthenticated, isLoading])

  return { isAuthenticated, isLoading }
}
