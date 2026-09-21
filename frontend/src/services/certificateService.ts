import { apiClient } from './api';
import {
  CertificateListItem,
  CertificatePaginatedList,
  CertificateStatusResponse,
  CertificateUploadResponse,
} from '../types/certificate';

export const certificateService = {
  async uploadCertificate(file: File): Promise<CertificateUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<CertificateUploadResponse>(
      '/certificates/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  async getCertificateStatus(id: string): Promise<CertificateStatusResponse> {
    const response = await apiClient.get<CertificateStatusResponse>(
      `/certificates/${id}/status`
    );
    return response.data;
  },

  async getCertificate(id: string): Promise<CertificateListItem> {
    const response = await apiClient.get<CertificateListItem>(`/certificates/${id}`);
    return response.data;
  },

  async listCertificates(
    page = 1,
    limit = 20,
    filters?: {
      status?: string;
      verdict?: string;
      search?: string;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<CertificatePaginatedList> {
    const response = await apiClient.get<CertificatePaginatedList>('/certificates', {
      params: { page, limit, ...filters },
    });
    return response.data;
  },


  async deleteCertificate(id: string): Promise<void> {
    await apiClient.delete(`/certificates/${id}`);
  },
};
