/**
 * Integration API client for NeuroSync
 * Handles GitHub, Jira, Slack, and other data source integrations
 */

import { getAuthHeaders } from '../auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Integration {
  id: string
  project_id: string
  type: 'github' | 'jira' | 'slack' | 'confluence' | 'notion'
  name: string
  status: 'connected' | 'disconnected' | 'error' | 'syncing'
  config: IntegrationConfig
  last_sync: string | null
  sync_status: 'idle' | 'syncing' | 'completed' | 'failed'
  sync_progress?: number
  error_message?: string
  created_at: string
  updated_at: string
  stats: IntegrationStats
  oauth_connected?: boolean
}

export interface IntegrationConfig {
  // Common fields for all integrations
  name?: string
  type?: 'github' | 'jira' | 'slack' | 'confluence' | 'notion'
  
  // GitHub specific
  repository_url?: string
  github_token?: string
  branches?: string[]
  include_issues?: boolean
  include_prs?: boolean
  include_wiki?: boolean

  // Jira specific
  jira_url?: string
  jira_email?: string
  jira_token?: string
  project_key?: string
  projects?: string[]
  username?: string
  include_comments?: boolean
  status_filters?: string[]

  // Slack specific
  slack_token?: string
  workspace_id?: string
  channels?: string[]
  include_threads?: boolean
  date_range?: {
    start: string
    end: string
  }

  // Confluence specific
  confluence_url?: string
  confluence_username?: string
  confluence_token?: string
  spaces?: string[]
  include_attachments?: boolean

  // Notion specific
  notion_token?: string
  database_ids?: string[]
  include_pages?: boolean
  selected_pages?: string[]
  selected_databases?: string[]

  // General settings
  sync_frequency?: 'manual' | 'hourly' | 'daily' | 'weekly'
  auto_sync?: boolean
  file_filters?: string[]
  exclude_patterns?: string[]
}

export interface IntegrationStats {
  total_documents: number
  last_sync_documents: number
  total_size_mb?: number
  sync_duration_seconds?: number
  error_count?: number
  success_rate?: number
  indexed_documents?: number
}

export interface ConnectIntegrationRequest {
  type: 'github' | 'jira' | 'slack' | 'confluence' | 'notion'
  name: string
  config: IntegrationConfig
}

export interface OAuthStartRequest {
  integration_type: 'github' | 'jira' | 'slack' | 'confluence' | 'notion'
  redirect_uri?: string
}

export interface OAuthStartResponse {
  authUrl: string
  state: string
}

export interface OAuthCompleteRequest {
  code: string
  state: string
}

export interface UpdateIntegrationRequest {
  name?: string
  config?: Partial<IntegrationConfig>
  status?: 'connected' | 'disconnected'
}

export interface SyncResult {
  integration_id: string
  sync_id: string
  status: 'started' | 'completed' | 'failed'
  documents_processed: number
  documents_added: number
  documents_updated: number
  documents_deleted: number
  duration_seconds: number
  error_message?: string
  started_at: string
  completed_at?: string
}

export interface DataSource {
  id: string
  integration_id: string
  type: 'file' | 'issue' | 'pr' | 'message' | 'page'
  title: string
  url?: string
  content_preview: string
  last_updated: string
  size_bytes: number
  metadata: Record<string, any>
}

export interface ApiError {
  detail: string
  code?: string
}

class IntegrationApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'IntegrationApiError'
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

    throw new IntegrationApiError(errorMessage, response.status, errorCode)
  }

  return response.json()
}

