/**
 * Integration hooks for NeuroSync
 * Provides React hooks for integration management, syncing, and data source browsing
 */

import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  integrationApi,
  Integration,
  ConnectIntegrationRequest,
  UpdateIntegrationRequest,
  SyncResult,
  DataSource,
  IntegrationApiError
} from '../lib/api/integrations'

/**
 * Hook to get all integrations for a project
 */
export function useIntegrations(projectId: string | undefined) {
  const integrationsQuery = useQuery({
    queryKey: ['integrations', projectId],
    queryFn: () => integrationApi.getIntegrations(projectId!),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  return {
    integrations: integrationsQuery.data || [],
    isLoading: integrationsQuery.isLoading,
    error: integrationsQuery.error,
    refetch: integrationsQuery.refetch
  }
}

/**
 * Hook to get a specific integration
 */
export function useIntegration(projectId: string | undefined, integrationId: string | undefined) {
  const integrationQuery = useQuery({
    queryKey: ['integration', projectId, integrationId],
    queryFn: () => integrationApi.getIntegration(projectId!, integrationId!),
    enabled: !!projectId && !!integrationId,
    staleTime: 1 * 60 * 1000, // 1 minute
  })

  return {
    integration: integrationQuery.data,
    isLoading: integrationQuery.isLoading,
    error: integrationQuery.error,
    refetch: integrationQuery.refetch
  }
}

/**
 * Hook for integration CRUD operations
 */
export function useIntegrationMutations(projectId: string | undefined) {
  const queryClient = useQueryClient()

  // Connect integration mutation
  const connectIntegrationMutation = useMutation({
    mutationFn: (data: ConnectIntegrationRequest) => integrationApi.connectIntegration(projectId!, data),
    onSuccess: (newIntegration) => {
      // Update integrations list
      queryClient.setQueryData(['integrations', projectId], (old: Integration[] = []) => [
        ...old,
        newIntegration
      ])
      toast.success(`${newIntegration.name} connected successfully!`)
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to connect integration')
    }
  })

  // Update integration mutation
  const updateIntegrationMutation = useMutation({
    mutationFn: ({ integrationId, data }: { integrationId: string; data: UpdateIntegrationRequest }) =>
      integrationApi.updateIntegration(projectId!, integrationId, data),
    onSuccess: (updatedIntegration) => {
      // Update integrations list
      queryClient.setQueryData(['integrations', projectId], (old: Integration[] = []) =>
        old.map(i => i.id === updatedIntegration.id ? updatedIntegration : i)
      )
      // Update individual integration cache
      queryClient.setQueryData(['integration', projectId, updatedIntegration.id], updatedIntegration)
      toast.success('Integration updated successfully!')
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to update integration')
    }
  })

  // Delete integration mutation
  const deleteIntegrationMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.deleteIntegration(projectId!, integrationId),
    onSuccess: (_, integrationId) => {
      // Remove from integrations list
      queryClient.setQueryData(['integrations', projectId], (old: Integration[] = []) =>
        old.filter(i => i.id !== integrationId)
      )
      // Remove individual integration cache
      queryClient.removeQueries({ queryKey: ['integration', projectId, integrationId] })
      toast.success('Integration deleted successfully!')
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to delete integration')
    }
  })

  return {
    connectIntegration: connectIntegrationMutation.mutate,
    updateIntegration: updateIntegrationMutation.mutate,
    deleteIntegration: deleteIntegrationMutation.mutate,
    isConnecting: connectIntegrationMutation.isPending,
    isUpdating: updateIntegrationMutation.isPending,
    isDeleting: deleteIntegrationMutation.isPending
  }
}

/**
 * Hook for integration syncing operations
 */
export function useIntegrationSync(projectId: string | undefined) {
  const queryClient = useQueryClient()
  const [syncingIntegrations, setSyncingIntegrations] = useState<Set<string>>(new Set())

  // Sync integration mutation
  const syncIntegrationMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.syncIntegration(projectId!, integrationId),
    onMutate: (integrationId) => {
      // Add to syncing set
      setSyncingIntegrations(prev => new Set(prev).add(integrationId))
      
      // Optimistically update integration status
      queryClient.setQueryData(['integration', projectId, integrationId], (old: Integration | undefined) => {
        if (!old) return old
        return { ...old, sync_status: 'syncing' as const, sync_progress: 0 }
      })
    },
    onSuccess: (syncResult, integrationId) => {
      // Remove from syncing set
      setSyncingIntegrations(prev => {
        const newSet = new Set(prev)
        newSet.delete(integrationId)
        return newSet
      })
      
      // Update integration with sync results
      queryClient.setQueryData(['integration', projectId, integrationId], (old: Integration | undefined) => {
        if (!old) return old
        return {
          ...old,
          sync_status: syncResult.status === 'completed' ? 'completed' : 'failed',
          last_sync: syncResult.completed_at || syncResult.started_at,
          sync_progress: 100
        }
      })
      
      // Refetch integrations to get updated stats
      queryClient.invalidateQueries({ queryKey: ['integrations', projectId] })
      
      toast.success('Sync started successfully!')
    },
    onError: (error: IntegrationApiError, integrationId) => {
      // Remove from syncing set
      setSyncingIntegrations(prev => {
        const newSet = new Set(prev)
        newSet.delete(integrationId)
        return newSet
      })
      
      // Update integration with error status
      queryClient.setQueryData(['integration', projectId, integrationId], (old: Integration | undefined) => {
        if (!old) return old
        return { ...old, sync_status: 'failed' as const, error_message: error.message }
      })
      
      toast.error(error.message || 'Failed to start sync')
    }
  })

  // Test integration mutation
  const testIntegrationMutation = useMutation({
    mutationFn: (integrationId: string) => integrationApi.testIntegration(projectId!, integrationId),
    onSuccess: (result) => {
      if (result.status === 'success') {
        toast.success(result.message || 'Integration test successful!')
      } else {
        toast.error(result.message || 'Integration test failed')
      }
    },
    onError: (error: IntegrationApiError) => {
      toast.error(error.message || 'Failed to test integration')
    }
  })

  return {
    syncIntegration: syncIntegrationMutation.mutate,
    testIntegration: testIntegrationMutation.mutate,
    isSyncing: (integrationId: string) => syncingIntegrations.has(integrationId),
    isTesting: testIntegrationMutation.isPending,
    syncingIntegrations: Array.from(syncingIntegrations)
  }
}

