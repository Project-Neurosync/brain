import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { 
  BriefcaseIcon,
  MapPinIcon,
  ClockIcon,
  DollarSignIcon,
  UsersIcon,
  RocketIcon,
  HeartIcon,
  TrendingUpIcon,
  GlobeIcon,
  CodeIcon,
  PaletteIcon,
  BarChart3Icon
} from 'lucide-react'

const openPositions = [
  {
    title: 'Senior Full-Stack Engineer',
    department: 'Engineering',
    location: 'San Francisco, CA / Remote',
    type: 'Full-time',
    experience: 'Senior',
    description: 'Build the core platform that powers AI-driven knowledge transfer for development teams.',
    requirements: ['5+ years full-stack development', 'React/TypeScript', 'Node.js/Python', 'Cloud platforms'],
    salary: '$160k - $220k'
  },
  {
    title: 'AI/ML Engineer',
    department: 'Engineering',
    location: 'San Francisco, CA / Remote',
    type: 'Full-time',
    experience: 'Mid-Senior',
    description: 'Develop and optimize AI models for code analysis, natural language processing, and knowledge extraction.',
    requirements: ['3+ years ML experience', 'Python/PyTorch', 'NLP expertise', 'LLM fine-tuning'],
    salary: '$150k - $200k'
  },
  {
    title: 'Product Designer',
    department: 'Design',
    location: 'San Francisco, CA / Remote',
    type: 'Full-time',
    experience: 'Mid-Senior',
    description: 'Design intuitive experiences that make complex AI capabilities accessible to developers.',
    requirements: ['4+ years product design', 'Figma expertise', 'Developer tools experience', 'Design systems'],
    salary: '$130k - $180k'
  },
  {
    title: 'DevOps Engineer',
    department: 'Engineering',
    location: 'Remote',
    type: 'Full-time',
    experience: 'Senior',
    description: 'Scale our infrastructure to handle millions of AI queries and ensure 99.9% uptime.',
    requirements: ['5+ years DevOps', 'Kubernetes/Docker', 'AWS/GCP', 'Infrastructure as Code'],
    salary: '$140k - $190k'
  },
  {
    title: 'Customer Success Manager',
    department: 'Customer Success',
    location: 'San Francisco, CA / Remote',
    type: 'Full-time',
    experience: 'Mid-level',
    description: 'Help enterprise customers maximize value from NeuroSync and drive product adoption.',
    requirements: ['3+ years customer success', 'Technical background', 'Enterprise software', 'Strong communication'],
    salary: '$90k - $130k'
  },
  {
    title: 'Technical Writer',
    department: 'Product',
    location: 'Remote',
    type: 'Full-time',
    experience: 'Mid-level',
    description: 'Create comprehensive documentation, tutorials, and guides for developers using NeuroSync.',
    requirements: ['3+ years technical writing', 'Developer tools experience', 'API documentation', 'Content strategy'],
    salary: '$80k - $120k'
  }
]

const benefits = [
  {
    icon: DollarSignIcon,
    title: 'Competitive Compensation',
    description: 'Top-tier salaries, equity, and performance bonuses'
  },
  {
    icon: HeartIcon,
    title: 'Health & Wellness',
    description: 'Premium health, dental, vision, and mental health support'
  },
  {
    icon: ClockIcon,
    title: 'Flexible Schedule',
    description: 'Work-life balance with flexible hours and unlimited PTO'
  },
  {
    icon: GlobeIcon,
    title: 'Remote-First',
    description: 'Work from anywhere with quarterly team gatherings'
  },
  {
    icon: TrendingUpIcon,
    title: 'Growth Opportunities',
    description: 'Learning budget, conferences, and career development'
  },
  {
    icon: RocketIcon,
    title: 'Cutting-Edge Tech',
    description: 'Work with the latest AI and development technologies'
  }
]

const values = [
  {
    title: 'Innovation First',
    description: 'We push boundaries and solve hard problems with creative solutions.'
  },
  {
    title: 'Developer Empathy',
    description: 'We understand developers because we are developers.'
  },
  {
    title: 'Transparent Culture',
    description: 'Open communication, honest feedback, and shared decision-making.'
  },
  {
    title: 'Continuous Learning',
    description: 'We invest in growth and embrace new technologies and methodologies.'
  }
]

const getDepartmentIcon = (department: string) => {
  switch (department) {
    case 'Engineering': return CodeIcon
    case 'Design': return PaletteIcon
    case 'Product': return BarChart3Icon
    case 'Customer Success': return UsersIcon
    default: return BriefcaseIcon
  }
}

