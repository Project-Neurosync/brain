'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Github, CheckCircle, XCircle, GitBranch } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectIntegrationModal } from '@/components/integrations/ConnectIntegrationModal'
import { useAuth } from '@/hooks/useAuth'
import { useIntegration, useIntegrationMutations } from '@/hooks/useIntegrations'

export default function GitHubIntegrationPage() {
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
    'github'
  )

  const { testIntegration } = useIntegrationMutations(projectId)

  const handleTest = async () => {
    if (!integration) return
    
    setTestingConnection(true)
    setTestResult(null)
    
    try {
      const result = await testIntegration(integration.id)
      
      setTestResult({
        success: true,
        message: 'Successfully connected to GitHub repository!'
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to connect to GitHub'
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
        <div className="bg-slate-100 p-3 rounded-lg">
          <Github className="h-6 w-6 text-slate-800" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">GitHub Integration</h1>
          <p className="text-gray-600">
            Connect your GitHub repository to analyze code, issues, and pull requests
          </p>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
            <CardDescription>
              Manage your GitHub repository connection
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
                    <h3 className="font-medium text-green-900">Connected to GitHub</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your GitHub repository is successfully connected
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Repository:</span>
                    <span className="font-medium">{integration.config.repository_url}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Branches:</span>
                    <span className="font-medium">
                      {integration.config.branches && integration.config.branches.length > 0 
                        ? integration.config.branches.join(', ') 
                        : 'main, master'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include Issues:</span>
                    <span className="font-medium">
                      {integration.config.include_issues ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Include PRs:</span>
                    <span className="font-medium">
                      {integration.config.include_prs ? 'Yes' : 'No'}
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
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex items-start gap-3">
                  <Github className="h-5 w-5 text-slate-600 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-slate-900">Connect to GitHub</h3>
                    <p className="text-sm text-slate-700 mt-1">
                      Connect your GitHub repository to analyze code, issues, and pull requests in NeuroSync
                    </p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => setIsModalOpen(true)}
                  className="w-full"
                >
                  Connect GitHub
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documentation</CardTitle>
            <CardDescription>
              Learn how to use the GitHub integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">What is synced?</h3>
                <p className="text-sm text-gray-600">
                  The GitHub integration syncs code repositories, issues, pull requests, and comments from your GitHub repository.
                </p>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">Requirements</h3>
                <ul className="list-disc text-sm text-gray-600 pl-5 space-y-1">
                  <li>GitHub repository (public or private)</li>
                  <li>Personal Access Token with appropriate scopes</li>
                  <li>Repository URL (e.g., https://github.com/username/repo)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-1">How to get a GitHub token</h3>
                <ol className="list-decimal text-sm text-gray-600 pl-5 space-y-1">
                  <li>Go to <a href="https://github.com/settings/tokens" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">GitHub Personal Access Tokens</a></li>
                  <li>Click "Generate new token" and select "Fine-grained token"</li>
                  <li>Give it a name (e.g., "NeuroSync Integration")</li>
                  <li>Set the expiration date</li>
                  <li>Select the repository access and required permissions:
                    <ul className="list-disc ml-5 mt-1">
                      <li>Repository access: Only select repositories</li>
                      <li>Permissions: Contents (read), Issues (read), Pull Requests (read), Metadata (read)</li>
                    </ul>
                  </li>
                  <li>Click "Generate token" and copy the token</li>
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
        integrationType="github"
      />
    </div>
  )
}
