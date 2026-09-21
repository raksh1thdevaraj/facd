export type VerificationVerdict = 'AUTHENTIC' | 'SUSPICIOUS' | 'MANIPULATED';

export type FindingSeverity = 'CRITICAL' | 'MAJOR' | 'WARNING' | 'INFO';

export interface FileMetadata {
  filename: string;
  file_size_kb: number;
  file_format: string;
  sha256_checksum: string;
  upload_timestamp: string;
}

export interface AcademicCredentials {
  student_name?: string | null;
  student_name_confidence?: number;
  register_number?: string | null;
  register_number_confidence?: number;
  institution_name?: string | null;
  institution_name_confidence?: number;
  course_degree?: string | null;
  course_degree_confidence?: number;
  degree_title?: string | null;
  degree_title_confidence?: number;
  grade_or_marks?: string | null;
  grade_or_marks_confidence?: number;
  gpa_or_grade?: string | null;
  gpa_or_grade_confidence?: number;
  issue_date?: string | null;
  issue_date_confidence?: number;
  graduation_date?: string | null;
  graduation_date_confidence?: number;
  certificate_number?: string | null;
  certificate_number_confidence?: number;
  overall_ocr_confidence?: number;
  ocr_confidence_scores?: Record<string, number>;
  qr_code_data?: string | null;
}

export interface SubsystemScoreItem {
  name: string;
  score: number;
  weight?: number;
  weight_percentage?: number;
  weighted_score?: number;
  status: string;
  detail?: string;
  notes?: string;
  findings_count?: number;
}

export interface VisualEvidencePaths {
  original_image?: string | null;
  unified_overlay?: string | null;
  forensic_heatmap?: string | null;
  gradcam_heatmap?: string | null;
  preprocessed_preview_url?: string | null;
  original_image_url?: string | null;
  gradcam_heatmap_url?: string | null;
  ela_difference_url?: string | null;
}

export interface FindingBullet {
  id?: string;
  severity: FindingSeverity;
  category?: string;
  title?: string;
  description: string;
  module?: string;
  code?: string;
  evidence_value?: string | null;
  location?: Record<string, unknown> | null;
  bounding_box?: [number, number, number, number] | null;
}

export interface FeatureAttribution {
  feature_name: string;
  display_name?: string;
  domain_group?: string;
  feature_value: number;
  shap_value: number;
  impact_percentage?: number;
  direction?: string;
  contribution_direction?: string;
  magnitude?: number;
}

export interface OverlayAnomaly {
  box_id?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  layer: 'ocr' | 'forensics' | 'copy_move' | 'typography';
  label?: string;
  confidence?: number;
  severity?: FindingSeverity;
  description?: string;
}

export interface FullVerificationReport {
  report_id: string;
  certificate_id: string;
  generated_at: string;
  created_at?: string;
  verifier_username?: string;
  file_metadata: FileMetadata;
  verdict: VerificationVerdict;
  primary_verdict?: VerificationVerdict;
  authenticity_score: number;
  authenticity_percentage?: number;
  risk_score?: number;
  risk_band?: string;
  confidence_score?: number;
  confidence_rating?: string;
  tier_status?: string;
  tier_classification?: string;
  veto_applied?: boolean;
  veto_reason?: string | null;
  executive_summary: string;
  extracted_fields?: AcademicCredentials;
  credentials?: AcademicCredentials;
  subsystem_scores: SubsystemScoreItem[] | Record<string, SubsystemScoreItem>;
  findings: FindingBullet[];
  top_features?: FeatureAttribution[];
  visual_evidence?: VisualEvidencePaths;
  anomalies?: OverlayAnomaly[];
  overlay_anomalies?: OverlayAnomaly[];
  report_hmac_signature?: string;
  hmac_signature?: string;
  verification_url?: string;
  qr_code_path?: string | null;
  qr_code_image_path?: string | null;
  pdf_path?: string | null;
  json_path?: string | null;
  legal_disclaimer?: string;
  disclaimer?: string;
  processing_time_ms?: number;
}
