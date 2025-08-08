'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, FileText, CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectIntegrationModal } from '@/components/integrations/ConnectIntegrationModal'
import { useAuth } from '@/hooks/useAuth'
import { useIntegration, useIntegrationMutations, useIntegrationSync } from '@/hooks/useIntegrations'

export default function ConfluenceIntegrationPage() {
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
    'confluence'
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
        message: 'Successfully connected to Confluence!'
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to connect to Confluence'
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
        <div className="bg-blue-100 p-3 rounded-lg">
          <FileText className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Confluence Integration</h1>
          <p className="text-gray-600">
            Connect your Confluence workspace to make your documentation searchable
          </p>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Manage your Confluence connection
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
                    <h3 className="font-medium text-green-900">Connected to Confluence</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your Confluence workspace is successfully connected
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">URL:</span>
                    <span className="font-medium">{integration.config.confluence_url}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Username:</span>
                    <span className="font-medium">{integration.config.confluence_username}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Spaces:</span>
                    <span className="font-medium">
                      {integration.config.spaces && integration.config.spaces.length > 0 
                        ? integration.config.spaces.join(', ') 
                        : 'All spaces'}
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
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
                  <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-blue-900">Connect to Confluence</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Connect your Confluence workspace to make your documentation searchable in NeuroSync
                    </p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => setIsModalOpen(true)}
                  className="w-full"
                >
                  Connect Confluence
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>
              Learn how to use the Confluence integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">What is synced?</h3>
                <p className="text-sm text-gray-600">
                  The Confluence integration syncs pages, blogs, and comments from your Confluence workspace.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Requirements</h3>
                <ul className="list-disc text-sm text-gray-600 pl-5 space-y-1">
                  <li>Confluence Cloud or Server instance</li>
                  <li>Admin access or API token with read permissions</li>
                  <li>Confluence URL (e.g., https://yourcompany.atlassian.net/wiki)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to get an API token</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Go to <a href="https://id.atlassian.com/manage/api-tokens" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Atlassian API Tokens</a></li>
                  <li>Click "Create API token"</li>
                  <li>Enter a label (e.g., "NeuroSync Integration")</li>
                  <li>Copy the token and paste it in the connection form</li>
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
        integrationType="confluence"
      />
    </div>
  )
}
