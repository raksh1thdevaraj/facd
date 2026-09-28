import axios from 'axios';
import { auth } from '../config/firebase';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach Firebase ID Token or stored JWT Bearer token
apiClient.interceptors.request.use(async (config) => {
  let token = localStorage.getItem('access_token');
  
  // If Firebase currentUser exists, ensure we have a fresh valid token
  if (auth.currentUser) {
    try {
      token = await auth.currentUser.getIdToken();
      localStorage.setItem('access_token', token);
    } catch {
      // Keep cached token on network error
    }
  }

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Remove default Content-Type for multipart FormData so boundary is generated automatically
  if (config.data instanceof FormData && config.headers) {
    delete config.headers['Content-Type'];
  }

  return config;
});

// Response Interceptor: Silent token refresh on 401
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip refresh attempt on login or refresh endpoint failures
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      // 1. Try Firebase Auth force token refresh if user is signed in
      if (auth.currentUser) {
        try {
          const freshToken = await auth.currentUser.getIdToken(true);
          localStorage.setItem('access_token', freshToken);
          apiClient.defaults.headers.common.Authorization = `Bearer ${freshToken}`;
          processQueue(null, freshToken);
          originalRequest.headers.Authorization = `Bearer ${freshToken}`;
          return apiClient(originalRequest);
        } catch (fbErr) {
          processQueue(fbErr, null);
        } finally {
          isRefreshing = false;
        }
      }

      // 2. Fallback to classic refresh token endpoint
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        isRefreshing = false;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        apiClient.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
