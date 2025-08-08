'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { authApi } from '@/lib/api/auth'
import { authService } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  CreditCardIcon, 
  CalendarIcon, 
  TrendingUpIcon,
  DollarSignIcon,
  BarChart3Icon
} from 'lucide-react'

interface TokenUsage {
  tokens_remaining: number
  tokens_total: number
  tokens_used_today: number
  tokens_used_this_month: number
  reset_date: string
  current_cost: number
  projected_monthly_cost: number
}

export default function BillingPage() {
  const { user, isAuthenticated } = useAuth()
  const [tokenUsage, setTokenUsage] = useState<TokenUsage | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTokenUsage = async () => {
      if (!isAuthenticated) return
      
      try {
        const usage = await authApi.getTokenUsage()
        setTokenUsage(usage)
      } catch (error) {
        console.error('Failed to fetch token usage:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTokenUsage()
  }, [isAuthenticated])

  const getSubscriptionColor = (tier: string) => {
    switch (tier) {
      case 'enterprise': return 'bg-purple-100 text-purple-800'
      case 'professional': return 'bg-blue-100 text-blue-800'
      default: return 'bg-green-100 text-green-800'
    }
  }

  const getSubscriptionPrice = (tier: string) => {
    switch (tier) {
      case 'enterprise': return '$49/month'
      case 'professional': return '$29/month'
      default: return '$19/month'
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Billing & Usage</h1>
        <p className="text-gray-600 mt-2">
          Manage your subscription and monitor your usage
        </p>
      </div>

      {/* Current Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCardIcon className="h-5 w-5" />
            Current Subscription
          </CardTitle>
          <CardDescription>
            Your current plan and billing information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge className={getSubscriptionColor(user?.subscription_tier || 'starter')}>
                  {user?.subscription_tier ? user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1) : 'Starter'}
                </Badge>
                <span className="text-2xl font-bold">
                  {getSubscriptionPrice(user?.subscription_tier || 'starter')}
                </span>
              </div>
              <p className="text-sm text-gray-600">
                Next billing date: {tokenUsage?.reset_date ? new Date(tokenUsage.reset_date).toLocaleDateString() : 'N/A'}
              </p>
            </div>
            <Button variant="outline">
              Upgrade Plan
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Usage Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tokens Remaining</CardTitle>
            <BarChart3Icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tokenUsage?.tokens_remaining?.toLocaleString() || '0'}
            </div>
            <div className="mt-2">
              <div className="h-2">
                <Progress 
                  value={tokenUsage ? (tokenUsage.tokens_remaining / tokenUsage.tokens_total) * 100 : 0} 
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              of {tokenUsage?.tokens_total?.toLocaleString() || '0'} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Usage</CardTitle>
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tokenUsage?.tokens_used_today?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              tokens used today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Usage</CardTitle>
            <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tokenUsage?.tokens_used_this_month?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              tokens this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Cost</CardTitle>
            <DollarSignIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${tokenUsage?.current_cost?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              this month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>
            Your recent billing transactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b">
              <div>
                <p className="font-medium">NeuroSync Professional</p>
                <p className="text-sm text-gray-600">December 2024</p>
              </div>
              <div className="text-right">
                <p className="font-medium">$29.00</p>
                <Badge variant="outline" className="text-xs">Paid</Badge>
              </div>
            </div>
            <div className="flex items-center justify-between py-2 border-b">
              <div>
                <p className="font-medium">NeuroSync Professional</p>
                <p className="text-sm text-gray-600">November 2024</p>
              </div>
              <div className="text-right">
                <p className="font-medium">$29.00</p>
                <Badge variant="outline" className="text-xs">Paid</Badge>
              </div>
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">NeuroSync Professional</p>
                <p className="text-sm text-gray-600">October 2024</p>
              </div>
              <div className="text-right">
                <p className="font-medium">$29.00</p>
                <Badge variant="outline" className="text-xs">Paid</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
          <CardDescription>
            Manage your payment information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center">
                <span className="text-white text-xs font-bold">VISA</span>
              </div>
              <div>
                <p className="font-medium">•••• •••• •••• 4242</p>
                <p className="text-sm text-gray-600">Expires 12/25</p>
              </div>
            </div>
            <Button variant="outline">
              Update
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
