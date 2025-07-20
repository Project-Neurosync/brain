'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import Link from 'next/link'
import { 
  CodeIcon,
  KeyIcon,
  BookOpenIcon,
  ZapIcon,
  ShieldIcon,
  GlobeIcon,
  CopyIcon,
  CheckIcon,
  ExternalLinkIcon,
  DatabaseIcon,
  BrainIcon,
  SearchIcon
} from 'lucide-react'

export default function APIPage() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(id)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/auth/login',
      description: 'Authenticate user and receive access token',
      auth: false,
      example: `curl -X POST "https://api.neurosync.ai/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "password123"}'`
    },
    {
      method: 'POST',
      path: '/api/v1/ai/query',
      description: 'Submit AI query and get intelligent response',
      auth: true,
      example: `curl -X POST "https://api.neurosync.ai/v1/ai/query" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "How does authentication work?", "project_id": "proj_123"}'`
    },
    {
      method: 'GET',
      path: '/api/v1/projects',
      description: 'List all projects for authenticated user',
      auth: true,
      example: `curl -X GET "https://api.neurosync.ai/v1/projects" \\
  -H "Authorization: Bearer YOUR_TOKEN"`
    }
  ]

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-green-100 text-green-800'
      case 'POST': return 'bg-blue-100 text-blue-800'
      case 'PUT': return 'bg-orange-100 text-orange-800'
      case 'DELETE': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            API Documentation
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            NeuroSync
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> API</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Powerful REST API to integrate NeuroSync's AI capabilities into your applications and workflows.
          </p>
          
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="#getting-started">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="#endpoints">View Endpoints</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <ZapIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>99.9%</CardTitle>
                  <CardDescription>API Uptime</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <GlobeIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>&lt;200ms</CardTitle>
                  <CardDescription>Avg Response</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <ShieldIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Enterprise</CardTitle>
                  <CardDescription>Security</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <BookOpenIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>RESTful</CardTitle>
                  <CardDescription>Design</CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Getting Started */}
      <section id="getting-started" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Getting Started</h2>
              <p className="text-xl text-gray-600">
                Start integrating with NeuroSync API in minutes.
              </p>
            </div>

            <Tabs defaultValue="authentication" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="authentication">Authentication</TabsTrigger>
                <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
                <TabsTrigger value="rate-limits">Rate Limits</TabsTrigger>
              </TabsList>

              <TabsContent value="authentication" className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <KeyIcon className="h-5 w-5" />
                      API Authentication
                    </CardTitle>
                    <CardDescription>
                      NeuroSync API uses Bearer token authentication. Get your API key from the dashboard.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">1. Get Your API Key</h4>
                        <p className="text-gray-600 mb-4">
                          Navigate to your dashboard settings and generate a new API key.
                        </p>
                        <Button variant="outline" asChild>
                          <Link href="/dashboard/settings">
                            <KeyIcon className="h-4 w-4 mr-2" />
                            Generate API Key
                          </Link>
                        </Button>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">2. Include in Headers</h4>
                        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg relative">
                          <pre className="text-sm">
{`Authorization: Bearer YOUR_API_KEY
Content-Type: application/json`}
                          </pre>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="absolute top-2 right-2 text-gray-400 hover:text-gray-100"
                            onClick={() => copyToClipboard('Authorization: Bearer YOUR_API_KEY\nContent-Type: application/json', 'auth-headers')}
                          >
                            {copiedCode === 'auth-headers' ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="quickstart" className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ZapIcon className="h-5 w-5" />
                      Quick Start Example
                    </CardTitle>
                    <CardDescription>
                      Make your first API call to query NeuroSync AI.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Example: AI Query</h4>
                        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg relative">
                          <pre className="text-sm overflow-x-auto">
{`curl -X POST "https://api.neurosync.ai/v1/ai/query" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How does user authentication work?",
    "project_id": "proj_abc123"
  }'`}
                          </pre>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="absolute top-2 right-2 text-gray-400 hover:text-gray-100"
                            onClick={() => copyToClipboard(`curl -X POST "https://api.neurosync.ai/v1/ai/query" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How does user authentication work?",
    "project_id": "proj_abc123"
  }'`, 'quickstart-example')}
                          >
                            {copiedCode === 'quickstart-example' ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Response</h4>
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <pre className="text-sm text-gray-700">
{`{
  "response": "The project uses JWT-based authentication...",
  "tokens_used": 45,
  "cost": 0.002,
  "sources": [
    {
      "title": "auth.py",
      "type": "code",
      "relevance": 0.95
    }
  ]
}`}
                          </pre>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="rate-limits" className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ShieldIcon className="h-5 w-5" />
                      Rate Limits
                    </CardTitle>
                    <CardDescription>
                      API rate limits by subscription tier.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="border rounded-lg p-4 text-center">
                        <h4 className="font-medium text-gray-900 mb-2">Starter</h4>
                        <div className="text-2xl font-bold text-purple-600 mb-1">100</div>
                        <p className="text-sm text-gray-600">requests per minute</p>
                      </div>

                      <div className="border rounded-lg p-4 text-center">
                        <h4 className="font-medium text-gray-900 mb-2">Professional</h4>
                        <div className="text-2xl font-bold text-blue-600 mb-1">500</div>
                        <p className="text-sm text-gray-600">requests per minute</p>
                      </div>

                      <div className="border rounded-lg p-4 text-center">
                        <h4 className="font-medium text-gray-900 mb-2">Enterprise</h4>
                        <div className="text-2xl font-bold text-green-600 mb-1">2000</div>
                        <p className="text-sm text-gray-600">requests per minute</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </section>

      {/* API Endpoints */}
      <section id="endpoints" className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">API Endpoints</h2>
              <p className="text-xl text-gray-600">
                Complete reference for all available endpoints.
              </p>
            </div>

            <div className="space-y-6">
              {endpoints.map((endpoint, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={getMethodColor(endpoint.method)}>
                          {endpoint.method}
                        </Badge>
                        <code className="text-lg font-mono">{endpoint.path}</code>
                        {endpoint.auth && (
                          <Badge variant="outline" className="text-xs">
                            <KeyIcon className="h-3 w-3 mr-1" />
                            Auth Required
                          </Badge>
                        )}
                      </div>
                    </div>
                    <CardDescription>{endpoint.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-900 text-gray-100 p-4 rounded-lg relative">
                      <pre className="text-sm overflow-x-auto">{endpoint.example}</pre>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="absolute top-2 right-2 text-gray-400 hover:text-gray-100"
                        onClick={() => copyToClipboard(endpoint.example, `example-${index}`)}
                      >
                        {copiedCode === `example-${index}` ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Use Cases</h2>
              <p className="text-xl text-gray-600">
                Common integration patterns and use cases.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                    <BrainIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>AI-Powered Chatbots</CardTitle>
                  <CardDescription>
                    Build intelligent chatbots that understand your codebase and documentation.
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mb-4">
                    <SearchIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Smart Search</CardTitle>
                  <CardDescription>
                    Add semantic search capabilities to your applications and documentation.
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <DatabaseIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Knowledge Management</CardTitle>
                  <CardDescription>
                    Automatically organize and retrieve information from multiple data sources.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Support */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Need Help with Integration?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Our developer support team is here to help you get up and running quickly.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/contact">Contact Support</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/docs">View Full Docs</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
