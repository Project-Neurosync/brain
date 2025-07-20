'use client'

import { useEffect } from 'react'
import { useRequireAuth } from '@/hooks/useAuth'
import { Brain } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useRequireAuth()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Brain className="h-12 w-12 text-purple-600 animate-pulse" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading NeuroSync</h2>
          <p className="text-gray-600">Verifying your authentication...</p>
          <div className="mt-4">
            <div className="w-8 h-8 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto"></div>
          </div>
        </div>
      </div>
    )
  }

  // If not authenticated, useRequireAuth will handle redirect
  if (!isAuthenticated) {
    return null
  }

  // Render protected content
  return <>{children}</>
}
