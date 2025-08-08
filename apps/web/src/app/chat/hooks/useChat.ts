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
  sendMessage: (content: string) => Promise<ChatResponse | null>;
  clearMessages: () => void;
}

export function useChat(
  projectId: string | null,
  conversationId: string | null
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string): Promise<ChatResponse | null> => {
    if (!content.trim()) return null;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message: content,
          project_id: projectId,
          conversation_id: conversationId,
          stream: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: data.id,
        role: 'assistant',
        content: data.message,
        timestamp: new Date(data.timestamp),
        sources: data.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
      return data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Add error message to chat
      const errorChatMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorChatMessage]);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [projectId, conversationId]);

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
