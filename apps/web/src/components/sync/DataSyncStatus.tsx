/**
 * Data Sync Status Component
 * Shows real-time sync status for all integrations
 */

'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  XCircle, 
  Clock,
  FileText,
  Github,
  Slack,
  ExternalLink,
  TrendingUp,
  Calendar,
  Activity
} from 'lucide-react'
import { Button } from '../ui/button'
import { useIntegrations, useIntegrationSync } from '../../hooks/useIntegrations'

interface SyncStatus {
  id: string
  integration_name: string
  integration_type: string
  status: 'idle' | 'syncing' | 'completed' | 'failed'
  last_sync: string
  next_sync: string
  progress: number
  items_synced: number
  total_items: number
  error_message?: string
  sync_duration?: number
}

interface DataSyncStatusProps {
  projectId: string
}

export function DataSyncStatus({ projectId }: DataSyncStatusProps) {
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  const { integrations } = useIntegrations(projectId)
  const { syncIntegration, isSyncing } = useIntegrationSync(projectId)

  // Mock sync statuses - in real implementation, this would come from WebSocket or polling
  useEffect(() => {
    if (integrations) {
      const mockStatuses: SyncStatus[] = integrations.map(integration => ({
        id: integration.id,
        integration_name: integration.name,
        integration_type: integration.type,
        status: Math.random() > 0.7 ? 'syncing' : 'completed',
        last_sync: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        next_sync: new Date(Date.now() + Math.random() * 3600000).toISOString(),
        progress: Math.random() > 0.7 ? Math.floor(Math.random() * 100) : 100,
        items_synced: Math.floor(Math.random() * 500),
        total_items: Math.floor(Math.random() * 600) + 500,
        sync_duration: Math.floor(Math.random() * 300) + 30
      }))
      setSyncStatuses(mockStatuses)
    }
  }, [integrations])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'syncing':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
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
        return <FileText className="h-5 w-5" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'syncing':
        return 'border-blue-200 bg-blue-50'
      case 'completed':
        return 'border-green-200 bg-green-50'
      case 'failed':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const handleRefreshAll = async () => {
    setIsRefreshing(true)
    try {
      // Trigger sync for all integrations
      for (const status of syncStatuses) {
        await syncIntegration(status.id)
      }
    } catch (error) {
      console.error('Failed to refresh syncs:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Data Sync Status</h2>
          <p className="text-gray-600 mt-1">Monitor real-time synchronization across all integrations</p>
        </div>
        <Button
          onClick={handleRefreshAll}
          disabled={isRefreshing}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh All
        </Button>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Syncs</p>
              <p className="text-2xl font-bold text-blue-600">
                {syncStatuses.filter(s => s.status === 'syncing').length}
              </p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {syncStatuses.filter(s => s.status === 'completed').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-red-600">
                {syncStatuses.filter(s => s.status === 'failed').length}
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Items</p>
              <p className="text-2xl font-bold text-gray-900">
                {syncStatuses.reduce((sum, s) => sum + s.items_synced, 0).toLocaleString()}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-gray-500" />
          </div>
        </div>
      </div>

      {/* Sync Status Cards */}
      <div className="space-y-4">
        {syncStatuses.map((status) => (
          <motion.div
            key={status.id}
            className={`bg-white border rounded-lg p-6 ${getStatusColor(status.status)}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getIntegrationIcon(status.integration_type)}
                <div>
                  <h3 className="font-semibold text-gray-900">{status.integration_name}</h3>
                  <p className="text-sm text-gray-600 capitalize">{status.integration_type} Integration</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(status.status)}
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {status.status}
                </span>
              </div>
            </div>

            {/* Progress Bar for Active Syncs */}
            {status.status === 'syncing' && (
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                  <span>Progress: {status.items_synced} / {status.total_items} items</span>
                  <span>{status.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="bg-blue-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${status.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {/* Sync Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="h-4 w-4" />
                <span>Last sync: {formatTimeAgo(status.last_sync)}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-4 w-4" />
                <span>Next sync: {formatTimeAgo(status.next_sync)}</span>
              </div>
              {status.sync_duration && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Activity className="h-4 w-4" />
                  <span>Duration: {formatDuration(status.sync_duration)}</span>
                </div>
              )}
            </div>

            {/* Error Message */}
            {status.status === 'failed' && status.error_message && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm text-red-700">{status.error_message}</span>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2 mt-4">
              <Button
                size="sm"
                variant="outline"
                onClick={() => syncIntegration(status.id)}
                disabled={status.status === 'syncing'}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Sync Now
              </Button>
              <Button size="sm" variant="ghost">
                View Details
              </Button>
            </div>
          </motion.div>
        ))}
      </div>

      {syncStatuses.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Integrations</h3>
          <p className="text-gray-600">Connect your first integration to start syncing data.</p>
        </div>
      )}
    </div>
  )
}
