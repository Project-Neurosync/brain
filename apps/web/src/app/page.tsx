'use client'

import { motion } from 'framer-motion'
import { 
  Brain, 
  Code, 
  Search, 
  Users, 
  Zap, 
  ArrowRight, 
  CheckCircle,
  Star,
  Github,
  MessageSquare,
  FileText,
  BarChart3,
  Check
} from 'lucide-react'
import Link from 'next/link'
import { useState } from 'react'

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 }
}

const slideInLeft = {
  initial: { opacity: 0, x: -50 },
  animate: { opacity: 1, x: 0 }
}

const slideInRight = {
  initial: { opacity: 0, x: 50 },
  animate: { opacity: 1, x: 0 }
}

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}

const scaleIn = {
  initial: { opacity: 0, scale: 0.8 },
  animate: { opacity: 1, scale: 1 }
}

export default function HomePage() {
  const [email, setEmail] = useState('')

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Intelligence',
      description: 'Context-aware responses using GPT-4 that understand your entire project ecosystem.'
    },
    {
      icon: Search,
      title: 'Semantic Search',
      description: 'Find exactly what you need across all your project data with intelligent search.'
    },
    {
      icon: Code,
      title: 'Multi-Source Integration',
      description: 'Connect GitHub, Jira, Slack, Confluence, and more in one unified knowledge hub.'
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description: 'Seamless knowledge sharing that keeps your entire team in sync.'
    },
    {
      icon: Zap,
      title: 'Real-time Updates',
      description: 'Always up-to-date information that evolves with your project.'
    },
    {
      icon: BarChart3,
      title: 'Smart Analytics',
      description: 'Insights into team knowledge patterns and project understanding.'
    }
  ]

  const personas = [
    {
      title: 'For Developers',
      subtitle: 'Effortless Knowledge Transfer',
      description: 'AI-powered onboarding and project context with search functionality',
      icon: Code,
      gradient: 'from-primary-500 to-secondary-500'
    },
    {
      title: 'For Researchers',
      subtitle: 'Unified Research Hub',
      description: 'All findings always accessible in one intelligent workspace',
      icon: FileText,
      gradient: 'from-secondary-500 to-accent-500'
    },
    {
      title: 'For Teams',
      subtitle: 'Your AI Writing Partner',
      description: 'Draft, organize, never lose an idea with collaborative intelligence',
      icon: Users,
      gradient: 'from-accent-500 to-primary-500'
    }
  ]

  const benefits = [
    'No more endless KT calls and meetings',
    'No outdated Confluence pages',
    'No information locked in someone\'s head',
    'Context stays with project forever',
    'All repos, Jira updates, and chats synced',
    'Simple, secure, always up to date'
  ]

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="relative z-50 bg-black/60 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.div 
              className="flex items-center space-x-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <img 
                src="/images/cerebryx.svg" 
                alt="Cerebryx Logo" 
                className="h-12 w-auto"
              />

            </motion.div>

            <motion.div 
              className="hidden md:flex items-center space-x-8"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Link href="#features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </Link>
              <Link href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="/docs" className="text-gray-300 hover:text-white transition-colors">
                Docs
              </Link>
              <Link href="/login" className="btn-secondary">
                Sign In
              </Link>
              <Link href="/signup" className="btn-primary">
                Get Started
              </Link>
            </motion.div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-black via-gray-950 to-gray-900">
        <div className="absolute inset-0 bg-gradient-mesh opacity-5"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <motion.div 
            className="text-center"
            variants={staggerContainer}
            initial="initial"
            animate="animate"
          >
            <motion.div
              variants={fadeInUp}
              className="mb-8"
            >
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-primary-900/30 text-primary-200 mb-6">
                <Star className="w-4 h-4 mr-2" />
                Your Project's Second Brain
              </span>
            </motion.div>

            <motion.h1 
              variants={fadeInUp}
              className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-100 mb-6"
            >
              AI-Powered{' '}
              <span className="text-gradient-primary">
                Knowledge Transfer
              </span>
            </motion.h1>

            <motion.p 
              variants={fadeInUp}
              className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed"
            >
              If you're onboarding new devs, handing off projects, or managing big codebases — 
              <span className="font-semibold text-white"> Cerebryx is your project's second brain</span>
            </motion.p>

            <motion.div 
              variants={fadeInUp}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
            >
              <Link href="/signup" className="btn-primary btn-lg group">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link href="/demo" className="btn-secondary btn-lg">
                Watch Demo
              </Link>
            </motion.div>

            <motion.div 
              variants={fadeInUp}
              className="text-sm text-gray-400"
            >
              ✨ No credit card required • 14-day free trial • Setup in 5 minutes
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Personas Section */}
      <section className="py-24 bg-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-4">
              For Visual Minds of All Kinds
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Whether you're a developer, researcher, or team lead, NeuroSync adapts to your workflow
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {personas.map((persona, index) => (
              <motion.div
                key={persona.title}
                className="card-hover p-8 text-center"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className={`w-16 h-16 bg-gradient-to-r ${persona.gradient} rounded-2xl flex items-center justify-center mx-auto mb-6`}>
                  <persona.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-100 mb-2">{persona.title}</h3>
                <h4 className="text-lg font-medium text-primary-400 mb-3">{persona.subtitle}</h4>
                <p className="text-gray-300">{persona.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-6">
                Why Cerebryx?
              </h2>
              <p className="text-xl text-gray-300 mb-8">
                Context never gets lost. Every decision, update, and discussion always accessible.
              </p>
              
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={benefit}
                    className="flex items-center space-x-3"
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" />
                    <span className="text-gray-300">{benefit}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              className="relative"
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="bg-gray-950 rounded-2xl shadow-xl p-8 border border-gray-800">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-100">All repos, Jira updates, and chats</h3>
                    <p className="text-gray-400 text-sm">synced in one living AI knowledge hub</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center space-x-3 p-3 bg-gray-900 rounded-lg">
                    <Github className="w-5 h-5 text-gray-300" />
                    <span className="text-sm text-gray-300">GitHub repositories synced</span>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-gray-900 rounded-lg">
                    <FileText className="w-5 h-5 text-gray-300" />
                    <span className="text-sm text-gray-300">Jira tickets integrated</span>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-gray-900 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-gray-300" />
                    <span className="text-sm text-gray-300">Slack conversations indexed</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 bg-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-4">
              Pricing
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Simple, transparent pricing for teams of all sizes
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Starter Tier */}
            <motion.div
              className="pricing-card relative card"
              variants={fadeInUp}
            >
              <div className="absolute -top-4 left-6">
                <div className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </div>
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Starter</h3>
                <p className="text-gray-400 mb-6">Perfect for small teams</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-100">$19</span>
                  <span className="text-gray-400">/user/month</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">3 projects per user</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">5 users max per project</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">200 AI tokens per user</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">Basic integrations</span>
                  </li>
                </ul>
                <button className="btn-primary w-full">
                  Start Free Trial
                </button>
              </div>
            </motion.div>

            {/* Professional Tier */}
            <motion.div
              className="pricing-card relative border-2 border-primary-500 bg-gray-950 rounded-2xl"
              variants={fadeInUp}
            >
              <div className="absolute -top-4 left-6">
                <div className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Popular
                </div>
              </div>
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Professional</h3>
                <p className="text-gray-400 mb-6">Best for growing teams</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-100">$29</span>
                  <span className="text-gray-400">/user/month</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">5 projects per user</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">15 users max per project</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">400 AI tokens per user</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">Advanced integrations</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">Priority support</span>
                  </li>
                </ul>
                <button className="btn-primary w-full">
                  Start Free Trial
                </button>
              </div>
            </motion.div>

            {/* Enterprise Tier */}
            <motion.div
              className="pricing-card relative card"
              variants={fadeInUp}
            >
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Enterprise</h3>
                <p className="text-gray-400 mb-6">For large organizations</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-100">$49</span>
                  <span className="text-gray-400">/user/month</span>
                </div>
                <ul className="space-y-4 mb-8">
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">Unlimited projects</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">50 users max per project</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">800 AI tokens per user</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">All integrations</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-5 w-5 text-green-500 mr-3" />
                    <span className="text-gray-300">Dedicated support</span>
                  </li>
                </ul>
                <button className="btn-primary w-full">
                  Contact Sales
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Everything you need to transform how your team shares and discovers knowledge
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="card p-6"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-100 mb-2">{feature.title}</h3>
                <p className="text-gray-300">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-primary-600 to-secondary-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Team's Knowledge?
            </h2>
            <p className="text-xl text-primary-100 mb-8">
              Join thousands of developers who've made knowledge transfer effortless
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link href="/signup" className="btn-lg bg-white text-primary-600 hover:bg-gray-50 shadow-lg">
                Start Free Trial
              </Link>
              <Link href="/contact" className="btn-lg border-2 border-white text-white hover:bg-white hover:text-primary-600">
                Contact Sales
              </Link>
            </div>
            
            <p className="text-primary-200 text-sm mt-6">
              14-day free trial • No credit card required • Cancel anytime
            </p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">NeuroSync</span>
              </div>
              <p className="text-gray-400 mb-4">
                AI-powered developer knowledge transfer platform
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-4">Product</h3>
              <ul className="space-y-2">
                <li><Link href="/features" className="hover:text-white transition-colors">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link href="/integrations" className="hover:text-white transition-colors">Integrations</Link></li>
                <li><Link href="/security" className="hover:text-white transition-colors">Security</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-4">Company</h3>
              <ul className="space-y-2">
                <li><Link href="/about" className="hover:text-white transition-colors">About</Link></li>
                <li><Link href="/blog" className="hover:text-white transition-colors">Blog</Link></li>
                <li><Link href="/careers" className="hover:text-white transition-colors">Careers</Link></li>
                <li><Link href="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-white mb-4">Support</h3>
              <ul className="space-y-2">
                <li><Link href="/docs" className="hover:text-white transition-colors">Documentation</Link></li>
                <li><Link href="/help" className="hover:text-white transition-colors">Help Center</Link></li>
                <li><Link href="/status" className="hover:text-white transition-colors">Status</Link></li>
                <li><Link href="/api" className="hover:text-white transition-colors">API</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400">
              2024 NeuroSync. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">Privacy</Link>
              <Link href="/terms" className="text-gray-400 hover:text-white transition-colors">Terms</Link>
              <Link href="/cookies" className="text-gray-400 hover:text-white transition-colors">Cookies</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
