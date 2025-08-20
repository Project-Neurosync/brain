import axios from 'axios';

// Get API URL from environment variable or use default
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable sending cookies with requests
});

// User API
export const getUserProfile = async () => {
  try {
    const response = await api.get('/api/v1/users/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }
};

// Projects API
export const getProjects = async () => {
  try {
    const response = await api.get('/api/v1/projects');
    return response.data;
  } catch (error) {
    console.error('Error fetching projects:', error);
    return [];
  }
};

// Stats API
export const getDashboardStats = async () => {
  try {
    const response = await api.get('/api/v1/stats/dashboard');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return {
      totalProjects: 0,
      aiQueries: 0,
      teamMembers: 0,
      documentsSynced: 0
    };
  }
};

// Auth API
export const login = async (email: string, password: string) => {
  try {
    const response = await api.post('/api/v1/auth/login', { email, password });
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = () => {
  api.post('/api/v1/auth/logout');
  window.location.href = '/login';
};

// AI Queries API
export const getRecentAIQueries = async (limit: number = 5) => {
  try {
    const response = await api.get(`/api/v1/ai/queries/recent?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recent AI queries:', error);
    return [];
  }
};

export const createAIQuery = async (query: string, projectId: string) => {
  try {
    const response = await api.post('/api/v1/ai/query', { query, project_id: projectId });
    return response.data;
  } catch (error) {
    console.error('Error creating AI query:', error);
    throw error;
  }
};

// Integrations API
export const getIntegrations = async () => {
  try {
    const response = await api.get('/api/v1/integrations');
    return response.data;
  } catch (error) {
    console.error('Error fetching integrations:', error);
    return [];
  }
};

export const getIntegrationTypes = async () => {
  try {
    const response = await api.get('/api/v1/integrations/types');
    return response.data;
  } catch (error) {
    console.error('Error fetching integration types:', error);
    return [];
  }
};

export default api;
