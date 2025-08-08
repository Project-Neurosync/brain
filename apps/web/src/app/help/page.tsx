'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  HelpCircleIcon, 
  SearchIcon, 
  BookOpenIcon,
  MessageSquareIcon,
  MailIcon,
  PhoneIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ExternalLinkIcon
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface FAQItem {
  question: string
  answer: string
  category: string
}

const faqData: FAQItem[] = [
  {
    question: "How do I get started with NeuroSync?",
    answer: "Getting started is easy! First, create your account and choose a subscription plan. Then, you can start creating projects, uploading documents, and asking AI-powered questions about your codebase or knowledge base.",
    category: "Getting Started"
  },
  {
    question: "What types of files can I upload?",
    answer: "NeuroSync supports various file formats including code files (.js, .py, .java, .cpp, etc.), documents (.pdf, .docx, .txt), and can integrate with GitHub repositories, Jira projects, and Slack channels.",
    category: "File Management"
  },
  {
    question: "How does the AI query system work?",
    answer: "Our AI system uses advanced language models to understand your questions and search through your uploaded content. It provides contextual answers based on your specific codebase and documentation.",
    category: "AI Features"
  },
  {
    question: "What are tokens and how are they used?",
    answer: "Tokens are units of usage for AI queries. Each question you ask consumes tokens based on the complexity and length of the query and response. Different subscription tiers include different token allowances.",
    category: "Billing"
  },
  {
    question: "Can I integrate with GitHub?",
    answer: "Yes! NeuroSync can connect to your GitHub repositories to automatically sync your code and documentation. This allows the AI to provide more accurate and up-to-date answers about your projects.",
    category: "Integrations"
  },
  {
    question: "Is my data secure?",
    answer: "Absolutely. We use enterprise-grade security measures including encryption at rest and in transit, secure authentication, and comply with industry standards to protect your data.",
    category: "Security"
  },
  {
    question: "How do I upgrade my subscription?",
    answer: "You can upgrade your subscription at any time from the Billing page in your dashboard. Changes take effect immediately, and you'll be prorated for any unused time on your current plan.",
    category: "Billing"
  },
  {
    question: "What happens if I exceed my token limit?",
    answer: "If you exceed your monthly token limit, you can purchase additional token packs or upgrade to a higher tier. Your account won't be suspended, but additional usage may incur overage charges.",
    category: "Billing"
  }
]

const categories = Array.from(new Set(faqData.map(item => item.category)))

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null)
  const [contactForm, setContactForm] = useState({
    subject: '',
    message: '',
    priority: 'medium'
  })
  const { toast } = useToast()

  const filteredFAQs = faqData.filter(item => {
    const matchesSearch = item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.answer.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const handleContactSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const response = await fetch('/api/v1/support/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include', // Include cookies for authentication
        body: JSON.stringify(contactForm)
      })

      if (!response.ok) {
        throw new Error(`Error submitting contact form: ${response.statusText}`)
      }

      toast({
        title: "Message sent!",
        description: "We'll get back to you within 24 hours.",
      })
      
      setContactForm({
        subject: '',
        message: '',
        priority: 'medium'
      })
    } catch (error) {
      console.error('Error submitting contact form:', error)
      toast({
        title: "Message failed to send",
        description: "Please try again or contact support@neurosync.ai directly.",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Help Center</h1>
        <p className="text-gray-600 mt-2">
          Find answers to your questions and get support
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpenIcon className="h-5 w-5 text-blue-600" />
              Documentation
            </CardTitle>
            <CardDescription>
              Comprehensive guides and tutorials
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              View Docs
              <ExternalLinkIcon className="h-4 w-4 ml-2" />
            </Button>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareIcon className="h-5 w-5 text-green-600" />
              Community
            </CardTitle>
            <CardDescription>
              Join our community discussions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              Join Community
              <ExternalLinkIcon className="h-4 w-4 ml-2" />
            </Button>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MailIcon className="h-5 w-5 text-purple-600" />
              Contact Support
            </CardTitle>
            <CardDescription>
              Get direct help from our team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              Contact Us
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* FAQ Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircleIcon className="h-5 w-5" />
            Frequently Asked Questions
          </CardTitle>
          <CardDescription>
            Find quick answers to common questions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search FAQs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={selectedCategory === 'All' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory('All')}
              >
                All
              </Button>
              {categories.map(category => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>

          {/* FAQ Items */}
          <div className="space-y-4">
            {filteredFAQs.map((faq, index) => (
              <div key={index} className="border rounded-lg">
                <button
                  className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50"
                  onClick={() => setExpandedFAQ(expandedFAQ === index ? null : index)}
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">
                      {faq.category}
                    </Badge>
                    <span className="font-medium">{faq.question}</span>
                  </div>
                  {expandedFAQ === index ? (
                    <ChevronDownIcon className="h-4 w-4" />
                  ) : (
                    <ChevronRightIcon className="h-4 w-4" />
                  )}
                </button>
                {expandedFAQ === index && (
                  <div className="px-4 pb-3 text-gray-600">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>

          {filteredFAQs.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No FAQs found matching your search criteria.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Contact Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Contact Support</CardTitle>
            <CardDescription>
              Can't find what you're looking for? Send us a message.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleContactSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Subject</label>
                <Input
                  value={contactForm.subject}
                  onChange={(e) => setContactForm({ ...contactForm, subject: e.target.value })}
                  placeholder="Brief description of your issue"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium">Priority</label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md"
                  value={contactForm.priority}
                  onChange={(e) => setContactForm({ ...contactForm, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Message</label>
                <Textarea
                  value={contactForm.message}
                  onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                  placeholder="Describe your issue in detail..."
                  rows={4}
                  required
                />
              </div>
              <Button type="submit" className="w-full">
                Send Message
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Other Ways to Reach Us</CardTitle>
            <CardDescription>
              Alternative contact methods
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-3">
              <MailIcon className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium">Email Support</p>
                <p className="text-sm text-gray-600">support@neurosync.ai</p>
                <p className="text-xs text-gray-500">Response within 24 hours</p>
              </div>
            </div>
            
            <Separator />
            
            <div className="flex items-center gap-3">
              <PhoneIcon className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium">Phone Support</p>
                <p className="text-sm text-gray-600">+1 (555) 123-4567</p>
                <p className="text-xs text-gray-500">Mon-Fri, 9AM-6PM PST</p>
              </div>
            </div>
            
            <Separator />
            
            <div className="flex items-center gap-3">
              <MessageSquareIcon className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium">Live Chat</p>
                <p className="text-sm text-gray-600">Available in-app</p>
                <p className="text-xs text-gray-500">Mon-Fri, 9AM-6PM PST</p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Enterprise Support</h4>
              <p className="text-sm text-blue-700">
                Enterprise customers get priority support with dedicated account management 
                and faster response times.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resources */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Resources</CardTitle>
          <CardDescription>
            Helpful links and resources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <a href="#" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
              <BookOpenIcon className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium">API Documentation</p>
                <p className="text-sm text-gray-600">Developer resources</p>
              </div>
            </a>
            <a href="#" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
              <ExternalLinkIcon className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium">Status Page</p>
                <p className="text-sm text-gray-600">System status</p>
              </div>
            </a>
            <a href="#" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
              <MessageSquareIcon className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium">Feature Requests</p>
                <p className="text-sm text-gray-600">Suggest improvements</p>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
