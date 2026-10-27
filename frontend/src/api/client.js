import axios from 'axios';

export const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    const raw = import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '');
    return raw.endsWith('/api/v1') ? raw : `${raw}/api/v1`;
  }
  if (typeof window !== 'undefined' && window.location) {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isLocalhost) {
      return `${window.location.origin}/api/v1`;
    }
  }
  return 'http://localhost:8000/api/v1';
};

export const getMediaBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    const raw = import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '');
    return raw.replace(/\/api\/v1\/?$/, '').replace(/\/api\/?$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isLocalhost) {
      return window.location.origin;
    }
  }
  return 'http://localhost:8000';
};

export const getMediaUrl = (downloadUrl, token) => {
  if (!downloadUrl) return '';
  const base = getMediaBaseUrl();
  const cleanPath = downloadUrl.startsWith('/') ? downloadUrl : `/${downloadUrl}`;
  const authToken = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null);
  const tokenParam = authToken ? (cleanPath.includes('?') ? `&token=${encodeURIComponent(authToken)}` : `?token=${encodeURIComponent(authToken)}`) : '';
  return `${base}${cleanPath}${tokenParam}`;
};

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if invalid or expired
      const isAuthRoute = window.location.pathname.startsWith('/login') || window.location.pathname.startsWith('/register');
      if (!isAuthRoute && localStorage.getItem('token')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
