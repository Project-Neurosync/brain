/**
 * Create Project Modal Component
 * Modal form for creating new projects with validation and integration setup
 */

'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button, Input, Textarea, Label } from '../ui'
import { X, Github, Slack, ExternalLink, Loader2, Zap } from 'lucide-react'
import { useProjectMutations } from '../../hooks/useProjects'
import { CreateProjectRequest } from '../../lib/api/projects'
import { ConnectIntegrationModal } from '../integrations/ConnectIntegrationModal'
import { IntegrationConfig } from '../../lib/api/integrations'

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (projectId: string) => void
}

export function CreateProjectModal({ isOpen, onClose, onSuccess }: CreateProjectModalProps) {
  const [formData, setFormData] = useState<CreateProjectRequest>({
    name: '',
    description: '',
    repository_url: '',
    jira_project_key: '',
    slack_channel: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isIntegrationModalOpen, setIsIntegrationModalOpen] = useState(false)
  const [selectedIntegrationType, setSelectedIntegrationType] = useState<string | null>(null)
  const [pendingIntegrationConfigs, setPendingIntegrationConfigs] = useState<Record<string, IntegrationConfig>>({})

  const { createProject, isCreating } = useProjectMutations()

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required'
    } else if (formData.name.length < 3) {
      newErrors.name = 'Project name must be at least 3 characters'
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Project description is required'
    } else if (formData.description.length < 10) {
      newErrors.description = 'Description must be at least 10 characters'
    }

    // Validate GitHub URL format if provided
    if (formData.repository_url && !isValidGitHubUrl(formData.repository_url)) {
      newErrors.repository_url = 'Please enter a valid GitHub repository URL'
    }

    // Validate Jira project key format if provided
    if (formData.jira_project_key && !isValidJiraKey(formData.jira_project_key)) {
      newErrors.jira_project_key = 'Please enter a valid Jira project key (e.g., PROJ)'
    }

    // Validate Slack channel format if provided
    if (formData.slack_channel && !isValidSlackChannel(formData.slack_channel)) {
      newErrors.slack_channel = 'Please enter a valid Slack channel (e.g., #general)'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const isValidGitHubUrl = (url: string): boolean => {
    const githubPattern = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/
    return githubPattern.test(url)
  }

  const isValidJiraKey = (key: string): boolean => {
    const jiraPattern = /^[A-Z][A-Z0-9]*$/
    return jiraPattern.test(key)
  }

  const isValidSlackChannel = (channel: string): boolean => {
    const slackPattern = /^#[\w-]+$/
    return slackPattern.test(channel)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    // Clean up empty optional fields
    const cleanedData: CreateProjectRequest = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      ...(formData.repository_url && { repository_url: formData.repository_url.trim() }),
      ...(formData.jira_project_key && { jira_project_key: formData.jira_project_key.trim().toUpperCase() }),
      ...(formData.slack_channel && { slack_channel: formData.slack_channel.trim() })
    }

    createProject(cleanedData, {
      onSuccess: (project) => {
        handleClose()
        onSuccess?.(project.id)
      }
    })
  }

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      repository_url: '',
      jira_project_key: '',
      slack_channel: ''
    })
    setErrors({})
    setPendingIntegrationConfigs({})
    onClose()
  }

  const handleOpenIntegrationModal = (type: string) => {
    setSelectedIntegrationType(type)
    setIsIntegrationModalOpen(true)
  }

  const handleIntegrationModalClose = () => {
    setIsIntegrationModalOpen(false)
    setSelectedIntegrationType(null)
  }

  const handleOAuthComplete = (config: IntegrationConfig) => {
    // Store the integration config for later use when creating the project
    if (config.type) {
      const configType = config.type
      setPendingIntegrationConfigs(prev => ({
        ...prev,
        [configType]: config
      }))
      
      // Update form data based on integration type
      if (configType === 'github' && config.repository_url) {
        setFormData(prev => ({
          ...prev,
          repository_url: config.repository_url
        }))
      } else if (configType === 'jira' && config.project_key) {
        setFormData(prev => ({
          ...prev,
          jira_project_key: config.project_key
        }))
      } else if (configType === 'slack' && config.channels) {
        // Only use the first channel if available
        const slackChannel = config.channels.length > 0 ? config.channels[0] : ''
        setFormData(prev => ({
          ...prev,
          slack_channel: slackChannel
        }))
      }
    }
  }

  const handleInputChange = (field: keyof CreateProjectRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            <div className="flex items-center justify-between">
              Create New Project
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <div>
              <Label className="mb-2 block">Project Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('name', e.target.value)}
                placeholder="My Awesome Project"
                className={errors.name ? 'border-red-500' : ''}
                disabled={isCreating}
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            <div>
              <Label className="mb-2 block">Description *</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleInputChange('description', e.target.value)}
                placeholder="Describe what this project is about and what knowledge it will contain..."
                rows={3}
                className={errors.description ? 'border-red-500' : ''}
                disabled={isCreating}
              />
              {errors.description && (
                <p className="text-sm text-red-500 mt-1">{errors.description}</p>
              )}
            </div>
          </div>

          {/* Integration Setup */}
          <div className="space-y-4">
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Integration Setup (Optional)
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Connect your tools to automatically sync project knowledge
              </p>
            </div>

            <div>
              <Label className="flex items-center gap-2">
                <Github className="h-4 w-4" />
                GitHub Repository
              </Label>
              <div className="flex gap-2 mb-1">
                <Input
                  id="repository_url"
                  value={formData.repository_url}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('repository_url', e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className={`flex-1 ${errors.repository_url ? 'border-red-500' : ''}`}
                  disabled={isCreating}
                />
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => handleOpenIntegrationModal('github')}
                  className="whitespace-nowrap"
                  disabled={isCreating}
                >
                  <Github className="h-4 w-4 mr-2" />
                  Connect with OAuth
                </Button>
              </div>
              {errors.repository_url && (
                <p className="text-sm text-red-500 mt-1">{errors.repository_url}</p>
              )}
            </div>

            <div>
              <Label className="flex items-center gap-2">
                <ExternalLink className="h-4 w-4" />
                Jira Project Key
              </Label>
              <div className="flex gap-2 mb-1">
                <Input
                  id="jira_project_key"
                  value={formData.jira_project_key}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('jira_project_key', e.target.value.toUpperCase())}
                  placeholder="PROJ"
                  className={`flex-1 ${errors.jira_project_key ? 'border-red-500' : ''}`}
                  disabled={isCreating}
                />
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => handleOpenIntegrationModal('jira')}
                  className="whitespace-nowrap"
                  disabled={isCreating}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Connect with OAuth
                </Button>
              </div>
              {errors.jira_project_key && (
                <p className="text-sm text-red-500 mt-1">{errors.jira_project_key}</p>
              )}
            </div>

            <div>
              <Label className="flex items-center gap-2">
                <Slack className="h-4 w-4" />
                Slack Channel
              </Label>
              <div className="flex gap-2 mb-1">
                <Input
                  id="slack_channel"
                  value={formData.slack_channel}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('slack_channel', e.target.value)}
                  placeholder="#general"
                  className={`flex-1 ${errors.slack_channel ? 'border-red-500' : ''}`}
                  disabled={isCreating}
                />
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => handleOpenIntegrationModal('slack')}
                  className="whitespace-nowrap"
                  disabled={isCreating}
                >
                  <Slack className="h-4 w-4 mr-2" />
                  Connect with OAuth
                </Button>
              </div>
              {errors.slack_channel && (
                <p className="text-sm text-red-500 mt-1">{errors.slack_channel}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isCreating}
              className="min-w-[120px]"
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Project'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
