/**
 * AI Chat API client for NeuroSync
 * Handles AI conversations, streaming responses, and query management
 */

import { getAuthHeaders } from '../auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  tokens_used?: number
  confidence_score?: number
  sources?: DocumentSource[]
  metadata?: Record<string, any>
}

export interface DocumentSource {
  id: string
  title: string
  type: 'github' | 'jira' | 'slack' | 'document' | 'meeting'
  url?: string
  excerpt: string
  relevance_score: number
  last_updated: string
}

export interface ChatSession {
  id: string
  project_id: string
  title: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  total_tokens: number
  status: 'active' | 'archived'
}

export interface SendMessageRequest {
  message: string
  project_id: string
  session_id?: string
  context_filters?: {
    sources?: string[]
    date_range?: {
      start: string
      end: string
    }
    file_types?: string[]
  }
  ai_settings?: {
    model: 'gpt-4' | 'gpt-3.5-turbo'
    temperature?: number
    max_tokens?: number
  }
}

export interface SendMessageResponse {
  message: ChatMessage
  session_id: string
  tokens_used: number
  sources: DocumentSource[]
  estimated_cost: number
}

export interface StreamingResponse {
  type: 'token' | 'sources' | 'complete' | 'error'
  content?: string
  sources?: DocumentSource[]
  message?: ChatMessage
  error?: string
}

export interface ApiError {
  detail: string
  code?: string
}

class ChatApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ChatApiError'
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

    throw new ChatApiError(errorMessage, response.status, errorCode)
  }

  return response.json()
}

export class ChatApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Get all chat sessions for a project
   */
  async getChatSessions(projectId: string): Promise<ChatSession[]> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/sessions`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Get a specific chat session with messages
   */
  async getChatSession(projectId: string, sessionId: string): Promise<ChatSession> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/sessions/${sessionId}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Create a new chat session
   */
  async createChatSession(projectId: string, title?: string): Promise<ChatSession> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/sessions`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    })

    return handleApiResponse(response)
  }

  /**
   * Send a message and get streaming response
   */
  async sendMessage(data: SendMessageRequest): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new ChatApiError(`HTTP ${response.status}`, response.status)
    }

    if (!response.body) {
      throw new ChatApiError('No response body', 500)
    }

    return response.body
  }

  /**
   * Send a message and get non-streaming response
   */
  async sendMessageSync(data: SendMessageRequest): Promise<SendMessageResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return handleApiResponse(response)
  }

  /**
   * Update chat session title
   */
  async updateChatSession(
    projectId: string,
    sessionId: string,
    updates: { title?: string; status?: 'active' | 'archived' }
  ): Promise<ChatSession> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/sessions/${sessionId}`, {
      method: 'PUT',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    })

    return handleApiResponse(response)
  }

  /**
   * Delete a chat session
   */
  async deleteChatSession(projectId: string, sessionId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Get chat history for a project
   */
  async getChatHistory(
    projectId: string,
    options?: {
      limit?: number
      offset?: number
      search?: string
    }
  ): Promise<{ messages: ChatMessage[]; total: number }> {
    const params = new URLSearchParams()
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.offset) params.append('offset', options.offset.toString())
    if (options?.search) params.append('search', options.search)

    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/history?${params}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Search through chat messages
   */
  async searchMessages(
    projectId: string,
    query: string,
    options?: {
      limit?: number
      session_id?: string
    }
  ): Promise<ChatMessage[]> {
    const params = new URLSearchParams({ query })
    if (options?.limit) params.append('limit', options.limit.toString())
    if (options?.session_id) params.append('session_id', options.session_id)

    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/search?${params}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Get suggested questions based on project context
   */
  async getSuggestedQuestions(projectId: string): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/chat/suggestions`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })

    return handleApiResponse(response)
  }

  /**
   * Parse streaming response
   */
  async *parseStreamingResponse(stream: ReadableStream<Uint8Array>): AsyncGenerator<StreamingResponse> {
    const reader = stream.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim() === '') continue
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') return

            try {
              const parsed: StreamingResponse = JSON.parse(data)
              yield parsed
            } catch (error) {
              console.error('Failed to parse streaming response:', error)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
}

// Export singleton instance
export const chatApi = new ChatApi()

// Export error class for error handling
export { ChatApiError }
