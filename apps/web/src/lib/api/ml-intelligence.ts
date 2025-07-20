/**
 * ML Intelligence API client for NeuroSync
 * Handles data importance scoring, duplicate detection, and timeline storage
 */

import { getAuthHeaders } from '../auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface DataItem {
  content: string
  metadata: {
    source_type: string
    file_path?: string
    language?: string
    author?: string
    created_at: string
    project_id: string
    [key: string]: any
  }
}

export interface ImportanceScoreResult {
  importance_score: number
  importance_level: 'very_low' | 'low' | 'medium' | 'high' | 'very_high'
  confidence: number
  reasoning: string
  factors: {
    content_quality: number
    temporal_relevance: number
    author_importance: number
    project_relevance: number
    engagement_metrics: number
    structural_features: number
  }
  timeline_category: 'recent' | 'last_month' | 'last_quarter' | 'last_year' | 'historical'
}

export interface BatchScoreRequest {
  items: DataItem[]
  project_id: string
  importance_threshold?: number
  batch_size?: number
}

export interface BatchScoreResult {
  results: Array<{
    item_id: string
    importance_analysis: ImportanceScoreResult
    processing_time_ms: number
  }>
  batch_stats: {
    total_items: number
    processed_items: number
    avg_importance_score: number
    high_importance_count: number
    processing_time_ms: number
  }
}

export interface DuplicateDetectionRequest {
  items: DataItem[]
  project_id: string
  similarity_threshold?: number
  content_signature_threshold?: number
}

export interface DuplicateDetectionResult {
  duplicates: Array<{
    item_id: string
    duplicate_of: string
    similarity_score: number
    detection_method: 'content_signature' | 'semantic_similarity'
    confidence: number
  }>
  unique_items: string[]
  duplicate_groups: Array<{
    representative_id: string
    duplicate_ids: string[]
    group_size: number
  }>
}

export interface TimelineStorageRequest {
  data_items: Array<{
    content: string
    metadata: Record<string, any>
    importance_score: number
    timeline_category: string
  }>
  project_id: string
  storage_tier?: 'hot' | 'warm' | 'cold' | 'frozen'
}

export interface TimelineStorageResult {
  stored_items: number
  storage_distribution: {
    hot: number
    warm: number
    cold: number
    frozen: number
  }
  total_storage_mb: number
  processing_time_ms: number
}

export interface MLAnalytics {
  project_id: string
  total_items_processed: number
  importance_distribution: {
    very_high: number
    high: number
    medium: number
    low: number
    very_low: number
  }
  timeline_distribution: {
    recent: number
    last_month: number
    last_quarter: number
    last_year: number
    historical: number
  }
  duplicate_detection_stats: {
    total_duplicates_found: number
    duplicate_rate: number
    storage_saved_mb: number
  }
  performance_metrics: {
    avg_scoring_time_ms: number
    avg_duplicate_detection_time_ms: number
    avg_storage_time_ms: number
  }
}

export interface FeedbackRequest {
  item_id: string
  project_id: string
  feedback_type: 'importance_correction' | 'duplicate_correction' | 'timeline_correction'
  feedback_data: {
    corrected_importance_score?: number
    is_duplicate?: boolean
    corrected_timeline_category?: string
    user_notes?: string
  }
}

export interface ApiError {
  detail: string
  code?: string
}

class MLIntelligenceApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'MLIntelligenceApiError'
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({ 
      detail: `HTTP ${response.status}: ${response.statusText}` 
    }))
    throw new MLIntelligenceApiError(error.detail, response.status, error.code)
  }
  return response.json()
}

export class MLIntelligenceApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Score the importance of a single data item
   */
  async scoreDataImportance(
    dataItem: DataItem,
    projectId: string
  ): Promise<ImportanceScoreResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/score-importance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        data_item: dataItem,
        project_id: projectId
      })
    })

    return handleApiResponse<ImportanceScoreResult>(response)
  }

  /**
   * Score importance for multiple items in batch
   */
  async scoreBatch(data: BatchScoreRequest): Promise<BatchScoreResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/score-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<BatchScoreResult>(response)
  }

  /**
   * Detect duplicates in a set of data items
   */
  async detectDuplicates(data: DuplicateDetectionRequest): Promise<DuplicateDetectionResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/detect-duplicates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<DuplicateDetectionResult>(response)
  }

  /**
   * Store data items in timeline-based storage
   */
  async storeTimelineData(data: TimelineStorageRequest): Promise<TimelineStorageResult> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/timeline-storage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse<TimelineStorageResult>(response)
  }

  /**
   * Retrieve timeline data with filtering
   */
  async retrieveTimelineData(
    projectId: string,
    options?: {
      timeline_categories?: string[]
      importance_threshold?: number
      limit?: number
      offset?: number
      start_date?: string
      end_date?: string
    }
  ): Promise<{
    items: Array<{
      id: string
      content: string
      metadata: Record<string, any>
      importance_score: number
      timeline_category: string
      storage_tier: string
      created_at: string
    }>
    total: number
    timeline_distribution: Record<string, number>
  }> {
    const params = new URLSearchParams({ project_id: projectId })
    
    if (options?.timeline_categories) {
      params.append('timeline_categories', options.timeline_categories.join(','))
    }
    if (options?.importance_threshold) {
      params.append('importance_threshold', options.importance_threshold.toString())
    }
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.offset) params.append('offset', options.offset.toString())
    if (options?.start_date) params.append('start_date', options.start_date)
    if (options?.end_date) params.append('end_date', options.end_date)

    const response = await fetch(`${this.baseUrl}/api/v1/ml/timeline-data?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse(response)
  }

  /**
   * Get ML intelligence analytics for a project
   */
  async getAnalytics(projectId: string): Promise<MLAnalytics> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/analytics/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })

    return handleApiResponse<MLAnalytics>(response)
  }

  /**
   * Provide feedback to improve ML models
   */
  async provideFeedback(data: FeedbackRequest): Promise<{ message: string; learning_applied: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    })

    return handleApiResponse(response)
  }

  /**
   * Get ML intelligence service health
   */
  async getHealth(): Promise<{
    status: string
    importance_scoring_status: string
    duplicate_detection_status: string
    timeline_storage_status: string
    performance_metrics: {
      avg_scoring_time_ms: number
      avg_duplicate_detection_time_ms: number
      avg_storage_time_ms: number
    }
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/ml/health`, {
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
export const mlIntelligenceApi = new MLIntelligenceApi()

// Export error class for error handling
export { MLIntelligenceApiError }
