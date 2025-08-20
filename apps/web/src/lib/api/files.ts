/**
 * Files API client for NeuroSync
 * Handles file upload, processing, and management
 */

import { ApiResponse } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface FileUploadResponse {
  message: string
  project_id: string
  files: Array<{
    filename: string
    size: number
    type: string
    status: string
    message: string
  }>
  total_files: number
  total_size: number
}

export interface SupportedTypesResponse {
  supported_extensions: string[]
  max_file_size_mb: number
  description: string
}

export interface ProjectFilesResponse {
  project_id: string
  project_name: string
  files: Array<{
    id: string
    filename: string
    size: number
    type: string
    uploaded_at: string
  }>
  total_files: number
  message?: string
}

export class FilesApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Upload multiple files to a project
   * Creates a new project if project_id is not provided
   */
  async uploadFiles(
    files: FileList | File[],
    projectId?: string
  ): Promise<ApiResponse<FileUploadResponse>> {
    try {
      const formData = new FormData()
      
      // Add files to form data
      Array.from(files).forEach((file) => {
        formData.append('files', file)
      })
      
      // Add project ID if provided
      if (projectId) {
        formData.append('project_id', projectId)
      }

      const response = await fetch(`${this.baseUrl}/api/v1/files/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || 'Failed to upload files',
          data: null
        }
      }

      return {
        success: true,
        data: data,
        error: null
      }
    } catch (error) {
      console.error('Error uploading files:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
        data: null
      }
    }
  }

  /**
   * Get supported file types and limits
   */
  async getSupportedTypes(): Promise<ApiResponse<SupportedTypesResponse>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/files/supported-types`, {
        method: 'GET',
        credentials: 'include'
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || 'Failed to get supported types',
          data: null
        }
      }

      return {
        success: true,
        data: data,
        error: null
      }
    } catch (error) {
      console.error('Error getting supported types:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
        data: null
      }
    }
  }

  /**
   * Get files uploaded to a specific project
   */
  async getProjectFiles(projectId: string): Promise<ApiResponse<ProjectFilesResponse>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/files/project/${projectId}/files`, {
        method: 'GET',
        credentials: 'include'
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || 'Failed to get project files',
          data: null
        }
      }

      return {
        success: true,
        data: data,
        error: null
      }
    } catch (error) {
      console.error('Error getting project files:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
        data: null
      }
    }
  }
}

// Export singleton instance
export const filesApi = new FilesApiClient()
