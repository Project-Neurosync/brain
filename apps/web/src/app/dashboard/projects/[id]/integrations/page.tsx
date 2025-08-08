/**
 * Integrations Management Page
 * Interface for managing project data source integrations
 */

'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { 
  Plus, 
  Settings, 
  RefreshCw, 
  TestTube, 
  Trash2, 
  Github, 
  Slack, 
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Eye,
  Calendar,
  FileText,
  Activity,
  Zap
} from 'lucide-react'
import { Button } from '../../../../../components/ui/button'
import { Input } from '../../../../../components/ui/input'
import { 
  useIntegrations, 
  useIntegrationMutations,
  useIntegrationSync,
  useIntegrationTypes,
  useOAuthIntegration
} from '../../../../../hooks/useIntegrations'
import { useProject } from '../../../../../hooks/useProjects'
import { Integration } from '../../../../../lib/api/integrations'
import { ConnectIntegrationModal } from '../../../../../components/integrations/ConnectIntegrationModal'

export default function IntegrationsPage() {
  const params = useParams()
  const projectId = params.id as string
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false)
  const [selectedIntegrationType, setSelectedIntegrationType] = useState<string>('')

  const { project } = useProject(projectId)
  const { integrations, isLoading, error } = useIntegrations(projectId)
  const { deleteIntegration } = useIntegrationMutations(projectId)
  const { syncIntegration, testIntegration, isSyncing, isTesting } = useIntegrationSync(projectId)
  const { types: integrationTypes } = useIntegrationTypes()
  const { startOAuth, isAuthenticating } = useOAuthIntegration(projectId)

  const handleConnectIntegration = (type: string) => {
    setSelectedIntegrationType(type)
    setIsConnectModalOpen(true)
  }

  const handleDeleteIntegration = (integration: Integration) => {
    if (confirm(`Are you sure you want to delete the ${integration.name} integration? This will remove all synced data.`)) {
      deleteIntegration(integration.id)
    }
  }

  const handleSyncIntegration = (integrationId: string) => {
    syncIntegration(integrationId)
  }

  const handleTestIntegration = (integrationId: string) => {
    testIntegration(integrationId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load integrations. Please try again.</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-gray-600 mt-1">
            Connect your tools to automatically sync project knowledge
          </p>
        </div>
        <Button 
          onClick={() => setIsConnectModalOpen(true)} 
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Integration
        </Button>
      </div>

      {/* Connected Integrations */}
      {integrations.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {integrations.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onSync={() => handleSyncIntegration(integration.id)}
              onTest={() => handleTestIntegration(integration.id)}
              onDelete={() => handleDeleteIntegration(integration)}
              isSyncing={isSyncing(integration.id)}
              isTesting={isTesting}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            <Plus className="h-full w-full" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations yet</h3>
          <p className="text-gray-600 mb-6">
            Connect your first integration to start syncing project knowledge
          </p>
          <Button onClick={() => setIsConnectModalOpen(true)}>
            Add Your First Integration
          </Button>
        </div>
      )}

      {/* Available Integrations */}
      {integrations.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Integrations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {integrationTypes
              .filter(type => !integrations.some(i => i.type === type.type))
              .map((type) => (
                <AvailableIntegrationCard
                  key={type.type}
                  type={type}
                  onConnect={() => handleConnectIntegration(type.type)}
                  isConnecting={isAuthenticating}
                />
              ))}
          </div>
        </div>
      )}

      {/* Connect Integration Modal */}
      <ConnectIntegrationModal
        isOpen={isConnectModalOpen}
        onClose={() => {
          setIsConnectModalOpen(false)
          setSelectedIntegrationType('')
        }}
        projectId={projectId}
        integrationType={selectedIntegrationType}
      />
    </div>
  )
}

interface IntegrationCardProps {
  integration: Integration
  onSync: () => void
  onTest: () => void
  onDelete: () => void
  isSyncing: boolean
  isTesting: boolean
}

