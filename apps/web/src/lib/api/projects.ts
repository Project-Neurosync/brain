/**
 * Project Management API client for NeuroSync
 * Handles project creation, management, team invitations, and settings
 */

// Using cookie-based authentication - no need for manual headers

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Project {
  id: string
  name: string
  description: string
  repository_url?: string
  jira_project_key?: string
  slack_channel?: string
  status: 'active' | 'archived' | 'paused'
  created_at: string
  updated_at: string
  owner_id: string
  team_members: TeamMember[]
  integrations: ProjectIntegration[]
  settings: ProjectSettings
  stats: ProjectStats
}

export interface TeamMember {
  id: string
  user_id: string
  name: string
  email: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  joined_at: string
  last_active?: string
  avatar_url?: string
}

export interface ProjectIntegration {
  id: string
  type: 'github' | 'jira' | 'slack' | 'confluence'
  status: 'connected' | 'disconnected' | 'error'
  config: Record<string, any>
  last_sync?: string
  sync_status?: 'syncing' | 'completed' | 'failed'
}

export interface ProjectSettings {
  ai_model: 'gpt-4' | 'gpt-3.5-turbo'
  token_budget: number
  auto_sync: boolean
  notification_preferences: {
    email: boolean
    slack: boolean
    in_app: boolean
  }
  data_retention_days: number
  access_level: 'public' | 'team' | 'private'
}

export interface ProjectStats {
  total_documents: number
  total_queries: number
  tokens_used: number
  last_activity: string
  active_members: number
  knowledge_coverage: number
}

export interface CreateProjectRequest {
  name: string
  description: string
  repository_url?: string
  jira_project_key?: string
  slack_channel?: string
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  repository_url?: string
  jira_project_key?: string
  slack_channel?: string
  status?: 'active' | 'archived' | 'paused'
}

export interface InviteTeamMemberRequest {
  email: string
  role: 'admin' | 'member' | 'viewer'
  message?: string
}

export interface ApiError {
  detail: string
  code?: string
}

class ProjectApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ProjectApiError'
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
      errorMessage = response.statusText || errorMessage
    }

    throw new ProjectApiError(errorMessage, response.status, errorCode)
  }

  return response.json()
}

export class ProjectApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Get all projects for the current user
   */
  async getProjects(): Promise<Project[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Get a specific project by ID
   */
  async getProject(projectId: string): Promise<Project> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Create a new project
   */
  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Update an existing project
   */
  async updateProject(projectId: string, data: UpdateProjectRequest): Promise<Project> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Delete a project
   */
  async deleteProject(projectId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Invite a team member to a project
   */
  async inviteTeamMember(
    projectId: string,
    data: InviteTeamMemberRequest
  ): Promise<{ message: string; invitation_id: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/invite/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Remove a team member from a project
   */
  async removeTeamMember(
    projectId: string,
    userId: string
  ): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/members/${userId}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Update team member role
   */
  async updateTeamMemberRole(
    projectId: string,
    userId: string,
    role: 'admin' | 'member' | 'viewer'
  ): Promise<TeamMember> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/members/${userId}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ role }),
    })

    return handleApiResponse(response)
  }

  /**
   * Get project integrations
   */
  async getProjectIntegrations(projectId: string): Promise<ProjectIntegration[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/integrations/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Connect an integration
   */
  async connectIntegration(
    projectId: string,
    type: 'github' | 'jira' | 'slack' | 'confluence',
    config: Record<string, any>
  ): Promise<ProjectIntegration> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/integrations/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ type, config }),
    })

    return handleApiResponse(response)
  }

  /**
   * Disconnect an integration
   */
  async disconnectIntegration(
    projectId: string,
    integrationId: string
  ): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/integrations/${integrationId}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Trigger manual sync for an integration
   */
  async syncIntegration(
    projectId: string,
    integrationId: string
  ): Promise<{ message: string; sync_id: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/integrations/${integrationId}/sync/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Update project settings
   */
  async updateProjectSettings(
    projectId: string,
    settings: Partial<ProjectSettings>
  ): Promise<ProjectSettings> {
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/settings/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(settings),
    })

    return handleApiResponse(response)
  }
}

// Export singleton instance
export const projectApi = new ProjectApi()

// Export error class for error handling
export { ProjectApiError }
