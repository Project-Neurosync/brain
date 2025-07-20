'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Users, 
  DollarSign, 
  Activity, 
  TrendingUp, 
  Shield, 
  Search,
  UserCheck,
  UserX,
  Plus,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface DashboardStats {
  users: {
    total: number;
    active: number;
    new_this_month: number;
    growth_rate: number;
  };
  subscriptions: {
    total: number;
    breakdown: Record<string, number>;
  };
  revenue: {
    total: number;
    monthly: number;
    arr: number;
  };
  tokens: {
    total_used: number;
    monthly_used: number;
    avg_per_user: number;
  };
  projects: {
    total: number;
    active: number;
  };
}

interface User {
  id: string;
  email: string;
  subscription_tier: string;
  is_active: boolean;
  created_at: string;
  monthly_token_quota: number;
  tokens_used_this_month: number;
  bonus_tokens: number;
  subscription_status: string;
}

const AdminDashboard = () => {
  const [adminToken, setAdminToken] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('users');
  
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [userSearch, setUserSearch] = useState('');

  // Check if already authenticated (from localStorage)
  useEffect(() => {
    const savedToken = localStorage.getItem('admin_token');
    if (savedToken) {
      setAdminToken(savedToken);
      setIsAuthenticated(true);
      loadDashboardData(savedToken);
    }
  }, []);

  const authenticate = async () => {
    if (!adminToken.trim()) {
      setError('Please enter admin token');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: adminToken })
      });

      if (response.ok) {
        const result = await response.json();
        localStorage.setItem('admin_token', adminToken);
        setIsAuthenticated(true);
        await loadDashboardData(adminToken);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Invalid admin token' }));
        setError(errorData.detail || 'Invalid admin token');
      }
    } catch (err) {
      setError('Failed to authenticate');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardData = async (token: string) => {
    try {
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load dashboard stats
      const statsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/dashboard-stats`, { headers });
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setDashboardStats(stats);
      }

      // Load users
      const usersResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/users?page=1&limit=50&search=${userSearch}`, { headers });
      if (usersResponse.ok) {
        const usersData = await usersResponse.json();
        setUsers(usersData.users);
      }

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  const toggleUserStatus = async (userId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/users/${userId}/toggle-status`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await loadDashboardData(adminToken);
      }
    } catch (err) {
      console.error('Failed to toggle user status:', err);
    }
  };

  const addTokensToUser = async (userId: string, tokens: number) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/users/${userId}/add-tokens`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tokens, reason: 'Admin grant' })
      });

      if (response.ok) {
        await loadDashboardData(adminToken);
      }
    } catch (err) {
      console.error('Failed to add tokens:', err);
    }
  };

  const logout = () => {
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
    setAdminToken('');
    setDashboardStats(null);
    setUsers([]);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">
              <Shield className="h-8 w-8 mx-auto mb-2 text-purple-600" />
              NeuroSync Admin
            </CardTitle>
            <CardDescription>
              Enter your admin token to access the dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                type="password"
                placeholder="Admin Token"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && authenticate()}
              />
              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}
            </div>
            <Button 
              onClick={authenticate} 
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Authenticating...' : 'Access Dashboard'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">NeuroSync Admin</h1>
                <p className="text-sm text-gray-500">System Management Dashboard</p>
              </div>
            </div>
            <Button variant="outline" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboardStats.users.total}</div>
                <p className="text-xs text-muted-foreground">
                  +{dashboardStats.users.new_this_month} this month ({dashboardStats.users.growth_rate}%)
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${dashboardStats.revenue.monthly.toFixed(2)}</div>
                <p className="text-xs text-muted-foreground">
                  ARR: ${dashboardStats.revenue.arr.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboardStats.subscriptions.total}</div>
                <div className="flex gap-1 mt-1">
                  {Object.entries(dashboardStats.subscriptions.breakdown).map(([plan, count]) => (
                    <Badge key={plan} variant="secondary" className="text-xs">
                      {plan}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Monthly Token Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboardStats.tokens.monthly_used}</div>
                <p className="text-xs text-muted-foreground">
                  Avg: {dashboardStats.tokens.avg_per_user} per user
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Navigation */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            {['users', 'revenue', 'system', 'analytics'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Users Section */}
        {activeTab === 'users' && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>User Management</CardTitle>
                  <CardDescription>Manage user accounts and permissions</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Search className="h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search users..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="w-64"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {users.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {user.is_active ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                        <div>
                          <p className="font-medium">{user.email}</p>
                          <p className="text-sm text-gray-500">
                            {user.subscription_tier} • Created {new Date(user.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">
                          {user.tokens_used_this_month}/{user.monthly_token_quota} tokens
                        </p>
                        <p className="text-xs text-gray-500">
                          +{user.bonus_tokens} bonus
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => addTokensToUser(user.id, 100)}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add Tokens
                        </Button>
                        <Button
                          size="sm"
                          variant={user.is_active ? "destructive" : "default"}
                          onClick={() => toggleUserStatus(user.id)}
                        >
                          {user.is_active ? (
                            <>
                              <UserX className="h-4 w-4 mr-1" />
                              Deactivate
                            </>
                          ) : (
                            <>
                              <UserCheck className="h-4 w-4 mr-1" />
                              Activate
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Revenue Section */}
        {activeTab === 'revenue' && (
          <Card>
            <CardHeader>
              <CardTitle>Revenue Analytics</CardTitle>
              <CardDescription>Revenue breakdown and analytics</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500">
                Revenue analytics and detailed reporting will be displayed here.
              </p>
            </CardContent>
          </Card>
        )}

        {/* System Section */}
        {activeTab === 'system' && (
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>System monitoring and health checks</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500">
                System health metrics and monitoring will be displayed here.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Analytics Section */}
        {activeTab === 'analytics' && (
          <Card>
            <CardHeader>
              <CardTitle>Analytics</CardTitle>
              <CardDescription>Advanced analytics and insights</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500">
                Advanced analytics and reporting features will be available here.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
