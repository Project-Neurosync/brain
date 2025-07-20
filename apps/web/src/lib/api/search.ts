/**
 * Semantic Search API client for NeuroSync
 * Handles semantic code search, cross-source search, and contextual search
 */

import { getAuthHeaders } from '../auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SearchResult {
  id: string
  content: string
  title: string
  type: 'code' | 'documentation' | 'meeting' | 'issue' | 'slack_message' | 'email' | 'commit'
  source_type: string
  file_path?: string
  language?: string
  url?: string
  excerpt: string
  relevance_score: number
  importance_score: number
  final_score: number
  last_updated: string
  metadata: Record<string, any>
  highlights?: string[]
}

export interface SearchResponse {
  results: SearchResult[]
  total_results: number
  query_enhanced: string
  search_time_ms: number
  facets: SearchFacets
  suggestions: string[]
}

export interface SearchFacets {
  content_types: Array<{ type: string; count: number }>
  languages: Array<{ language: string; count: number }>
  sources: Array<{ source: string; count: number }>
  importance_levels: Array<{ level: string; count: number }>
  timeline_categories: Array<{ category: string; count: number }>
}

export interface SemanticCodeSearchRequest {
  query: string
  project_id: string
  language?: string
  file_types?: string[]
  importance_threshold?: number
  max_results?: number
  include_facets?: boolean
}

export interface CrossSourceSearchRequest {
  query: string
  project_id: string
  content_types?: string[]
  timeline_filter?: {
    start_date?: string
    end_date?: string
    categories?: string[]
  }
  importance_threshold?: number
  max_results?: number
  include_facets?: boolean
}

export interface ContextualSearchRequest {
  query: string
  project_id: string
  user_context?: {
    current_file?: string
    recent_files?: string[]
    current_task?: string
    role?: string
  }
  max_results?: number
  include_suggestions?: boolean
}

export interface SimilarCodeSearchRequest {
  code_snippet: string
  project_id: string
  language?: string
  similarity_threshold?: number
  max_results?: number
}

export interface SearchSuggestion {
  query: string
  description: string
  category: string
  confidence: number
}

export interface SearchAnalytics {
  total_searches: number
  popular_queries: Array<{ query: string; count: number }>
  search_patterns: Array<{ pattern: string; frequency: number }>
  user_engagement: {
    avg_results_clicked: number
    avg_search_session_length: number
    most_searched_content_types: string[]
  }
}

export interface ApiError {
  detail: string
  code?: string
}

class SearchApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'SearchApiError'
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({ 
      detail: `HTTP ${response.status}: ${response.statusText}` 
    }))
    throw new SearchApiError(error.detail, response.status, error.code)
  }
  return response.json()
}

export class SearchApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Perform semantic code search
   */
  async semanticCodeSearch(data: SemanticCodeSearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/semantic-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<SearchResponse>(response)
  }

  /**
   * Perform cross-source search across all data types
   */
  async crossSourceSearch(data: CrossSourceSearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/cross-source`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<SearchResponse>(response)
  }

  /**
   * Perform contextual search with user context awareness
   */
  async contextualSearch(data: ContextualSearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/contextual`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<SearchResponse>(response)
  }

  /**
   * Find similar code patterns
   */
  async similarCodeSearch(data: SimilarCodeSearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/similar-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<SearchResponse>(response)
  }

  /**
   * Get search suggestions for a project
   */
  async getSearchSuggestions(projectId: string): Promise<SearchSuggestion[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/suggestions/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse<SearchSuggestion[]>(response)
  }

  /**
   * Get search history for a project
   */
  async getSearchHistory(
    projectId: string,
    options?: {
      limit?: number
      offset?: number
      search_type?: string
    }
  ): Promise<{
    history: Array<{
      query: string
      search_type: string
      timestamp: string
      results_count: number
      search_id: string
    }>
    total: number
  }> {
    const params = new URLSearchParams()
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.offset) params.append('offset', options.offset.toString())
    if (options?.search_type) params.append('search_type', options.search_type)

    const response = await fetch(`${this.baseUrl}/api/v1/search/history/${projectId}?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse(response)
  }

  /**
   * Get search analytics for a project
   */
  async getSearchAnalytics(projectId: string): Promise<SearchAnalytics> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/analytics/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse<SearchAnalytics>(response)
  }

  /**
   * Check search service health
   */
  async getSearchHealth(): Promise<{
    status: string
    search_engine_status: string
    vector_db_status: string
    knowledge_graph_status: string
    response_time_ms: number
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/search/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse(response)
  }
}

// Export singleton instance
export const searchApi = new SearchApi()

// Export error class for error handling
export { SearchApiError }
