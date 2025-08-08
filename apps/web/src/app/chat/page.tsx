"use client";

import React from 'react';
import { ChatInterface } from './components/ChatInterface';

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">NeuroSync AI Chat</h1>
          <p className="text-gray-600 mt-2">
            Ask questions about your integrated data sources and get AI-powered insights
          </p>
        </div>
        
        <ChatInterface />
      </div>
    </div>
  );
}
