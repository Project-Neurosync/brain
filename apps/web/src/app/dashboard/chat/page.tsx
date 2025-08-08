"use client";

import React from 'react';
import { ChatInterface } from './components/ChatInterface';

export default function DashboardChatPage() {
  return (
    <div className="h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Chat</h1>
        <p className="text-gray-600 mt-1">
          Ask questions about your integrated data sources and get AI-powered insights
        </p>
      </div>
      
      <ChatInterface />
    </div>
  );
}
