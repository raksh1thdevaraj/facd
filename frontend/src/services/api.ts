import axios from 'axios';
import { HealthCheckResponse } from '../types';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for structured error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorDetails = error.response?.data || {
      message: error.message || 'An unexpected network error occurred.',
      error_code: 'NETWORK_ERROR',
      status_code: error.response?.status || 500,
    };
    return Promise.reject(errorDetails);
  }
);

export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};

export default apiClient;
