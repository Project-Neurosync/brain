"use client";

import { useState, useCallback } from 'react';
import { ChatMessage } from '../components/ChatInterface';

interface ChatResponse {
  id: string;
  message: string;
  conversation_id: string;
  sources: Array<{
    title: string;
    url?: string;
    type: string;
  }>;
  confidence: number;
  timestamp: string;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string, projectId?: string) => Promise<void>;
  clearMessages: () => void;
}

export function useChat(
  initialProjectId: string | null = null,
  initialConversationId: string | null = null
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId);

  const sendMessage = useCallback(async (content: string, projectId?: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Create placeholder assistant message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      sources: [],
    };
    
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message: content,
          project_id: projectId || initialProjectId,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (!data) continue;
              
              try {
                const parsed = JSON.parse(data);
                
                if (parsed.type === 'sources') {
                  // Update the assistant message with sources
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, sources: parsed.sources }
                      : msg
                  ));
                } else if (parsed.type === 'token') {
                  // Accumulate content tokens
                  accumulatedContent += parsed.content;
                  
                  // Update the assistant message with accumulated content
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ));
                } else if (parsed.type === 'complete') {
                  setIsLoading(false);
                  return;
                }
              } catch (e) {
                // Handle legacy format or plain text
                if (data === '[DONE]') {
                  setIsLoading(false);
                  return;
                }
                if (data.startsWith('Error:')) {
                  throw new Error(data);
                }
                
                // Treat as plain text token
                accumulatedContent += data;
                
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                ));
              }
            }
          }
        }
      }

      // Get conversation ID from response headers
      const newConversationId = response.headers.get('X-Conversation-ID');
      if (newConversationId) {
        setConversationId(newConversationId);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message');
      
      // Remove the placeholder message on error
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
    } finally {
      setIsLoading(false);
    }
  }, [initialProjectId, conversationId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };
}
