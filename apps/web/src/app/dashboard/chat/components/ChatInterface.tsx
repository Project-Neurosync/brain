"use client";

import React, { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ProjectSelector } from './ProjectSelector';
import { useChat } from '../hooks/useChat';
import { Loader2 } from 'lucide-react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    url?: string;
    type: string;
  }>;
}

export function ChatInterface() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages
  } = useChat(selectedProjectId, conversationId);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    try {
      const response = await sendMessage(content);
      if (response?.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleProjectChange = (projectId: string | null) => {
    setSelectedProjectId(projectId);
    // Clear conversation when switching projects
    setConversationId(null);
    clearMessages();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-250px)] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
          {selectedProjectId && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              Project Context
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          <ProjectSelector
            selectedProjectId={selectedProjectId}
            onProjectChange={handleProjectChange}
          />
          
          <button
            onClick={clearMessages}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center text-gray-500 mt-8">
            <div className="mb-4">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.405L3 21l2.595-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Welcome to NeuroSync AI Chat
              </h3>
              <p className="text-gray-600 max-w-md mx-auto">
                Ask questions about your integrated data sources. I can help you understand your code, 
                track issues, analyze team communications, and more.
              </p>
              {!selectedProjectId && (
                <p className="text-sm text-blue-600 mt-4">
                  💡 Select a project above to get context-specific answers
                </p>
              )}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>AI is thinking...</span>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder={
            selectedProjectId 
              ? "Ask about your project data..." 
              : "Ask a question or select a project for context..."
          }
        />
      </div>
    </div>
  );
}
