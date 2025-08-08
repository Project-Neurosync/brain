'use client'

/**
 * OAuth Callback Page
 * Handles the redirect from external OAuth providers and completes the OAuth flow
 */

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { integrationApi, IntegrationConfig } from '@/lib/api/integrations'
import { useLocalStorage } from '@/hooks/useLocalStorage'

interface OAuthCompleteResponse {
  access_token: string;
  integration_config: IntegrationConfig;
  integration_id: string;
  user_data: {
    username: string;
    name?: string;
    avatar_url?: string;
  };
}

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(true)
  const [pendingProjectId, setPendingProjectId] = useLocalStorage<string | null>('pendingProjectId', null)

  useEffect(() => {
    async function completeOAuth() {
      try {
        // Get the code and state from the URL
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const provider = searchParams.get('provider') || 'github'

        if (!code || !state) {
          setError('Missing required OAuth parameters')
          setIsProcessing(false)
          return
        }

        let result: OAuthCompleteResponse
        
        // We might be in one of two flows:
        // 1. From an existing project (pendingProjectId exists)
        // 2. During project creation (no pendingProjectId)
        if (pendingProjectId) {
          // Complete OAuth for existing project
          result = await integrationApi.completeOAuthFlow(
            pendingProjectId,
            code,
            state
          ) as OAuthCompleteResponse
        } else {
          // Complete OAuth without a project (for new project creation)
          result = await integrationApi.completeOAuthFlowWithoutProject(
            code,
            state,
            provider
          ) as OAuthCompleteResponse
        }

        // Don't clear the pending project ID until after we've redirected
        // We'll clear it after the redirect or message is sent
        const currentProjectId = pendingProjectId

        // Send success message to parent window
        if (window.opener) {
          window.opener.postMessage(
            { 
              type: 'oauth-success', 
              integration: provider,
              data: result,
              integration_id: result.integration_id, // Now properly typed
              status: 'connected'
            }, 
            window.location.origin
          )
          
          // Close this window after a short delay
          setTimeout(() => {
            // Clear the pending project ID before closing
            setPendingProjectId(null)
            window.close()
          }, 500)
        } else {
          // If window.opener is not available, redirect back
          const redirectPath = currentProjectId
            ? `/dashboard/projects/${currentProjectId}/integrations`
            : '/dashboard'
            
          // Clear the pendingProjectId after we've set up the redirect
          setPendingProjectId(null)
          
          // Redirect to the appropriate page
          router.push(redirectPath)
        }
      } catch (err: any) {
        console.error('OAuth completion error:', err)
        setError(err.message || 'Failed to complete OAuth process')
        
        // Send error to parent window if available
        if (window.opener) {
          window.opener.postMessage(
            { 
              type: 'oauth-error', 
              error: err.message || 'Authentication failed'
            }, 
            window.location.origin
          )
          
          // Close this window after a short delay
          setTimeout(() => {
            window.close()
          }, 1500)
        }
      } finally {
        setIsProcessing(false)
      }
    }

    completeOAuth()
  }, [searchParams, pendingProjectId, router, setPendingProjectId])

  // Simple UI for the callback page
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md rounded-lg border bg-white p-6 shadow-sm">
        <h1 className="mb-4 text-xl font-semibold text-gray-900">
          {isProcessing ? 'Completing Authentication...' : error ? 'Authentication Error' : 'Authentication Complete'}
        </h1>
        
        {isProcessing ? (
          <div className="flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-purple-500"></div>
            <p className="ml-2 text-gray-600">Processing your request...</p>
          </div>
        ) : error ? (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        ) : (
          <p className="text-green-600">
            Successfully authenticated! This window will close automatically.
          </p>
        )}
      </div>
    </div>
  )
}
