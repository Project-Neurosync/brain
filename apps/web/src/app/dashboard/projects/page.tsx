/**
 * Projects Dashboard Page
 * Main projects management interface with project cards, creation, and quick actions
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Plus, 
  Search, 
  Filter, 
  MoreHorizontal, 
  Users, 
  Calendar, 
  Activity,
  Github,
  Slack,
  ExternalLink,
  Settings,
  Archive,
  Trash2,
  Eye,
  TrendingUp,
  Upload,
  FileText
} from 'lucide-react'
import { Button } from '../../../components/ui/button'
import { Input } from '../../../components/ui/input'
import { CreateProjectModal } from '../../../components/projects/CreateProjectModal'
import { useProjects, useProjectMutations } from '../../../hooks/useProjects'
import { Project } from '../../../lib/api/projects'
import { filesApi } from '../../../lib/api/files'
import { projectApi } from '../../../lib/api/projects'

export default function ProjectsPage() {
  const router = useRouter()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'archived'>('all')
  const [uploadingFiles, setUploadingFiles] = useState(false)

  const { projects, isLoading, error } = useProjects()
  const { deleteProject } = useProjectMutations()

  // Filter projects based on search and status
  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         project.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = filterStatus === 'all' || project.status === filterStatus
    return matchesSearch && matchesStatus
  })

  const handleCreateProject = (projectId: string) => {
    router.push(`/dashboard/projects/${projectId}`)
  }

  const handleViewProject = (projectId: string) => {
    router.push(`/dashboard/projects/${projectId}`)
  }

  const handleDeleteProject = (projectId: string) => {
    if (confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      deleteProject(projectId)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploadingFiles(true)
    
    try {
      // Upload files directly - backend will create project automatically
      const uploadResponse = await filesApi.uploadFiles(files)
      
      if (!uploadResponse.success) {
        throw new Error(uploadResponse.error || 'Failed to upload files')
      }
      
      // Navigate to AI Chat for immediate RAG testing
      router.push(`/dashboard/chat?project=${uploadResponse.data?.project_id}`)
      
    } catch (error) {
      console.error('Error uploading files:', error)
      alert('Failed to upload files. Please try again.')
    } finally {
      setUploadingFiles(false)
      // Reset file input
      event.target.value = ''
    }
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
        <p className="text-red-600">Failed to load projects. Please try again.</p>
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
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage your knowledge bases and team collaboration
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={filterStatus === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('all')}
          >
            All
          </Button>
          <Button
            variant={filterStatus === 'active' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('active')}
          >
            Active
          </Button>
          <Button
            variant={filterStatus === 'archived' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('archived')}
          >
            Archived
          </Button>
        </div>
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-12">
          {projects.length === 0 ? (
            <div className="max-w-md mx-auto">
              <div className="mx-auto h-16 w-16 text-gray-400 mb-6">
                <Plus className="h-full w-full" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Get Started with NeuroSync</h3>
              <p className="text-gray-600 mb-8">
                Connect your existing tools or create a new project to start building your AI-powered knowledge base
              </p>
              
              {/* Integration Options */}
              <div className="space-y-4 mb-8">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Connect Your Tools</h4>
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 p-4 h-auto"
                    onClick={() => router.push('/dashboard/integrations')}
                  >
                    <Github className="h-5 w-5" />
                    <div className="text-left">
                      <div className="font-medium">GitHub</div>
                      <div className="text-xs text-gray-500">Import repositories</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 p-4 h-auto"
                    onClick={() => router.push('/dashboard/integrations')}
                  >
                    <div className="h-5 w-5 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">J</div>
                    <div className="text-left">
                      <div className="font-medium">Jira</div>
                      <div className="text-xs text-gray-500">Sync issues & tasks</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 p-4 h-auto"
                    onClick={() => router.push('/dashboard/integrations')}
                  >
                    <Slack className="h-5 w-5" />
                    <div className="text-left">
                      <div className="font-medium">Slack</div>
                      <div className="text-xs text-gray-500">Import conversations</div>
                    </div>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 p-4 h-auto"
                    onClick={() => router.push('/dashboard/integrations')}
                  >
                    <div className="h-5 w-5 bg-blue-500 rounded flex items-center justify-center text-white text-xs font-bold">C</div>
                    <div className="text-left">
                      <div className="font-medium">Confluence</div>
                      <div className="text-xs text-gray-500">Import documentation</div>
                    </div>
                  </Button>
                </div>
              </div>

              {/* File Upload Section */}
              <div className="space-y-4 mb-8">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Upload Documents for RAG Testing</h4>
                <div className="relative border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                  <FileText className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600">
                      Drop your documents here or click to browse
                    </p>
                    <p className="text-xs text-gray-500">
                      Supports: TXT, MD, PDF, DOCX (Max 10MB each)
                    </p>
                  </div>
                  <input 
                    type="file" 
                    multiple 
                    accept=".txt,.md,.pdf,.docx,.doc"
                    onChange={handleFileUpload} 
                    disabled={uploadingFiles}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                  />
                  {uploadingFiles && (
                    <div className="mt-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-xs text-blue-600 mt-1">Uploading files...</p>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  This will upload your documents for immediate RAG testing in the chat interface.
                </p>
              </div>

              {/* Divider */}
              <div className="relative mb-8">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or</span>
                </div>
              </div>

              {/* Manual Project Creation */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-900">Start Fresh</h4>
                <Button 
                  onClick={() => setIsCreateModalOpen(true)}
                  className="w-full flex items-center gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Create New Project
                </Button>
                <p className="text-xs text-gray-500">
                  Create an empty project and add data manually or through file uploads
                </p>
              </div>
            </div>
          ) : (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No matching projects</h3>
              <p className="text-gray-600">
                Try adjusting your search or filter criteria
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onView={() => handleViewProject(project.id)}
              onDelete={() => handleDeleteProject(project.id)}
            />
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateProject}
      />
    </div>
  )
}

