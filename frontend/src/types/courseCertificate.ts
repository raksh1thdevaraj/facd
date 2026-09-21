export type CourseVerificationStatus = 'VERIFIED' | 'SUSPICIOUS' | 'FRAUDULENT' | 'UNVERIFIED';

export interface CourseExtractedFields {
  candidate_name?: string | null;
  course_name?: string | null;
  certificate_id?: string | null;
  issue_date?: string | null;
  issuer?: string | null;
  ocr_confidence: number;
  grade?: string | null;
  signatory?: string | null;
  raw_text?: string | null;
}

export interface CourseQRResult {
  qr_detected: boolean;
  qr_decoded: boolean;
  payload?: string | null;
  points?: number[][] | null;
  details: Record<string, any>;
}

export interface CourseURLVerificationResult {
  url?: string | null;
  is_valid_url: boolean;
  resolved_issuer?: string | null;
  domain?: string | null;
  risk_level: string; // SAFE, SUSPICIOUS, MALICIOUS
  trust_score: number;
  domain_match: boolean;
  is_known_issuer: boolean;
  remarks?: string | null;
}

export interface CourseOnlineRecord {
  is_available: boolean;
  candidate_name?: string | null;
  course_name?: string | null;
  certificate_id?: string | null;
  issue_date?: string | null;
  issuer?: string | null;
  raw_details: Record<string, any>;
}

export interface CourseComparisonResult {
  name_match_score: number;
  course_match_score: number;
  cert_id_match_score: number;
  date_match_score: number;
  overall_match_score: number;
  online_record?: CourseOnlineRecord | null;
  discrepancies: string[];
  copied_qr_detected: boolean;
}

export interface CourseForensicResult {
  tampering_detected: boolean;
  tampering_probability: number;
  copy_move_detected: boolean;
  noise_inconsistency_score: number;
  suspicious_bounding_boxes: number[][];
}

export interface CourseSealSignatureResult {
  signature_detected: boolean;
  seal_detected: boolean;
  signature_score: number;
  seal_score: number;
  details: Record<string, any>;
}

export interface CourseVerificationDecision {
  status: CourseVerificationStatus;
  overall_authenticity_score: number;
  fraud_risk_score: number;
  decision_reasons: string[];
  risk_factors: string[];
  signal_scores: {
    online_verification?: number;
    field_matching?: number;
    document_integrity?: number;
    qr_verification?: number;
    domain_trust?: number;
    signature_seal?: number;
    [key: string]: number | undefined;
  };
}

export interface CourseVerificationResponse {
  verification_id: string;
  certificate_id?: string | null;
  filename: string;
  verified_at: string;
  decision: CourseVerificationDecision;
  extracted_fields: CourseExtractedFields;
  qr_result: CourseQRResult;
  url_result: CourseURLVerificationResult;
  comparison_result: CourseComparisonResult;
  forensic_result: CourseForensicResult;
  seal_signature_result?: CourseSealSignatureResult | null;
}

export interface IssuerInfo {
  id?: string;
  name: string;
  domain: string;
  is_active: boolean;
  trust_score: number;
}
