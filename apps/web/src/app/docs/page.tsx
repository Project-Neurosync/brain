import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'
import { 
  BookOpenIcon,
  SearchIcon,
  RocketIcon,
  CodeIcon,
  IntegrationsIcon,
  ShieldIcon,
  ApiIcon,
  HelpCircleIcon,
  ArrowRightIcon,
  PlayIcon,
  FileTextIcon,
  SettingsIcon
} from 'lucide-react'

const docSections = [
  {
    title: 'Getting Started',
    description: 'Quick start guide and basic concepts',
    icon: RocketIcon,
    color: 'bg-green-100 text-green-800',
    articles: [
      { title: 'Quick Start Guide', description: 'Get up and running in 5 minutes' },
      { title: 'Core Concepts', description: 'Understanding NeuroSync fundamentals' },
      { title: 'First Project Setup', description: 'Create your first knowledge base' },
      { title: 'Team Onboarding', description: 'Invite and manage team members' }
    ]
  },
  {
    title: 'Integrations',
    description: 'Connect your tools and platforms',
    icon: IntegrationsIcon,
    color: 'bg-blue-100 text-blue-800',
    articles: [
      { title: 'GitHub Integration', description: 'Sync repositories and pull requests' },
      { title: 'Slack Integration', description: 'Import conversations and threads' },
      { title: 'Jira Integration', description: 'Connect tickets and project data' },
      { title: 'Custom Integrations', description: 'Build your own connectors' }
    ]
  },
  {
    title: 'API Reference',
    description: 'Complete API documentation',
    icon: ApiIcon,
    color: 'bg-purple-100 text-purple-800',
    articles: [
      { title: 'Authentication', description: 'API keys and OAuth setup' },
      { title: 'REST API', description: 'Complete endpoint reference' },
      { title: 'GraphQL API', description: 'Query language and schema' },
      { title: 'Webhooks', description: 'Real-time event notifications' }
    ]
  },
  {
    title: 'AI Features',
    description: 'Leverage AI-powered capabilities',
    icon: CodeIcon,
    color: 'bg-orange-100 text-orange-800',
    articles: [
      { title: 'AI Chat Interface', description: 'Interact with your knowledge base' },
      { title: 'Code Analysis', description: 'Automated code documentation' },
      { title: 'Smart Search', description: 'Semantic search capabilities' },
      { title: 'Content Generation', description: 'AI-powered content creation' }
    ]
  },
  {
    title: 'Security & Privacy',
    description: 'Data protection and compliance',
    icon: ShieldIcon,
    color: 'bg-red-100 text-red-800',
    articles: [
      { title: 'Security Overview', description: 'Our security architecture' },
      { title: 'Data Encryption', description: 'How we protect your data' },
      { title: 'Compliance', description: 'SOC2, GDPR, and other standards' },
      { title: 'Access Controls', description: 'User permissions and roles' }
    ]
  },
  {
    title: 'Configuration',
    description: 'Customize and configure NeuroSync',
    icon: SettingsIcon,
    color: 'bg-indigo-100 text-indigo-800',
    articles: [
      { title: 'Project Settings', description: 'Configure project preferences' },
      { title: 'Team Management', description: 'User roles and permissions' },
      { title: 'Notification Settings', description: 'Customize alerts and updates' },
      { title: 'Advanced Configuration', description: 'Enterprise customization' }
    ]
  }
]

const popularArticles = [
  {
    title: 'Getting Started with NeuroSync',
    description: 'Complete beginner\'s guide to setting up your first project',
    category: 'Getting Started',
    readTime: '5 min read'
  },
  {
    title: 'GitHub Integration Setup',
    description: 'Step-by-step guide to connecting your GitHub repositories',
    category: 'Integrations',
    readTime: '3 min read'
  },
  {
    title: 'AI Chat Best Practices',
    description: 'How to get the most out of NeuroSync\'s AI features',
    category: 'AI Features',
    readTime: '7 min read'
  },
  {
    title: 'API Authentication',
    description: 'Setting up API keys and OAuth for programmatic access',
    category: 'API Reference',
    readTime: '4 min read'
  }
]

