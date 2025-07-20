import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { 
  ShieldIcon,
  LockIcon,
  KeyIcon,
  EyeIcon,
  ServerIcon,
  AwardIcon,
  CheckCircleIcon,
  AlertTriangleIcon
} from 'lucide-react'

const securityFeatures = [
  {
    icon: LockIcon,
    title: 'End-to-End Encryption',
    description: 'All data is encrypted in transit and at rest using AES-256 encryption',
    status: 'Implemented'
  },
  {
    icon: KeyIcon,
    title: 'Multi-Factor Authentication',
    description: 'Secure your account with TOTP, SMS, or hardware security keys',
    status: 'Available'
  },
  {
    icon: EyeIcon,
    title: 'Zero-Knowledge Architecture',
    description: 'We cannot access your encrypted data even if we wanted to',
    status: 'By Design'
  },
  {
    icon: ServerIcon,
    title: 'Infrastructure Security',
    description: 'Hosted on SOC2 compliant cloud infrastructure with regular audits',
    status: 'Certified'
  }
]

const compliance = [
  {
    name: 'SOC2 Type II',
    description: 'Annual security audits by independent third parties',
    status: 'Certified',
    icon: AwardIcon
  },
  {
    name: 'GDPR Compliant',
    description: 'Full compliance with European data protection regulations',
    status: 'Compliant',
    icon: CheckCircleIcon
  },
  {
    name: 'CCPA Compliant',
    description: 'California Consumer Privacy Act compliance',
    status: 'Compliant',
    icon: CheckCircleIcon
  },
  {
    name: 'ISO 27001',
    description: 'Information security management system certification',
    status: 'In Progress',
    icon: AlertTriangleIcon
  }
]

const securityPractices = [
  'Regular security audits and penetration testing',
  'Employee background checks and security training',
  'Secure development lifecycle (SDLC) practices',
  'Incident response and disaster recovery plans',
  'Regular security updates and patch management',
  'Access controls and principle of least privilege',
  'Continuous monitoring and threat detection',
  'Data backup and recovery procedures'
]

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Security & Compliance
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Your data is
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> secure</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            NeuroSync is built with security at its core. We implement enterprise-grade 
            security measures to protect your sensitive code and data.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/contact">Security Inquiry</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs/security">Security Docs</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Security Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Enterprise-Grade Security
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Every aspect of NeuroSync is designed with security in mind, from architecture to implementation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
            {securityFeatures.map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
                        <IconComponent className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-xl">{feature.title}</CardTitle>
                        <Badge variant="outline" className="text-green-600 border-green-200">
                          {feature.status}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Compliance & Certifications
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We maintain the highest standards of compliance with industry regulations and best practices.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {compliance.map((item, index) => {
              const IconComponent = item.icon
              const getStatusColor = (status: string) => {
                switch (status) {
                  case 'Certified':
                  case 'Compliant':
                    return 'text-green-600 bg-green-100'
                  case 'In Progress':
                    return 'text-orange-600 bg-orange-100'
                  default:
                    return 'text-gray-600 bg-gray-100'
                }
              }

              return (
                <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-lg">{item.name}</CardTitle>
                    <Badge className={getStatusColor(item.status)}>
                      {item.status}
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">{item.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Security Practices */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Our Security Practices
              </h2>
              <p className="text-xl text-gray-600">
                Comprehensive security measures across all aspects of our operations.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {securityPractices.map((practice, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircleIcon className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-gray-700">{practice}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Data Protection */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                How We Protect Your Data
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="text-center">
                <CardHeader>
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <LockIcon className="h-8 w-8 text-white" />
                  </div>
                  <CardTitle>Encryption Everywhere</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    All data is encrypted using AES-256 encryption both in transit (TLS 1.3) 
                    and at rest. Encryption keys are managed using industry-standard HSMs.
                  </p>
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ShieldIcon className="h-8 w-8 text-white" />
                  </div>
                  <CardTitle>Access Controls</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Role-based access controls ensure only authorized personnel can access 
                    systems. All access is logged and monitored in real-time.
                  </p>
                </CardContent>
              </Card>

              <Card className="text-center">
                <CardHeader>
                  <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ServerIcon className="h-8 w-8 text-white" />
                  </div>
                  <CardTitle>Secure Infrastructure</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Hosted on SOC2 compliant cloud infrastructure with network isolation, 
                    DDoS protection, and continuous security monitoring.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Security Team */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Dedicated Security Team
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Our security team includes former security engineers from Google, Microsoft, and other 
              leading tech companies. We're committed to maintaining the highest security standards.
            </p>
            
            <div className="bg-blue-50 rounded-lg p-8 mb-8">
              <h3 className="text-xl font-semibold text-blue-900 mb-4">
                Security Incident Response
              </h3>
              <p className="text-blue-800 mb-4">
                We have a 24/7 security incident response team ready to handle any security concerns. 
                Our average response time for critical security issues is under 1 hour.
              </p>
              <Button variant="outline" asChild>
                <Link href="/contact">Report Security Issue</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Transparency */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Transparency & Trust
              </h2>
              <p className="text-xl text-gray-600">
                We believe in complete transparency about our security practices.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Security Audits</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    We undergo regular third-party security audits and penetration testing. 
                    Our latest SOC2 Type II report is available upon request.
                  </p>
                  <Button variant="outline" size="sm">
                    Request Audit Report
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Bug Bounty Program</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    We run a responsible disclosure program and reward security researchers 
                    who help us identify and fix security vulnerabilities.
                  </p>
                  <Button variant="outline" size="sm">
                    Learn More
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
            Questions about our security?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Our security team is happy to answer any questions about our practices, 
            compliance, or specific security requirements.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/contact">Contact Security Team</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/docs/security">View Security Docs</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
