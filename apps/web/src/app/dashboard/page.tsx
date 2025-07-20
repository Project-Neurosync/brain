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
  Activity
} from 'lucide-react'
import Link from 'next/link'

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
  const stats = [
    {
      name: 'Total Projects',
      value: '12',
      change: '+2',
      changeType: 'positive',
      icon: FileText,
    },
    {
      name: 'AI Queries Today',
      value: '47',
      change: '+12%',
      changeType: 'positive',
      icon: MessageSquare,
    },
    {
      name: 'Team Members',
      value: '8',
      change: '+1',
      changeType: 'positive',
      icon: Users,
    },
    {
      name: 'Documents Synced',
      value: '1,247',
      change: '+89',
      changeType: 'positive',
      icon: Activity,
    },
  ]

  const recentProjects = [
    {
      id: 1,
      name: 'E-commerce Platform',
      description: 'Next.js and Stripe integration for online store',
      lastActivity: '2 hours ago',
      members: 5,
      status: 'active',
      progress: 75,
    },
    {
      id: 2,
      name: 'Mobile App Backend',
      description: 'FastAPI backend with PostgreSQL database',
      lastActivity: '5 hours ago',
      members: 3,
      status: 'active',
      progress: 60,
    },
    {
      id: 3,
      name: 'Data Analytics Dashboard',
      description: 'React dashboard with real-time analytics',
      lastActivity: '1 day ago',
      members: 4,
      status: 'review',
      progress: 90,
    },
  ]

  const recentQueries = [
    {
      id: 1,
      query: 'How do we handle user authentication in the mobile app?',
      project: 'Mobile App Backend',
      timestamp: '10 minutes ago',
      confidence: 95,
    },
    {
      id: 2,
      query: 'What are the current API rate limits for the payment service?',
      project: 'E-commerce Platform',
      timestamp: '1 hour ago',
      confidence: 88,
    },
    {
      id: 3,
      query: 'How to implement real-time notifications?',
      project: 'Data Analytics Dashboard',
      timestamp: '3 hours ago',
      confidence: 92,
    },
  ]

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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, John! 👋
        </h1>
        <p className="text-gray-600">
          Here's what's happening with your projects today.
        </p>
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
                        <span>{project.members} members</span>
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
                        <span>{query.project}</span>
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
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Github className="w-5 h-5 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">GitHub</span>
              </div>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <MessageSquare className="w-5 h-5 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">Slack</span>
              </div>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800">
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">Jira</span>
              </div>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-800">
                Setup Required
              </span>
            </div>
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
