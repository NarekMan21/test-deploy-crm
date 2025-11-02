import axios from 'axios';

// Use environment variable or fallback to default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const API_SERVER_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Helper function to get upload URL
export const getUploadUrl = (filename: string): string => {
  if (!filename) return '';
  const baseUrl = API_SERVER_URL.replace('/api', '');
  return `${baseUrl}/uploads/${encodeURIComponent(filename)}`;
};

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'logist' | 'work';
}

export interface Order {
  id: number;
  order_number?: number;
  customer_name: string;
  customer_phone?: string;
  customer_address?: string;
  phone_agreement_notes?: string;
  customer_requirements?: string;
  deadline?: string;
  price?: number;
  material_photo?: string;
  furniture_photo?: string;
  status: 'draft' | 'pending_confirmation' | 'confirmed' | 'in_progress' | 'ready' | 'delivered';
  created_at: string;
  updated_at: string;
}

export interface OrderHistory {
  timestamp: string;
  user: string;
  action: string;
  field_changes?: Record<string, any>;
}

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  getMe: () => api.get('/auth/me'),
};

// Orders API
export const ordersAPI = {
  getOrders: (status?: string) => api.get('/orders/', { params: { status_filter: status } }),
  getOrder: (id: number) => api.get(`/orders/${id}`),
  createOrder: (data: FormData) => api.post('/orders/', data),
  updateOrder: (id: number, data: FormData) => api.put(`/orders/${id}`, data),
  submitOrder: (id: number) => api.post(`/orders/${id}/submit`),
  confirmOrder: (id: number) => api.post(`/orders/${id}/confirm`),
  addOrderDetails: (id: number, data: FormData) => api.put(`/orders/${id}/details`, data),
  completeOrder: (id: number) => api.post(`/orders/${id}/complete`),
  markDelivered: (id: number) => api.post(`/orders/${id}/ready`),
  getOrderHistory: (id: number) => api.get(`/orders/${id}/history`),
};