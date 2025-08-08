'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { authService } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { 
  UsersIcon, 
  UserPlusIcon, 
  MailIcon,
  MoreVerticalIcon,
  CrownIcon,
  ShieldIcon,
  UserIcon
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface TeamMember {
  id: string
  name: string
  email: string
  role: 'owner' | 'admin' | 'member'
  status: 'active' | 'pending' | 'inactive'
  joined_date: string
  last_active: string
}

export default function TeamPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'admin' | 'member'>('member')
  const [loading, setLoading] = useState(false)
  const [fetchingMembers, setFetchingMembers] = useState(true)

  // Fetch team members on mount
  useEffect(() => {
    const fetchTeamMembers = async () => {
      setFetchingMembers(true)
      try {
        const response = await fetch('/api/v1/team/members', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for authentication
        })

        if (!response.ok) {
          throw new Error(`Failed to fetch team: ${response.statusText}`)
        }

        const data = await response.json()
        setTeamMembers(data.team_members || [])
      } catch (error) {
        console.error('Error fetching team members:', error)
        toast({
          title: "Failed to load team",
          description: error instanceof Error ? error.message : "An unexpected error occurred",
          variant: "destructive"
        })
      } finally {
        setFetchingMembers(false)
      }
    }

    if (user) {
      fetchTeamMembers()
    }
  }, [user, toast])

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return

    setLoading(true)
    try {
      const response = await fetch('/api/v1/team/invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email: inviteEmail,
          role: inviteRole,
          project_id: user?.current_project_id || 'default'
        })
      })

      if (!response.ok) {
        throw new Error(`Invitation failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Add the new member to the list
      setTeamMembers(prev => [...prev, data.invitation])
      setInviteEmail('')
      
      toast({
        title: "Invitation sent",
        description: `Invited ${inviteEmail} to join your team`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send invitation. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner': return <CrownIcon className="h-4 w-4 text-yellow-600" />
      case 'admin': return <ShieldIcon className="h-4 w-4 text-blue-600" />
      default: return <UserIcon className="h-4 w-4 text-gray-600" />
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner': return 'bg-yellow-100 text-yellow-800'
      case 'admin': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <UsersIcon className="h-6 w-6" />
            Team Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your team members and their permissions
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Team size</p>
          <p className="text-2xl font-bold text-purple-600">
            {teamMembers.filter(m => m.status === 'active').length}/{teamMembers.length}
          </p>
        </div>
      </div>

      {/* Invite New Member */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserPlusIcon className="h-5 w-5" />
            Invite Team Member
          </CardTitle>
          <CardDescription>
            Send an invitation to add a new member to your team
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleInviteMember} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Input
                  type="email"
                  placeholder="Enter email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                />
              </div>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as 'admin' | 'member')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <Button type="submit" disabled={loading}>
                {loading ? 'Sending...' : 'Send Invite'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Team Members List */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>
            Manage your team members and their roles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {teamMembers.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center gap-4">
                  <Avatar>
                    <AvatarFallback className="bg-gradient-to-r from-purple-500 to-blue-500 text-white">
                      {member.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{member.name}</h3>
                      {member.id === user?.id && <span className="text-sm text-gray-500">(You)</span>}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MailIcon className="h-3 w-3" />
                      {member.email}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Joined {new Date(member.joined_date).toLocaleDateString()} • 
                      Last active {member.last_active}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Badge className={getRoleBadgeColor(member.role)}>
                      <div className="flex items-center gap-1">
                        {getRoleIcon(member.role)}
                        {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                      </div>
                    </Badge>
                    <Badge className={getStatusBadgeColor(member.status)}>
                      {member.status.charAt(0).toUpperCase() + member.status.slice(1)}
                    </Badge>
                  </div>
                  
                  {member.role !== 'owner' && (
                    <Button variant="ghost" size="sm">
                      <MoreVerticalIcon className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Team Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Members</CardTitle>
            <UsersIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {teamMembers.filter(m => m.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">
              out of {teamMembers.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Invites</CardTitle>
            <MailIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {teamMembers.filter(m => m.status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">
              awaiting response
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Admins</CardTitle>
            <ShieldIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {teamMembers.filter(m => m.role === 'admin' || m.role === 'owner').length}
            </div>
            <p className="text-xs text-muted-foreground">
              with admin access
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
