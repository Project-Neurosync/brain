/**
 * AI Chat hooks for NeuroSync
 * Provides React hooks for chat operations, streaming, and message management
 */

import { useState, useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  chatApi,
  ChatSession,
  ChatMessage,
  SendMessageRequest,
  StreamingResponse,
  DocumentSource,
  ChatApiError
} from '../lib/api/chat'

/**
 * Hook to get all chat sessions for a project
 */
export function useChatSessions(projectId: string | undefined) {
  const sessionsQuery = useQuery({
    queryKey: ['chat-sessions', projectId],
    queryFn: () => chatApi.getChatSessions(projectId!),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  return {
    sessions: sessionsQuery.data || [],
    isLoading: sessionsQuery.isLoading,
    error: sessionsQuery.error,
    refetch: sessionsQuery.refetch
  }
}

/**
 * Hook to get a specific chat session
 */
export function useChatSession(projectId: string | undefined, sessionId: string | undefined) {
  const sessionQuery = useQuery({
    queryKey: ['chat-session', projectId, sessionId],
    queryFn: () => chatApi.getChatSession(projectId!, sessionId!),
    enabled: !!projectId && !!sessionId,
    staleTime: 30 * 1000, // 30 seconds
  })

  return {
    session: sessionQuery.data,
    isLoading: sessionQuery.isLoading,
    error: sessionQuery.error,
    refetch: sessionQuery.refetch
  }
}

/**
 * Hook for chat session management
 */
export function useChatSessionMutations(projectId: string | undefined) {
  const queryClient = useQueryClient()

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (title?: string) => chatApi.createChatSession(projectId!, title),
    onSuccess: (newSession) => {
      // Update sessions list
      queryClient.setQueryData(['chat-sessions', projectId], (old: ChatSession[] = []) => [
        newSession,
        ...old
      ])
      toast.success('New chat session created!')
    },
    onError: (error: ChatApiError) => {
      toast.error(error.message || 'Failed to create chat session')
    }
  })

  // Update session mutation
  const updateSessionMutation = useMutation({
    mutationFn: ({ sessionId, updates }: { 
      sessionId: string; 
      updates: { title?: string; status?: 'active' | 'archived' } 
    }) => chatApi.updateChatSession(projectId!, sessionId, updates),
    onSuccess: (updatedSession) => {
      // Update sessions list
      queryClient.setQueryData(['chat-sessions', projectId], (old: ChatSession[] = []) =>
        old.map(s => s.id === updatedSession.id ? updatedSession : s)
      )
      // Update individual session cache
      queryClient.setQueryData(['chat-session', projectId, updatedSession.id], updatedSession)
      toast.success('Chat session updated!')
    },
    onError: (error: ChatApiError) => {
      toast.error(error.message || 'Failed to update chat session')
    }
  })

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteChatSession(projectId!, sessionId),
    onSuccess: (_, sessionId) => {
      // Remove from sessions list
      queryClient.setQueryData(['chat-sessions', projectId], (old: ChatSession[] = []) =>
        old.filter(s => s.id !== sessionId)
      )
      // Remove individual session cache
      queryClient.removeQueries({ queryKey: ['chat-session', projectId, sessionId] })
      toast.success('Chat session deleted!')
    },
    onError: (error: ChatApiError) => {
      toast.error(error.message || 'Failed to delete chat session')
    }
  })

  return {
    createSession: createSessionMutation.mutate,
    updateSession: updateSessionMutation.mutate,
    deleteSession: deleteSessionMutation.mutate,
    isCreating: createSessionMutation.isPending,
    isUpdating: updateSessionMutation.isPending,
    isDeleting: deleteSessionMutation.isPending
  }
}

/**
 * Hook for AI chat streaming functionality
 */
