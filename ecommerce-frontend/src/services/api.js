import axios from 'axios';

// Use relative URL to leverage Vite proxy, or direct URL for production
const API_BASE_URL = import.meta.env.PROD ? 'http://13.201.63.10:8000' : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await api.post('/auth/refresh', {}, {
            headers: { 'refresh-token': refreshToken }
          });
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  refresh: (refreshToken) => api.post('/auth/refresh', {}, {
    headers: { 'refresh-token': refreshToken }
  }),
};

// Products API
export const productsAPI = {
  getAll: (page = 1, limit = 10, search = '') =>
    api.get(`/products/?page=${page}&limit=${limit}&search=${search}`),
  getById: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products/', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
};

// Categories API
export const categoriesAPI = {
  getAll: (page = 1, limit = 100, search = '') =>
    api.get(`/categories/?page=${page}&limit=${limit}&search=${search}`),
  getById: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories/', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
};

// Users API (Admin only)
export const usersAPI = {
  getAll: (page = 1, limit = 10, search = '', role = 'user') =>
    api.get(`/users/?page=${page}&limit=${limit}&search=${search}&role=${role}`),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Carts API
export const cartsAPI = {
  getAll: (page = 1, limit = 10) => api.get(`/carts/?page=${page}&limit=${limit}`),
  getById: (id) => api.get(`/carts/${id}`),
  create: (data) => api.post('/carts/', data),
  update: (id, data) => api.put(`/carts/${id}`, data),
  delete: (id) => api.delete(`/carts/${id}`),
};

// Orders API
export const ordersAPI = {
  getAll: (page = 1, limit = 10) => api.get(`/orders/?page=${page}&limit=${limit}`),
  getById: (id) => api.get(`/orders/${id}`),
  create: () => api.post('/orders/'),
  cancel: (id) => api.put(`/orders/${id}/cancel`),
};

// Dynamic Pricing API (Admin only)
export const dynamicPricingAPI = {
  getProducts: (page = 1, limit = 20) =>
    api.get(`/dynamic-pricing/products?page=${page}&limit=${limit}`),
  predict: (data) => api.post('/dynamic-pricing/predict', data),
  approve: (historyId) => api.post(`/dynamic-pricing/approve/${historyId}`),
  reject: (historyId) => api.post(`/dynamic-pricing/reject/${historyId}`),
  deactivate: (productId) => api.post(`/dynamic-pricing/deactivate/${productId}`),
  getHistory: (page = 1, limit = 20, statusFilter = null) => {
    const params = new URLSearchParams({ page, limit });
    if (statusFilter) params.append('status_filter', statusFilter);
    return api.get(`/dynamic-pricing/history?${params}`);
  },
  getProductHistory: (productId) => api.get(`/dynamic-pricing/history/${productId}`),
  // New endpoints
  flushHistory: (statusFilter = null) => {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    return api.delete(`/dynamic-pricing/history/flush?${params}`);
  },
  getTopChanges: (limit = 3) => api.get(`/dynamic-pricing/top-changes?limit=${limit}`),
  updateStatus: (historyId, newStatus) =>
    api.put(`/dynamic-pricing/history/${historyId}/status?new_status=${newStatus}`),
  getStats: () => api.get('/dynamic-pricing/stats'),
};

// Account API
export const accountAPI = {
  getMyInfo: () => api.get('/me/'),
  updateMyInfo: (data) => api.put('/me/', data),
  deleteMyAccount: () => api.delete('/me/'),
};

// Uploads API (Admin only)
export const uploadsAPI = {
  uploadImage: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/uploads/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadMultipleImages: (files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return api.post('/uploads/images', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Promotions API
export const promotionsAPI = {
  // Public endpoint - get carousel promotions (personalized if logged in)
  // Token is automatically added by the interceptor if available
  getCarousel: (limit = 5) => {
    // The interceptor automatically adds the Authorization header if token exists
    // This enables personalized promotions for logged-in users
    return api.get(`/promotions/carousel?limit=${limit}`);
  },

  // Admin endpoints
  getAll: (skip = 0, limit = 20, status = null) => {
    let url = `/promotions/all?skip=${skip}&limit=${limit}`;
    if (status) url += `&status=${status}`;
    return api.get(url);
  },
  getById: (promotionId) => api.get(`/promotions/${promotionId}`),
  update: (promotionId, data) => api.put(`/promotions/${promotionId}`, data),
  approve: (promotionId) => api.post(`/promotions/${promotionId}/approve`),

  // Regenerate with optional custom prompts
  regenerate: (promotionId, options = {}) =>
    api.post(`/promotions/${promotionId}/regenerate`, {
      custom_text_prompt: options.customTextPrompt || null,
      custom_image_prompt: options.customImagePrompt || null,
      regenerate_image: options.regenerateImage || false
    }),

  // Generate image with optional custom prompt
  generateImage: (promotionId, customPrompt = null) =>
    api.post(`/promotions/generate-image/${promotionId}`, {
      custom_prompt: customPrompt
    }),

  // Get default prompts for admin reference
  getDefaultPrompts: () => api.get('/promotions/admin/default-prompts'),

  deactivate: (promotionId) => api.post(`/promotions/${promotionId}/deactivate`),
  reactivate: (promotionId) => api.post(`/promotions/${promotionId}/reactivate`),
  delete: (promotionId) => api.delete(`/promotions/${promotionId}`),
};

// Demand Prediction API (Admin only)
export const demandPredictionAPI = {
  getProducts: (page = 1, limit = 20, demandLevel = null) => {
    const params = new URLSearchParams({ page, limit });
    if (demandLevel) params.append('demand_level', demandLevel);
    return api.get(`/demand-prediction/products?${params}`);
  },
  predict: (data) => api.post('/demand-prediction/predict', data),
  predictBulk: (data) => api.post('/demand-prediction/predict-bulk', data),
  acknowledge: (historyId) => api.post(`/demand-prediction/acknowledge/${historyId}`),
  delete: (historyId) => api.delete(`/demand-prediction/history/${historyId}`),
  getTrending: (limit = 10) => api.get(`/demand-prediction/trending?limit=${limit}`),
  getStats: () => api.get('/demand-prediction/stats'),
  getHistory: (page = 1, limit = 20, statusFilter = null, demandLevel = null) => {
    const params = new URLSearchParams({ page, limit });
    if (statusFilter) params.append('status_filter', statusFilter);
    if (demandLevel) params.append('demand_level', demandLevel);
    return api.get(`/demand-prediction/history?${params}`);
  },
  getProductHistory: (productId) => api.get(`/demand-prediction/history/${productId}`),
};

// Price Comparison API (SerpApi)
export const priceComparisonAPI = {
  compare: (productQuery) => api.get(`/price-comparison/${encodeURIComponent(productQuery)}`),
};

// Chat API
export const chatAPI = {
  sendMessage: (query, currentlyFetchedItems = []) =>
    api.post('/chat/', {
      query,
      currently_fetched_items: currentlyFetchedItems
    }),
};

export default api;
