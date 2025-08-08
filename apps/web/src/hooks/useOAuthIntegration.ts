/**
 * OAuth integration hooks for NeuroSync
 * Provides hooks for OAuth-based integration connection
 */

import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  integrationApi,
  Integration,
  IntegrationApiError,
  OAuthStartRequest,
  OAuthCompleteRequest,
  IntegrationConfig
} from '../lib/api/integrations'

/**
 * Hook for OAuth-based integration connection
 * Supports connecting integrations without requiring manual token entry
 */
export function useOAuthIntegration(projectId?: string | null) {
  const queryClient = useQueryClient()
  const [authWindows, setAuthWindows] = useState<Record<string, Window | null>>({})
  
  // Start OAuth flow mutation
  const startOAuthMutation = useMutation({
    mutationFn: async (integrationType: string) => {
      // For new project flow, we might not have a project ID yet
      if (!projectId) {
        // Store the integration type in session storage to be used after project creation
        sessionStorage.setItem('pendingOAuthIntegrationType', integrationType)
        
        // Return a placeholder for now - this will be handled differently in new project flow
        return {
          auth_url: '#pending-project-creation',
          state: 'pending-project-creation'
        }
      }
      
      return integrationApi.startOAuthFlow(
        projectId, 
        integrationType, 
        window.location.origin + '/oauth-callback'
      )
    },
    onSuccess: (data, integrationType) => {
      if (data.auth_url === '#pending-project-creation') {
        // This is a special case for new project flow - handled separately
        toast.success('Integration will be connected after project creation')
        return
      }
      
      // Open OAuth window
      const authWindow = window.open(
        data.auth_url,
        `oauth-${integrationType}`,
        'width=600,height=800,menubar=no'
      )
      
      if (!authWindow) {
        toast.error('Could not open authorization window. Please check your popup blocker settings.')
        return
      }
      
      // Store window reference
      setAuthWindows(prev => ({
        ...prev,
        [integrationType]: authWindow
      }))
      
      // Poll for window closure
      const pollTimer = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(pollTimer)
          
          // Check if integration was successful by querying the integrations list
          if (projectId) {
            queryClient.invalidateQueries({ queryKey: ['integrations', projectId] })
          }
          
          // Remove window reference
          setAuthWindows(prev => {
            const newState = { ...prev }
            delete newState[integrationType]
            return newState
          })
        }
      }, 500)
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to start OAuth flow')
    }
  })
  
  // Complete OAuth flow (typically called by a redirect handler)
  const completeOAuthMutation = useMutation({
    mutationFn: (params: OAuthCompleteRequest) => {
      if (!projectId) {
        throw new Error('Project ID is required to complete OAuth flow')
      }
      return integrationApi.completeOAuthFlow(projectId, params.code, params.state)
    },
    onSuccess: (result: { access_token: string; integration_config: IntegrationConfig }) => {
      // Create a synthetic integration object since the API returns token + config
      const integration: Integration = {
        id: crypto.randomUUID(),
        project_id: projectId || '',
        type: result.integration_config.type as any,
        name: result.integration_config.name || 'New Integration',
        status: 'connected',
        config: result.integration_config,
        last_sync: null,
        sync_status: 'idle',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        stats: {
          total_documents: 0,
          last_sync_documents: 0,
          indexed_documents: 0
        },
        oauth_connected: true
      };
      // Update integrations list
      queryClient.setQueryData(['integrations', projectId], (old: Integration[] = []) => {
        // If integration already exists, replace it with new integration data
        const exists = old.some(i => 
          i.type === integration.type && 
          i.project_id === integration.project_id
        )
        
        if (exists) {
          return old.map(i => {
            if (i.type === integration.type && i.project_id === integration.project_id) {
              return integration
            }
            return i
          })
        }
        
        // Otherwise add it as a new integration
        return [...old, integration]
      })
      
      toast.success(`${integration.name} connected successfully!`)
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to complete OAuth connection')
    }
  })

  // Helper to close auth window
  const closeAuthWindow = useCallback((integrationType: string) => {
    const window = authWindows[integrationType]
    if (window && !window.closed) {
      window.close()
    }
    
    setAuthWindows(prev => {
      const newState = { ...prev }
      delete newState[integrationType]
      return newState
    })
  }, [authWindows])
  
  // Start OAuth flow
  const startOAuth = useCallback((integrationType: string) => {
    startOAuthMutation.mutate(integrationType)
  }, [startOAuthMutation])
  
  // Get stored OAuth integration type (for new project flow)
  const getPendingOAuthIntegrationType = useCallback(() => {
    const type = sessionStorage.getItem('pendingOAuthIntegrationType')
    if (type) {
      sessionStorage.removeItem('pendingOAuthIntegrationType')
    }
    return type
  }, [])
  
  // Handle OAuth completion with newly created project ID
  const completeOAuthWithNewProject = useCallback((newProjectId: string) => {
    const integrationType = getPendingOAuthIntegrationType()
    if (integrationType) {
      // Start OAuth flow with the new project ID
      integrationApi.startOAuthFlow(
        newProjectId, 
        integrationType,
        window.location.origin + '/oauth-callback'
      ).then(data => {
        const authWindow = window.open(
          data.auth_url,
          `oauth-${integrationType}`,
          'width=600,height=800,menubar=no'
        )
        
        if (!authWindow) {
          toast.error('Could not open authorization window. Please check your popup blocker settings.')
        }
      }).catch(error => {
        toast.error('Failed to connect integration: ' + (error.message || ''))
      })
    }
  }, [getPendingOAuthIntegrationType])
  
  return {
    startOAuth,
    completeOAuth: completeOAuthMutation.mutate,
    completeOAuthWithNewProject,
    getPendingOAuthIntegrationType,
    closeAuthWindow,
    isAuthenticating: startOAuthMutation.isPending,
    isAuthWindows: authWindows
  }
}
