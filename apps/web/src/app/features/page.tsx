import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { 
  BrainIcon, 
  SearchIcon, 
  CodeIcon,
  UsersIcon,
  ShieldIcon,
  ZapIcon,
  GitBranchIcon,
  MessageSquareIcon,
  FileTextIcon,
  BarChart3Icon,
  IntegrationsIcon,
  ClockIcon
} from 'lucide-react'

const features = [
  {
    icon: BrainIcon,
    title: 'AI-Powered Knowledge Transfer',
    description: 'Intelligent context understanding that learns from your codebase, documentation, and team conversations.',
    benefits: ['Instant onboarding', 'Context-aware answers', 'Smart suggestions']
  },
  {
    icon: SearchIcon,
    title: 'Universal Search',
    description: 'Search across code, docs, chats, and meetings with semantic understanding.',
    benefits: ['Cross-platform search', 'Semantic matching', 'Relevance scoring']
  },
  {
    icon: CodeIcon,
    title: 'Code Intelligence',
    description: 'Deep code analysis with function mapping, dependency tracking, and impact analysis.',
    benefits: ['Function discovery', 'Dependency mapping', 'Change impact']
  },
  {
    icon: UsersIcon,
    title: 'Team Collaboration',
    description: 'Seamless team knowledge sharing with role-based access and project organization.',
    benefits: ['Team workspaces', 'Role permissions', 'Knowledge sharing']
  },
  {
    icon: IntegrationsIcon,
    title: 'Platform Integrations',
    description: 'Connect with GitHub, Jira, Slack, and more to centralize your development workflow.',
    benefits: ['GitHub sync', 'Jira integration', 'Slack connectivity']
  },
  {
    icon: ShieldIcon,
    title: 'Enterprise Security',
    description: 'SOC2 compliant with end-to-end encryption and granular access controls.',
    benefits: ['SOC2 compliance', 'Data encryption', 'Access controls']
  }
]

const useCases = [
  {
    title: 'For Developers',
    description: 'Effortless Knowledge Transfer',
    icon: CodeIcon,
    color: 'bg-blue-50 text-blue-600',
    features: ['AI-powered onboarding', 'Code context search', 'Function discovery', 'Impact analysis']
  },
  {
    title: 'For Researchers',
    description: 'Unified Research Hub',
    icon: FileTextIcon,
    color: 'bg-green-50 text-green-600',
    features: ['Research organization', 'Finding correlation', 'Knowledge graphs', 'Citation tracking']
  },
  {
    title: 'For Writers',
    description: 'Your AI Writing Partner',
    icon: MessageSquareIcon,
    color: 'bg-purple-50 text-purple-600',
    features: ['Draft assistance', 'Idea organization', 'Content search', 'Version tracking']
  },
  {
    title: 'For Teams',
    description: 'Collaborative Knowledge Base',
    icon: UsersIcon,
    color: 'bg-orange-50 text-orange-600',
    features: ['Team workspaces', 'Knowledge sharing', 'Onboarding automation', 'Context preservation']
  }
]

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Features Overview
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Everything you need for
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> knowledge transfer</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            NeuroSync combines AI intelligence with seamless integrations to create 
            the ultimate knowledge management platform for modern development teams.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/demo">Watch Demo</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Built for developers, by developers. Every feature designed to solve real knowledge transfer challenges.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mb-4">
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                    <CardDescription className="text-base">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {feature.benefits.map((benefit, idx) => (
                        <li key={idx} className="flex items-center text-sm text-gray-600">
                          <ZapIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          {benefit}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Built for Every Role
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Whether you're a developer, researcher, writer, or team lead - NeuroSync adapts to your workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {useCases.map((useCase, index) => {
              const IconComponent = useCase.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className={`w-12 h-12 ${useCase.color} rounded-lg flex items-center justify-center mb-4`}>
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <CardTitle className="text-xl">{useCase.title}</CardTitle>
                    <CardDescription className="text-base font-medium text-gray-900">
                      {useCase.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2">
                      {useCase.features.map((feature, idx) => (
                        <div key={idx} className="flex items-center text-sm text-gray-600">
                          <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mr-2 flex-shrink-0"></div>
                          {feature}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Technical Capabilities */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Technical Excellence
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Enterprise-grade architecture with cutting-edge AI capabilities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg">
              <BarChart3Icon className="h-8 w-8 text-purple-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">99.9% Uptime</h3>
              <p className="text-sm text-gray-600">Enterprise SLA with redundant infrastructure</p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
              <ZapIcon className="h-8 w-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">&lt;200ms Response</h3>
              <p className="text-sm text-gray-600">Lightning-fast AI-powered search</p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
              <ShieldIcon className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">SOC2 Compliant</h3>
              <p className="text-sm text-gray-600">Enterprise security and compliance</p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg">
              <ClockIcon className="h-8 w-8 text-orange-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">24/7 Support</h3>
              <p className="text-sm text-gray-600">Round-the-clock expert assistance</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to transform your knowledge transfer?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Join thousands of teams already using NeuroSync to accelerate onboarding and preserve critical knowledge.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/contact">Contact Sales</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
