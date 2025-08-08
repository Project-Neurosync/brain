'use client'

import { motion } from 'framer-motion'
import { 
  Brain, 
  TrendingUp, 
  Users, 
  MessageSquare, 
  FileText, 
  Clock, 
  ArrowRight,
  Plus,
  Search,
  Zap,
  Github,
  Calendar,
  Activity,
  Upload
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getUserProfile, getProjects, getDashboardStats, getRecentAIQueries } from '@/lib/api'
import { integrationApi } from '@/lib/api/integrations'
import { useRouter } from 'next/navigation'

interface User {
  name: string;
  email?: string;
}

interface Project {
  id: number | string;
  name: string;
  description: string;
  lastActivity: string;
  memberCount: number;
  status: string;
  progress: number;
}

interface DashboardStats {
  totalProjects: number;
  projectsChange: number;
  aiQueries: number;
  queriesChange: number;
  teamMembers: number;
  membersChange: number;
  documentsSynced: number;
  documentsChange: number;
}

interface DashboardStatCard {
  name: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: any;
}

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 }
}

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}

export default function DashboardPage() {
  const [user, setUser] = useState<User>({ name: '', email: '' })
  const [stats, setStats] = useState<DashboardStatCard[]>([
    {
      name: 'Total Projects',
      value: '0',
      change: '+0',
      changeType: 'neutral',
      icon: FileText,
    },
    {
      name: 'AI Queries Today',
      value: '0',
      change: '+0',
      changeType: 'neutral',
      icon: MessageSquare,
    },
    {
      name: 'Team Members',
      value: '0',
      change: '+0',
      changeType: 'neutral',
      icon: Users,
    },
    {
      name: 'Documents Synced',
      value: '0',
      change: '+0',
      changeType: 'neutral',
      icon: Activity,
    },
  ])

  const [recentProjects, setRecentProjects] = useState<Project[]>([])
  const [integrations, setIntegrations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const router = useRouter()

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Fetch user profile
        const userData = await getUserProfile()
        if (userData) {
          setUser(userData)
        }
        
        // Fetch projects
        const projectsData = await getProjects()
        if (projectsData && projectsData.length > 0) {
          setRecentProjects(projectsData.map((project: Project) => ({
            id: project.id,
            name: project.name,
            description: project.description,
            lastActivity: project.lastActivity,
            members: project.memberCount,
            status: project.status,
            progress: project.progress,
          })))
        }
        
        // Fetch dashboard stats
        const statsData = await getDashboardStats()
        if (statsData) {
          setStats([
            {
              name: 'Total Projects',
              value: statsData.totalProjects.toString(),
              change: statsData.projectsChange > 0 ? `+${statsData.projectsChange}` : statsData.projectsChange.toString(),
              changeType: statsData.projectsChange > 0 ? 'positive' : statsData.projectsChange < 0 ? 'negative' : 'neutral',
              icon: FileText,
            },
            {
              name: 'AI Queries Today',
              value: statsData.aiQueries.toString(),
              change: statsData.queriesChange > 0 ? `+${statsData.queriesChange}%` : `${statsData.queriesChange}%`,
              changeType: statsData.queriesChange > 0 ? 'positive' : statsData.queriesChange < 0 ? 'negative' : 'neutral',
              icon: MessageSquare,
            },
            {
              name: 'Team Members',
              value: statsData.teamMembers.toString(),
              change: statsData.membersChange > 0 ? `+${statsData.membersChange}` : statsData.membersChange.toString(),
              changeType: statsData.membersChange > 0 ? 'positive' : statsData.membersChange < 0 ? 'negative' : 'neutral',
              icon: Users,
            },
            {
              name: 'Documents Synced',
              value: statsData.documentsSynced.toLocaleString(),
              change: statsData.documentsChange > 0 ? `+${statsData.documentsChange}` : statsData.documentsChange.toString(),
              changeType: statsData.documentsChange > 0 ? 'positive' : statsData.documentsChange < 0 ? 'negative' : 'neutral',
              icon: Activity,
            },
          ])
        }
        
        // We already fetched projects above, no need to do it again
        
        // Fetch recent AI queries
        const recentQueriesData = await getRecentAIQueries(5)
        if (recentQueriesData && recentQueriesData.length > 0) {
          setRecentQueries(recentQueriesData.map((query: any) => ({
            id: query.id,
            query: query.query,
            project_name: query.project_name,
            timestamp: formatTimestamp(query.timestamp),
            confidence: query.confidence
          })))
        }
        
        // Fetch all user integrations (including projectless ones)
        const integrationsData = await integrationApi.getUserIntegrations()
        if (integrationsData) {
          setIntegrations(integrationsData)
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    // Helper function to format timestamp to relative time
    const formatTimestamp = (timestamp: string) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.round(diffMs / 60000)
      
      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`
      
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`
      
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
    }
    
    fetchData()
  }, [])

  const [recentQueries, setRecentQueries] = useState<Array<{
    id: string;
    query: string;
    project_name: string;
    timestamp: string;
    confidence: number;
  }>>([])

  const quickActions = [
    {
      name: 'Ask AI',
      description: 'Get instant answers from your project knowledge',
      icon: Brain,
      href: '/dashboard/chat',
      color: 'from-primary-500 to-secondary-500',
    },
    {
      name: 'Search Documents',
      description: 'Find information across all your projects',
      icon: Search,
      href: '/dashboard/search',
      color: 'from-secondary-500 to-accent-500',
    },
    {
      name: 'New Project',
      description: 'Start a new project and sync your data',
      icon: Plus,
      href: '/dashboard/projects/new',
      color: 'from-accent-500 to-primary-500',
    },
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-bold">
            {loading ? 'Loading...' : `Welcome back, ${user.name}!`} <span className="wave">👋</span>
          </h1>
          <p className="text-muted-foreground">Here's what's happening with your projects today.</p>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {stats.map((stat, index) => (
          <motion.div
            key={stat.name}
            variants={fadeInUp}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                <div className="flex items-center mt-2">
                  <span className={`text-sm font-medium ${
                    stat.changeType === 'positive' ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">from last week</span>
                </div>
              </div>
              <div className={`w-12 h-12 bg-gradient-to-r ${
                index === 0 ? 'from-primary-500 to-secondary-500' :
                index === 1 ? 'from-secondary-500 to-accent-500' :
                index === 2 ? 'from-accent-500 to-primary-500' :
                'from-primary-500 to-accent-500'
              } rounded-xl flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Quick Actions */}
        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-4">
            {quickActions.map((action, index) => (
              <Link
                key={action.name}
                href={action.href}
                className="block card-hover p-4 group"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-12 h-12 bg-gradient-to-r ${action.color} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform`}>
                    <action.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {action.name}
                    </h3>
                    <p className="text-sm text-gray-600">{action.description}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
                </div>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Recent Projects */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Projects</h2>
            <Link
              href="/dashboard/projects"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View all
            </Link>
          </div>
          
          <div className="space-y-4">
            {recentProjects.map((project) => (
              <div key={project.id} className="card p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{project.name}</h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        project.status === 'active' 
                          ? 'bg-success-100 text-success-800'
                          : 'bg-warning-100 text-warning-800'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mb-3">{project.description}</p>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <Users className="w-4 h-4" />
                <span>{project.memberCount} members</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{project.lastActivity}</span>
              </div>
            </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900 mb-2">
                      {project.progress}% complete
                    </div>
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full"
                        style={{ width: `${project.progress}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Recent AI Queries */}
      <motion.div
        className="mt-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent AI Queries</h2>
          <Link
            href="/dashboard/chat"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all
          </Link>
        </div>
        
        <div className="card">
          <div className="divide-y divide-gray-200">
            {recentQueries.map((query, index) => (
              <div key={query.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium mb-2">{query.query}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span className="flex items-center space-x-1">
                        <FileText className="w-4 h-4" />
                        <span>{query.project_name}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{query.timestamp}</span>
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <div className="flex items-center space-x-1">
                      <Zap className="w-4 h-4 text-primary-500" />
                      <span className="text-sm font-medium text-gray-900">{query.confidence}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Integration Status */}
      <motion.div
        className="mt-8 grid md:grid-cols-2 gap-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Status</h3>
          <div className="space-y-3">
            {loading ? (
              <div className="text-sm text-gray-500">Loading integrations...</div>
            ) : (
              <>
                {/* GitHub Integration */}
                {(() => {
                  const githubIntegration = integrations.find(i => i.type === 'github')
                  const isConnected = githubIntegration && githubIntegration.status === 'connected'
                  return (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Github className="w-5 h-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">GitHub</span>
                      </div>
                      {isConnected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          Connected
                        </span>
                      ) : (
                        <button 
                          onClick={() => router.push('/dashboard/integrations/github')}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  )
                })()}
                
                {/* Slack Integration */}
                {(() => {
                  const slackIntegration = integrations.find(i => i.type === 'slack')
                  const isConnected = slackIntegration && slackIntegration.status === 'connected'
                  return (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <MessageSquare className="w-5 h-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Slack</span>
                      </div>
                      {isConnected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          Connected
                        </span>
                      ) : (
                        <button 
                          onClick={() => router.push('/dashboard/integrations/slack')}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  )
                })()}
                
                {/* Jira Integration */}
                {(() => {
                  const jiraIntegration = integrations.find(i => i.type === 'jira')
                  const isConnected = jiraIntegration && jiraIntegration.status === 'connected'
                  return (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Calendar className="w-5 h-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Jira</span>
                      </div>
                      {isConnected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          Connected
                        </span>
                      ) : (
                        <button 
                          onClick={() => router.push('/dashboard/integrations/jira')}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  )
                })()}

                {/* Confluence Integration */}
                {(() => {
                  const confluenceIntegration = integrations.find(i => i.type === 'confluence')
                  const isConnected = confluenceIntegration && confluenceIntegration.status === 'connected'
                  return (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Confluence</span>
                      </div>
                      {isConnected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          Connected
                        </span>
                      ) : (
                        <button 
                          onClick={() => router.push('/dashboard/integrations/confluence')}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  )
                })()}

                {/* Notion Integration */}
                {(() => {
                  const notionIntegration = integrations.find(i => i.type === 'notion')
                  const isConnected = notionIntegration && notionIntegration.status === 'connected'
                  return (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-600" />
                        <span className="text-sm font-medium text-gray-900">Notion</span>
                      </div>
                      {isConnected ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          Connected
                        </span>
                      ) : (
                        <button 
                          onClick={() => router.push('/dashboard/integrations/notion')}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  )
                })()}
              </>
            )}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage This Month</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">AI Queries</span>
                <span className="text-sm text-gray-600">847 / 5,000</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full" style={{ width: '17%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Documents Processed</span>
                <span className="text-sm text-gray-600">1,247 / ∞</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-gradient-to-r from-secondary-500 to-accent-500 h-2 rounded-full" style={{ width: '100%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