interface ProjectCardProps {
  project: Project
  onView: () => void
  onDelete: () => void
}

function ProjectCard({ project, onView, onDelete }: ProjectCardProps) {
  const [showMenu, setShowMenu] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'archived':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {project.name}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-2">
            {project.description}
          </p>
        </div>
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowMenu(!showMenu)}
            className="h-8 w-8 p-0"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
          {showMenu && (
            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[160px]">
              <button
                onClick={() => { onView(); setShowMenu(false) }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Eye className="h-4 w-4" />
                View Project
              </button>
              <button
                onClick={() => { onDelete(); setShowMenu(false) }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
          {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
        </span>
      </div>

      {/* Integrations */}
      {project.integrations && project.integrations.length > 0 && (
        <div className="flex items-center gap-2 mb-4">
          {project.integrations.map((integration) => {
            const Icon = integration.type === 'github' ? Github : 
                        integration.type === 'slack' ? Slack : ExternalLink
            return (
              <div
                key={integration.id}
                className={`p-1.5 rounded ${
                  integration.status === 'connected' 
                    ? 'bg-green-100 text-green-600' 
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                <Icon className="h-3 w-3" />
              </div>
            )
          })}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {project.stats?.total_documents || 0}
          </div>
          <div className="text-gray-600">Docs</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {project.team_members?.length || 0}
          </div>
          <div className="text-gray-600">Members</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">
            {project.stats?.total_queries || 0}
          </div>
          <div className="text-gray-600">Queries</div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t">
        <div className="flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          Updated {formatDate(project.updated_at)}
        </div>
        {project.stats?.last_activity && (
          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            Active
          </div>
        )}
      </div>

      {/* Click overlay for navigation */}
      <div 
        className="absolute inset-0 cursor-pointer"
        onClick={onView}
        style={{ zIndex: 1 }}
      />
    </div>
  )
}
