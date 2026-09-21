export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface CertificateUploadResponse {
  certificate_id: string;
  filename: string;
  file_hash: string;
  file_size: number;
  status: JobStatus;
  created_at: string;
}

export interface CertificateStatusResponse {
  certificate_id: string;
  status: JobStatus;
  progress: number;
  error?: string | null;
  report_id?: string | null;
  updated_at: string;
}

export interface CertificateListItem {
  id: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  job_status: JobStatus;
  status?: JobStatus;
  job_progress: number;
  final_verdict?: string | null;
  verdict?: string | null;
  overall_authenticity_score?: number | null;
  authenticity_score?: number | null;
  report_id?: string | null;
  created_at: string;
}

export interface CertificatePaginatedList {
  items: CertificateListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