function IntegrationCard({ 
  integration, 
  onSync, 
  onTest, 
  onDelete, 
  isSyncing, 
  isTesting 
}: IntegrationCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-green-600 bg-green-100'
      case 'syncing':
        return 'text-blue-600 bg-blue-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      case 'disconnected':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4" />
      case 'syncing':
        return <RefreshCw className="h-4 w-4 animate-spin" />
      case 'error':
        return <XCircle className="h-4 w-4" />
      case 'disconnected':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getIntegrationIcon = (type: string) => {
    switch (type) {
      case 'github':
        return <Github className="h-6 w-6" />
      case 'slack':
        return <Slack className="h-6 w-6" />
      case 'jira':
        return <ExternalLink className="h-6 w-6" />
      default:
        return <FileText className="h-6 w-6" />
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            {getIntegrationIcon(integration.type)}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {integration.name}
            </h3>
            <p className="text-sm text-gray-600 capitalize">
              {integration.type} Integration
            </p>
          </div>
        </div>
        
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(integration.status)}`}>
          {getStatusIcon(integration.status)}
          <span className="capitalize">{integration.status}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {integration.stats.total_documents.toLocaleString()}
          </div>
          <div className="text-gray-600">Documents</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {integration.stats.total_size_mb.toFixed(1)}MB
          </div>
          <div className="text-gray-600">Size</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {Math.round(integration.stats.success_rate * 100)}%
          </div>
          <div className="text-gray-600">Success</div>
        </div>
      </div>

      {/* Sync Info */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="h-4 w-4" />
            Last sync: {formatDate(integration.last_sync)}
          </div>
          {integration.sync_progress !== undefined && integration.sync_status === 'syncing' && (
            <div className="flex items-center gap-2">
              <div className="w-16 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${integration.sync_progress}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{integration.sync_progress}%</span>
            </div>
          )}
        </div>
        
        {integration.error_message && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
            {integration.error_message}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSync}
          disabled={isSyncing || integration.status === 'disconnected'}
          className="flex items-center gap-2"
        >
          {isSyncing ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Sync Now
            </>
          )}
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={onTest}
          disabled={isTesting || integration.status === 'disconnected'}
          className="flex items-center gap-2"
        >
          <TestTube className="h-4 w-4" />
          Test
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={onDelete}
          className="flex items-center gap-2 text-red-600 hover:text-red-700"
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </Button>
      </div>
    </div>
  )
}

interface AvailableIntegrationCardProps {
  type: {
    type: string
    name: string
    description: string
    icon: string
    oauth_supported: boolean
  }
  onConnect: () => void
  isConnecting: boolean
}

function AvailableIntegrationCard({ type, onConnect, isConnecting }: AvailableIntegrationCardProps) {
  const getIntegrationIcon = (typeName: string) => {
    switch (typeName) {
      case 'github':
        return <Github className="h-8 w-8" />
      case 'slack':
        return <Slack className="h-8 w-8" />
      case 'jira':
        return <ExternalLink className="h-8 w-8" />
      default:
        return <FileText className="h-8 w-8" />
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:border-purple-300 hover:shadow-sm transition-all">
      <div className="text-center">
        <div className="mx-auto w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
          {getIntegrationIcon(type.type)}
        </div>
        <h3 className="font-semibold text-gray-900 mb-1">{type.name}</h3>
        <p className="text-sm text-gray-600 mb-4">{type.description}</p>
        
        <Button
          onClick={onConnect}
          disabled={isConnecting}
          size="sm"
          className="w-full"
        >
          {isConnecting ? 'Connecting...' : 'Connect'}
        </Button>
        
        {type.oauth_supported && (
          <div className="flex items-center justify-center gap-1 mt-2 text-xs text-gray-500">
            <Zap className="h-3 w-3" />
            OAuth supported
          </div>
        )}
      </div>
    </div>
  )
}
