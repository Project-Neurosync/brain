'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  SearchIcon, 
  FileTextIcon, 
  CodeIcon,
  MessageSquareIcon,
  CalendarIcon,
  FilterIcon,
  ClockIcon,
  ExternalLinkIcon
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface SearchResult {
  id: string
  title: string
  content: string
  type: 'code' | 'document' | 'chat' | 'meeting'
  source: string
  project: string
  timestamp: string
  relevance_score: number
  url?: string
}

export default function SearchPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'code' | 'document' | 'chat' | 'meeting'>('all')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch('/api/v1/search/cross-source', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
        body: JSON.stringify({
          query: query.trim(),
          project_id: user?.current_project_id || 'default',
          content_types: selectedFilter !== 'all' ? [selectedFilter] : undefined,
          limit: 20
        })
      })

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
      }

      const data = await response.json()
      setResults(data.results || [])
    } catch (error) {
      console.error('Search error:', error)
      toast({
        title: "Search failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive"
      })
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'code': return <CodeIcon className="h-4 w-4" />
      case 'document': return <FileTextIcon className="h-4 w-4" />
      case 'chat': return <MessageSquareIcon className="h-4 w-4" />
      case 'meeting': return <CalendarIcon className="h-4 w-4" />
      default: return <FileTextIcon className="h-4 w-4" />
    }
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'code': return 'bg-green-100 text-green-800'
      case 'document': return 'bg-blue-100 text-blue-800'
      case 'chat': return 'bg-purple-100 text-purple-800'
      case 'meeting': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 24) {
      return `${diffInHours}h ago`
    } else if (diffInHours < 168) {
      return `${Math.floor(diffInHours / 24)}d ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <SearchIcon className="h-6 w-6" />
          Search
        </h1>
        <p className="text-gray-600 mt-1">
          Search across your codebase, documents, and conversations
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Search for code, documents, discussions..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="text-base"
                />
              </div>
              <Button type="submit" disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2">
              <FilterIcon className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">Filter by type:</span>
              <div className="flex gap-2">
                {[
                  { value: 'all', label: 'All' },
                  { value: 'code', label: 'Code' },
                  { value: 'document', label: 'Documents' },
                  { value: 'chat', label: 'Chats' },
                  { value: 'meeting', label: 'Meetings' }
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={selectedFilter === filter.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedFilter(filter.value as any)}
                    type="button"
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Search Results ({results.length})
            </h2>
            <p className="text-sm text-gray-600">
              Sorted by relevance
            </p>
          </div>

          <div className="space-y-4">
            {results.map((result) => (
              <Card key={result.id} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getTypeBadgeColor(result.type)}>
                          <div className="flex items-center gap-1">
                            {getTypeIcon(result.type)}
                            {result.type.charAt(0).toUpperCase() + result.type.slice(1)}
                          </div>
                        </Badge>
                        <span className="text-sm text-gray-600">•</span>
                        <span className="text-sm text-gray-600">{result.project}</span>
                        <span className="text-sm text-gray-600">•</span>
                        <span className="text-sm text-gray-600">{result.source}</span>
                      </div>

                      <h3 className="text-lg font-semibold text-gray-900 mb-2 hover:text-purple-600">
                        {result.title}
                      </h3>

                      <p className="text-gray-700 mb-3 line-clamp-2">
                        {result.content}
                      </p>

                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <ClockIcon className="h-3 w-3" />
                          {formatTimestamp(result.timestamp)}
                        </div>
                        <div className="flex items-center gap-1">
                          <span>Relevance: {Math.round(result.relevance_score * 100)}%</span>
                        </div>
                        {result.url && (
                          <div className="flex items-center gap-1 text-purple-600 hover:text-purple-800">
                            <ExternalLinkIcon className="h-3 w-3" />
                            <span>View source</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {query && results.length === 0 && !loading && (
        <Card>
          <CardContent className="pt-6 text-center">
            <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No results found
            </h3>
            <p className="text-gray-600 mb-4">
              Try adjusting your search terms or filters
            </p>
            <Button variant="outline" onClick={() => setSelectedFilter('all')}>
              Clear filters
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Search Tips */}
      {!query && (
        <Card>
          <CardHeader>
            <CardTitle>Search Tips</CardTitle>
            <CardDescription>
              Get the most out of NeuroSync search
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">What you can search:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Code files and functions</li>
                  <li>• Documentation and README files</li>
                  <li>• Chat conversations</li>
                  <li>• Meeting notes and discussions</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">Search examples:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• "authentication middleware"</li>
                  <li>• "API rate limiting"</li>
                  <li>• "database migration"</li>
                  <li>• "error handling patterns"</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
