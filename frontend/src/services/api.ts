import axios from 'axios';

// Create axios instance
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  register: (userData: any) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

export const partnersAPI = {
  getAll: (params?: any) => api.get('/partners', { params }),
  getById: (id: number) => api.get(`/partners/${id}`),
  create: (data: any) => api.post('/partners', data),
  update: (id: number, data: any) => api.put(`/partners/${id}`, data),
  delete: (id: number) => api.delete(`/partners/${id}`),
  getRegions: () => api.get('/partners/regions'),
  getCapabilities: (category?: string) => 
    api.get('/partners/capabilities', { params: { category } }),
  getTierSummary: () => api.get('/partners/tiers/summary'),
};

export const feedbackAPI = {
  getAll: (params?: any) => api.get('/feedback', { params }),
  getById: (id: number) => api.get(`/feedback/${id}`),
  create: (data: any) => api.post('/feedback', data),
  update: (id: number, data: any) => api.put(`/feedback/${id}`, data),
  delete: (id: number) => api.delete(`/feedback/${id}`),
  getPartnerSummary: (partnerId: number) => 
    api.get(`/feedback/partner/${partnerId}/summary`),
  getAnalytics: () => api.get('/feedback/analytics/overview'),
};

export const vendorsAPI = {
  getMyProfile: () => api.get('/vendors/my-profile'),
  updateMyProfile: (data: any) => api.put('/vendors/my-profile', data),
  uploadDocument: (file: File, documentType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    return api.post('/vendors/upload-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMyDocuments: () => api.get('/vendors/my-documents'),
  deleteDocument: (documentId: number) => 
    api.delete(`/vendors/documents/${documentId}`),
  getProfileCompletionStatus: () => api.get('/vendors/profile-completion-status'),
};

export const analyticsAPI = {
  getDashboardOverview: () => api.get('/analytics/dashboard-overview'),
  getPartnerPerformance: (partnerId?: number) => 
    api.get('/analytics/partner-performance', { params: { partner_id: partnerId } }),
  getFeedbackTrends: (months: number = 12) => 
    api.get('/analytics/feedback-trends', { params: { months } }),
  getTopPerformers: (limit: number = 10) => 
    api.get('/analytics/top-performers', { params: { limit } }),
  getRiskAlerts: () => api.get('/analytics/risk-alerts'),
  exportData: (format: string = 'json') => 
    api.get('/analytics/export-data', { params: { format } }),
};

export const adminAPI = {
  getUsers: (params?: any) => api.get('/admin/users', { params }),
  createUser: (data: any) => api.post('/admin/users', data),
  updateUser: (id: number, data: any) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/admin/users/${id}`),
  getSystemStats: () => api.get('/admin/system-stats'),
  createRegion: (data: any) => api.post('/admin/regions', data),
  createCapability: (data: any) => api.post('/admin/capabilities', data),
  getAuditLog: (params?: any) => api.get('/admin/audit-log', { params }),
  triggerMaintenance: (maintenanceType: string) => 
    api.post('/admin/system-maintenance', { maintenance_type: maintenanceType }),
  healthCheck: () => api.get('/admin/health-check'),
};