const quickLinks = [
  { title: 'API Status', href: '/status', icon: PlayIcon },
  { title: 'Changelog', href: '/changelog', icon: FileTextIcon },
  { title: 'Support', href: '/contact', icon: HelpCircleIcon },
  { title: 'Community', href: '/community', icon: IntegrationsIcon }
]

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Documentation
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Everything you need to know about
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> NeuroSync</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Comprehensive guides, API references, and tutorials to help you get the most 
            out of NeuroSync's AI-powered knowledge management platform.
          </p>
          
          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-8">
            <div className="relative">
              <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                placeholder="Search documentation..."
                className="pl-12 pr-4 py-3 text-lg border-2 border-gray-200 focus:border-purple-500"
              />
            </div>
          </div>
          
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/docs/getting-started">Get Started</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs/api">API Reference</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {quickLinks.map((link, index) => {
                const IconComponent = link.icon
                return (
                  <Link key={index} href={link.href}>
                    <Card className="hover:shadow-md transition-shadow text-center">
                      <CardContent className="pt-6">
                        <IconComponent className="h-6 w-6 text-purple-600 mx-auto mb-2" />
                        <p className="text-sm font-medium">{link.title}</p>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Documentation Sections
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Find detailed guides and references for every aspect of NeuroSync.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
            {docSections.map((section, index) => {
              const IconComponent = section.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                        <IconComponent className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{section.title}</CardTitle>
                        <Badge className={section.color} variant="secondary">
                          {section.articles.length} articles
                        </Badge>
                      </div>
                    </div>
                    <CardDescription>{section.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {section.articles.map((article, idx) => (
                        <Link key={idx} href={`/docs/${section.title.toLowerCase().replace(/\s+/g, '-')}/${article.title.toLowerCase().replace(/\s+/g, '-')}`}>
                          <div className="flex items-center justify-between p-2 rounded hover:bg-gray-50 transition-colors">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{article.title}</p>
                              <p className="text-xs text-gray-600">{article.description}</p>
                            </div>
                            <ArrowRightIcon className="h-4 w-4 text-gray-400" />
                          </div>
                        </Link>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Popular Articles */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Popular Articles
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Most read guides and tutorials from our documentation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {popularArticles.map((article, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline">{article.category}</Badge>
                    <span className="text-xs text-gray-500">{article.readTime}</span>
                  </div>
                  <CardTitle className="text-lg hover:text-purple-600 transition-colors">
                    <Link href={`/docs/${article.title.toLowerCase().replace(/\s+/g, '-')}`}>
                      {article.title}
                    </Link>
                  </CardTitle>
                  <CardDescription>{article.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/docs/${article.title.toLowerCase().replace(/\s+/g, '-')}`}>
                      Read Article
                      <ArrowRightIcon className="h-3 w-3 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Developer Resources */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Developer Resources
            </h2>
            <p className="text-xl text-gray-600 mb-12">
              Additional resources to help you build with NeuroSync.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <CodeIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Code Examples</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    Ready-to-use code snippets and examples for common use cases.
                  </p>
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/docs/examples">View Examples</Link>
                  </Button>
                </CardContent>
              </Card>

              <Card className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <BookOpenIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Tutorials</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    Step-by-step tutorials for building with NeuroSync APIs.
                  </p>
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/docs/tutorials">Start Learning</Link>
                  </Button>
                </CardContent>
              </Card>

              <Card className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <HelpCircleIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>Support</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    Get help from our community and support team.
                  </p>
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/contact">Get Support</Link>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to get started?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Follow our quick start guide and have NeuroSync up and running in minutes.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/docs/getting-started">Quick Start Guide</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