/**
 * Hook for integration sync history
 */
export function useIntegrationSyncHistory(
  projectId: string | undefined,
  integrationId: string | undefined
) {
  const syncHistoryQuery = useQuery({
    queryKey: ['integration-sync-history', projectId, integrationId],
    queryFn: () => integrationApi.getSyncHistory(projectId!, integrationId!, { limit: 20 }),
    enabled: !!projectId && !!integrationId,
    staleTime: 30 * 1000, // 30 seconds
  })

  return {
    syncHistory: syncHistoryQuery.data || [],
    isLoading: syncHistoryQuery.isLoading,
    error: syncHistoryQuery.error,
    refetch: syncHistoryQuery.refetch
  }
}

/**
 * Hook for browsing data sources from an integration
 */
export function useIntegrationDataSources(
  projectId: string | undefined,
  integrationId: string | undefined
) {
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(0)
  const pageSize = 20

  const dataSourcesQuery = useQuery({
    queryKey: ['integration-data-sources', projectId, integrationId, searchQuery, typeFilter, currentPage],
    queryFn: () => integrationApi.getDataSources(projectId!, integrationId!, {
      limit: pageSize,
      offset: currentPage * pageSize,
      search: searchQuery || undefined,
      type: typeFilter || undefined
    }),
    enabled: !!projectId && !!integrationId,
    staleTime: 1 * 60 * 1000, // 1 minute
  })

  const search = useCallback((query: string) => {
    setSearchQuery(query)
    setCurrentPage(0)
  }, [])

  const filterByType = useCallback((type: string) => {
    setTypeFilter(type)
    setCurrentPage(0)
  }, [])

  const nextPage = useCallback(() => {
    const totalPages = Math.ceil((dataSourcesQuery.data?.total || 0) / pageSize)
    if (currentPage < totalPages - 1) {
      setCurrentPage(prev => prev + 1)
    }
  }, [currentPage, dataSourcesQuery.data?.total, pageSize])

  const prevPage = useCallback(() => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1)
    }
  }, [currentPage])

  return {
    dataSources: dataSourcesQuery.data?.sources || [],
    totalSources: dataSourcesQuery.data?.total || 0,
    isLoading: dataSourcesQuery.isLoading,
    error: dataSourcesQuery.error,
    searchQuery,
    typeFilter,
    currentPage,
    pageSize,
    totalPages: Math.ceil((dataSourcesQuery.data?.total || 0) / pageSize),
    search,
    filterByType,
    nextPage,
    prevPage,
    refetch: dataSourcesQuery.refetch
  }
}

/**
 * Hook for getting available integration types
 */
export function useIntegrationTypes() {
  const typesQuery = useQuery({
    queryKey: ['integration-types'],
    queryFn: () => integrationApi.getIntegrationTypes(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  return {
    types: typesQuery.data || [],
    isLoading: typesQuery.isLoading,
    error: typesQuery.error
  }
}

/**
 * Hook for OAuth integration flow
 */
export function useOAuthIntegration(projectId: string | undefined) {
  const [isAuthenticating, setIsAuthenticating] = useState(false)

  const startOAuth = useCallback(async (type: string) => {
    if (!projectId) {
      toast.error('No project selected')
      return
    }

    setIsAuthenticating(true)
    try {
      const redirectUrl = `${window.location.origin}/dashboard/projects/${projectId}/integrations/oauth/callback`
      const { auth_url } = await integrationApi.startOAuthFlow(projectId, type, redirectUrl)
      
      // Open OAuth window
      const authWindow = window.open(
        auth_url,
        'oauth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      )

      // Listen for OAuth completion
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return
        
        if (event.data.type === 'oauth-success') {
          authWindow?.close()
          toast.success('Integration connected successfully!')
          window.removeEventListener('message', handleMessage)
          setIsAuthenticating(false)
        } else if (event.data.type === 'oauth-error') {
          authWindow?.close()
          toast.error(event.data.error || 'OAuth authentication failed')
          window.removeEventListener('message', handleMessage)
          setIsAuthenticating(false)
        }
      }

      window.addEventListener('message', handleMessage)

      // Handle window closed manually
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed)
          window.removeEventListener('message', handleMessage)
          setIsAuthenticating(false)
        }
      }, 1000)

    } catch (error) {
      toast.error('Failed to start OAuth flow')
      setIsAuthenticating(false)
    }
  }, [projectId])

  return {
    startOAuth,
    isAuthenticating
  }
}
