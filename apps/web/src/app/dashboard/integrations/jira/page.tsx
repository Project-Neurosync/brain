'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, TicketCheck, CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectIntegrationModal } from '@/components/integrations/ConnectIntegrationModal'
import { useAuth } from '@/hooks/useAuth'
import { useIntegration, useIntegrationMutations, useIntegrationSync } from '@/hooks/useIntegrations'

// Custom Jira icon since it's not in lucide-react
const JiraIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className="h-full w-full"
  >
    <path d="M11.53 2.3A1.85 1.85 0 0 0 10 4.06v15.88c0 1.24 1.64 2.06 3 1.47l8-3.5c1.52-.67 1.52-2.27 0-2.94l-8-3.5A1.85 1.85 0 0 0 10 13V4.06c0-1.31 1.64-2.06 3-1.47l8 3.5c1.52.67 1.52 2.27 0 2.94l-2.57 1.13" fill="none" />
    <path d="M7 5.07A1.82 1.82 0 0 0 5.89 6.5v11c0 1.24-1.64 2.06-3 1.47l-1.86-.82" fill="none" />
  </svg>
)

export default function JiraIntegrationPage() {
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
    'jira'
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
        message: 'Successfully connected to Jira instance!'
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to connect to Jira'
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
          <div className="h-6 w-6 text-blue-600">
            <JiraIcon />
          </div>
        </div>
        <div>
          <h1 className="text-2xl font-bold">Jira Integration</h1>
          <p className="text-gray-600">
            Connect your Jira projects to analyze issues, tasks, and project management data
          </p>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Manage your Jira connection
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
                    <h3 className="font-medium text-green-900">Connected to Jira</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your Jira instance is successfully connected
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Jira URL:</span>
                    <span className="font-medium">{integration.config.jira_url}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Projects:</span>
                    <span className="font-medium">
                      {integration.config.projects && integration.config.projects.length > 0 
                        ? integration.config.projects.join(', ') 
                        : 'All accessible projects'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Username:</span>
                    <span className="font-medium">
                      {integration.config.username || 'Not specified'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include Comments:</span>
                    <span className="font-medium">
                      {integration.config.include_comments ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Sync Frequency:</span>
                    <span className="font-medium capitalize">
                      {integration.config.sync_frequency || 'daily'}
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
                  <div className="h-5 w-5 text-blue-600 mt-0.5">
                    <JiraIcon />
                  </div>
                  <div>
                    <h3 className="font-medium text-blue-900">Connect to Jira</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Connect your Jira instance to analyze issues, tasks, and project management data in NeuroSync
                    </p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => setIsModalOpen(true)}
                  className="w-full"
                >
                  Connect Jira
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>
              Learn how to use the Jira integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">What is synced?</h3>
                <p className="text-sm text-gray-600">
                  The Jira integration syncs issues, tasks, comments, and attachments from your Jira projects.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Requirements</h3>
                <ul className="list-disc text-sm text-gray-600 pl-5 space-y-1">
                  <li>Jira Cloud or Server instance URL</li>
                  <li>API token or username/password for authentication</li>
                  <li>Project keys to sync (optional, will sync all accessible projects if not specified)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to get a Jira API token</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Log in to <a href="https://id.atlassian.com/manage-profile/security/api-tokens" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Atlassian account settings</a></li>
                  <li>Click "Create API token"</li>
                  <li>Enter a label for your token (e.g., "NeuroSync Integration")</li>
                  <li>Click "Create" and copy your token</li>
                </ol>
                <p className="text-sm text-gray-600 mt-2">
                  <strong>Note:</strong> For Jira Server/Data Center instances, you'll need to use basic authentication with your username and password or create a service account.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Finding your Jira URL</h3>
                <p className="text-sm text-gray-600">
                  For Jira Cloud, your URL is typically in the format: <code>https://your-domain.atlassian.net</code><br />
                  For Jira Server, use your instance URL (e.g., <code>https://jira.yourdomain.com</code>)
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
        integrationType="jira"
      />
    </div>
  )
}
