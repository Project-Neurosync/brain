/**
 * File Upload Component
 * Handles document and file uploads with drag & drop
 */

'use client'

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, 
  File, 
  FileText, 
  Image, 
  Video, 
  Music,
  Archive,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Plus,
  FolderOpen
} from 'lucide-react'
import { Button } from '../ui/button'
import { useProjectMutations } from '../../hooks/useProjects'

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  url?: string
  error?: string
  preview?: string
}

interface FileUploadProps {
  projectId: string
  onUploadComplete?: (files: UploadedFile[]) => void
  maxFiles?: number
  maxSize?: number // in MB
  acceptedTypes?: string[]
}

export function FileUpload({ 
  projectId, 
  onUploadComplete, 
  maxFiles = 10, 
  maxSize = 50,
  acceptedTypes = ['.pdf', '.doc', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg']
}: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { } = useProjectMutations()

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image className="h-5 w-5" />
    if (type.startsWith('video/')) return <Video className="h-5 w-5" />
    if (type.startsWith('audio/')) return <Music className="h-5 w-5" />
    if (type.includes('pdf')) return <FileText className="h-5 w-5" />
    if (type.includes('zip') || type.includes('rar')) return <Archive className="h-5 w-5" />
    return <File className="h-5 w-5" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return `File size exceeds ${maxSize}MB limit`
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (acceptedTypes.length > 0 && !acceptedTypes.includes(fileExtension)) {
      return `File type ${fileExtension} is not supported`
    }

    return null
  }

  const processFiles = async (files: FileList) => {
    if (uploadedFiles.length + files.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`)
      return
    }

    setIsUploading(true)
    const newFiles: UploadedFile[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const validationError = validateFile(file)

      const uploadedFile: UploadedFile = {
        id: `${Date.now()}-${i}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: validationError ? 'failed' : 'uploading',
        progress: 0,
        error: validationError || undefined
      }

      newFiles.push(uploadedFile)
    }

    setUploadedFiles(prev => [...prev, ...newFiles])

    // Process valid files
    for (const uploadedFile of newFiles) {
      if (uploadedFile.status === 'failed') continue

      try {
        // Find the original file
        const originalFile = Array.from(files).find(f => 
          f.name === uploadedFile.name && f.size === uploadedFile.size
        )

        if (originalFile) {
          // Create FormData for upload
          const formData = new FormData()
          formData.append('file', originalFile)
          formData.append('project_id', projectId)

          // Set up upload with progress tracking
          const xhr = new XMLHttpRequest()
          
          // Track upload progress
          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const progress = Math.round((event.loaded / event.total) * 90) // 90% for upload, 10% for processing
              setUploadedFiles(prev => prev.map(f => 
                f.id === uploadedFile.id ? { ...f, progress } : f
              ))
            }
          }

          // Set up promise to handle completion
          const uploadPromise = new Promise<void>((resolve, reject) => {
            xhr.onload = function() {
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve()
              } else {
                reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`))
              }
            }
            
            xhr.onerror = () => reject(new Error('Network error during upload'))
          })

          // Start upload
          xhr.open('POST', '/api/v1/documents/upload', true)
          // Include credentials for authentication cookies
          xhr.withCredentials = true
          xhr.send(formData)

          // Wait for upload to complete
          await uploadPromise

          // Update file status to processing
          setUploadedFiles(prev => prev.map(f => 
            f.id === uploadedFile.id 
              ? { ...f, status: 'processing', progress: 95 }
              : f
          ))

          // Get processing status
          const response = await fetch(`/api/v1/documents/status/${uploadedFile.id}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          })

          if (!response.ok) {
            throw new Error(`Failed to get processing status: ${response.statusText}`)
          }

          const processingResult = await response.json()

          // Complete upload with real data
          setUploadedFiles(prev => prev.map(f => 
            f.id === uploadedFile.id 
              ? { 
                  ...f, 
                  status: 'completed', 
                  progress: 100,
                  url: processingResult.url || `/api/v1/documents/${uploadedFile.id}`,
                  preview: originalFile.type.startsWith('image/') 
                    ? URL.createObjectURL(originalFile) 
                    : undefined
                }
              : f
          ))
        }
      } catch (error) {
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadedFile.id 
            ? { ...f, status: 'failed', error: 'Upload failed' }
            : f
        ))
      }
    }

    setIsUploading(false)
    
    // Call completion callback
    if (onUploadComplete) {
      const completedFiles = newFiles.filter(f => f.status === 'completed')
      onUploadComplete(completedFiles)
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      processFiles(files)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      processFiles(files)
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const retryUpload = (fileId: string) => {
    setUploadedFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, status: 'uploading', progress: 0, error: undefined }
        : f
    ))
    // In real implementation, retry the actual upload
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragOver 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            {isDragOver ? (
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="p-4 bg-blue-100 rounded-full"
              >
                <FolderOpen className="h-8 w-8 text-blue-600" />
              </motion.div>
            ) : (
              <div className="p-4 bg-gray-100 rounded-full">
                <Upload className="h-8 w-8 text-gray-600" />
              </div>
            )}
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {isDragOver ? 'Drop files here' : 'Upload Documents'}
            </h3>
            <p className="text-gray-600 mb-4">
              Drag and drop files here, or click to browse
            </p>
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Choose Files
            </Button>
          </div>
          
          <div className="text-sm text-gray-500">
            <p>Supported formats: {acceptedTypes.join(', ')}</p>
            <p>Maximum file size: {maxSize}MB • Maximum files: {maxFiles}</p>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      <AnimatePresence>
        {uploadedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <h4 className="font-medium text-gray-900">Uploaded Files ({uploadedFiles.length})</h4>
            
            {uploadedFiles.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="bg-white border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getFileIcon(file.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {file.status === 'uploading' && (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                    {file.status === 'processing' && (
                      <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
                    )}
                    {file.status === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {file.status === 'failed' && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeFile(file.id)}
                      className="h-6 w-6 p-0"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
                
                {/* Progress Bar */}
                {(file.status === 'uploading' || file.status === 'processing') && (
                  <div className="mb-2">
                    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                      <span>
                        {file.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                      </span>
                      <span>{file.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <motion.div
                        className={`h-1.5 rounded-full ${
                          file.status === 'uploading' ? 'bg-blue-500' : 'bg-yellow-500'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${file.progress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  </div>
                )}
                
                {/* Error Message */}
                {file.status === 'failed' && file.error && (
                  <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    {file.error}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => retryUpload(file.id)}
                      className="ml-2 h-auto p-0 text-red-600 hover:text-red-700"
                    >
                      Retry
                    </Button>
                  </div>
                )}
                
                {/* Preview for Images */}
                {file.preview && file.status === 'completed' && (
                  <div className="mt-2">
                    <img
                      src={file.preview}
                      alt={file.name}
                      className="h-20 w-20 object-cover rounded border"
                    />
                  </div>
                )}
                
                {/* Success Actions */}
                {file.status === 'completed' && (
                  <div className="flex items-center gap-2 mt-2">
                    <Button size="sm" variant="outline">
                      View
                    </Button>
                    {file.url && (
                      <Button size="sm" variant="ghost">
                        <a href={file.url} target="_blank" rel="noopener noreferrer">
                          Download
                        </a>
                      </Button>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
