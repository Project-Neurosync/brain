'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Slack, CheckCircle, XCircle, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectIntegrationModal } from '@/components/integrations/ConnectIntegrationModal'
import { useAuth } from '@/hooks/useAuth'
import { useIntegration, useIntegrationMutations, useIntegrationSync } from '@/hooks/useIntegrations'

export default function SlackIntegrationPage() {
  const router = useRouter()
  const { user } = useAuth()
  const projectId = user?.current_project_id || ''
  
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [testingConnection, setTestingConnection] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null)

  const { integration, isLoading, error, refetch } = useIntegration(
    projectId,
    'slack'
  )

  const { testIntegration } = useIntegrationSync(projectId)

  const handleTest = async () => {
    if (!integration) return
    
    setTestingConnection(true)
    setTestResult(null)
    
    try {
      const result = await testIntegration(integration.id)
      
      setTestResult({
        success: true,
        message: 'Successfully connected to Slack!'
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to connect to Slack'
      })
    } finally {
      setTestingConnection(false)
    }
  }

  return (
    <div className="container py-8">
      <Button
        variant="ghost"
        className="mb-6 pl-0 flex items-center gap-2"
        onClick={() => router.back()}
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>
      
      <div className="flex items-center gap-4 mb-8">
        <div className="bg-purple-100 p-3 rounded-lg">
          <Slack className="h-6 w-6 text-purple-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Slack Integration</h1>
          <p className="text-gray-600">
            Connect your Slack workspace to analyze conversations and knowledge sharing
          </p>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Manage your Slack workspace connection
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-8 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              </div>
            ) : integration ? (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-green-900">Connected to Slack</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your Slack workspace is successfully connected
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Workspace ID:</span>
                    <span className="font-medium">{integration.config.workspace_id}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Channels:</span>
                    <span className="font-medium">
                      {integration.config.channels && integration.config.channels.length > 0 
                        ? integration.config.channels.join(', ') 
                        : 'All accessible channels'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include Threads:</span>
                    <span className="font-medium">
                      {integration.config.include_threads ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Sync Frequency:</span>
                    <span className="font-medium capitalize">
                      {integration.config.sync_frequency || 'hourly'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Last sync:</span>
                    <span className="font-medium">
                      {integration.last_sync 
                        ? new Date(integration.last_sync).toLocaleString() 
                        : 'Never'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <span className="font-medium capitalize">{integration.status}</span>
                  </div>
                </div>
                
                <div className="pt-4 border-t space-y-3">
                  <Button 
                    onClick={handleTest}
                    disabled={testingConnection}
                    className="w-full"
                  >
                    {testingConnection ? 'Testing...' : 'Test Connection'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => setIsModalOpen(true)}
                    className="w-full"
                  >
                    Update Connection
                  </Button>
                </div>
                
                {testResult && (
                  <div className={`bg-${testResult.success ? 'green' : 'red'}-50 border border-${testResult.success ? 'green' : 'red'}-200 rounded-lg p-4 flex items-start gap-3`}>
                    {testResult.success ? (
                      <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                    )}
                    <div>
                      <h3 className={`font-medium text-${testResult.success ? 'green' : 'red'}-900`}>
                        {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                      </h3>
                      <p className={`text-sm text-${testResult.success ? 'green' : 'red'}-700 mt-1`}>
                        {testResult.message}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-start gap-3">
                  <Slack className="h-5 w-5 text-purple-600 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-purple-900">Connect to Slack</h3>
                    <p className="text-sm text-purple-700 mt-1">
                      Connect your Slack workspace to analyze conversations and knowledge sharing in NeuroSync
                    </p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => setIsModalOpen(true)}
                  className="w-full"
                >
                  Connect Slack
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>
              Learn how to use the Slack integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">What is synced?</h3>
                <p className="text-sm text-gray-600">
                  The Slack integration syncs messages, threads, and files from your Slack workspace channels.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Requirements</h3>
                <ul className="list-disc text-sm text-gray-600 pl-5 space-y-1">
                  <li>Slack workspace with admin or bot installation permissions</li>
                  <li>Bot User OAuth Token with appropriate scopes</li>
                  <li>Workspace ID (e.g., T1234567890)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to get a Slack Bot Token</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Go to <a href="https://api.slack.com/apps" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Slack API Apps</a></li>
                  <li>Click "Create New App" and select "From scratch"</li>
                  <li>Enter a name (e.g., "NeuroSync") and select your workspace</li>
                  <li>Go to "OAuth & Permissions" in the sidebar</li>
                  <li>Under "Scopes", add the following Bot Token Scopes:
                    <ul className="list-disc ml-5 mt-1">
                      <li>channels:history</li>
                      <li>channels:read</li>
                      <li>users:read</li>
                      <li>groups:history (for private channels)</li>
                      <li>groups:read (for private channels)</li>
                    </ul>
                  </li>
                  <li>Click "Install to Workspace" at the top of the page</li>
                  <li>Copy the "Bot User OAuth Token" (begins with xoxb-)</li>
                </ol>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Finding your Workspace ID</h3>
                <p className="text-sm text-gray-600">
                  Your Workspace ID is in the URL when you're logged into Slack in a browser. It starts with "T" followed by alphanumeric characters (e.g., T1234567890).
                </p>
              </div>
              
              <div className="pt-4 border-t">
                <h3 className="font-medium mb-2">Need Help?</h3>
                <Button variant="outline" className="w-full" onClick={() => router.push('/dashboard/support')}>
                  Contact Support
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Connect Integration Modal */}
      <ConnectIntegrationModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          refetch()
        }}
        projectId={projectId}
        integrationType="slack"
      />
    </div>
  )
}
