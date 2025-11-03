import axios from 'axios';

// Use environment variable or fallback to default
// Для production: используем полный URL, для dev: localhost
let API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
let API_SERVER_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:8000';

// Если URL не содержит протокол (только имя хоста), добавляем https:// и .onrender.com
if (API_BASE_URL && !API_BASE_URL.startsWith('http')) {
  // Если это просто имя хоста (например, "crmpy-backend"), добавляем полный URL
  const baseHost = API_BASE_URL.includes('/') ? API_BASE_URL.split('/')[0] : API_BASE_URL;
  API_BASE_URL = `https://${baseHost}.onrender.com/api`;
}
if (API_SERVER_URL && !API_SERVER_URL.startsWith('http')) {
  // Если это просто имя хоста, добавляем полный URL
  API_SERVER_URL = `https://${API_SERVER_URL}.onrender.com`;
}

// Логируем URL для отладки
console.log('[API] API_BASE_URL:', API_BASE_URL);
console.log('[API] API_SERVER_URL:', API_SERVER_URL);

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
  const fullUrl = config.baseURL && config.url ? `${config.baseURL}${config.url}` : config.url || 'unknown';
  console.log('[API] Request:', config.method?.toUpperCase(), config.url, 'Full URL:', fullUrl);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  console.error('[API] Request error:', error);
  return Promise.reject(error);
});

// Handle token expiration
api.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.status, error.response?.data, error.config?.url);
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
  login: (username: string, password: string) => {
    console.log('[API] login called with:', { username, password: '***' });
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    console.log('[API] FormData:', formData.toString());
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  getMe: () => api.get('/auth/me'),
};

// Orders API
export const ordersAPI = {
  getOrders: (status?: string) => api.get('/orders/', { params: { status_filter: status } }),
  getOrder: (id: number) => api.get(`/orders/${id}`),
  createOrder: (data: FormData) => api.post('/orders/', data),
  updateOrder: (id: number, data: FormData) => api.put(`/orders/${id}`, data),
  deleteOrder: (id: number) => api.delete(`/orders/${id}`),
  submitOrder: (id: number) => api.post(`/orders/${id}/submit`),
  confirmOrder: (id: number) => api.post(`/orders/${id}/confirm`),
  addOrderDetails: (id: number, data: FormData) => api.put(`/orders/${id}/details`, data),
  completeOrder: (id: number) => api.post(`/orders/${id}/complete`),
  markDelivered: (id: number) => api.post(`/orders/${id}/ready`),
  getOrderHistory: (id: number) => api.get(`/orders/${id}/history`),
};