export interface TimeSeriesDataPoint {
  date: string;
  total: number;
  fraud: number;
  authentic: number;
  suspicious: number;
}

export interface ModalityBreakdownItem {
  modality: string;
  count: number;
  percentage: number;
}

export interface PipelineLatencyBreakdown {
  ingestion: number;
  preprocessing: number;
  ocr: number;
  forensics: number;
  ml_inference: number;
  report_generation: number;
}

export interface SystemHealthDiagnostic {
  db_status: string;
  db_latency_ms: number;
  storage_used_gb: number;
  storage_total_gb: number;
  ocr_engine_status: string;
  ml_device: string;
  latency_breakdown: PipelineLatencyBreakdown;
}

export interface AnalyticsSummaryResponse {
  total_certificates_verified: number;
  total_authentic_count: number;
  total_suspicious_count: number;
  total_manipulated_count: number;
  overall_fraud_rate_percentage: number;
  average_pipeline_latency_seconds: number;
  verdict_distribution: Record<string, number>;
  manipulation_modalities: ModalityBreakdownItem[];
  daily_trends: TimeSeriesDataPoint[];
}

export interface Institution {
  id: string;
  name: string;
  code: string;
  contact_email: string;
  is_active: boolean;
  template_count: number;
  record_count: number;
  created_at: string;
}

export interface InstitutionCreate {
  name: string;
  code: string;
  contact_email: string;
}

export interface InstitutionPaginatedList {
  items: Institution[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface TemplateItem {
  template_id: string;
  institution_id: string;
  institution_name: string;
  template_name: string;
  degree_program?: string | null;
  uploaded_at: string;
  seal_roi?: { x: number; y: number; width: number; height: number } | null;
}

export interface AuditLogItem {
  id: string;
  user_id?: string | null;
  certificate_id?: string | null;
  action: string;
  ip_address?: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogPaginatedList {
  items: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
