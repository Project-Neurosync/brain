'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { 
  PlayIcon, 
  CalendarIcon,
  ClockIcon,
  UserIcon,
  MailIcon,
  BuildingIcon,
  CheckIcon
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

const demoFeatures = [
  'AI-powered code analysis and documentation',
  'Intelligent search across your entire codebase',
  'Team knowledge sharing and onboarding',
  'Integration with GitHub, Jira, and Slack',
  'Real-time collaboration features',
  'Custom workflow automation'
]

const demoBenefits = [
  {
    title: '10x Faster Onboarding',
    description: 'New team members get up to speed in hours, not weeks'
  },
  {
    title: '90% Less KT Meetings',
    description: 'AI handles most knowledge transfer automatically'
  },
  {
    title: '50% Faster Development',
    description: 'Instant access to context and documentation'
  }
]

export default function DemoPage() {
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    teamSize: '',
    useCase: ''
  })
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Simulate form submission
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      setSubmitted(true)
      toast({
        title: "Demo scheduled!",
        description: "We'll send you a calendar invite shortly.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to schedule demo. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-white">
        <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
          <div className="container mx-auto px-4 text-center">
            <div className="max-w-2xl mx-auto">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckIcon className="h-8 w-8 text-green-600" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-6">
                Demo Scheduled Successfully!
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Thank you for your interest in NeuroSync. We'll send you a calendar invite within the next few minutes.
              </p>
              
              <div className="bg-white rounded-lg p-6 shadow-lg mb-8">
                <h3 className="text-lg font-semibold mb-4">What to Expect:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div className="flex items-start gap-3">
                    <ClockIcon className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <p className="font-medium">30-minute session</p>
                      <p className="text-sm text-gray-600">Personalized to your use case</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <PlayIcon className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <p className="font-medium">Live demonstration</p>
                      <p className="text-sm text-gray-600">See NeuroSync in action</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <UserIcon className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <p className="font-medium">Q&A session</p>
                      <p className="text-sm text-gray-600">Get all your questions answered</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <BuildingIcon className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <p className="font-medium">Custom setup</p>
                      <p className="text-sm text-gray-600">Tailored to your team's needs</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-4 justify-center">
                <Button size="lg" asChild>
                  <Link href="/signup">Start Free Trial</Link>
                </Button>
                <Button variant="outline" size="lg" asChild>
                  <Link href="/contact">Contact Sales</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Live Demo
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            See NeuroSync in
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> action</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Schedule a personalized demo and discover how NeuroSync can transform 
            your team's knowledge transfer and onboarding process.
          </p>
          
          {/* Demo Video Placeholder */}
          <div className="max-w-4xl mx-auto mb-12">
            <div className="relative bg-gray-900 rounded-lg overflow-hidden shadow-2xl">
              <div className="aspect-video flex items-center justify-center">
                <div className="text-center">
                  <div className="w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <PlayIcon className="h-10 w-10 text-white ml-1" />
                  </div>
                  <p className="text-white text-lg">Watch NeuroSync Demo</p>
                  <p className="text-gray-300 text-sm">3 minutes overview</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              What You'll See in the Demo
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our demo covers all the key features that make NeuroSync essential for development teams.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-16">
            {demoFeatures.map((feature, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <CheckIcon className="h-4 w-4 text-white" />
                </div>
                <span className="text-gray-700">{feature}</span>
              </div>
            ))}
          </div>

          {/* Benefits */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {demoBenefits.map((benefit, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-2xl text-purple-600">{benefit.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{benefit.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Request Form */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Schedule Your Demo
              </h2>
              <p className="text-xl text-gray-600">
                Get a personalized demonstration tailored to your team's needs.
              </p>
            </div>

            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarIcon className="h-5 w-5" />
                  Demo Request
                </CardTitle>
                <CardDescription>
                  Fill out this form and we'll schedule a 30-minute demo session
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Full Name *</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        required
                        placeholder="Enter your full name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">Work Email *</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                        placeholder="Enter your work email"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="company">Company *</Label>
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                        required
                        placeholder="Your company name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="role">Your Role</Label>
                      <Input
                        id="role"
                        value={formData.role}
                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                        placeholder="e.g., Engineering Manager"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="teamSize">Team Size</Label>
                      <select
                        id="teamSize"
                        value={formData.teamSize}
                        onChange={(e) => setFormData({ ...formData, teamSize: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="">Select team size</option>
                        <option value="1-5">1-5 people</option>
                        <option value="6-15">6-15 people</option>
                        <option value="16-50">16-50 people</option>
                        <option value="51-200">51-200 people</option>
                        <option value="200+">200+ people</option>
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="useCase">Primary Use Case</Label>
                      <select
                        id="useCase"
                        value={formData.useCase}
                        onChange={(e) => setFormData({ ...formData, useCase: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="">Select use case</option>
                        <option value="onboarding">Team onboarding</option>
                        <option value="knowledge-transfer">Knowledge transfer</option>
                        <option value="documentation">Documentation</option>
                        <option value="code-review">Code review</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>

                  <Button type="submit" size="lg" className="w-full" disabled={loading}>
                    {loading ? (
                      <>
                        <CalendarIcon className="h-4 w-4 mr-2 animate-pulse" />
                        Scheduling Demo...
                      </>
                    ) : (
                      <>
                        <CalendarIcon className="h-4 w-4 mr-2" />
                        Schedule Demo
                      </>
                    )}
                  </Button>
                </form>

                <div className="mt-6 text-center text-sm text-gray-600">
                  <p>
                    Prefer to start with a free trial?{' '}
                    <Link href="/signup" className="text-purple-600 hover:text-purple-700 font-medium">
                      Sign up here
                    </Link>
                  </p>
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
            Ready to see the difference?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Join hundreds of teams who have already transformed their knowledge transfer process with NeuroSync.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary">
              Schedule Demo
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600">
              Start Free Trial
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