export function useStreamingChat(projectId: string | undefined) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentMessage, setCurrentMessage] = useState('')
  const [sources, setSources] = useState<DocumentSource[]>([])
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const queryClient = useQueryClient()

  const sendMessage = useCallback(async (
    request: SendMessageRequest,
    onMessageUpdate?: (content: string) => void,
    onComplete?: (message: ChatMessage, sessionId: string) => void
  ) => {
    if (!projectId) {
      toast.error('No project selected')
      return
    }

    setIsStreaming(true)
    setCurrentMessage('')
    setSources([])
    setError(null)

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController()

    try {
      const stream = await chatApi.sendMessage(request)
      const streamingGenerator = chatApi.parseStreamingResponse(stream)

      for await (const chunk of streamingGenerator) {
        // Check if cancelled
        if (abortControllerRef.current?.signal.aborted) {
          break
        }

        switch (chunk.type) {
          case 'token':
            if (chunk.content) {
              setCurrentMessage(prev => {
                const newContent = prev + chunk.content
                onMessageUpdate?.(newContent)
                return newContent
              })
            }
            break

          case 'sources':
            if (chunk.sources) {
              setSources(chunk.sources)
            }
            break

          case 'complete':
            if (chunk.message) {
              // Update chat session cache
              if (request.session_id) {
                queryClient.setQueryData(
                  ['chat-session', projectId, request.session_id],
                  (old: ChatSession | undefined) => {
                    if (!old) return old
                    return {
                      ...old,
                      messages: [...old.messages, chunk.message!],
                      updated_at: new Date().toISOString()
                    }
                  }
                )
              }
              
              onComplete?.(chunk.message, request.session_id || '')
            }
            break

          case 'error':
            setError(chunk.error || 'An error occurred')
            toast.error(chunk.error || 'Failed to send message')
            break
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }, [projectId, queryClient])

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsStreaming(false)
      toast('Message cancelled')
    }
  }, [])

  return {
    sendMessage,
    cancelStreaming,
    isStreaming,
    currentMessage,
    sources,
    error,
    clearError: () => setError(null)
  }
}

/**
 * Hook for chat history and search
 */
export function useChatHistory(projectId: string | undefined) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ChatMessage[]>([])
  const [isSearching, setIsSearching] = useState(false)

  // Get chat history
  const historyQuery = useQuery({
    queryKey: ['chat-history', projectId],
    queryFn: () => chatApi.getChatHistory(projectId!, { limit: 50 }),
    enabled: !!projectId,
    staleTime: 1 * 60 * 1000, // 1 minute
  })

  // Search messages
  const searchMessages = useCallback(async (query: string) => {
    if (!projectId || !query.trim()) {
      setSearchResults([])
      return
    }

    setIsSearching(true)
    try {
      const results = await chatApi.searchMessages(projectId, query, { limit: 20 })
      setSearchResults(results)
    } catch (error) {
      toast.error('Failed to search messages')
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }, [projectId])

  return {
    history: historyQuery.data?.messages || [],
    totalMessages: historyQuery.data?.total || 0,
    isLoading: historyQuery.isLoading,
    searchQuery,
    setSearchQuery,
    searchResults,
    isSearching,
    searchMessages,
    refetch: historyQuery.refetch
  }
}

/**
 * Hook for suggested questions
 */
export function useSuggestedQuestions(projectId: string | undefined) {
  const suggestionsQuery = useQuery({
    queryKey: ['chat-suggestions', projectId],
    queryFn: () => chatApi.getSuggestedQuestions(projectId!),
    enabled: !!projectId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  return {
    suggestions: suggestionsQuery.data || [],
    isLoading: suggestionsQuery.isLoading,
    error: suggestionsQuery.error,
    refetch: suggestionsQuery.refetch
  }
}

/**
 * Hook for managing chat UI state
 */
export function useChatUI() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [showSources, setShowSources] = useState(false)
  const [messageInput, setMessageInput] = useState('')

  return {
    selectedSessionId,
    setSelectedSessionId,
    isSidebarOpen,
    setIsSidebarOpen,
    showSources,
    setShowSources,
    messageInput,
    setMessageInput,
    clearInput: () => setMessageInput('')
  }
}
