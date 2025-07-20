import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { 
  CheckIcon, 
  XIcon,
  StarIcon,
  UsersIcon,
  ZapIcon,
  ShieldIcon
} from 'lucide-react'

const plans = [
  {
    name: 'Starter',
    price: '$19',
    period: 'per user/month',
    description: 'Perfect for small teams getting started',
    popular: false,
    features: [
      '5 team members',
      '3 projects',
      '10,000 AI tokens/month',
      'Basic integrations (GitHub, Slack)',
      'Standard support',
      'Basic search',
      '1GB storage'
    ],
    notIncluded: [
      'Advanced AI models',
      'Custom integrations',
      'Priority support',
      'Advanced analytics'
    ]
  },
  {
    name: 'Professional',
    price: '$29',
    period: 'per user/month',
    description: 'For growing teams with advanced needs',
    popular: true,
    features: [
      '15 team members',
      '10 projects',
      '50,000 AI tokens/month',
      'All integrations (GitHub, Jira, Slack)',
      'Priority support',
      'Advanced search & analytics',
      '10GB storage',
      'Custom workflows',
      'API access'
    ],
    notIncluded: [
      'Custom integrations',
      'Dedicated support',
      'On-premise deployment'
    ]
  },
  {
    name: 'Enterprise',
    price: '$49',
    period: 'per user/month',
    description: 'For large organizations with custom requirements',
    popular: false,
    features: [
      'Unlimited team members',
      'Unlimited projects',
      '200,000 AI tokens/month',
      'All integrations + custom',
      'Dedicated support',
      'Advanced analytics & reporting',
      '100GB storage',
      'Custom workflows & automations',
      'Full API access',
      'SSO & advanced security',
      'On-premise deployment option',
      'Custom training'
    ],
    notIncluded: []
  }
]

const tokenPacks = [
  {
    name: 'Small Pack',
    tokens: '10,000',
    price: '$12',
    description: 'Extra tokens for light usage'
  },
  {
    name: 'Medium Pack',
    tokens: '50,000',
    price: '$47',
    description: 'Perfect for regular AI interactions'
  },
  {
    name: 'Large Pack',
    tokens: '150,000',
    price: '$127',
    description: 'For heavy AI usage and large teams'
  },
  {
    name: 'Enterprise Pack',
    tokens: '500,000',
    price: '$397',
    description: 'Maximum tokens for enterprise workflows'
  }
]

const faqs = [
  {
    question: 'How do AI tokens work?',
    answer: 'AI tokens are consumed when you interact with our AI features like chat, search, and code analysis. Each plan includes a monthly token allocation, and you can purchase additional token packs as needed.'
  },
  {
    question: 'Can I change plans anytime?',
    answer: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and we\'ll prorate any billing adjustments.'
  },
  {
    question: 'What integrations are included?',
    answer: 'Starter includes GitHub and Slack. Professional adds Jira and other popular tools. Enterprise includes all integrations plus custom options.'
  },
  {
    question: 'Is there a free trial?',
    answer: 'Yes! We offer a 14-day free trial with full access to Professional features. No credit card required.'
  },
  {
    question: 'What about data security?',
    answer: 'All plans include enterprise-grade security with encryption at rest and in transit. Enterprise plans add SSO, advanced access controls, and compliance features.'
  }
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Simple, Transparent Pricing
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Choose the perfect plan for
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> your team</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Start with our free trial, then choose a plan that scales with your team. 
            All plans include our core AI features and integrations.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/contact">Contact Sales</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Pricing Plans */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Subscription Plans
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              All plans include our core features. Choose based on team size and usage needs.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {plans.map((plan, index) => (
              <Card key={index} className={`relative ${plan.popular ? 'border-purple-500 shadow-lg scale-105' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-purple-600 text-white px-4 py-1">
                      <StarIcon className="h-3 w-3 mr-1" />
                      Most Popular
                    </Badge>
                  </div>
                )}
                
                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600 ml-2">{plan.period}</span>
                  </div>
                  <CardDescription className="text-base mt-2">
                    {plan.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-6">
                  <div className="space-y-3">
                    {plan.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center">
                        <CheckIcon className="h-4 w-4 text-green-500 mr-3 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                    {plan.notIncluded.map((feature, idx) => (
                      <div key={idx} className="flex items-center opacity-50">
                        <XIcon className="h-4 w-4 text-gray-400 mr-3 flex-shrink-0" />
                        <span className="text-sm text-gray-500">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <Button 
                    className={`w-full ${plan.popular ? 'bg-purple-600 hover:bg-purple-700' : ''}`}
                    variant={plan.popular ? 'default' : 'outline'}
                    asChild
                  >
                    <Link href="/signup">
                      {plan.name === 'Enterprise' ? 'Contact Sales' : 'Start Free Trial'}
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Token Packs */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Token Add-ons
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Need more AI interactions? Purchase additional token packs for any plan.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {tokenPacks.map((pack, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <ZapIcon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl">{pack.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold text-gray-900">{pack.price}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-semibold text-purple-600 mb-2">
                    {pack.tokens} tokens
                  </p>
                  <p className="text-sm text-gray-600 mb-4">
                    {pack.description}
                  </p>
                  <Button variant="outline" className="w-full">
                    Purchase
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Comparison */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose NeuroSync?
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <UsersIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Team-First Design</h3>
              <p className="text-gray-600">
                Built for collaboration with role-based access, team workspaces, and seamless knowledge sharing.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <ZapIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI-Powered Intelligence</h3>
              <p className="text-gray-600">
                Advanced AI that understands your codebase, learns from your patterns, and provides contextual insights.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShieldIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
              <p className="text-gray-600">
                SOC2 compliant with enterprise-grade security, encryption, and compliance features.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="max-w-3xl mx-auto space-y-6">
            {faqs.map((faq, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{faq.question}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
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
            Join thousands of teams using NeuroSync to accelerate knowledge transfer and onboarding.
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
