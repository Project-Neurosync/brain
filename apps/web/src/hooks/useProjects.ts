/**
 * Project management hooks for NeuroSync
 * Provides React hooks for project operations and state management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  projectApi,
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  InviteTeamMemberRequest,
  ProjectSettings,
  ProjectApiError
} from '../lib/api/projects'

/**
 * Hook to get all projects for the current user
 */
export function useProjects() {
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectApi.getProjects(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  return {
    projects: projectsQuery.data || [],
    isLoading: projectsQuery.isLoading,
    error: projectsQuery.error,
    refetch: projectsQuery.refetch
  }
}

/**
 * Hook to get a specific project by ID
 */
export function useProject(projectId: string | undefined) {
  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectApi.getProject(projectId!),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  return {
    project: projectQuery.data,
    isLoading: projectQuery.isLoading,
    error: projectQuery.error,
    refetch: projectQuery.refetch
  }
}

/**
 * Hook for project CRUD operations
 */
export function useProjectMutations() {
  const queryClient = useQueryClient()

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: (data: CreateProjectRequest) => projectApi.createProject(data),
    onSuccess: (newProject) => {
      // Update projects list
      queryClient.setQueryData(['projects'], (old: Project[] = []) => [
        ...old,
        newProject
      ])
      toast.success('Project created successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to create project')
    }
  })

  // Update project mutation
  const updateProjectMutation = useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: UpdateProjectRequest }) =>
      projectApi.updateProject(projectId, data),
    onSuccess: (updatedProject) => {
      // Update projects list
      queryClient.setQueryData(['projects'], (old: Project[] = []) =>
        old.map(p => p.id === updatedProject.id ? updatedProject : p)
      )
      // Update individual project cache
      queryClient.setQueryData(['project', updatedProject.id], updatedProject)
      toast.success('Project updated successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to update project')
    }
  })

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: string) => projectApi.deleteProject(projectId),
    onSuccess: (_, projectId) => {
      // Remove from projects list
      queryClient.setQueryData(['projects'], (old: Project[] = []) =>
        old.filter(p => p.id !== projectId)
      )
      // Remove individual project cache
      queryClient.removeQueries({ queryKey: ['project', projectId] })
      toast.success('Project deleted successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to delete project')
    }
  })

  return {
    createProject: createProjectMutation.mutate,
    updateProject: updateProjectMutation.mutate,
    deleteProject: deleteProjectMutation.mutate,
    isCreating: createProjectMutation.isPending,
    isUpdating: updateProjectMutation.isPending,
    isDeleting: deleteProjectMutation.isPending
  }
}

/**
 * Hook for team member management
 */
export function useTeamManagement(projectId: string | undefined) {
  const queryClient = useQueryClient()

  // Invite team member mutation
  const inviteTeamMemberMutation = useMutation({
    mutationFn: (data: InviteTeamMemberRequest) =>
      projectApi.inviteTeamMember(projectId!, data),
    onSuccess: () => {
      // Refetch project to get updated team members
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      toast.success('Team member invited successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to invite team member')
    }
  })

  // Remove team member mutation
  const removeTeamMemberMutation = useMutation({
    mutationFn: (userId: string) =>
      projectApi.removeTeamMember(projectId!, userId),
    onSuccess: () => {
      // Refetch project to get updated team members
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      toast.success('Team member removed successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to remove team member')
    }
  })

  // Update team member role mutation
  const updateTeamMemberRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: 'admin' | 'member' | 'viewer' }) =>
      projectApi.updateTeamMemberRole(projectId!, userId, role),
    onSuccess: () => {
      // Refetch project to get updated team members
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      toast.success('Team member role updated successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to update team member role')
    }
  })

  return {
    inviteTeamMember: inviteTeamMemberMutation.mutate,
    removeTeamMember: removeTeamMemberMutation.mutate,
    updateTeamMemberRole: updateTeamMemberRoleMutation.mutate,
    isInviting: inviteTeamMemberMutation.isPending,
    isRemoving: removeTeamMemberMutation.isPending,
    isUpdatingRole: updateTeamMemberRoleMutation.isPending
  }
}

