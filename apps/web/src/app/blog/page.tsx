import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { 
  CalendarIcon,
  ClockIcon,
  UserIcon,
  ArrowRightIcon,
  TrendingUpIcon,
  BookOpenIcon
} from 'lucide-react'

const featuredPost = {
  title: 'The Future of AI-Powered Knowledge Transfer',
  excerpt: 'How artificial intelligence is revolutionizing the way development teams share and preserve institutional knowledge.',
  author: 'Sarah Johnson',
  date: '2024-01-15',
  readTime: '8 min read',
  category: 'AI & Technology',
  image: '/blog/ai-knowledge-transfer.jpg',
  featured: true
}

const blogPosts = [
  {
    title: 'Building Better Onboarding: 5 Strategies That Actually Work',
    excerpt: 'Learn from successful engineering teams about what makes onboarding effective and how to implement these strategies in your organization.',
    author: 'Alex Chen',
    date: '2024-01-12',
    readTime: '6 min read',
    category: 'Team Management',
    image: '/blog/onboarding-strategies.jpg'
  },
  {
    title: 'Why Documentation Dies (And How to Keep It Alive)',
    excerpt: 'The common pitfalls that kill documentation projects and practical solutions to maintain living, useful documentation.',
    author: 'Mike Rodriguez',
    date: '2024-01-10',
    readTime: '5 min read',
    category: 'Documentation',
    image: '/blog/documentation-alive.jpg'
  },
  {
    title: 'The Hidden Cost of Knowledge Silos in Engineering Teams',
    excerpt: 'Quantifying the real impact of knowledge hoarding and how it affects productivity, innovation, and team morale.',
    author: 'Emily Zhang',
    date: '2024-01-08',
    readTime: '7 min read',
    category: 'Productivity',
    image: '/blog/knowledge-silos.jpg'
  },
  {
    title: 'From Chaos to Clarity: Organizing Your Team\'s Knowledge Base',
    excerpt: 'Practical frameworks for structuring information so your team can actually find what they need when they need it.',
    author: 'Sarah Johnson',
    date: '2024-01-05',
    readTime: '4 min read',
    category: 'Organization',
    image: '/blog/organizing-knowledge.jpg'
  },
  {
    title: 'The Psychology of Knowledge Sharing: Why Smart People Hoard Information',
    excerpt: 'Understanding the psychological barriers to knowledge sharing and how to create a culture that encourages open collaboration.',
    author: 'Dr. Lisa Park',
    date: '2024-01-03',
    readTime: '9 min read',
    category: 'Culture',
    image: '/blog/psychology-sharing.jpg'
  },
  {
    title: 'Measuring the ROI of Knowledge Management Tools',
    excerpt: 'How to quantify the business impact of investing in knowledge management and what metrics actually matter.',
    author: 'Alex Chen',
    date: '2024-01-01',
    readTime: '6 min read',
    category: 'Business',
    image: '/blog/roi-knowledge-tools.jpg'
  }
]

