"use client";

import React from 'react';
import { ChatMessage } from './ChatInterface';
import { User, Bot, ExternalLink } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-600'
          }`}>
            {isUser ? (
              <User className="w-4 h-4" />
            ) : (
              <Bot className="w-4 h-4" />
            )}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-2 rounded-lg ${
            isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-100 text-gray-900'
          }`}>
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
          </div>

          {/* Sources (for assistant messages) */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-2 space-y-1">
              <div className="text-xs text-gray-500 font-medium">Sources:</div>
              <div className="space-y-1">
                {message.sources.map((source, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-2 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded"
                  >
                    <span className="capitalize bg-gray-200 px-1 rounded text-xs">
                      {source.type}
                    </span>
                    <span className="flex-1 truncate">{source.title}</span>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="text-xs text-gray-500 mt-1">
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
