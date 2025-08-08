'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  UserIcon, 
  CreditCardIcon, 
  BellIcon,
  ShieldIcon,
  KeyIcon,
  DatabaseIcon,
  PlugIcon,
  HelpCircleIcon,
  ChevronRightIcon
} from 'lucide-react'

const settingsCategories = [
  {
    title: 'Profile',
    description: 'Manage your personal information and account details',
    icon: UserIcon,
    href: '/dashboard/settings/profile',
    color: 'text-blue-600'
  },
  {
    title: 'Billing',
    description: 'View your subscription, usage, and payment methods',
    icon: CreditCardIcon,
    href: '/dashboard/settings/billing',
    color: 'text-green-600'
  },
  {
    title: 'Notifications',
    description: 'Configure your notification preferences',
    icon: BellIcon,
    href: '/dashboard/settings/notifications',
    color: 'text-purple-600'
  },
  {
    title: 'Security',
    description: 'Manage your security settings and two-factor authentication',
    icon: ShieldIcon,
    href: '/dashboard/settings/security',
    color: 'text-red-600'
  },
  {
    title: 'API Keys',
    description: 'Generate and manage your API keys',
    icon: KeyIcon,
    href: '/dashboard/settings/api-keys',
    color: 'text-orange-600'
  },
  {
    title: 'Data & Privacy',
    description: 'Control your data and privacy settings',
    icon: DatabaseIcon,
    href: '/dashboard/settings/privacy',
    color: 'text-indigo-600'
  },
  {
    title: 'Integrations',
    description: 'Connect with external services and tools',
    icon: PlugIcon,
    href: '/dashboard/settings/integrations',
    color: 'text-teal-600'
  },
  {
    title: 'Support',
    description: 'Get help and contact our support team',
    icon: HelpCircleIcon,
    href: '/dashboard/settings/support',
    color: 'text-gray-600'
  }
]

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Settings Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingsCategories.map((category) => {
          const IconComponent = category.icon
          return (
            <Link key={category.href} href={category.href}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer group">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-lg bg-gray-50 group-hover:bg-gray-100 transition-colors`}>
                        <IconComponent className={`h-6 w-6 ${category.color}`} />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
                          {category.title}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {category.description}
                        </p>
                      </div>
                    </div>
                    <ChevronRightIcon className="h-5 w-5 text-gray-400 group-hover:text-purple-600 transition-colors" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common settings and actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/dashboard/settings/profile">
                <UserIcon className="h-4 w-4 mr-2" />
                Update Profile
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/dashboard/settings/billing">
                <CreditCardIcon className="h-4 w-4 mr-2" />
                View Billing
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/dashboard/settings/security">
                <ShieldIcon className="h-4 w-4 mr-2" />
                Security Settings
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Account Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Account Overview</CardTitle>
          <CardDescription>
            Quick overview of your account status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">Active</div>
              <div className="text-sm text-gray-600">Account Status</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">Professional</div>
              <div className="text-sm text-gray-600">Current Plan</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">5</div>
              <div className="text-sm text-gray-600">Team Members</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">3</div>
              <div className="text-sm text-gray-600">Active Projects</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
