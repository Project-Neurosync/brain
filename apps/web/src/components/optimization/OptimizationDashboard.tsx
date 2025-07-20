/**
 * Cost Optimization Dashboard
 * Displays AI cost optimization metrics, savings, and model selection insights
 */

'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingDown,
  Zap,
  Brain,
  DollarSign,
  Clock,
  BarChart3,
  Settings,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Button, Badge, Progress } from '../ui'

interface OptimizationMetrics {
  totalQueries: number
  totalCostSaved: number
  savingsPercentage: number
  avgResponseTime: number
  modelDistribution: Record<string, number>
  cacheHitRate: number
}

interface ModelInfo {
  name: string
  tier: string
  costPer1k: number
  qualityScore: number
  bestFor: string
}

export function OptimizationDashboard() {
  const [metrics, setMetrics] = useState<OptimizationMetrics | null>(null)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)

  // Mock data for demonstration - replace with actual API calls
  useEffect(() => {
    const mockMetrics: OptimizationMetrics = {
      totalQueries: 1847,
      totalCostSaved: 0.127,
      savingsPercentage: 73.2,
      avgResponseTime: 1.4,
      modelDistribution: {
        'gpt-4o-mini': 1205,
        'gpt-4o': 487,
        'gpt-4': 155
      },
      cacheHitRate: 28.5
    }

    const mockModels: ModelInfo[] = [
      {
        name: 'gpt-4o-mini',
        tier: 'balanced',
        costPer1k: 0.00015,
        qualityScore: 8.5,
        bestFor: 'General queries, documentation'
      },
      {
        name: 'gpt-4o',
        tier: 'premium',
        costPer1k: 0.005,
        qualityScore: 9.5,
        bestFor: 'Complex analysis, code generation'
      },
      {
        name: 'gpt-4',
        tier: 'flagship',
        costPer1k: 0.03,
        qualityScore: 10.0,
        bestFor: 'Critical tasks, security analysis'
      },
      {
        name: 'gpt-3.5-turbo',
        tier: 'fast',
        costPer1k: 0.0015,
        qualityScore: 7.0,
        bestFor: 'Simple Q&A, quick responses'
      }
    ]

    setTimeout(() => {
      setMetrics(mockMetrics)
      setModels(mockModels)
      setLoading(false)
    }, 1000)
  }, [])

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'fast': return 'bg-green-100 text-green-800'
      case 'balanced': return 'bg-blue-100 text-blue-800'
      case 'premium': return 'bg-purple-100 text-purple-800'
      case 'flagship': return 'bg-amber-100 text-amber-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'fast': return <Zap className="h-4 w-4" />
      case 'balanced': return <BarChart3 className="h-4 w-4" />
      case 'premium': return <Brain className="h-4 w-4" />
      case 'flagship': return <Settings className="h-4 w-4" />
      default: return <Info className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!metrics) return null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cost Optimization</h2>
          <p className="text-gray-600 mt-1">
            AI model selection and cost savings dashboard
          </p>
        </div>
        <Button variant="outline" className="flex items-center gap-2">
          <Settings className="h-4 w-4" />
          Configure
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cost Saved</CardTitle>
              <TrendingDown className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                ${metrics.totalCostSaved.toFixed(3)}
              </div>
              <p className="text-xs text-gray-600">
                {metrics.savingsPercentage}% reduction
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
              <Brain className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.totalQueries.toLocaleString()}</div>
              <p className="text-xs text-gray-600">
                Processed with optimization
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
              <Clock className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.avgResponseTime}s</div>
              <p className="text-xs text-gray-600">
                Optimized for speed
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.cacheHitRate}%</div>
              <p className="text-xs text-gray-600">
                Queries served from cache
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Model Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Model Usage Distribution
            </CardTitle>
            <CardDescription>
              How queries are distributed across AI models
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(metrics.modelDistribution).map(([model, count]) => {
              const percentage = (count / metrics.totalQueries) * 100
              const modelInfo = models.find(m => m.name === model)
              
              return (
                <div key={model} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={getTierColor(modelInfo?.tier || 'balanced')}>
                        {getTierIcon(modelInfo?.tier || 'balanced')}
                        {model}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600">
                      {count} queries ({percentage.toFixed(1)}%)
                    </div>
                  </div>
                  <Progress value={percentage} className="h-2" />
                </div>
              )
            })}
          </CardContent>
        </Card>

        {/* Available Models */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Available Models
            </CardTitle>
            <CardDescription>
              AI models with cost and quality metrics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {models.map((model) => (
              <div key={model.name} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className={getTierColor(model.tier)}>
                      {getTierIcon(model.tier)}
                      {model.name}
                    </Badge>
                  </div>
                  <div className="text-sm font-medium">
                    ${model.costPer1k.toFixed(5)}/1k tokens
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Quality Score</span>
                    <div className="flex items-center gap-1">
                      <Progress value={model.qualityScore * 10} className="h-1 w-16" />
                      <span className="font-medium">{model.qualityScore}/10</span>
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-600">{model.bestFor}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Optimization Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-green-600" />
            Optimization Insights
          </CardTitle>
          <CardDescription>
            How our intelligent model selection saves costs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600 mb-2">
                {metrics.savingsPercentage}%
              </div>
              <div className="text-sm text-green-800 font-medium mb-1">Cost Reduction</div>
              <div className="text-xs text-green-600">
                vs. always using premium models
              </div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600 mb-2">
                {((metrics.modelDistribution['gpt-4o-mini'] || 0) / metrics.totalQueries * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-blue-800 font-medium mb-1">Efficient Routing</div>
              <div className="text-xs text-blue-600">
                queries use cost-optimized models
              </div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600 mb-2">
                {metrics.avgResponseTime}s
              </div>
              <div className="text-sm text-purple-800 font-medium mb-1">Fast Response</div>
              <div className="text-xs text-purple-600">
                average query processing time
              </div>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <div className="font-medium text-amber-800 mb-1">Smart Model Selection</div>
                <div className="text-sm text-amber-700">
                  Our system automatically analyzes query complexity and selects the most cost-effective model 
                  while maintaining quality. Simple queries use efficient models, complex tasks get premium processing.
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