export class IntegrationApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Get all integrations for a project
   */
  async getIntegrations(projectId: string): Promise<Integration[]> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }
  
  /**
   * Get all integrations for the current user (including projectless ones)
   */
  async getUserIntegrations(): Promise<Integration[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/integrations/user`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Get a specific integration
   */
  async getIntegration(projectId: string, integrationId: string): Promise<Integration> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/${integrationId}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Connect a new integration
   */
  async connectIntegration(projectId: string, data: ConnectIntegrationRequest): Promise<Integration> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Update an existing integration
   */
  async updateIntegration(
    projectId: string,
    integrationId: string,
    data: UpdateIntegrationRequest
  ): Promise<Integration> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/${integrationId}`, {
      method: 'PUT',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Delete an integration
   */
  async deleteIntegration(projectId: string, integrationId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/${integrationId}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Trigger manual sync for an integration
   */
  async syncIntegration(projectId: string, integrationId: string): Promise<SyncResult> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/${integrationId}/sync`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Get sync history for an integration
   */
  async getSyncHistory(
    projectId: string,
    integrationId: string,
    options?: { limit?: number; offset?: number }
  ): Promise<SyncResult[]> {
    const params = new URLSearchParams()
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.offset) params.append('offset', options.offset.toString())

    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}/integrations/${integrationId}/sync/history?${params}`,
      {
        method: 'GET',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      }
    )

    return handleApiResponse(response)
  }

  // OAuth methods are defined later in the class
  
  /**
   * Test integration connection
   */
  async testIntegration(
    projectId: string,
    integrationId: string
  ): Promise<{ status: 'success' | 'error'; message: string; details?: any }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/${integrationId}/test`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Get data sources from an integration
   */
  async getDataSources(
    projectId: string,
    integrationId: string,
    options?: {
      limit?: number
      offset?: number
      type?: string
      search?: string
    }
  ): Promise<{ sources: DataSource[]; total: number }> {
    const params = new URLSearchParams()
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.offset) params.append('offset', options.offset.toString())
    if (options?.type) params.append('type', options.type)
    if (options?.search) params.append('search', options.search)

    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}/integrations/${integrationId}/sources?${params}`,
      {
        method: 'GET',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      }
    )

    return handleApiResponse(response)
  }

  /**
   * Get available integration types and their requirements
   */
  async getIntegrationTypes(): Promise<{
    type: string
    name: string
    description: string
    icon: string
    required_fields?: string[]
    optional_fields?: string[]
    oauth_supported: boolean
  }[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/integrations/types`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    // Get the raw response data
    const data = await handleApiResponse<any[]>(response)
    
    // Map backend 'id' property to frontend 'type' property to fix property mismatch
    return data.map(item => ({
      ...item,
      type: item.id, // Map backend 'id' to frontend 'type'
    }))
    
  }

  /**
   * Start OAuth flow for an integration
   */
  async startOAuthFlow(
    projectId: string,
    type: string,
    redirectUrl: string
  ): Promise<{ auth_url: string; state: string }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/oauth/start`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ type, redirect_url: redirectUrl }),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }

  /**
   * Complete OAuth flow for an integration
   */
  async completeOAuthFlow(
    projectId: string,
    code: string,
    state: string
  ): Promise<{ access_token: string; integration_config: IntegrationConfig }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/integrations/oauth/complete`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code, state }),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }
  
  /**
   * Complete OAuth flow without requiring a project ID (for project creation flow)
   */
  async completeOAuthFlowWithoutProject(
    code: string,
    state: string,
    integrationType: string
  ): Promise<{ access_token: string; integration_config: IntegrationConfig }> {
    const response = await fetch(`${this.baseUrl}/api/v1/integrations/oauth/complete`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code, state, integration_type: integrationType }),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }
  
  /**
   * Start OAuth flow without requiring a project ID (for project creation flow)
   */
  async startOAuthFlowWithoutProject(
    type: string,
    redirectUrl: string
  ): Promise<{ auth_url: string; state: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/integrations/oauth/start`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ integration_type: type, redirect_url: redirectUrl }),
      credentials: 'include',
    })

    return handleApiResponse(response)
  }
}

// Export singleton instance
export const integrationApi = new IntegrationApi()

// Export error class for error handling
export { IntegrationApiError }