const getDepartmentColor = (department: string) => {
  switch (department) {
    case 'Engineering': return 'bg-blue-100 text-blue-800'
    case 'Design': return 'bg-purple-100 text-purple-800'
    case 'Product': return 'bg-green-100 text-green-800'
    case 'Customer Success': return 'bg-orange-100 text-orange-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

export default function CareersPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            Join Our Team
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Build the future of
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> knowledge transfer</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Join a passionate team of engineers, designers, and innovators working to solve 
            one of the biggest challenges in software development: effective knowledge sharing.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="#open-positions">View Open Positions</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/about">Learn About Us</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Company Values */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Our Values
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              These principles guide everything we do and shape our culture.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {values.map((value, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-xl">{value.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{value.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Work at NeuroSync?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              We offer comprehensive benefits and a culture that supports your growth and well-being.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {benefits.map((benefit, index) => {
              const IconComponent = benefit.icon
              return (
                <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-lg">{benefit.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-600">{benefit.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Open Positions */}
      <section id="open-positions" className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Open Positions
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Join our growing team and help shape the future of developer productivity.
            </p>
          </div>

          <div className="max-w-6xl mx-auto space-y-6">
            {openPositions.map((position, index) => {
              const DepartmentIcon = getDepartmentIcon(position.department)
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                            <DepartmentIcon className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <h3 className="text-xl font-semibold text-gray-900">{position.title}</h3>
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                              <Badge className={getDepartmentColor(position.department)}>
                                {position.department}
                              </Badge>
                              <div className="flex items-center gap-1">
                                <MapPinIcon className="h-3 w-3" />
                                {position.location}
                              </div>
                              <div className="flex items-center gap-1">
                                <ClockIcon className="h-3 w-3" />
                                {position.type}
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 mb-4">{position.description}</p>
                        
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-900 mb-2">Key Requirements:</h4>
                          <div className="flex flex-wrap gap-2">
                            {position.requirements.map((req, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {req}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1 text-green-600">
                            <DollarSignIcon className="h-3 w-3" />
                            <span className="font-medium">{position.salary}</span>
                          </div>
                          <Badge variant="outline" className="text-purple-600">
                            {position.experience} Level
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="lg:w-auto">
                        <Button size="lg" asChild>
                          <Link href={`/careers/${position.title.toLowerCase().replace(/\s+/g, '-')}`}>
                            Apply Now
                          </Link>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Culture */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Life at NeuroSync
            </h2>
            <p className="text-xl text-gray-600 mb-12">
              We're building more than just a product – we're creating a culture where 
              innovation thrives and everyone can do their best work.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">25+</div>
                <div className="text-gray-600">Team Members</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">12</div>
                <div className="text-gray-600">Countries</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">4.9/5</div>
                <div className="text-gray-600">Employee Satisfaction</div>
              </div>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-8">
              <h3 className="text-xl font-semibold text-blue-900 mb-4">
                Remote-First, Connection-Focused
              </h3>
              <p className="text-blue-800 mb-6">
                We believe great work happens when people have flexibility and autonomy. 
                Our team spans the globe, and we come together quarterly for team retreats 
                and collaboration sessions.
              </p>
              <div className="flex justify-center gap-4">
                <Button variant="outline" asChild>
                  <Link href="/about">Meet the Team</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/blog">Read Our Blog</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Application Process */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Our Hiring Process
              </h2>
              <p className="text-xl text-gray-600">
                We've designed our process to be thorough yet respectful of your time.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold">1</span>
                </div>
                <h3 className="font-semibold mb-2">Application</h3>
                <p className="text-sm text-gray-600">Submit your application and we'll review it within 48 hours</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold">2</span>
                </div>
                <h3 className="font-semibold mb-2">Phone Screen</h3>
                <p className="text-sm text-gray-600">30-minute conversation about your background and interests</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold">3</span>
                </div>
                <h3 className="font-semibold mb-2">Technical Interview</h3>
                <p className="text-sm text-gray-600">Role-specific technical discussion or coding challenge</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold">4</span>
                </div>
                <h3 className="font-semibold mb-2">Team Interview</h3>
                <p className="text-sm text-gray-600">Meet your potential teammates and discuss culture fit</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to join our mission?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Help us build the future of knowledge transfer and make a real impact 
            on how development teams work together.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="#open-positions">View Open Positions</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/contact">Get in Touch</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
