import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { 
  GitBranchIcon,
  MessageSquareIcon,
  TicketIcon,
  CalendarIcon,
  FileTextIcon,
  DatabaseIcon,
  CloudIcon,
  ZapIcon,
  CheckIcon,
  ArrowRightIcon
} from 'lucide-react'

const integrations = [
  {
    name: 'GitHub',
    description: 'Sync repositories, pull requests, issues, and commit history',
    icon: GitBranchIcon,
    category: 'Development',
    features: ['Code sync', 'PR analysis', 'Issue tracking', 'Commit history'],
    status: 'Available',
    color: 'bg-gray-900 text-white'
  },
  {
    name: 'Slack',
    description: 'Import conversations, threads, and team communications',
    icon: MessageSquareIcon,
    category: 'Communication',
    features: ['Channel sync', 'Thread import', 'Message search', 'Team context'],
    status: 'Available',
    color: 'bg-purple-600 text-white'
  },
  {
    name: 'Jira',
    description: 'Connect tickets, sprints, and project management data',
    icon: TicketIcon,
    category: 'Project Management',
    features: ['Ticket sync', 'Sprint data', 'Project tracking', 'Status updates'],
    status: 'Available',
    color: 'bg-blue-600 text-white'
  },
  {
    name: 'Confluence',
    description: 'Import documentation, wikis, and knowledge base articles',
    icon: FileTextIcon,
    category: 'Documentation',
    features: ['Page sync', 'Wiki import', 'Version history', 'Content search'],
    status: 'Available',
    color: 'bg-blue-500 text-white'
  }
]

const categories = [
  {
    name: 'Development',
    description: 'Code repositories, CI/CD, and development tools',
    count: integrations.filter(i => i.category === 'Development').length
  },
  {
    name: 'Communication',
    description: 'Team chat, messaging, and collaboration platforms',
    count: integrations.filter(i => i.category === 'Communication').length
  },
  {
    name: 'Project Management',
    description: 'Task tracking, project planning, and workflow tools',
    count: integrations.filter(i => i.category === 'Project Management').length
  },
  {
    name: 'Documentation',
    description: 'Knowledge bases, wikis, and documentation platforms',
    count: integrations.filter(i => i.category === 'Documentation').length
  },
  {
    name: 'Productivity',
    description: 'Calendar, notes, and productivity applications',
    count: integrations.filter(i => i.category === 'Productivity').length
  }
]

const benefits = [
  {
    title: 'Unified Knowledge Base',
    description: 'All your tools and data in one searchable, AI-powered platform'
  },
  {
    title: 'Automatic Sync',
    description: 'Real-time synchronization keeps your knowledge base up-to-date'
  },
  {
    title: 'Context Preservation',
    description: 'Maintain relationships between code, discussions, and documentation'
  },
  {
    title: 'Smart Search',
    description: 'AI-powered search across all your integrated platforms'
  }
]

export default function IntegrationsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Integrations
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Connect your entire
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> tech stack</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            NeuroSync integrates with all your favorite tools to create a unified knowledge base. 
            No more switching between platforms to find information.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">Start Connecting</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/contact">Request Integration</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Integration Categories
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We support integrations across all the tools your team uses daily.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {categories.map((category, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{category.name}</CardTitle>
                    <Badge variant="outline">{category.count} integrations</Badge>
                  </div>
                  <CardDescription>{category.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Available Integrations */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Available Integrations
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Connect with the tools your team already uses and loves.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
            {integrations.map((integration, index) => {
              const IconComponent = integration.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 ${integration.color} rounded-lg flex items-center justify-center`}>
                        <IconComponent className="h-6 w-6" />
                      </div>
                      <div>
                        <CardTitle className="text-xl">{integration.name}</CardTitle>
                        <Badge 
                          variant={integration.status === 'Available' ? 'default' : 'secondary'}
                          className={integration.status === 'Available' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}
                        >
                          {integration.status}
                        </Badge>
                      </div>
                    </div>
                    <CardDescription>{integration.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Key Features:</p>
                        <div className="grid grid-cols-2 gap-1">
                          {integration.features.map((feature, idx) => (
                            <div key={idx} className="flex items-center text-sm text-gray-600">
                              <CheckIcon className="h-3 w-3 text-green-500 mr-1 flex-shrink-0" />
                              {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <Button 
                        variant={integration.status === 'Available' ? 'default' : 'outline'} 
                        size="sm" 
                        className="w-full"
                        disabled={integration.status !== 'Available'}
                      >
                        {integration.status === 'Available' ? 'Connect Now' : 'Coming Soon'}
                        {integration.status === 'Available' && <ArrowRightIcon className="h-4 w-4 ml-2" />}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Integrate with NeuroSync?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Unlock the full potential of your existing tools and data.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {benefits.map((benefit, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                      <CheckIcon className="h-4 w-4 text-white" />
                    </div>
                    {benefit.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{benefit.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Setting up integrations is simple and secure.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-white text-xl font-bold">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Connect Your Tools</h3>
              <p className="text-gray-600">
                Authenticate with your existing tools using secure OAuth connections. 
                We never store your passwords.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-white text-xl font-bold">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Sync Your Data</h3>
              <p className="text-gray-600">
                NeuroSync automatically imports and synchronizes your data, 
                maintaining relationships and context.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-white text-xl font-bold">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Search & Discover</h3>
              <p className="text-gray-600">
                Use AI-powered search to find information across all your 
                connected tools from one unified interface.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Integrations */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Need a Custom Integration?
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Enterprise customers can request custom integrations for their specific tools and workflows. 
              Our team will work with you to build exactly what you need.
            </p>
            
            <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center gap-8">
                  <div className="text-center">
                    <CloudIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm font-medium">API Integrations</p>
                  </div>
                  <div className="text-center">
                    <DatabaseIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm font-medium">Database Connectors</p>
                  </div>
                  <div className="text-center">
                    <ZapIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm font-medium">Webhook Support</p>
                  </div>
                </div>
                
                <div className="mt-6">
                  <Button size="lg" asChild>
                    <Link href="/contact">Request Custom Integration</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to connect your tools?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Start building your unified knowledge base today. Connect all your tools 
            and unlock the power of AI-driven insights.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/demo">See Integrations Demo</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
