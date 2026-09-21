import { apiClient } from './api';
import {
  CourseVerificationResponse,
  CourseURLVerificationResult,
  IssuerInfo,
} from '../types/courseCertificate';

export const courseCertificateService = {
  /**
   * Upload and immediately verify course certificate document
   */
  async verifyCourseCertificate(file: File): Promise<CourseVerificationResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<CourseVerificationResponse>(
      '/course-certificates/verify',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Get past course verification record by ID
   */
  async getVerificationRecord(verificationId: string): Promise<any> {
    const response = await apiClient.get(`/course-certificates/${verificationId}`);
    return response.data;
  },

  /**
   * Download publication-grade PDF verification audit report
   */
  async downloadReport(verificationId: string, filename?: string): Promise<void> {
    const response = await apiClient.get(`/course-certificates/${verificationId}/report`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/pdf' });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || `course_verification_report_${verificationId.slice(0, 8)}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },

  /**
   * List authoritative issuers in registry
   */
  async listIssuers(): Promise<IssuerInfo[]> {
    const response = await apiClient.get<IssuerInfo[]>('/course-certificates/issuers/list');
    return response.data;
  },

  /**
   * Standalone test of verification URL against SSRF and Issuer Registry
   */
  async verifyUrl(url: string): Promise<CourseURLVerificationResult> {
    const response = await apiClient.post<CourseURLVerificationResult>(
      '/course-certificates/verify-url',
      { url }
    );
    return response.data;
  },
};
