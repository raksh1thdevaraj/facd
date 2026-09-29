import axios from 'axios';
import { auth } from '../config/firebase';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 120 seconds explicit timeout to prevent client abort during analysis
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

  // When sending FormData, explicitly delete Content-Type so browser/axios sets multipart boundary
  if (config.data instanceof FormData && config.headers) {
    if (typeof (config.headers as any).delete === 'function') {
      (config.headers as any).delete('Content-Type');
      (config.headers as any).delete('content-type');
    } else {
      delete config.headers['Content-Type'];
      delete config.headers['content-type'];
    }
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

    // 0. Transparently retry transient 503 / connection errors (e.g. hot-reloads) once
    if (
      originalRequest &&
      !originalRequest._networkRetry &&
      (error.response?.status === 503 || error.code === 'ERR_NETWORK' || error.message?.includes('Network Error'))
    ) {
      originalRequest._networkRetry = true;
      await new Promise((resolve) => setTimeout(resolve, 1200));
      return apiClient(originalRequest);
    }

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

    // 3. Network and Server Unavailable Retry Interceptor (502/503/504/ECONNREFUSED/ECONNRESET)
    const isNetworkError =
      !error.response ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ERR_NETWORK' ||
      error.message?.includes('Network Error');
    const isServerUnavailable =
      error.response?.status === 502 ||
      error.response?.status === 503 ||
      error.response?.status === 504;

    if (
      (isNetworkError || isServerUnavailable) &&
      (!originalRequest._retryCount || originalRequest._retryCount < 2) &&
      !originalRequest.url?.includes('/health')
    ) {
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
      const delayMs = originalRequest._retryCount * 1200;

      // Wait briefly before retrying to give backend a chance to initialize
      await new Promise((resolve) => setTimeout(resolve, delayMs));

      return apiClient(originalRequest);
    }

    return Promise.reject(error);
  }
);

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
