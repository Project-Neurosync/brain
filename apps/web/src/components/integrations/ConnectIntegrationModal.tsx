/**
 * Connect Integration Modal Component
 * Modal for connecting new integrations with configuration options
 */

'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Textarea } from '../ui/textarea'
import { Label } from '../ui/label'
import { X, Github, Slack, ExternalLink, Loader2, Eye, EyeOff, Zap } from 'lucide-react'
import { useIntegrationMutations, useIntegrationTypes, useOAuthIntegration } from '../../hooks/useIntegrations'
import { ConnectIntegrationRequest, IntegrationConfig } from '../../lib/api/integrations'

interface ConnectIntegrationModalProps {
  isOpen: boolean
  onClose: () => void
  projectId: string
  integrationType?: string
}

export function ConnectIntegrationModal({ 
  isOpen, 
  onClose, 
  projectId, 
  integrationType 
}: ConnectIntegrationModalProps) {
  const [selectedType, setSelectedType] = useState(integrationType || '')
  const [formData, setFormData] = useState<ConnectIntegrationRequest>({
    type: 'github',
    name: '',
    config: {}
  })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { types: integrationTypes } = useIntegrationTypes()
  const { connectIntegration, isConnecting } = useIntegrationMutations(projectId)
  const { startOAuth, isAuthenticating } = useOAuthIntegration(projectId)

  // Update form when integration type changes
  useEffect(() => {
    if (selectedType) {
      const typeInfo = integrationTypes.find(t => t.type === selectedType)
      setFormData({
        type: selectedType as any,
        name: typeInfo?.name || '',
        config: getDefaultConfig(selectedType)
      })
    }
  }, [selectedType, integrationTypes])

  // Set initial type when modal opens
  useEffect(() => {
    if (isOpen && integrationType) {
      setSelectedType(integrationType)
    }
  }, [isOpen, integrationType])

  const getDefaultConfig = (type: string): IntegrationConfig => {
    switch (type) {
      case 'github':
        return {
          repository_url: '',
          github_token: '',
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
      default:
        return {
          sync_frequency: 'daily',
          auto_sync: true
        }
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Integration name is required'
    }

    // Type-specific validation
    switch (selectedType) {
      case 'github':
        if (!formData.config.repository_url) {
          newErrors.repository_url = 'Repository URL is required'
        } else if (!isValidGitHubUrl(formData.config.repository_url)) {
          newErrors.repository_url = 'Please enter a valid GitHub repository URL'
        }
        if (!formData.config.github_token) {
          newErrors.github_token = 'GitHub token is required'
        }
        break

      case 'jira':
        if (!formData.config.jira_url) {
          newErrors.jira_url = 'Jira URL is required'
        }
        if (!formData.config.jira_email) {
          newErrors.jira_email = 'Jira email is required'
        }
        if (!formData.config.jira_token) {
          newErrors.jira_token = 'Jira API token is required'
        }
        if (!formData.config.project_key) {
          newErrors.project_key = 'Project key is required'
        }
        break

      case 'slack':
        if (!formData.config.slack_token) {
          newErrors.slack_token = 'Slack token is required'
        }
        if (!formData.config.workspace_id) {
          newErrors.workspace_id = 'Workspace ID is required'
        }
        break
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const isValidGitHubUrl = (url: string): boolean => {
    const githubPattern = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/
    return githubPattern.test(url)
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
    await startOAuth(selectedType)
  }

  const handleClose = () => {
    setFormData({
      type: 'github',
      name: '',
      config: {}
    })
    setSelectedType('')
    setErrors({})
    onClose()
  }

  const handleInputChange = (field: string, value: any) => {
    if (field.startsWith('config.')) {
      const configField = field.replace('config.', '')
      setFormData(prev => ({
        ...prev,
        config: { ...prev.config, [configField]: value }
      }))
    } else {
      setFormData(prev => ({ ...prev, [field]: value }))
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
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
      default:
        return null
    }
  }

  const selectedTypeInfo = integrationTypes.find(t => t.type === selectedType)
  const supportsOAuth = selectedTypeInfo?.oauth_supported

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            Connect Integration
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              className="h-6 w-6 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Integration Type Selection */}
          {!integrationType && (
            <div>
              <Label>Integration Type</Label>
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
              {/* OAuth Option */}
              {supportsOAuth && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-blue-900">Quick Connect with OAuth</h3>
                      <p className="text-sm text-blue-700 mt-1">
                        Connect securely without entering tokens manually
                      </p>
                    </div>
                    <Button
                      type="button"
                      onClick={handleOAuthConnect}
                      disabled={isAuthenticating}
                      className="flex items-center gap-2"
                    >
                      <Zap className="h-4 w-4" />
                      {isAuthenticating ? 'Connecting...' : 'Connect with OAuth'}
                    </Button>
                  </div>
                </div>
              )}

              {supportsOAuth && (
                <div className="text-center text-sm text-gray-500">
                  <span>or configure manually</span>
                </div>
              )}

              {/* Basic Information */}
              <div>
                <Label htmlFor="name">Integration Name</Label>
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

              {/* GitHub Configuration */}
              {selectedType === 'github' && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="repository_url">Repository URL</Label>
                    <Input
                      id="repository_url"
                      value={formData.config.repository_url || ''}
                      onChange={(e) => handleInputChange('config.repository_url', e.target.value)}
                      placeholder="https://github.com/username/repository"
                      className={errors.repository_url ? 'border-red-500' : ''}
                      disabled={isConnecting}
                    />
                    {errors.repository_url && (
                      <p className="text-sm text-red-500 mt-1">{errors.repository_url}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="github_token">GitHub Personal Access Token</Label>
                    <div className="relative">
                      <Input
                        id="github_token"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.config.github_token || ''}
                        onChange={(e) => handleInputChange('config.github_token', e.target.value)}
                        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                        className={errors.github_token ? 'border-red-500' : ''}
                        disabled={isConnecting}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                    {errors.github_token && (
                      <p className="text-sm text-red-500 mt-1">{errors.github_token}</p>
                    )}
                    <p className="text-xs text-gray-600 mt-1">
                      Create a token at GitHub Settings → Developer settings → Personal access tokens
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="branches">Branches to sync (comma-separated)</Label>
                    <Input
                      id="branches"
                      value={formData.config.branches?.join(', ') || ''}
                      onChange={(e) => handleInputChange('config.branches', e.target.value.split(',').map(b => b.trim()))}
                      placeholder="main, develop"
                      disabled={isConnecting}
                    />
                  </div>
                </div>
              )}

              {/* Jira Configuration */}
              {selectedType === 'jira' && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="jira_url">Jira URL</Label>
                    <Input
                      id="jira_url"
                      value={formData.config.jira_url || ''}
                      onChange={(e) => handleInputChange('config.jira_url', e.target.value)}
                      placeholder="https://yourcompany.atlassian.net"
                      className={errors.jira_url ? 'border-red-500' : ''}
                      disabled={isConnecting}
                    />
                    {errors.jira_url && (
                      <p className="text-sm text-red-500 mt-1">{errors.jira_url}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="jira_email">Jira Email</Label>
                    <Input
                      id="jira_email"
                      type="email"
                      value={formData.config.jira_email || ''}
                      onChange={(e) => handleInputChange('config.jira_email', e.target.value)}
                      placeholder="your.email@company.com"
                      className={errors.jira_email ? 'border-red-500' : ''}
                      disabled={isConnecting}
                    />
                    {errors.jira_email && (
                      <p className="text-sm text-red-500 mt-1">{errors.jira_email}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="jira_token">Jira API Token</Label>
                    <div className="relative">
                      <Input
                        id="jira_token"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.config.jira_token || ''}
                        onChange={(e) => handleInputChange('config.jira_token', e.target.value)}
                        placeholder="API token from Jira"
                        className={errors.jira_token ? 'border-red-500' : ''}
                        disabled={isConnecting}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                    {errors.jira_token && (
                      <p className="text-sm text-red-500 mt-1">{errors.jira_token}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="project_key">Project Key</Label>
                    <Input
                      id="project_key"
                      value={formData.config.project_key || ''}
                      onChange={(e) => handleInputChange('config.project_key', e.target.value.toUpperCase())}
                      placeholder="PROJ"
                      className={errors.project_key ? 'border-red-500' : ''}
                      disabled={isConnecting}
                    />
                    {errors.project_key && (
                      <p className="text-sm text-red-500 mt-1">{errors.project_key}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Slack Configuration */}
              {selectedType === 'slack' && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="slack_token">Slack Bot Token</Label>
                    <div className="relative">
                      <Input
                        id="slack_token"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.config.slack_token || ''}
                        onChange={(e) => handleInputChange('config.slack_token', e.target.value)}
                        placeholder="xoxb-xxxxxxxxxxxx"
                        className={errors.slack_token ? 'border-red-500' : ''}
                        disabled={isConnecting}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                    {errors.slack_token && (
                      <p className="text-sm text-red-500 mt-1">{errors.slack_token}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="workspace_id">Workspace ID</Label>
                    <Input
                      id="workspace_id"
                      value={formData.config.workspace_id || ''}
                      onChange={(e) => handleInputChange('config.workspace_id', e.target.value)}
                      placeholder="T1234567890"
                      className={errors.workspace_id ? 'border-red-500' : ''}
                      disabled={isConnecting}
                    />
                    {errors.workspace_id && (
                      <p className="text-sm text-red-500 mt-1">{errors.workspace_id}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="channels">Channels to sync (comma-separated)</Label>
                    <Input
                      id="channels"
                      value={formData.config.channels?.join(', ') || ''}
                      onChange={(e) => handleInputChange('config.channels', e.target.value.split(',').map(c => c.trim()))}
                      placeholder="#general, #development"
                      disabled={isConnecting}
                    />
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isConnecting}
                >
                  Cancel
                </Button>
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
              </div>
            </>
          )}
        </form>
      </DialogContent>
    </Dialog>
  )
}