/**
 * Hook for project integrations
 */
export function useProjectIntegrations(projectId: string | undefined) {
  const queryClient = useQueryClient()

  // Get integrations query
  const integrationsQuery = useQuery({
    queryKey: ['project-integrations', projectId],
    queryFn: () => projectApi.getProjectIntegrations(projectId!),
    enabled: !!projectId,
    staleTime: 1 * 60 * 1000, // 1 minute
  })

  // Connect integration mutation
  const connectIntegrationMutation = useMutation({
    mutationFn: ({ type, config }: { type: 'github' | 'jira' | 'slack' | 'confluence'; config: Record<string, any> }) =>
      projectApi.connectIntegration(projectId!, type, config),
    onSuccess: () => {
      // Refetch integrations
      queryClient.invalidateQueries({ queryKey: ['project-integrations', projectId] })
      toast.success('Integration connected successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to connect integration')
    }
  })

  // Disconnect integration mutation
  const disconnectIntegrationMutation = useMutation({
    mutationFn: (integrationId: string) =>
      projectApi.disconnectIntegration(projectId!, integrationId),
    onSuccess: () => {
      // Refetch integrations
      queryClient.invalidateQueries({ queryKey: ['project-integrations', projectId] })
      toast.success('Integration disconnected successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to disconnect integration')
    }
  })

  // Sync integration mutation
  const syncIntegrationMutation = useMutation({
    mutationFn: (integrationId: string) =>
      projectApi.syncIntegration(projectId!, integrationId),
    onSuccess: () => {
      // Refetch integrations to get updated sync status
      queryClient.invalidateQueries({ queryKey: ['project-integrations', projectId] })
      toast.success('Integration sync started!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to sync integration')
    }
  })

  return {
    integrations: integrationsQuery.data || [],
    isLoading: integrationsQuery.isLoading,
    error: integrationsQuery.error,
    connectIntegration: connectIntegrationMutation.mutate,
    disconnectIntegration: disconnectIntegrationMutation.mutate,
    syncIntegration: syncIntegrationMutation.mutate,
    isConnecting: connectIntegrationMutation.isPending,
    isDisconnecting: disconnectIntegrationMutation.isPending,
    isSyncing: syncIntegrationMutation.isPending,
    refetch: integrationsQuery.refetch
  }
}

/**
 * Hook for project settings
 */
export function useProjectSettings(projectId: string | undefined) {
  const queryClient = useQueryClient()

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (settings: Partial<ProjectSettings>) =>
      projectApi.updateProjectSettings(projectId!, settings),
    onSuccess: (updatedSettings) => {
      // Update project cache with new settings
      queryClient.setQueryData(['project', projectId], (old: Project | undefined) => {
        if (!old) return old
        return { ...old, settings: updatedSettings }
      })
      toast.success('Project settings updated successfully!')
    },
    onError: (error: ProjectApiError) => {
      toast.error(error.message || 'Failed to update project settings')
    }
  })

  return {
    updateSettings: updateSettingsMutation.mutate,
    isUpdating: updateSettingsMutation.isPending
  }
}

/**
 * Hook for project statistics and analytics
 */
export function useProjectStats(projectId: string | undefined) {
  const { project } = useProject(projectId)

  return {
    stats: project?.stats,
    totalDocuments: project?.stats?.total_documents || 0,
    totalQueries: project?.stats?.total_queries || 0,
    tokensUsed: project?.stats?.tokens_used || 0,
    activeMembers: project?.stats?.active_members || 0,
    knowledgeCoverage: project?.stats?.knowledge_coverage || 0,
    lastActivity: project?.stats?.last_activity
  }
}
