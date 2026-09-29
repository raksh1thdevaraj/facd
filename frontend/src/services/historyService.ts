import apiClient from './api';
import {
  VerificationHistorySummary,
  VerificationHistoryDetail,
  HistoryQueryParams,
} from '../types/history';

export const historyService = {
  /**
   * Fetch list of past verification summaries from the history ledger.
   */
  async getHistory(params?: HistoryQueryParams): Promise<VerificationHistorySummary[]> {
    const res = await apiClient.get<any>('/verifications/history', {
      params: {
        page: params?.page || 1,
        limit: params?.limit || 50,
        order: params?.order || 'desc',
        search: params?.search || undefined,
        usn: params?.usn || undefined,
        student_name: params?.student_name || undefined,
        verdict: params?.verdict && params.verdict !== 'ALL' ? params.verdict : undefined,
        document_type:
          params?.document_type && params.document_type !== 'ALL' ? params.document_type : undefined,
        format: 'array',
      },
    });

    const data = res.data;
    if (Array.isArray(data)) {
      return data;
    }
    if (data && Array.isArray(data.items)) {
      return data.items;
    }
    return [];
  },

  /**
   * Fetch complete forensic dossier and RAG/QR breakdown of a specific historical verification.
   */
  async getHistoryDetail(id: string): Promise<VerificationHistoryDetail> {
    const res = await apiClient.get<VerificationHistoryDetail>(`/verifications/history/${id}`);
    return res.data;
  },

  /**
   * Delete a single verification record by ID.
   */
  async deleteHistoryItem(id: string): Promise<void> {
    await apiClient.delete(`/verifications/history/${id}`);
  },

  /**
   * Reset / clear all verification history.
   */
  async clearAllHistory(): Promise<{ success: boolean; deleted_count: number }> {
    const res = await apiClient.delete<any>('/verifications/history/clear');
    return res.data;
  },
};
