'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { authService } from '@/lib/auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  SendIcon, 
  BotIcon, 
  UserIcon,
  SparklesIcon,
  ClockIcon,
  CoinsIcon,
  BrainIcon
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  tokens_used?: number
  model_used?: string
}

export default function ChatPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your NeuroSync AI assistant. I can help you understand your codebase, answer questions about your projects, and assist with development tasks. What would you like to know?",
      role: 'assistant',
      timestamp: new Date(),
      model_used: 'gpt-4o-mini'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !authService.getAccessToken()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Simulate API call to backend
      const response = await fetch('/api/v1/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getAccessToken()}`
        },
        body: JSON.stringify({
          query: inputValue,
          context: messages.slice(-5).map(m => ({ role: m.role, content: m.content }))
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get AI response')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response || "I'm sorry, I couldn't process your request right now. Please try again.",
        role: 'assistant',
        timestamp: new Date(),
        tokens_used: data.tokens_used || 0,
        model_used: data.model_used || 'gpt-4o-mini'
      }

      setMessages(prev => [...prev, assistantMessage])

      if (data.tokens_used) {
        toast({
          title: "Query processed",
          description: `Used ${data.tokens_used} tokens with ${data.model_used}`,
        })
      }
    } catch (error) {
      console.error('Chat error:', error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm sorry, I encountered an error processing your request. Please try again or check your connection.",
        role: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, errorMessage])
      
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getModelBadgeColor = (model: string) => {
    switch (model) {
      case 'gpt-4': return 'bg-purple-100 text-purple-800'
      case 'gpt-4o': return 'bg-blue-100 text-blue-800'
      case 'gpt-4o-mini': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BrainIcon className="h-6 w-6 text-purple-600" />
              AI Chat
            </h1>
            <p className="text-gray-600 mt-1">
              Ask questions about your codebase and projects
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-600">Tokens remaining</p>
              <p className="text-lg font-semibold text-purple-600">
                {user?.tokens_remaining?.toLocaleString() || '0'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 p-6">
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <BotIcon className="h-4 w-4 text-white" />
                  </div>
                )}
                
                <div
                  className={`max-w-[70%] ${
                    message.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  } rounded-lg p-4`}
                >
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200/20">
                    <div className="flex items-center gap-2 text-xs opacity-70">
                      <ClockIcon className="h-3 w-3" />
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                    
                    {message.role === 'assistant' && (
                      <div className="flex items-center gap-2">
                        {message.tokens_used && (
                          <Badge variant="outline" className="text-xs">
                            <CoinsIcon className="h-3 w-3 mr-1" />
                            {message.tokens_used}
                          </Badge>
                        )}
                        {message.model_used && (
                          <Badge className={`text-xs ${getModelBadgeColor(message.model_used)}`}>
                            {message.model_used}
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <UserIcon className="h-4 w-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <BotIcon className="h-4 w-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <SparklesIcon className="h-4 w-4 animate-pulse" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your codebase..."
                  disabled={isLoading}
                  className="text-base"
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="px-6"
              >
                <SendIcon className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <p>Press Enter to send, Shift+Enter for new line</p>
              <p>Powered by NeuroSync AI</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
