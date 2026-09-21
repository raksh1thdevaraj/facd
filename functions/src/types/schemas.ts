/**
 * Normalized Firestore Data Model & Entity Schemas
 * AI-Based Fraud Academic Certificate Detection Platform
 */

export type UserRole = "student" | "institution_verifier" | "admin";

export type CertificateStatus = "queued" | "processing" | "verified" | "flagged_fraud";

export interface UserDocument {
  uid: string;
  email: string;
  role: UserRole;
  organization: string;
  createdAt: FirebaseFirestore.Timestamp | string;
  updatedAt?: FirebaseFirestore.Timestamp | string;
}

export interface CertificateDocument {
  docId: string;
  uploaderUid: string;
  storagePath: string;
  fileHash: string; // SHA-256 checksum
  originalFileName: string;
  mimeType: "application/pdf" | "image/png" | "image/jpeg";
  fileSizeBytes: number;
  status: CertificateStatus;
  uploadTimestamp: FirebaseFirestore.Timestamp | string;
  updatedAt: FirebaseFirestore.Timestamp | string;
  reviewedBy?: string | null;
  reviewNotes?: string | null;
  reviewedAt?: FirebaseFirestore.Timestamp | string | null;
}

export interface TamperingFlags {
  font_mismatch: boolean;
  stamp_forged: boolean;
  metadata_anomaly: boolean;
  ocr_text_mismatch: boolean;
  ela_anomaly_detected?: boolean;
  copy_move_detected?: boolean;
}

export interface DetectedAnomaly {
  category: "typography" | "forensics" | "metadata" | "registry" | "seal";
  description: string;
  confidence: number; // 0.0 - 1.0
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface FraudReportDocument {
  certificateId: string;
  fraudScore: number; // 0.0 (clean) to 1.0 (fraudulent)
  tamperingFlags: TamperingFlags;
  detectedAnomalies: DetectedAnomaly[];
  verifiedByModelVersion: string;
  timestamp: FirebaseFirestore.Timestamp | string;
  manualOverturn?: {
    overturnedBy: string;
    originalStatus: CertificateStatus;
    newStatus: CertificateStatus;
    reason: string;
    timestamp: FirebaseFirestore.Timestamp | string;
  };
  rawModelOutput?: Record<string, unknown>;
}

export interface AuditLogDocument {
  id?: string;
  timestamp: FirebaseFirestore.Timestamp | string;
  actorUid: string; // user UID or "SYSTEM_AI_WORKER"
  action:
    | "CERTIFICATE_UPLOADED"
    | "AI_ANALYSIS_STARTED"
    | "AI_ANALYSIS_COMPLETED"
    | "MANUAL_REVIEW_SUBMITTED"
    | "FLAGGED_AS_FRAUD"
    | "VERIFIED_AUTHENTIC";
  certificateId: string;
  ipAddress: string;
  metadata?: Record<string, unknown>;
}