const categories = [
  'All Posts',
  'AI & Technology',
  'Team Management',
  'Documentation',
  'Productivity',
  'Organization',
  'Culture',
  'Business'
]

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-20">
        <div className="container mx-auto px-4 text-center">
          <Badge className="mb-4 bg-purple-100 text-purple-800">
            NeuroSync Blog
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Insights on knowledge transfer and
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"> team productivity</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Learn from industry experts about building better development teams, 
            improving knowledge sharing, and creating more efficient workflows.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">Start Reading</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/contact">Subscribe to Newsletter</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Featured Post */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center gap-2 mb-8">
              <TrendingUpIcon className="h-5 w-5 text-purple-600" />
              <span className="text-lg font-semibold text-gray-900">Featured Article</span>
            </div>
            
            <Card className="overflow-hidden hover:shadow-xl transition-shadow">
              <div className="md:flex">
                <div className="md:w-1/2">
                  <div className="h-64 md:h-full bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center">
                    <BookOpenIcon className="h-16 w-16 text-purple-600" />
                  </div>
                </div>
                <div className="md:w-1/2 p-8">
                  <Badge className="mb-4 bg-purple-100 text-purple-800">
                    {featuredPost.category}
                  </Badge>
                  <h2 className="text-3xl font-bold text-gray-900 mb-4">
                    {featuredPost.title}
                  </h2>
                  <p className="text-gray-600 mb-6 text-lg">
                    {featuredPost.excerpt}
                  </p>
                  
                  <div className="flex items-center gap-6 mb-6 text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      <UserIcon className="h-4 w-4" />
                      {featuredPost.author}
                    </div>
                    <div className="flex items-center gap-2">
                      <CalendarIcon className="h-4 w-4" />
                      {new Date(featuredPost.date).toLocaleDateString()}
                    </div>
                    <div className="flex items-center gap-2">
                      <ClockIcon className="h-4 w-4" />
                      {featuredPost.readTime}
                    </div>
                  </div>
                  
                  <Button asChild>
                    <Link href={`/blog/${featuredPost.title.toLowerCase().replace(/\s+/g, '-')}`}>
                      Read Article
                      <ArrowRightIcon className="h-4 w-4 ml-2" />
                    </Link>
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-12 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Browse by Category</h3>
            <div className="flex flex-wrap gap-3">
              {categories.map((category, index) => (
                <Button
                  key={index}
                  variant={index === 0 ? 'default' : 'outline'}
                  size="sm"
                  className={index === 0 ? '' : 'hover:bg-purple-50 hover:border-purple-300'}
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Blog Posts Grid */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-12">
              <h2 className="text-3xl font-bold text-gray-900">Latest Articles</h2>
              <Button variant="outline" asChild>
                <Link href="/blog/archive">View All Posts</Link>
              </Button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {blogPosts.map((post, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <BookOpenIcon className="h-12 w-12 text-gray-400" />
                  </div>
                  
                  <CardHeader>
                    <Badge variant="outline" className="w-fit mb-2">
                      {post.category}
                    </Badge>
                    <CardTitle className="text-lg leading-tight hover:text-purple-600 transition-colors">
                      <Link href={`/blog/${post.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        {post.title}
                      </Link>
                    </CardTitle>
                    <CardDescription className="line-clamp-3">
                      {post.excerpt}
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                      <div className="flex items-center gap-1">
                        <UserIcon className="h-3 w-3" />
                        {post.author}
                      </div>
                      <div className="flex items-center gap-1">
                        <CalendarIcon className="h-3 w-3" />
                        {new Date(post.date).toLocaleDateString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <ClockIcon className="h-3 w-3" />
                        {post.readTime}
                      </div>
                    </div>
                    
                    <Button variant="outline" size="sm" className="w-full" asChild>
                      <Link href={`/blog/${post.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        Read More
                        <ArrowRightIcon className="h-3 w-3 ml-2" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Newsletter Signup */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Stay Updated
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Get the latest insights on knowledge management, team productivity, 
              and AI-powered development tools delivered to your inbox.
            </p>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <input
                    type="email"
                    placeholder="Enter your email address"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <Button>
                    Subscribe
                  </Button>
                </div>
                <p className="text-sm text-gray-500 mt-3">
                  No spam, unsubscribe at any time. We respect your privacy.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Popular Tags */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-8">
              Popular Topics
            </h2>
            
            <div className="flex flex-wrap justify-center gap-3">
              {[
                'Knowledge Management',
                'Team Onboarding',
                'AI in Development',
                'Documentation',
                'Remote Teams',
                'Developer Productivity',
                'Code Review',
                'Technical Writing',
                'Team Culture',
                'Workflow Automation'
              ].map((tag, index) => (
                <Badge key={index} variant="outline" className="px-4 py-2 hover:bg-purple-50 hover:border-purple-300 cursor-pointer">
                  #{tag.replace(/\s+/g, '').toLowerCase()}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to transform your team's knowledge sharing?
          </h2>
          <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
            Put these insights into practice with NeuroSync's AI-powered knowledge management platform.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-purple-600" asChild>
              <Link href="/demo">See How It Works</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
