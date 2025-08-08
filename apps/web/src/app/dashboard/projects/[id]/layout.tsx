/**
 * Project Layout
 * Navigation layout for individual project pages
 */

'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  MessageSquare, 
  Settings, 
  Users, 
  Database,
  Plug,
  BarChart3
} from 'lucide-react'
import { cn } from '../../../../lib/utils'

interface ProjectLayoutProps {
  children: React.ReactNode
  params: {
    id: string
  }
}

const navigation = [
  {
    name: 'Overview',
    href: '',
    icon: LayoutDashboard
  },
  {
    name: 'Chat',
    href: '/chat',
    icon: MessageSquare
  },
  {
    name: 'Data',
    href: '/data',
    icon: Database
  },
  {
    name: 'Integrations',
    href: '/integrations',
    icon: Plug
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3
  },
  {
    name: 'Team',
    href: '/team',
    icon: Users
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings
  }
]

export default function ProjectLayout({ children, params }: ProjectLayoutProps) {
  const pathname = usePathname()
  const projectId = params.id
  const basePath = `/dashboard/projects/${projectId}`

  const isActive = (href: string) => {
    const fullPath = basePath + href
    return pathname === fullPath || (href === '' && pathname === basePath)
  }

  return (
    <div className="flex h-full">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Project</h2>
          <p className="text-sm text-gray-600 mt-1">ID: {projectId}</p>
        </div>
        
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const href = basePath + item.href
              const active = isActive(item.href)
              
              return (
                <li key={item.name}>
                  <Link
                    href={href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative',
                      active
                        ? 'bg-purple-50 text-purple-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    )}
                  >
                    {active && (
                      <motion.div
                        layoutId="activeTab"
                        className="absolute inset-0 bg-purple-50 rounded-lg"
                        initial={false}
                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                      />
                    )}
                    <item.icon className={cn(
                      'h-5 w-5 relative z-10',
                      active ? 'text-purple-600' : 'text-gray-500'
                    )} />
                    <span className="relative z-10">{item.name}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
