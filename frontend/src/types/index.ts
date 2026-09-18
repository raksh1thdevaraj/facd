export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH';

export type CheckStatus = 'PASSED' | 'WARNING' | 'FAILED' | 'SKIPPED';

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface PixelBoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OCRToken {
  text: string;
  confidence: number;
  bbox: BoundingBox;
  pixel_bbox: PixelBoundingBox;
}

export interface CertificateFields {
  student_name?: string | null;
  student_name_confidence: number;
  register_number?: string | null;
  register_number_confidence: number;
  institution_name?: string | null;
  institution_name_confidence: number;
  course_degree?: string | null;
  course_degree_confidence: number;
  grade_or_marks?: string | null;
  grade_or_marks_confidence: number;
  issue_date?: string | null;
  issue_date_confidence: number;
  certificate_number?: string | null;
  certificate_number_confidence: number;
}

export interface ConsistencyCheckItem {
  rule_id: string;
  name: string;
  status: CheckStatus;
  confidence: number;
  details: string;
  field_affected?: string | null;
}

export interface TextConsistencyOutput {
  document_id: string;
  overall_status: CheckStatus;
  consistency_risk_score: number;
  checks: ConsistencyCheckItem[];
}

export interface SuspiciousRegion {
  region_id: string;
  bbox: BoundingBox;
  pixel_bbox: PixelBoundingBox;
  forensic_type: string;
  anomaly_score: number;
  description: string;
}

export interface ForensicsOutput {
  document_id: string;
  ela_heatmap_path: string;
  ela_score: number;
  copy_move_detected: boolean;
  copy_move_clusters_count: number;
  copy_move_score: number;
  font_irregularity_score: number;
  noise_inconsistency_score: number;
  forensics_risk_score: number;
  suspicious_regions: SuspiciousRegion[];
}

export interface TemplateMatchOutput {
  matched_template_id?: string | null;
  matched_template_name?: string | null;
  layout_similarity_score?: number | null;
  logo_signature_similarity?: number | null;
  template_risk_score: number;
  record_found: boolean;
  record_field_matches: Record<string, boolean>;
}

export interface MLInferenceOutput {
  model_version: string;
  model_type: 'tabular_baseline' | 'cnn_visual' | 'fused_multimodal';
  manipulation_probability: number;
  predicted_class: 'genuine' | 'manipulated';
  feature_contributions: Record<string, number>;
  gradcam_heatmap_path?: string | null;
}

export interface ContributingFactor {
  factor_id: string;
  category: 'FORENSICS' | 'TEXT_CONSISTENCY' | 'OCR' | 'ML_MODEL' | 'TEMPLATE';
  impact: 'LOW' | 'MEDIUM' | 'HIGH';
  weight_percentage: number;
  description: string;
}

export interface VerificationReportDTO {
  verification_id: string;
  document_id: string;
  timestamp: string;
  verifier_username: string;
  risk_score: number;
  risk_band: RiskBand;
  extracted_fields: CertificateFields;
  consistency_results: TextConsistencyOutput;
  forensics_results: ForensicsOutput;
  template_results?: TemplateMatchOutput | null;
  ml_results: MLInferenceOutput;
  contributing_factors: ContributingFactor[];
  summary_verdict: string;
  disclaimer: string;
}

export interface ServiceStatus {
  database: string;
  redis?: string;
  storage: string;
}

export interface HealthCheckResponse {
  status: 'ok' | 'degraded';
  app_name: string;
  environment: string;
  version: string;
  services: ServiceStatus;
}
