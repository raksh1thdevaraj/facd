import api from './api';
import { FullVerificationReport } from '../types/report';

export const reportService = {
  async getReport(reportId: string): Promise<FullVerificationReport> {
    const response = await api.get<FullVerificationReport>(`/reports/${reportId}`);
    return response.data;
  },

  async downloadReportPdf(reportId: string): Promise<void> {
    const response = await api.get(`/reports/${reportId}/pdf`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `verification_report_${reportId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async downloadReportJson(reportId: string): Promise<void> {
    const response = await api.get(`/reports/${reportId}/json`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `verification_report_${reportId}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async verifyReportIntegrity(reportId: string): Promise<{ is_valid: boolean; status?: string; message: string; [key: string]: unknown }> {
    const response = await api.get<{ is_valid: boolean; status?: string; message: string; [key: string]: unknown }>(`/reports/${reportId}/verify`);
    return response.data;
  },
};
