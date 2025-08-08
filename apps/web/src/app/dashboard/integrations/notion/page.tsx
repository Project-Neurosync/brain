'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, FileText, CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectIntegrationModal } from '@/components/integrations/ConnectIntegrationModal'
import { useAuth } from '@/hooks/useAuth'
import { useIntegration, useIntegrationMutations, useIntegrationSync } from '@/hooks/useIntegrations'

export default function NotionIntegrationPage() {
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
    // We use the integration type as identifier
    'notion'
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
        message: 'Successfully connected to Notion!'
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to connect to Notion'
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
        <div className="bg-gray-100 p-3 rounded-lg">
          <FileText className="h-6 w-6 text-gray-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Notion Integration</h1>
          <p className="text-gray-600">
            Connect your Notion workspace to make your documents searchable
          </p>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Manage your Notion connection
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
                    <h3 className="font-medium text-green-900">Connected to Notion</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your Notion workspace is successfully connected
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Integration Token:</span>
                    <span className="font-medium">•••••••••••••••••</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Databases:</span>
                    <span className="font-medium">
                      {integration.config.database_ids && integration.config.database_ids.length > 0 
                        ? `${integration.config.database_ids.length} databases` 
                        : 'All accessible databases'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include Pages:</span>
                    <span className="font-medium">
                      {integration.config.include_pages ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include Comments:</span>
                    <span className="font-medium">
                      {integration.config.include_comments ? 'Yes' : 'No'}
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
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-start gap-3">
                  <FileText className="h-5 w-5 text-gray-600 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-gray-900">Connect to Notion</h3>
                    <p className="text-sm text-gray-700 mt-1">
                      Connect your Notion workspace to make your documents searchable in NeuroSync
                    </p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => setIsModalOpen(true)}
                  className="w-full"
                >
                  Connect Notion
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>
              Learn how to use the Notion integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">What is synced?</h3>
                <p className="text-sm text-gray-600">
                  The Notion integration syncs pages, databases, and comments from your Notion workspace.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Requirements</h3>
                <ul className="list-disc text-sm text-gray-600 pl-5 space-y-1">
                  <li>Notion workspace with admin or integration creation access</li>
                  <li>Integration token with read permissions</li>
                  <li>Database IDs (optional, for specific databases)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to get an integration token</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Go to <a href="https://www.notion.so/my-integrations" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Notion Integrations</a></li>
                  <li>Click "New integration"</li>
                  <li>Enter a name (e.g., "NeuroSync")</li>
                  <li>Select your workspace</li>
                  <li>Set capabilities (at minimum: Read content, Read user information)</li>
                  <li>Click "Submit" and copy the token</li>
                </ol>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to find a database ID</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Open a Notion database in your browser</li>
                  <li>Look at the URL, e.g., https://notion.so/workspace/8e4895b0f1a34e8aaa7ca...</li>
                  <li>The database ID is the last part of the URL</li>
                </ol>
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
        integrationType="notion"
      />
    </div>
  )
}
