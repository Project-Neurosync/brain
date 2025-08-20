/**
 * Common API types and interfaces for NeuroSync
 */

export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ErrorResponse {
  detail: string
  code?: string
  field?: string
}

export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

export interface User extends BaseEntity {
  email: string
  name?: string
  avatar_url?: string
  is_active: boolean
}

export interface Project extends BaseEntity {
  name: string
  description: string
  status: 'active' | 'archived' | 'draft'
  progress: number
  user_id: string
  project_metadata?: Record<string, any>
}

export interface Integration extends BaseEntity {
  type: 'github' | 'jira' | 'slack' | 'confluence' | 'notion'
  name: string
  status: 'connected' | 'disconnected' | 'error'
  config: Record<string, any>
  user_id: string
  project_id?: string
}

export interface Document extends BaseEntity {
  title: string
  content: string
  source: string
  metadata: Record<string, any>
  project_id: string
  user_id: string
}

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  sources?: Array<{
    title: string
    content: string
    confidence: number
  }>
}

export interface ChatConversation extends BaseEntity {
  title?: string
  messages: ChatMessage[]
  project_id?: string
  user_id: string
}
