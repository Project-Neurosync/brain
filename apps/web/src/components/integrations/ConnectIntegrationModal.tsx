/**
 * Connect Integration Modal Component
 * Modal for connecting new integrations with OAuth-first approach
 * Following the new user onboarding flow for NeuroSync
 */

'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { X, Github, Slack, ExternalLink, Loader2, Eye, EyeOff, FileText } from 'lucide-react'
import { useIntegrationMutations, useIntegrationTypes, useOAuthIntegration } from '../../hooks/useIntegrations'
import { ConnectIntegrationRequest, IntegrationConfig } from '../../lib/api/integrations'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface ConnectIntegrationModalProps {
  isOpen: boolean
  onClose: () => void
  projectId?: string
  integrationType?: string
  onOAuthComplete?: (config: IntegrationConfig) => void
}

export function ConnectIntegrationModal({ 
  isOpen, 
  onClose, 
  projectId, 
  integrationType,
  onOAuthComplete
}: ConnectIntegrationModalProps) {
  // Using a key approach to ensure proper unmounting/remounting
  const dialogKey = isOpen ? 'open-modal' : 'closed-modal';
  
  // Initialize state only once when modal opens
  const [selectedType, setSelectedType] = useState<string>('')
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState<ConnectIntegrationRequest>({
    type: 'github',
    name: '',
    config: {
      // Default config
      repository_url: '',
      branches: ['main', 'master'],
      include_issues: true,
      include_prs: true,
      sync_frequency: 'daily',
      auto_sync: true
    }
  })
  
  // Define a proper type for the errors object that matches our nested structure
  type ValidationErrors = {
    name?: string;
    config?: {
      repository_url?: string;
      jira_url?: string;
      jira_email?: string;
      jira_token?: string;
      project_key?: string;
      slack_token?: string;
      workspace_id?: string;
      confluence_url?: string;
      confluence_username?: string;
      confluence_token?: string;
      notion_token?: string;
    };
  };

  const [errors, setErrors] = useState<ValidationErrors>({})

  const { types: integrationTypes } = useIntegrationTypes()
  const { connectIntegration, isConnecting } = useIntegrationMutations(projectId)
  const { startOAuth, isAuthenticating } = useOAuthIntegration(projectId)

  // Set initial type and reset form data when modal opens
  useEffect(() => {
    if (isOpen) {
      // Set selected type from prop if available
      if (integrationType) {
        setSelectedType(integrationType)
      }
    } else {
      // Reset state when modal closes
      setSelectedType('')
      setFormData({
        type: 'github',
        name: '',
        config: getDefaultConfig('github')
      })
      setErrors({})
    }
  }, [isOpen, integrationType])
  
  // Update form when integration type changes (only if we have a selected type)
  useEffect(() => {
    if (selectedType && isOpen) {
      const typeInfo = integrationTypes.find(t => t.type === selectedType)
      setFormData({
        type: selectedType as any,
        name: typeInfo?.name ? `My ${typeInfo.name} Integration` : '',
        config: getDefaultConfig(selectedType)
      })
    }
  }, [selectedType, integrationTypes, isOpen])

  const getDefaultConfig = (type: string): IntegrationConfig => {
    switch (type) {
      case 'github':
        return {
          repository_url: '',
          branches: ['main', 'master'],
          include_issues: true,
          include_prs: true,
          include_wiki: false,
          sync_frequency: 'daily',
          auto_sync: true
        }
      case 'jira':
        return {
          jira_url: '',
          jira_email: '',
          jira_token: '',
          project_key: '',
          include_comments: true,
          status_filters: ['To Do', 'In Progress', 'Done'],
          sync_frequency: 'daily',
          auto_sync: true
        }
      case 'slack':
        return {
          slack_token: '',
          workspace_id: '',
          channels: [],
          include_threads: true,
          sync_frequency: 'hourly',
          auto_sync: true
        }
      case 'confluence':
        return {
          confluence_url: '',
          confluence_username: '',
          confluence_token: '',
          spaces: [],
          include_attachments: true,
          include_comments: true,
          sync_frequency: 'daily',
          auto_sync: true
        }
      case 'notion':
        return {
          notion_token: '',
          database_ids: [],
          include_pages: true,
          include_comments: true,
          sync_frequency: 'daily',
          auto_sync: true
        }
      default:
        return {
          sync_frequency: 'daily',
          auto_sync: true
        }
    }
  }

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Integration name is required'
    }

    // Initialize config errors object
    newErrors.config = {}
    
    // Type-specific validation
    switch (selectedType) {
      case 'jira':
        if (!formData.config.jira_url) {
          newErrors.config.jira_url = 'Jira URL is required'
        }
        if (!formData.config.jira_email) {
          newErrors.config.jira_email = 'Jira email is required'
        }
        if (!formData.config.jira_token) {
          newErrors.config.jira_token = 'Jira API token is required'
        }
        break

      case 'slack':
        if (!formData.config.slack_token) {
          newErrors.config.slack_token = 'Slack token is required'
        }
        if (!formData.config.workspace_id) {
          newErrors.config.workspace_id = 'Workspace ID is required'
        }
        break
      
      case 'confluence':
        if (!formData.config.confluence_url) {
          newErrors.config.confluence_url = 'Confluence URL is required'
        }
        if (!formData.config.confluence_username) {
          newErrors.config.confluence_username = 'Confluence username is required'
        }
        if (!formData.config.confluence_token) {
          newErrors.config.confluence_token = 'Confluence API token is required'
        }
        break
      
      case 'notion':
        if (!formData.config.notion_token) {
          newErrors.config.notion_token = 'Notion API token is required'
        }
        break
    }

    // If no config errors, remove the empty config object
    if (Object.keys(newErrors.config).length === 0) {
      delete newErrors.config;
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    connectIntegration(formData, {
      onSuccess: () => {
        handleClose()
      }
    })
  }

  const handleOAuthConnect = async () => {
    try {
      // If this is a projectless flow (no projectId) and we have onOAuthComplete callback,
      // we need to set up a message listener to handle the OAuth completion
      if (!projectId && onOAuthComplete) {
        // Set up window message listener for OAuth callback window
        const messageHandler = (event: MessageEvent) => {
          // Validate origin
          if (event.origin !== window.location.origin) return;
          
          // Check if this is our OAuth success message
          if (event.data?.type === 'oauth-success' && event.data?.integration === selectedType) {
            // Call the onOAuthComplete callback with the integration config
            onOAuthComplete(event.data.data?.integration_config)
            // Close the modal
            handleClose()
            // Remove the event listener
            window.removeEventListener('message', messageHandler)
          }
        };
        
        // Add the message event listener
        window.addEventListener('message', messageHandler);
      }
      
      // Start the OAuth flow
      startOAuth(selectedType)
      
      // If we're in a projectless flow, we'll close the modal after OAuth completes via the message event
      if (!projectId && onOAuthComplete) {
        // We don't close the modal here - it will close when OAuth completes
      } else if (projectId) {
        // For project-based flow, we can close the modal now - the hook will handle updating integrations
        handleClose()
      }
    } catch (error) {
      console.error('OAuth flow error:', error)
    }
  }

  const handleClose = () => {
    onClose()
  }

  const handleInputChange = (field: string, value: any) => {
    if (field.startsWith('config.')) {
      const configField = field.replace('config.', '')
      setFormData(prev => ({
        ...prev,
        config: { ...prev.config, [configField]: value }
      }))
      
      // Clear error for config fields
      if (errors.config && errors.config[configField as keyof ValidationErrors['config']]) {
        setErrors(prev => ({
          ...prev,
          config: { ...prev.config, [configField]: undefined }
        }))
      }
    } else {
      setFormData(prev => ({ ...prev, [field]: value }))
      
      // Clear error for top-level fields
      if (field === 'name' && errors.name) {
        setErrors(prev => ({ ...prev, name: undefined }))
      }
    }
  }

  const getIntegrationIcon = (type: string) => {
    switch (type) {
      case 'github':
        return <Github className="h-5 w-5" />
      case 'slack':
        return <Slack className="h-5 w-5" />
      case 'jira':
        return <ExternalLink className="h-5 w-5" />
      case 'confluence':
        return <FileText className="h-5 w-5" />
      case 'notion':
        return <FileText className="h-5 w-5" />
      default:
        return null
    }
  }

  const selectedTypeInfo = integrationTypes.find(t => t.type === selectedType)
  
  // Default GitHub to always support OAuth even if integration types are empty
  const supportsOAuth = selectedType === 'github' ? true : selectedTypeInfo?.oauth_supported

  // Simple close handler that calls the parent's onClose
  const handleModalClose = () => {
    onClose()
  }
  
  return (
    <Dialog 
      key={dialogKey}
      open={isOpen} 
      onOpenChange={(open) => {
        if (!open) handleModalClose()
      }}
    >
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Connect Integration</DialogTitle>
          {selectedTypeInfo && (
            <DialogDescription>
              Connect your {selectedTypeInfo.name} to NeuroSync AI {projectId ? 'for this project' : 'to get started'}.
            </DialogDescription>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="absolute right-4 top-4"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </Button>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Integration Type Selection */}
          {!integrationType && (
            <div>
              <Label className="mb-2 block">Integration Type</Label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
                {integrationTypes.map((type) => (
                  <button
                    key={type.type}
                    type="button"
                    onClick={() => setSelectedType(type.type)}
                    className={`p-4 border rounded-lg text-left transition-colors ${
                      selectedType === type.type
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      {getIntegrationIcon(type.type)}
                      <span className="font-medium">{type.name}</span>
                    </div>
                    <p className="text-sm text-gray-600">{type.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedType && (
            <>
              {/* GitHub uses OAuth exclusively */}
              {selectedType === 'github' && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-md p-4 mb-4">
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                    <Github className="h-4 w-4" /> 
                    Connect with GitHub OAuth
                  </h4>
                  <p className="text-sm mb-3">
                    Securely connect your GitHub repositories and authorize NeuroSync to access your code.
                  </p>
                  <Button
                    type="button"
                    variant="default"
                    className="gap-2 w-full sm:w-auto"
                    onClick={handleOAuthConnect}
                    disabled={isAuthenticating}
                  >
                    {isAuthenticating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <Github className="h-4 w-4" /> 
                        Connect with GitHub
                      </>
                    )}
                  </Button>
                  <p className="text-sm mt-3 text-gray-600">
                    After connecting, you'll be able to select repositories and configure GitHub integration options.
                  </p>
                </div>
              )}

              {/* Non-GitHub integrations: show their specific configuration */}
              {selectedType !== 'github' && (
                <>
                  {/* Generic OAuth options for any other integration types that support it */}
                  {supportsOAuth && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-md p-4 mb-4">
                      <h4 className="font-semibold text-sm mb-2 flex items-center gap-2"> 
                        Connect with {selectedTypeInfo?.name} OAuth
                      </h4>
                      <p className="text-sm mb-3">
                        Securely connect your {selectedTypeInfo?.name} account without sharing credentials.
                      </p>
                      <Button
                        type="button"
                        variant="default"
                        className="gap-2 w-full sm:w-auto"
                        onClick={handleOAuthConnect}
                        disabled={isAuthenticating}
                      >
                        {isAuthenticating ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          <>
                            Connect with {selectedTypeInfo?.name}
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                  
                  {/* Manual configuration options for integrations without OAuth */}
                  {!supportsOAuth && (
                    <div className="space-y-4">
                      {/* Jira Configuration */}
                      {selectedType === 'jira' && (
                        <div className="space-y-4">
                          <div>
                            <Label className="mb-2 block">Jira URL</Label>
                            <Input
                              id="jira_url"
                              value={formData.config.jira_url || ''}
                              onChange={(e) => handleInputChange('config.jira_url', e.target.value)}
                              placeholder="https://yourcompany.atlassian.net"
                              className={errors.config?.jira_url ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.jira_url && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.jira_url}</p>
                            )}
                          </div>
                          <div>
                            <Label className="mb-2 block">Jira Email</Label>
                            <Input
                              id="jira_email"
                              type="email"
                              value={formData.config.jira_email || ''}
                              onChange={(e) => handleInputChange('config.jira_email', e.target.value)}
                              placeholder="your.email@company.com"
                              className={errors.config?.jira_email ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.jira_email && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.jira_email}</p>
                            )}
                          </div>
                          <div>
                            <Label className="mb-2 block">API Token</Label>
                            <Input
                              id="jira_token"
                              type={showPassword ? 'text' : 'password'}
                              value={formData.config.jira_token || ''}
                              onChange={(e) => handleInputChange('config.jira_token', e.target.value)}
                              placeholder="API token from Atlassian account"
                              className={errors.config?.jira_token ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.jira_token && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.jira_token}</p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Confluence Configuration */}
                      {selectedType === 'confluence' && (
                        <div className="space-y-4">
                          <div>
                            <Label className="mb-2 block">Confluence URL</Label>
                            <Input
                              id="confluence_url"
                              value={formData.config.confluence_url || ''}
                              onChange={(e) => handleInputChange('config.confluence_url', e.target.value)}
                              placeholder="https://yourcompany.atlassian.net/wiki"
                              className={errors.config?.confluence_url ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.confluence_url && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.confluence_url}</p>
                            )}
                          </div>
                          <div>
                            <Label className="mb-2 block">Username</Label>
                            <Input
                              id="confluence_username"
                              value={formData.config.confluence_username || ''}
                              onChange={(e) => handleInputChange('config.confluence_username', e.target.value)}
                              placeholder="your.email@company.com"
                              className={errors.config?.confluence_username ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.confluence_username && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.confluence_username}</p>
                            )}
                          </div>
                          <div>
                            <Label className="mb-2 block">API Token</Label>
                            <Input
                              id="confluence_token"
                              type={showPassword ? 'text' : 'password'}
                              value={formData.config.confluence_token || ''}
                              onChange={(e) => handleInputChange('config.confluence_token', e.target.value)}
                              placeholder="API token from Atlassian account"
                              className={errors.config?.confluence_token ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.confluence_token && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.confluence_token}</p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Slack Configuration */}
                      {selectedType === 'slack' && (
                        <div className="space-y-4">
                          <div>
                            <Label className="mb-2 block">Slack Bot Token</Label>
                            <Input
                              id="slack_token"
                              type={showPassword ? 'text' : 'password'}
                              value={formData.config.slack_token || ''}
                              onChange={(e) => handleInputChange('config.slack_token', e.target.value)}
                              placeholder="xoxb-..."
                              className={errors.config?.slack_token ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.slack_token && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.slack_token}</p>
                            )}
                          </div>
                          <div>
                            <Label className="mb-2 block">Workspace ID</Label>
                            <Input
                              id="workspace_id"
                              value={formData.config.workspace_id || ''}
                              onChange={(e) => handleInputChange('config.workspace_id', e.target.value)}
                              placeholder="T1234567890"
                              className={errors.config?.workspace_id ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.workspace_id && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.workspace_id}</p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Notion Configuration */}
                      {selectedType === 'notion' && (
                        <div className="space-y-4">
                          <div>
                            <Label className="mb-2 block">Notion Integration Token</Label>
                            <Input
                              id="notion_token"
                              type={showPassword ? 'text' : 'password'}
                              value={formData.config.notion_token || ''}
                              onChange={(e) => handleInputChange('config.notion_token', e.target.value)}
                              placeholder="secret_..."
                              className={errors.config?.notion_token ? 'border-red-500' : ''}
                              disabled={isConnecting}
                            />
                            {errors.config?.notion_token && (
                              <p className="text-sm text-red-500 mt-1">{errors.config.notion_token}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Common fields for all integration types */}
              <div>
                <Label className="mb-2 block">Integration Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder={`My ${selectedTypeInfo?.name} Integration`}
                  className={errors.name ? 'border-red-500' : ''}
                  disabled={isConnecting}
                />
                {errors.name && (
                  <p className="text-sm text-red-500 mt-1">{errors.name}</p>
                )}
              </div>
              
              {/* Footer buttons */}
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isConnecting || isAuthenticating}
                >
                  Cancel
                </Button>
                {selectedType !== 'github' && !supportsOAuth && (
                  <Button
                    type="submit"
                    disabled={isConnecting}
                    className="min-w-[120px]"
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      'Connect Integration'
                    )}
                  </Button>
                )}
              </DialogFooter>
            </>
          )}
        </form>
      </DialogContent>
    </Dialog>
  )
}
