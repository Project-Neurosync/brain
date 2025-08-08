'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  Home,
  MessageSquare,
  FolderOpen,
  Settings,
  Users,
  Search,
  Bell,
  Menu,
  X,
  LogOut,
  User,
  CreditCard,
  HelpCircle
} from 'lucide-react'
import { useAuth, useProfile, useTokenUsage } from '@/hooks/useAuth'
import ProtectedRoute from '@/components/ProtectedRoute'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'AI Chat', href: '/dashboard/chat', icon: MessageSquare },
  { name: 'Projects', href: '/dashboard/projects', icon: FolderOpen },
  { name: 'Team', href: '/dashboard/team', icon: Users },
  { name: 'Search', href: '/dashboard/search', icon: Search },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <DashboardContent>{children}</DashboardContent>
    </ProtectedRoute>
  )
}

function DashboardContent({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const { user: profileUser } = useProfile()
  const { tokenUsage } = useTokenUsage()

  // Use profile data if available, fallback to auth user data
  const currentUser = profileUser || user

  const getTokenColor = (remaining: number, total: number) => {
    const percentage = (remaining / total) * 100
    if (percentage > 50) return 'text-green-600 bg-green-100'
    if (percentage > 25) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getSubscriptionBadge = (tier: string) => {
    const badges = {
      starter: 'bg-blue-100 text-blue-800',
      professional: 'bg-purple-100 text-purple-800',
      enterprise: 'bg-gray-100 text-gray-800'
    }
    return badges[tier as keyof typeof badges] || badges.starter
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <div className="absolute inset-0 bg-gray-600 opacity-75" />
            </motion.div>

            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl lg:hidden"
            >
              <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
                <Link href="/dashboard" className="flex items-center space-x-2">
                  <Brain className="h-8 w-8 text-purple-600" />
                  <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                    NeuroSync
                  </span>
                </Link>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <SidebarContent 
                navigation={navigation} 
                pathname={pathname} 
                currentUser={currentUser}
                tokenUsage={tokenUsage}
                getTokenColor={getTokenColor}
                getSubscriptionBadge={getSubscriptionBadge}
                logout={logout}
              />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-6 border-b border-gray-200">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-purple-600" />
              <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                NeuroSync
              </span>
            </Link>
          </div>
          <SidebarContent 
            navigation={navigation} 
            pathname={pathname} 
            currentUser={currentUser}
            tokenUsage={tokenUsage}
            getTokenColor={getTokenColor}
            getSubscriptionBadge={getSubscriptionBadge}
            logout={logout}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top navigation */}
        <div className="sticky top-0 z-10 flex h-16 bg-white shadow-sm border-b border-gray-200">
          <button
            type="button"
            className="px-4 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex flex-1 justify-between px-4 lg:px-6">
            <div className="flex flex-1">
              {/* Search will go here */}
            </div>
            <div className="ml-4 flex items-center space-x-4">
              {/* Notifications */}
              <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full">
                <Bell className="h-5 w-5" />
              </button>

              {/* User menu */}
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {currentUser?.name?.charAt(0)?.toUpperCase() || 'U'}
                    </span>
                  </div>
                </div>
                <div className="hidden md:block">
                  <div className="text-sm font-medium text-gray-900">
                    {currentUser?.name || 'User'}
                  </div>
                  <div className="text-xs text-gray-500 capitalize">
                    {currentUser?.subscription_tier || 'starter'} plan
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  )
}

function SidebarContent({ 
  navigation, 
  pathname, 
  currentUser, 
  tokenUsage, 
  getTokenColor, 
  getSubscriptionBadge, 
  logout 
}: {
  navigation: any[]
  pathname: string
  currentUser: any
  tokenUsage: any
  getTokenColor: (remaining: number, total: number) => string
  getSubscriptionBadge: (tier: string) => string
  logout: () => void
}) {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-purple-100 text-purple-700 border-r-2 border-purple-600'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <item.icon
                className={`mr-3 h-5 w-5 flex-shrink-0 ${
                  isActive ? 'text-purple-600' : 'text-gray-400 group-hover:text-gray-600'
                }`}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Token Usage */}
      {tokenUsage && (
        <div className="px-4 py-4 border-t border-gray-200">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">AI Tokens</span>
              <span className={`text-xs px-2 py-1 rounded-full ${getTokenColor(tokenUsage.tokens_remaining, tokenUsage.tokens_total)}`}>
                {tokenUsage.tokens_remaining}/{tokenUsage.tokens_total}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.max(5, (tokenUsage.tokens_remaining / tokenUsage.tokens_total) * 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Resets on {new Date(tokenUsage.reset_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center space-x-3 mb-4">
          <div className="flex-shrink-0">
            <div className="h-10 w-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">
                {currentUser?.name?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {currentUser?.name || 'User'}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {currentUser?.email || 'user@example.com'}
            </p>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
              getSubscriptionBadge(currentUser?.subscription_tier || 'starter')
            }`}>
              {currentUser?.subscription_tier || 'starter'}
            </span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-1">
          <Link
            href="/dashboard/settings/profile"
            className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <User className="mr-3 h-4 w-4 text-gray-400" />
            Profile
          </Link>
          <Link
            href="/dashboard/settings/billing"
            className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <CreditCard className="mr-3 h-4 w-4 text-gray-400" />
            Billing
          </Link>
          <Link
            href="/help"
            className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <HelpCircle className="mr-3 h-4 w-4 text-gray-400" />
            Help
          </Link>
          <button
            onClick={logout}
            className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="mr-3 h-4 w-4 text-gray-400" />
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
