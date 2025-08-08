import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { 
  BrainIcon, 
  UsersIcon, 
  TargetIcon,
  RocketIcon,
  HeartIcon,
  TrendingUpIcon,
  GlobeIcon,
  AwardIcon
} from 'lucide-react'

const values = [
  {
    icon: BrainIcon,
    title: 'Innovation First',
    description: 'We push the boundaries of AI and knowledge management to solve real problems for development teams.'
  },
  {
    icon: UsersIcon,
    title: 'Team-Centric',
    description: 'Every feature is designed with team collaboration and knowledge sharing at its core.'
  },
  {
    icon: HeartIcon,
    title: 'Developer Love',
    description: 'Built by developers, for developers. We understand the pain points and craft solutions that actually work.'
  },
  {
    icon: TrendingUpIcon,
    title: 'Continuous Growth',
    description: 'We\'re constantly learning, iterating, and improving based on user feedback and emerging technologies.'
  }
]

const stats = [
  {
    number: '10,000+',
    label: 'Active Users',
    description: 'Developers and teams worldwide'
  },
  {
    number: '500+',
    label: 'Companies',
    description: 'From startups to enterprises'
  },
  {
    number: '1M+',
    label: 'AI Queries',
    description: 'Processed monthly'
  },
  {
    number: '99.9%',
    label: 'Uptime',
    description: 'Reliable service guarantee'
  }
]

const team = [
  {
    name: 'Alex Chen',
    role: 'CEO & Co-founder',
    bio: 'Former engineering lead at Google. Passionate about AI and developer productivity.',
    image: 'AC'
  },
  {
    name: 'Sarah Johnson',
    role: 'CTO & Co-founder',
    bio: 'AI researcher with 10+ years in machine learning and natural language processing.',
    image: 'SJ'
  },
  {
    name: 'Mike Rodriguez',
    role: 'Head of Product',
    bio: 'Product leader focused on developer experience and team collaboration tools.',
    image: 'MR'
  },
  {
    name: 'Emily Zhang',
    role: 'Head of Engineering',
    bio: 'Full-stack engineer passionate about building scalable, reliable systems.',
    image: 'EZ'
  }
]

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            About NeuroSync
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            We're building the future of
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> knowledge transfer</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            NeuroSync was born from the frustration of endless knowledge transfer meetings, 
            outdated documentation, and the constant struggle to onboard new team members effectively.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/careers">Join Our Team</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/contact">Get in Touch</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">
              Our Mission
            </h2>
            <p className="text-xl text-gray-600 mb-12 leading-relaxed">
              To eliminate the friction in knowledge transfer and make every team member productive from day one. 
              We believe that knowledge should flow freely within organizations, enabling faster innovation, 
              better collaboration, and more successful projects.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
              <Card className="border-l-4 border-l-purple-500">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <TargetIcon className="h-6 w-6 text-purple-600" />
                    <CardTitle>The Problem</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Development teams waste countless hours in knowledge transfer meetings, 
                    struggle with outdated documentation, and face steep learning curves when 
                    joining new projects. Critical knowledge often lives in someone's head, 
                    creating bottlenecks and single points of failure.
                  </p>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <RocketIcon className="h-6 w-6 text-blue-600" />
                    <CardTitle>Our Solution</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    NeuroSync creates a living, intelligent knowledge base that learns from your 
                    codebase, documentation, and team conversations. It provides instant, contextual 
                    answers and enables seamless knowledge transfer without the traditional overhead.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Our Values
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The principles that guide everything we do at NeuroSync.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {values.map((value, index) => {
              const IconComponent = value.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mb-4">
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-xl">{value.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-600">{value.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Growing with Our Community
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We're proud to serve thousands of developers and teams worldwide.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-purple-600 mb-2">
                  {stat.number}
                </div>
                <div className="text-xl font-semibold text-gray-900 mb-1">
                  {stat.label}
                </div>
                <div className="text-gray-600">
                  {stat.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Meet Our Team
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We're a passionate team of engineers, researchers, and product builders 
              dedicated to solving knowledge transfer challenges.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
            {team.map((member, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-20 h-20 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-white text-xl font-bold">{member.image}</span>
                  </div>
                  <CardTitle className="text-lg">{member.name}</CardTitle>
                  <CardDescription className="text-purple-600 font-medium">
                    {member.role}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{member.bio}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Our Story
              </h2>
            </div>
            
            <div className="prose prose-lg max-w-none text-gray-600">
              <p className="text-xl leading-relaxed mb-6">
                NeuroSync started in 2023 when our founders, Alex and Sarah, were leading engineering 
                teams at different tech companies. They both faced the same challenge: how to effectively 
                transfer knowledge between team members without spending hours in meetings or maintaining 
                outdated documentation.
              </p>
              
              <p className="text-lg leading-relaxed mb-6">
                After countless frustrating experiences with traditional knowledge management tools, 
                they realized that the solution needed to be intelligent, contextual, and seamlessly 
                integrated into existing workflows. The idea for NeuroSync was born.
              </p>
              
              <p className="text-lg leading-relaxed mb-6">
                Today, we're a team of passionate engineers and researchers working to make knowledge 
                transfer effortless for development teams worldwide. We're backed by leading investors 
                and trusted by companies from startups to Fortune 500 enterprises.
              </p>
              
              <div className="flex items-center justify-center gap-8 mt-12">
                <div className="flex items-center gap-2">
                  <GlobeIcon className="h-5 w-5 text-purple-600" />
                  <span className="text-sm font-medium">San Francisco, CA</span>
                </div>
                <div className="flex items-center gap-2">
                  <AwardIcon className="h-5 w-5 text-purple-600" />
                  <span className="text-sm font-medium">Y Combinator S23</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Want to join our mission?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            We're always looking for talented individuals who share our passion for 
            improving developer productivity and team collaboration.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/careers">View Open Positions</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/contact">Contact Us</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
