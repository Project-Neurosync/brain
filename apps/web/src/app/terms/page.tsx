import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ScaleIcon,
  ShieldIcon,
  FileTextIcon,
  AlertTriangleIcon
} from 'lucide-react'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Legal
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Terms of
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> Service</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Last updated: December 2024
          </p>
        </div>
      </section>

      {/* Terms Content */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            {/* Quick Overview */}
            <Card className="mb-12">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileTextIcon className="h-5 w-5" />
                  Quick Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  These Terms of Service ("Terms") govern your use of NeuroSync's services. By using our platform, you agree to these terms. Here are the key points:
                </p>
                <ul className="space-y-2 text-gray-600">
                  <li>• You must be 18+ to use our services</li>
                  <li>• You're responsible for your account security</li>
                  <li>• We respect your data and privacy</li>
                  <li>• Usage must comply with applicable laws</li>
                  <li>• We may update these terms with notice</li>
                </ul>
              </CardContent>
            </Card>

            <div className="prose prose-lg max-w-none">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-600 mb-6">
                By accessing and using NeuroSync ("Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
              <p className="text-gray-600 mb-6">
                NeuroSync is an AI-powered knowledge transfer platform that helps development teams share context, onboard new members, and maintain institutional knowledge. The service includes web applications, APIs, integrations, and related features.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">When you create an account with us, you must provide information that is accurate, complete, and current at all times. You are responsible for:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Safeguarding your password and account credentials</li>
                  <li>All activities that occur under your account</li>
                  <li>Notifying us immediately of any unauthorized use</li>
                  <li>Ensuring your team members comply with these terms</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Acceptable Use</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">You agree not to use the Service to:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Violate any applicable laws or regulations</li>
                  <li>Infringe on intellectual property rights</li>
                  <li>Upload malicious code or harmful content</li>
                  <li>Attempt to gain unauthorized access to our systems</li>
                  <li>Use the service for competitive analysis or reverse engineering</li>
                  <li>Exceed usage limits or abuse our resources</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data and Privacy</h2>
              <p className="text-gray-600 mb-6">
                Your privacy is important to us. Our Privacy Policy explains how we collect, use, and protect your information. By using our service, you consent to the collection and use of information in accordance with our Privacy Policy.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Intellectual Property</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">The Service and its original content, features, and functionality are and will remain the exclusive property of NeuroSync and its licensors. You retain ownership of your data and content, but grant us necessary rights to provide the service.</p>
                <p>You grant us a non-exclusive, worldwide, royalty-free license to use, reproduce, and display your content solely for the purpose of providing the service.</p>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Payment Terms</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">For paid services:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Fees are charged in advance on a monthly or annual basis</li>
                  <li>All fees are non-refundable except as required by law</li>
                  <li>We may change pricing with 30 days notice</li>
                  <li>Failure to pay may result in service suspension</li>
                  <li>You're responsible for all taxes and fees</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Service Availability</h2>
              <p className="text-gray-600 mb-6">
                We strive to maintain high availability but cannot guarantee uninterrupted service. We may temporarily suspend service for maintenance, updates, or due to circumstances beyond our control. We are not liable for any downtime or service interruptions.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Limitation of Liability</h2>
              <p className="text-gray-600 mb-6">
                In no event shall NeuroSync, its directors, employees, partners, agents, suppliers, or affiliates be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from your use of the service.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Termination</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">We may terminate or suspend your account and access to the service immediately, without prior notice or liability, for any reason, including:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Breach of these Terms</li>
                  <li>Non-payment of fees</li>
                  <li>Violation of acceptable use policies</li>
                  <li>At our sole discretion</li>
                </ul>
                <p className="mt-4">Upon termination, your right to use the service will cease immediately.</p>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Changes to Terms</h2>
              <p className="text-gray-600 mb-6">
                We reserve the right to modify or replace these Terms at any time. If a revision is material, we will provide at least 30 days notice prior to any new terms taking effect. Your continued use of the service after changes constitutes acceptance of the new terms.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Governing Law</h2>
              <p className="text-gray-600 mb-6">
                These Terms shall be interpreted and governed by the laws of the State of California, United States, without regard to conflict of law provisions. Any disputes shall be resolved in the courts of California.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Contact Information</h2>
              <p className="text-gray-600 mb-6">
                If you have any questions about these Terms, please contact us at:
                <br />
                Email: legal@neurosync.ai
                <br />
                Address: 123 Market Street, Suite 456, San Francisco, CA 94105
              </p>
            </div>

            {/* Important Notice */}
            <Card className="mt-12 border-orange-200 bg-orange-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-800">
                  <AlertTriangleIcon className="h-5 w-5" />
                  Important Notice
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-orange-700">
                  These terms are legally binding. If you don't agree with any part of these terms, 
                  you should not use our service. For questions about these terms, please contact our legal team.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
