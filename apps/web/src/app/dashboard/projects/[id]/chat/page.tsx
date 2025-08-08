/**
 * AI Chat Interface Page
 * Main chat interface for AI-powered project knowledge queries
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import { 
  Send, 
  Plus, 
  MessageSquare, 
  Search, 
  Settings, 
  Sidebar, 
  X,
  Bot,
  User,
  FileText,
  Github,
  Slack,
  ExternalLink,
  Clock,
  Zap,
  StopCircle,
  Lightbulb
} from 'lucide-react'
import { Button } from '../../../../../components/ui/button'
import { Input } from '../../../../../components/ui/input'
import { Textarea } from '../../../../../components/ui/textarea'
import { 
  useChatSessions, 
  useChatSession, 
  useChatSessionMutations,
  useStreamingChat,
  useSuggestedQuestions,
  useChatUI
} from '../../../../../hooks/useChat'
import { useProject } from '../../../../../hooks/useProjects'
import { ChatMessage, DocumentSource } from '../../../../../lib/api/chat'

export default function ChatPage() {
  const params = useParams()
  const projectId = params.id as string
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { project } = useProject(projectId)
  const { sessions, isLoading: sessionsLoading } = useChatSessions(projectId)
  const { createSession } = useChatSessionMutations(projectId)
  const { suggestions } = useSuggestedQuestions(projectId)
  const {
    selectedSessionId,
    setSelectedSessionId,
    isSidebarOpen,
    setIsSidebarOpen,
    showSources,
    setShowSources,
    messageInput,
    setMessageInput,
    clearInput
  } = useChatUI()

  const { session, isLoading: sessionLoading } = useChatSession(projectId, selectedSessionId || undefined)
  const {
    sendMessage,
    cancelStreaming,
    isStreaming,
    currentMessage,
    sources,
    error
  } = useStreamingChat(projectId)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [session?.messages, currentMessage])

  // Select first session by default
  useEffect(() => {
    if (sessions.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessions[0].id)
    }
  }, [sessions, selectedSessionId, setSelectedSessionId])

  const handleSendMessage = async () => {
    if (!messageInput.trim() || isStreaming) return

    const message = messageInput.trim()
    clearInput()

    // Create new session if none selected
    let sessionId = selectedSessionId
    if (!sessionId) {
      const newSession = await new Promise<string>((resolve) => {
        createSession(undefined, {
          onSuccess: (session) => {
            setSelectedSessionId(session.id)
            resolve(session.id)
          }
        })
      })
      sessionId = newSession
    }

    await sendMessage({
      message,
      project_id: projectId,
      session_id: sessionId,
      ai_settings: {
        model: project?.settings?.ai_model || 'gpt-4'
      }
    })
  }

  const handleSuggestionClick = (suggestion: string) => {
    setMessageInput(suggestion)
  }

  const handleNewChat = () => {
    createSession(undefined, {
      onSuccess: (session) => {
        setSelectedSessionId(session.id)
      }
    })
  }

  if (sessionsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-gray-50">
      {/* Sidebar */}
      {isSidebarOpen && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Chat Sessions</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSidebarOpen(false)}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <Button onClick={handleNewChat} className="w-full flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-2">
            {sessions.map((chatSession) => (
              <button
                key={chatSession.id}
                onClick={() => setSelectedSessionId(chatSession.id)}
                className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                  selectedSessionId === chatSession.id
                    ? 'bg-purple-50 border border-purple-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <MessageSquare className="h-4 w-4 text-gray-400 mt-1" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {chatSession.title || 'New Chat'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {chatSession.messages.length} messages
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(chatSession.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {!isSidebarOpen && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsSidebarOpen(true)}
                  className="h-8 w-8 p-0"
                >
                  <Sidebar className="h-4 w-4" />
                </Button>
              )}
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {project?.name} AI Assistant
                </h1>
                <p className="text-sm text-gray-600">
                  Ask questions about your project knowledge
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSources(!showSources)}
                className={showSources ? 'bg-purple-50' : ''}
              >
                <FileText className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!session && sessions.length === 0 ? (
            <WelcomeScreen 
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              onNewChat={handleNewChat}
            />
          ) : sessionLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <>
              {session?.messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              
              {/* Streaming Message */}
              {isStreaming && currentMessage && (
                <MessageBubble
                  message={{
                    id: 'streaming',
                    role: 'assistant',
                    content: currentMessage,
                    timestamp: new Date().toISOString()
                  }}
                  isStreaming={true}
                />
              )}
              
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Sources Panel */}
        {showSources && sources.length > 0 && (
          <div className="bg-white border-t border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Sources</h3>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {sources.map((source) => (
                <SourceCard key={source.id} source={source} />
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <Textarea
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                placeholder="Ask anything about your project..."
                rows={1}
                className="resize-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
              />
            </div>
            <div className="flex items-center gap-2">
              {isStreaming ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={cancelStreaming}
                  className="flex items-center gap-2"
                >
                  <StopCircle className="h-4 w-4" />
                  Stop
                </Button>
              ) : (
                <Button
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim()}
                  className="flex items-center gap-2"
                >
                  <Send className="h-4 w-4" />
                  Send
                </Button>
              )}
            </div>
          </div>
          
          {error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
  isStreaming?: boolean
}

function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-purple-600' : 'bg-gray-200'
        }`}>
          {isUser ? (
            <User className="h-4 w-4 text-white" />
          ) : (
            <Bot className="h-4 w-4 text-gray-600" />
          )}
        </div>
        
        <div className={`rounded-lg p-4 ${
          isUser 
            ? 'bg-purple-600 text-white' 
            : 'bg-white border border-gray-200'
        }`}>
          <div className="prose prose-sm max-w-none">
            <p className={isUser ? 'text-white' : 'text-gray-900'}>
              {message.content}
              {isStreaming && <span className="animate-pulse">|</span>}
            </p>
          </div>
          
          {!isUser && message.tokens_used && (
            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
              <Zap className="h-3 w-3" />
              {message.tokens_used} tokens
              {message.confidence_score && (
                <span>• {Math.round(message.confidence_score * 100)}% confidence</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface SourceCardProps {
  source: DocumentSource
}

function SourceCard({ source }: SourceCardProps) {
  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'github':
        return <Github className="h-3 w-3" />
      case 'slack':
        return <Slack className="h-3 w-3" />
      case 'jira':
        return <ExternalLink className="h-3 w-3" />
      default:
        return <FileText className="h-3 w-3" />
    }
  }

  return (
    <div className="flex items-start gap-2 p-2 bg-gray-50 rounded text-xs">
      <div className="text-gray-400 mt-0.5">
        {getSourceIcon(source.type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 truncate">{source.title}</p>
        <p className="text-gray-600 line-clamp-2">{source.excerpt}</p>
        <div className="flex items-center gap-2 mt-1 text-gray-400">
          <Clock className="h-3 w-3" />
          {new Date(source.last_updated).toLocaleDateString()}
          <span>• {Math.round(source.relevance_score * 100)}% relevant</span>
        </div>
      </div>
    </div>
  )
}

interface WelcomeScreenProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
  onNewChat: () => void
}

function WelcomeScreen({ suggestions, onSuggestionClick, onNewChat }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <div className="mb-8">
        <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4 mx-auto">
          <Bot className="h-8 w-8 text-purple-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to NeuroSync AI
        </h2>
        <p className="text-gray-600 max-w-md">
          Ask questions about your project, get insights from your codebase, 
          and explore your knowledge base with AI assistance.
        </p>
      </div>

      {suggestions.length > 0 && (
        <div className="w-full max-w-2xl">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium text-gray-700">Suggested questions</span>
          </div>
          <div className="grid gap-3">
            {suggestions.slice(0, 4).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="text-left p-4 bg-white border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors"
              >
                <p className="text-sm text-gray-900">{suggestion}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <Button onClick={onNewChat} className="mt-8 flex items-center gap-2">
        <Plus className="h-4 w-4" />
        Start New Chat
      </Button>
    </div>
  )
}
