import apiClient from './api';
import {
  AnalyticsSummaryResponse,
  SystemHealthDiagnostic,
  Institution,
  InstitutionCreate,
  InstitutionPaginatedList,
  TemplateItem,
  AuditLogPaginatedList,
} from '../types/admin';

export const adminService = {
  async getAnalyticsSummary(bypassCache: boolean = false): Promise<AnalyticsSummaryResponse> {
    const response = await apiClient.get<AnalyticsSummaryResponse>(
      `/admin/analytics/summary?bypass_cache=${bypassCache}`
    );
    return response.data;
  },

  async getSystemHealth(): Promise<SystemHealthDiagnostic> {
    const response = await apiClient.get<SystemHealthDiagnostic>('/admin/system/health');
    return response.data;
  },

  async listInstitutions(page: number = 1, limit: number = 20): Promise<InstitutionPaginatedList> {
    const response = await apiClient.get<InstitutionPaginatedList>(
      `/institutions?page=${page}&limit=${limit}`
    );
    return response.data;
  },

  async registerInstitution(data: InstitutionCreate): Promise<Institution> {
    const response = await apiClient.post<Institution>('/institutions', data);
    return response.data;
  },

  async toggleInstitutionStatus(id: string): Promise<Institution> {
    const response = await apiClient.patch<Institution>(`/institutions/${id}/toggle-status`);
    return response.data;
  },

  async listTemplates(institutionId?: string): Promise<TemplateItem[]> {
    const url = institutionId ? `/templates?institution_id=${institutionId}` : '/templates';
    const response = await apiClient.get<TemplateItem[]>(url);
    return response.data;
  },

  async listAuditLogs(
    page: number = 1,
    limit: number = 50,
    action?: string,
    certificateId?: string
  ): Promise<AuditLogPaginatedList> {
    let url = `/audit-logs?page=${page}&limit=${limit}`;
    if (action) url += `&action=${encodeURIComponent(action)}`;
    if (certificateId) url += `&certificate_id=${encodeURIComponent(certificateId)}`;
    const response = await apiClient.get<AuditLogPaginatedList>(url);
    return response.data;
  },
};
