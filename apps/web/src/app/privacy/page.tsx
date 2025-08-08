import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ShieldIcon,
  LockIcon,
  EyeIcon,
  DatabaseIcon,
  UserIcon,
  AlertTriangleIcon
} from 'lucide-react'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Privacy & Security
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Privacy
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> Policy</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Your privacy is fundamental to our mission. Learn how we protect and handle your data.
          </p>
          <p className="text-lg text-gray-500">
            Last updated: December 2024
          </p>
        </div>
      </section>

      {/* Privacy Principles */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Our Privacy Principles
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              These principles guide every decision we make about your data.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <LockIcon className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Data Minimization</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  We only collect data that's necessary to provide our service and improve your experience.
                </p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <ShieldIcon className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Strong Security</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Enterprise-grade encryption and security measures protect your data at all times.
                </p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <EyeIcon className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Full Transparency</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  You always know what data we have, how we use it, and can control your preferences.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Privacy Policy Content */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="prose prose-lg max-w-none">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Information We Collect</h2>
              
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Account Information</h3>
              <p className="text-gray-600 mb-4">
                When you create an account, we collect your name, email address, and company information. 
                This helps us provide personalized service and communicate with you about your account.
              </p>

              <h3 className="text-xl font-semibold text-gray-900 mb-3">Usage Data</h3>
              <p className="text-gray-600 mb-4">
                We collect information about how you use NeuroSync, including features accessed, 
                queries made, and performance metrics. This helps us improve our service and provide better AI responses.
              </p>

              <h3 className="text-xl font-semibold text-gray-900 mb-3">Content Data</h3>
              <p className="text-gray-600 mb-6">
                To provide our AI-powered features, we process the content you upload, including code, 
                documentation, and chat messages. This data is used solely to provide our service to you.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. How We Use Your Information</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">We use your information to:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Provide and maintain our service</li>
                  <li>Process AI queries and provide intelligent responses</li>
                  <li>Communicate with you about your account and our service</li>
                  <li>Improve our algorithms and service quality</li>
                  <li>Ensure security and prevent fraud</li>
                  <li>Comply with legal obligations</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Data Sharing and Disclosure</h2>
              <p className="text-gray-600 mb-4">
                We do not sell, trade, or rent your personal information to third parties. We may share your information only in these limited circumstances:
              </p>
              <div className="text-gray-600 mb-6">
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Service Providers:</strong> Trusted partners who help us operate our service (e.g., cloud hosting, analytics)</li>
                  <li><strong>Legal Requirements:</strong> When required by law or to protect our rights and users</li>
                  <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                  <li><strong>With Your Consent:</strong> When you explicitly agree to share information</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Data Security</h2>
              <p className="text-gray-600 mb-4">
                We implement industry-standard security measures to protect your data:
              </p>
              <div className="text-gray-600 mb-6">
                <ul className="list-disc pl-6 space-y-2">
                  <li>Encryption in transit and at rest using AES-256</li>
                  <li>Regular security audits and penetration testing</li>
                  <li>Access controls and authentication mechanisms</li>
                  <li>SOC2 Type II compliance</li>
                  <li>Employee security training and background checks</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data Retention</h2>
              <p className="text-gray-600 mb-6">
                We retain your data only as long as necessary to provide our service and comply with legal obligations. 
                Account data is retained while your account is active. Content data may be retained for up to 90 days 
                after deletion to enable recovery. You can request immediate deletion of your data at any time.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Your Rights and Choices</h2>
              <div className="text-gray-600 mb-6">
                <p className="mb-4">You have the right to:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Access:</strong> Request a copy of your personal data</li>
                  <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
                  <li><strong>Erasure:</strong> Request deletion of your personal data</li>
                  <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
                  <li><strong>Restriction:</strong> Limit how we process your data</li>
                  <li><strong>Objection:</strong> Object to certain types of processing</li>
                </ul>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. International Data Transfers</h2>
              <p className="text-gray-600 mb-6">
                NeuroSync is based in the United States. If you're accessing our service from outside the US, 
                your data may be transferred to and processed in the US. We ensure appropriate safeguards are in place 
                for international transfers, including standard contractual clauses and adequacy decisions.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Children's Privacy</h2>
              <p className="text-gray-600 mb-6">
                Our service is not intended for children under 13. We do not knowingly collect personal information 
                from children under 13. If we become aware that we have collected such information, we will delete it promptly.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Changes to This Policy</h2>
              <p className="text-gray-600 mb-6">
                We may update this Privacy Policy from time to time. We will notify you of any material changes by 
                posting the new policy on our website and sending you an email notification. Your continued use of 
                our service after changes constitutes acceptance of the updated policy.
              </p>

              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Contact Us</h2>
              <p className="text-gray-600 mb-6">
                If you have questions about this Privacy Policy or our data practices, please contact us:
                <br />
                Email: privacy@neurosync.ai
                <br />
                Address: 123 Market Street, Suite 456, San Francisco, CA 94105
                <br />
                Data Protection Officer: dpo@neurosync.ai
              </p>
            </div>

            {/* Data Processing Notice */}
            <Card className="mt-12 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-800">
                  <DatabaseIcon className="h-5 w-5" />
                  AI Data Processing
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-blue-700 mb-4">
                  <strong>Important:</strong> Our AI features require processing your content to provide intelligent responses. 
                  This processing happens in secure, encrypted environments and your data is never used to train public AI models.
                </p>
                <p className="text-blue-700">
                  You can control AI processing in your account settings and opt out at any time.
                </p>
              </CardContent>
            </Card>

            {/* GDPR Notice */}
            <Card className="mt-6 border-purple-200 bg-purple-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-800">
                  <UserIcon className="h-5 w-5" />
                  GDPR & CCPA Compliance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-purple-700">
                  We comply with GDPR, CCPA, and other privacy regulations. EU and California residents have additional 
                  rights regarding their personal data. Contact us at privacy@neurosync.ai to exercise these rights.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}
