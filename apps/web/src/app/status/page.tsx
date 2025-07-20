'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { 
  CheckCircleIcon,
  AlertTriangleIcon,
  XCircleIcon,
  ClockIcon,
  TrendingUpIcon,
  ServerIcon,
  DatabaseIcon,
  CloudIcon,
  ZapIcon,
  RefreshCwIcon
} from 'lucide-react'

interface ServiceStatus {
  name: string
  status: 'operational' | 'degraded' | 'down' | 'maintenance'
  description: string
  uptime: string
  responseTime: string
  lastChecked: string
}

interface Incident {
  id: string
  title: string
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved'
  severity: 'minor' | 'major' | 'critical'
  description: string
  startTime: string
  endTime?: string
  updates: {
    time: string
    message: string
    status: string
  }[]
}

export default function StatusPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'API Gateway',
      status: 'operational',
      description: 'Core API endpoints and authentication',
      uptime: '99.98%',
      responseTime: '145ms',
      lastChecked: new Date().toISOString()
    },
    {
      name: 'AI Processing',
      status: 'operational',
      description: 'AI query processing and model inference',
      uptime: '99.95%',
      responseTime: '1.2s',
      lastChecked: new Date().toISOString()
    },
    {
      name: 'Vector Database',
      status: 'operational',
      description: 'Semantic search and embeddings storage',
      uptime: '99.99%',
      responseTime: '89ms',
      lastChecked: new Date().toISOString()
    },
    {
      name: 'Data Ingestion',
      status: 'operational',
      description: 'GitHub, Slack, and Jira integrations',
      uptime: '99.92%',
      responseTime: '2.1s',
      lastChecked: new Date().toISOString()
    },
    {
      name: 'Web Application',
      status: 'operational',
      description: 'Frontend dashboard and user interface',
      uptime: '99.97%',
      responseTime: '234ms',
      lastChecked: new Date().toISOString()
    },
    {
      name: 'Authentication',
      status: 'operational',
      description: 'User login and session management',
      uptime: '99.99%',
      responseTime: '67ms',
      lastChecked: new Date().toISOString()
    }
  ])

  const [incidents, setIncidents] = useState<Incident[]>([
    {
      id: '1',
      title: 'Increased API Response Times',
      status: 'resolved',
      severity: 'minor',
      description: 'Some users experienced slower than normal API response times due to increased traffic.',
      startTime: '2024-01-15T14:30:00Z',
      endTime: '2024-01-15T15:45:00Z',
      updates: [
        {
          time: '2024-01-15T15:45:00Z',
          message: 'Issue has been resolved. All services are operating normally.',
          status: 'resolved'
        },
        {
          time: '2024-01-15T15:15:00Z',
          message: 'We have identified the cause and are implementing a fix.',
          status: 'identified'
        },
        {
          time: '2024-01-15T14:30:00Z',
          message: 'We are investigating reports of increased API response times.',
          status: 'investigating'
        }
      ]
    }
  ])

  const [loading, setLoading] = useState(false)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />
      case 'degraded':
        return <AlertTriangleIcon className="h-5 w-5 text-yellow-600" />
      case 'down':
        return <XCircleIcon className="h-5 w-5 text-red-600" />
      case 'maintenance':
        return <ClockIcon className="h-5 w-5 text-blue-600" />
      default:
        return <CheckCircleIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'bg-green-100 text-green-800'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800'
      case 'down':
        return 'bg-red-100 text-red-800'
      case 'maintenance':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800'
      case 'major':
        return 'bg-orange-100 text-orange-800'
      case 'minor':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getIncidentStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
        return 'bg-green-100 text-green-800'
      case 'monitoring':
        return 'bg-blue-100 text-blue-800'
      case 'identified':
        return 'bg-orange-100 text-orange-800'
      case 'investigating':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const refreshStatus = async () => {
    setLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Update last checked times
    setServices(prev => prev.map(service => ({
      ...service,
      lastChecked: new Date().toISOString()
    })))
    
    setLoading(false)
  }

  const overallStatus = services.every(s => s.status === 'operational') 
    ? 'operational' 
    : services.some(s => s.status === 'down') 
    ? 'down' 
    : 'degraded'

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            System Status
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            NeuroSync
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> Status</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Real-time status and uptime monitoring for all NeuroSync services and infrastructure.
          </p>
          
          {/* Overall Status */}
          <Card className="max-w-2xl mx-auto">
            <CardContent className="pt-6">
              <div className="flex items-center justify-center gap-4">
                {getStatusIcon(overallStatus)}
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {overallStatus === 'operational' ? 'All Systems Operational' : 
                     overallStatus === 'down' ? 'Service Disruption' : 'Degraded Performance'}
                  </h2>
                  <p className="text-gray-600">
                    {overallStatus === 'operational' 
                      ? 'All services are running normally'
                      : 'Some services are experiencing issues'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Services Status */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-12">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Service Status</h2>
                <p className="text-xl text-gray-600">
                  Current status of all NeuroSync services and components.
                </p>
              </div>
              <Button 
                variant="outline" 
                onClick={refreshStatus}
                disabled={loading}
                className="flex items-center gap-2"
              >
                <RefreshCwIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>

            <div className="space-y-4">
              {services.map((service, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(service.status)}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                          <p className="text-gray-600">{service.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6 text-right">
                        <div>
                          <Badge className={getStatusColor(service.status)}>
                            {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600">
                          <div>Uptime: <span className="font-medium">{service.uptime}</span></div>
                          <div>Response: <span className="font-medium">{service.responseTime}</span></div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Performance Metrics */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
              <p className="text-xl text-gray-600">
                Key performance indicators over the last 30 days.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <TrendingUpIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>99.97%</CardTitle>
                  <CardDescription>Overall Uptime</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <ZapIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>187ms</CardTitle>
                  <CardDescription>Avg Response Time</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <ServerIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>0</CardTitle>
                  <CardDescription>Critical Incidents</CardDescription>
                </CardHeader>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <DatabaseIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>2.1s</CardTitle>
                  <CardDescription>AI Query Time</CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Incidents */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Recent Incidents</h2>
              <p className="text-xl text-gray-600">
                History of service incidents and their resolutions.
              </p>
            </div>

            {incidents.length > 0 ? (
              <div className="space-y-6">
                {incidents.map((incident) => (
                  <Card key={incident.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">{incident.title}</CardTitle>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className={getIncidentStatusColor(incident.status)}>
                              {incident.status.charAt(0).toUpperCase() + incident.status.slice(1)}
                            </Badge>
                            <Badge className={getSeverityColor(incident.severity)}>
                              {incident.severity.charAt(0).toUpperCase() + incident.severity.slice(1)}
                            </Badge>
                          </div>
                        </div>
                        <div className="text-right text-sm text-gray-600">
                          <div>Started: {new Date(incident.startTime).toLocaleString()}</div>
                          {incident.endTime && (
                            <div>Resolved: {new Date(incident.endTime).toLocaleString()}</div>
                          )}
                        </div>
                      </div>
                      <CardDescription>{incident.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <h4 className="font-medium text-gray-900">Updates:</h4>
                        {incident.updates.map((update, idx) => (
                          <div key={idx} className="flex gap-3 text-sm">
                            <div className="text-gray-500 min-w-0 flex-shrink-0">
                              {new Date(update.time).toLocaleString()}
                            </div>
                            <div className="text-gray-700">{update.message}</div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6 text-center">
                  <CheckCircleIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No Recent Incidents
                  </h3>
                  <p className="text-gray-600">
                    All systems have been running smoothly with no reported incidents in the last 30 days.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>

      {/* Subscribe to Updates */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Stay Informed
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Subscribe to status updates and get notified about incidents and maintenance windows.
            </p>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <input
                    type="email"
                    placeholder="Enter your email address"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <Button>
                    Subscribe
                  </Button>
                </div>
                <p className="text-sm text-gray-500 mt-3">
                  Get notified about incidents, maintenance, and service updates.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Support */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Need Help?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            If you're experiencing issues not reflected on this page, please contact our support team.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/contact">Contact Support</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/docs">View Documentation</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
