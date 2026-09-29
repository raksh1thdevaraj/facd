export type VerificationVerdict = 'AUTHENTIC' | 'SUSPICIOUS' | 'FRAUDULENT';

export interface VerificationHistorySummary {
  id: string;
  timestamp: string;
  original_filename: string;
  document_type: 'VTU_MARKSCARD' | 'ONLINE_COURSE_CERTIFICATE' | string;
  student_name: string;
  identifier: string;
  issuer: string;
  verdict: VerificationVerdict | string;
  confidence_score: number;
  qr_status: boolean;
  tampering_flags: string[];
  remarks: string;
}

export interface VerificationHistoryDetail extends VerificationHistorySummary {
  full_details?: {
    extracted_data?: {
      student_name?: string;
      identifier?: string;
      issuer?: string;
      date?: string;
      score_or_cgpa?: string;
      [key: string]: any;
    };
    extracted_fields?: {
      student_name?: string;
      reg_no?: string;
      institution_name?: string;
      mother_name?: string;
      father_name?: string;
      sgpa?: string;
      [key: string]: any;
    };
    rag_validation?: {
      schema_matched?: boolean;
      arithmetic_valid?: boolean;
      anomalies_detected?: string[];
      mismatch_report?: string;
      [key: string]: any;
    };
    qr_verification?: {
      detected?: boolean;
      payload_or_url?: string | null;
      matches_document_text?: boolean;
      url?: string | null;
      domain_valid?: boolean;
      [key: string]: any;
    };
    forensic_cards?: Record<string, any>;
    gemini_analysis?: Record<string, any>;
    rejection_reasons?: string[];
    warnings?: string[];
    details?: Record<string, any>;
    [key: string]: any;
  };
}

export interface HistoryQueryParams {
  page?: number;
  limit?: number;
  order?: 'asc' | 'desc';
  search?: string;
  usn?: string;
  student_name?: string;
  verdict?: string;
  document_type?: string;
  format?: 'array' | 'paginated';
}
