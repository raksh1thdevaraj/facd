/**
 * Cloud Functions for Firebase v2
 * AI-Based Fraud Academic Certificate Detection Pipeline
 */

import * as crypto from "crypto";
import { onObjectFinalized } from "firebase-functions/v2/storage";
import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as logger from "firebase-functions/logger";
import { initializeApp, getApps } from "firebase-admin/app";
import { getFirestore, FieldValue } from "firebase-admin/firestore";
import { getStorage } from "firebase-admin/storage";
import axios from "axios";
import {
  CertificateDocument,
  CertificateStatus,
  FraudReportDocument,
  AuditLogDocument,
  UserRole,
} from "./types/schemas";

if (getApps().length === 0) {
  initializeApp();
}

const db = getFirestore();
const storage = getStorage();

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"];
const DEFAULT_INFERENCE_ENDPOINT =
  process.env.AI_INFERENCE_ENDPOINT || "http://127.0.0.1:8000/api/v1/course-certificates/verify";
const MODEL_VERSION = process.env.AI_MODEL_VERSION || "v2.4-hybrid-ela-ocr";

/**
 * Triggered when a new certificate file is uploaded to Cloud Storage.
 * Path pattern expected: certificates/{userId}/{certificateId}/{fileName}
 */
export const processCertificateUpload = onObjectFinalized(
  {
    cpu: 2,
    memory: "1GiB",
    timeoutSeconds: 300,
    region: "us-central1",
  },
  async (event) => {
    const object = event.data;
    const filePath = object.name;
    const contentType = object.contentType || "";
    const sizeBytes = Number(object.size || 0);

    if (!filePath || !filePath.startsWith("certificates/")) {
      logger.info(`Ignoring non-certificate path: ${filePath}`);
      return;
    }

    const pathSegments = filePath.split("/");
    if (pathSegments.length < 4) {
      logger.warn(`Invalid certificate storage path layout: ${filePath}`);
      return;
    }

    const userId = pathSegments[1];
    const certificateId = pathSegments[2];
    const fileName = pathSegments.slice(3).join("/");

    logger.info(
      `Processing certificate upload: certId=${certificateId}, userId=${userId}, size=${sizeBytes}B, type=${contentType}`
    );

    // 1. Metadata Validation
    if (!ALLOWED_MIME_TYPES.includes(contentType.toLowerCase())) {
      logger.error(`Rejected invalid MIME type: ${contentType} for file: ${filePath}`);
      await markCertificateError(certificateId, userId, filePath, fileName, "INVALID_MIME_TYPE");
      return;
    }

    if (sizeBytes > MAX_FILE_SIZE_BYTES) {
      logger.error(`Rejected oversized file: ${sizeBytes} bytes exceeds 10MB limit.`);
      await markCertificateError(certificateId, userId, filePath, fileName, "FILE_TOO_LARGE");
      return;
    }

    // 2. Download Buffer & Compute SHA-256 Checksum
    const bucket = storage.bucket(object.bucket);
    const file = bucket.file(filePath);
    const [fileBuffer] = await file.download();

    const sha256Hash = crypto.createHash("sha256").update(fileBuffer).digest("hex");
    logger.info(`Computed SHA-256 for ${certificateId}: ${sha256Hash}`);

    // Check for duplicate tampering / duplicate submission
    const existingDuplicate = await db
      .collection("certificates")
      .where("fileHash", "==", sha256Hash)
      .where("docId", "!=", certificateId)
      .limit(1)
      .get();

    if (!existingDuplicate.empty) {
      logger.warn(`Duplicate certificate payload detected with identical SHA-256: ${sha256Hash}`);
    }

    // 3. Mark Certificate as 'processing'
    const certRef = db.collection("certificates").doc(certificateId);
    const initialCertData: Partial<CertificateDocument> = {
      docId: certificateId,
      uploaderUid: userId,
      storagePath: filePath,
      fileHash: sha256Hash,
      originalFileName: fileName,
      mimeType: contentType as any,
      fileSizeBytes: sizeBytes,
      status: "processing",
      uploadTimestamp: FieldValue.serverTimestamp() as any,
      updatedAt: FieldValue.serverTimestamp() as any,
    };
    await certRef.set(initialCertData, { merge: true });

    // Record Audit Log for Start of Processing
    await recordAuditLog({
      timestamp: FieldValue.serverTimestamp() as any,
      actorUid: "SYSTEM_AI_WORKER",
      action: "AI_ANALYSIS_STARTED",
      certificateId,
      ipAddress: "cloud-functions-internal",
      metadata: { fileHash: sha256Hash, storagePath: filePath },
    });

    // 4. Generate Signed URL and Invoke AI Fraud Detection Inference API
    let fraudScore = 0.0;
    let tamperingFlags = {
      font_mismatch: false,
      stamp_forged: false,
      metadata_anomaly: false,
      ocr_text_mismatch: false,
    };
    let detectedAnomalies: any[] = [];
    let rawModelOutput: Record<string, unknown> = {};

    try {
      const [signedUrl] = await file.getSignedUrl({
        action: "read",
        expires: Date.now() + 15 * 60 * 1000, // 15 minutes
      });

      // Call Inference Backend
      logger.info(`Dispatching analysis payload to inference API: ${DEFAULT_INFERENCE_ENDPOINT}`);
      const aiResponse = await axios.post(
        DEFAULT_INFERENCE_ENDPOINT,
        {
          certificate_id: certificateId,
          user_id: userId,
          file_url: signedUrl,
          file_hash: sha256Hash,
          mime_type: contentType,
        },
        {
          headers: { "Content-Type": "application/json" },
          timeout: 120000,
          validateStatus: () => true, // Handle status code manually
        }
      );

      if (aiResponse.status >= 200 && aiResponse.status < 300) {
        const body = aiResponse.data;
        rawModelOutput = body;
        fraudScore = Number(body.fraud_risk_score ?? body.fraudScore ?? 0.05);

        if (body.tampering_flags || body.tamperingFlags) {
          tamperingFlags = { ...tamperingFlags, ...(body.tampering_flags || body.tamperingFlags) };
        }
        if (Array.isArray(body.detected_anomalies || body.detectedAnomalies)) {
          detectedAnomalies = body.detected_anomalies || body.detectedAnomalies;
        }
      } else {
        logger.warn(
          `AI Inference endpoint returned HTTP ${aiResponse.status}. Falling back to heuristic rule analysis.`
        );
        // Fallback heuristic scoring
        fraudScore = evaluateFallbackHeuristics(fileName, sizeBytes, contentType);
      }
    } catch (aiErr: any) {
      logger.warn(`AI Inference network failure: ${aiErr.message}. Executing localized fallback verification.`);
      fraudScore = evaluateFallbackHeuristics(fileName, sizeBytes, contentType);
    }

    // 5. Determine Verdict and Atomically Update Firestore
    const finalStatus: CertificateStatus = fraudScore >= 0.40 ? "flagged_fraud" : "verified";

    const batch = db.batch();

    // Update Certificate Status
    batch.update(certRef, {
      status: finalStatus,
      updatedAt: FieldValue.serverTimestamp(),
    });

    // Write Detailed Fraud Report (Read restricted to Verifiers and Admins)
    const reportRef = db.collection("fraud_reports").doc(certificateId);
    const reportData: FraudReportDocument = {
      certificateId,
      fraudScore,
      tamperingFlags,
      detectedAnomalies,
      verifiedByModelVersion: MODEL_VERSION,
      timestamp: FieldValue.serverTimestamp() as any,
      rawModelOutput,
    };
    batch.set(reportRef, reportData);

    await batch.commit();

    // Record Final Audit Log Entry
    await recordAuditLog({
      timestamp: FieldValue.serverTimestamp() as any,
      actorUid: "SYSTEM_AI_WORKER",
      action: finalStatus === "flagged_fraud" ? "FLAGGED_AS_FRAUD" : "VERIFIED_AUTHENTIC",
      certificateId,
      ipAddress: "cloud-functions-internal",
      metadata: { fraudScore, finalStatus, modelVersion: MODEL_VERSION },
    });

    logger.info(`Completed processing for ${certificateId}: finalStatus=${finalStatus}, score=${fraudScore}`);
  }
);

/**
 * HTTPS Callable Function for authorized human reviewers (Verifier or Admin)
 * to confirm or overturn automated fraud flags.
 */
export const verifyCertificateManualReview = onCall(
  {
    region: "us-central1",
    enforceAppCheck: false, // Set to true in production once App Check tokens are distributed
  },
  async (request) => {
    // 1. Enforce Authentication
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be authenticated to perform manual reviews.");
    }

    const callerUid = request.auth.uid;
    const { certificateId, verdict, reviewNotes } = request.data;

    if (!certificateId || typeof certificateId !== "string") {
      throw new HttpsError("invalid-argument", "Valid 'certificateId' parameter is required.");
    }

    if (verdict !== "verified" && verdict !== "flagged_fraud") {
      throw new HttpsError("invalid-argument", "Verdict must be either 'verified' or 'flagged_fraud'.");
    }

    if (!reviewNotes || typeof reviewNotes !== "string" || reviewNotes.trim().length < 5) {
      throw new HttpsError("invalid-argument", "Detailed 'reviewNotes' (min 5 characters) are required for audit.");
    }

    // 2. Enforce Role Authorization ('institution_verifier' or 'admin')
    const callerUserDoc = await db.collection("users").doc(callerUid).get();
    const callerRole: UserRole =
      (request.auth.token.role as UserRole) ||
      (callerUserDoc.exists ? callerUserDoc.data()?.role : "student");

    if (callerRole !== "institution_verifier" && callerRole !== "admin") {
      logger.warn(`Permission denied: UID ${callerUid} with role '${callerRole}' attempted manual review.`);
      throw new HttpsError(
        "permission-denied",
        "Insufficient privileges: Only institution verifiers or administrators can execute manual reviews."
      );
    }

    // 3. Atomically Update Certificate and Fraud Report
    const certRef = db.collection("certificates").doc(certificateId);
    const reportRef = db.collection("fraud_reports").doc(certificateId);

    const result = await db.runTransaction(async (transaction) => {
      const certDoc = await transaction.get(certRef);
      if (!certDoc.exists) {
        throw new HttpsError("not-found", `Certificate with ID ${certificateId} does not exist.`);
      }

      const originalStatus = certDoc.data()?.status;

      transaction.update(certRef, {
        status: verdict,
        reviewedBy: callerUid,
        reviewNotes: reviewNotes.trim(),
        reviewedAt: FieldValue.serverTimestamp(),
        updatedAt: FieldValue.serverTimestamp(),
      });

      transaction.set(
        reportRef,
        {
          manualOverturn: {
            overturnedBy: callerUid,
            originalStatus,
            newStatus: verdict,
            reason: reviewNotes.trim(),
            timestamp: FieldValue.serverTimestamp(),
          },
        },
        { merge: true }
      );

      return { originalStatus, newStatus: verdict };
    });

    // 4. Record Immutable Audit Log
    await recordAuditLog({
      timestamp: FieldValue.serverTimestamp() as any,
      actorUid: callerUid,
      action: "MANUAL_REVIEW_SUBMITTED",
      certificateId,
      ipAddress: request.rawRequest.ip || "unknown",
      metadata: {
        originalStatus: result.originalStatus,
        overturnedTo: verdict,
        reviewNotes: reviewNotes.trim(),
        reviewerRole: callerRole,
      },
    });

    logger.info(
      `Manual review recorded: cert=${certificateId}, reviewer=${callerUid}, verdict=${verdict}`
    );

    return {
      success: true,
      certificateId,
      previousStatus: result.originalStatus,
      currentStatus: verdict,
      reviewedBy: callerUid,
    };
  }
);

/**
 * Helper to record errors in certificate document.
 */
async function markCertificateError(
  certificateId: string,
  userId: string,
  filePath: string,
  fileName: string,
  errorCode: string
) {
  const certRef = db.collection("certificates").doc(certificateId);
  await certRef.set(
    {
      docId: certificateId,
      uploaderUid: userId,
      storagePath: filePath,
      originalFileName: fileName,
      status: "flagged_fraud",
      reviewNotes: `Automated upload rejection: ${errorCode}`,
      updatedAt: FieldValue.serverTimestamp(),
    },
    { merge: true }
  );

  await recordAuditLog({
    timestamp: FieldValue.serverTimestamp() as any,
    actorUid: "SYSTEM_AI_WORKER",
    action: "FLAGGED_AS_FRAUD",
    certificateId,
    ipAddress: "cloud-functions-internal",
    metadata: { errorCode, filePath },
  });
}

/**
 * Helper to write immutable audit logs.
 */
async function recordAuditLog(logData: AuditLogDocument): Promise<void> {
  try {
    await db.collection("audit_logs").add(logData);
  } catch (err: any) {
    logger.error("Failed to append to audit_logs collection:", err);
  }
}

/**
 * Fallback heuristic analysis if external AI server is unreachable.
 */
function evaluateFallbackHeuristics(fileName: string, sizeBytes: number, contentType: string): number {
  let score = 0.05;
  const lowerName = fileName.toLowerCase();

  if (lowerName.includes("sample") || lowerName.includes("fake") || lowerName.includes("edit")) {
    score += 0.65;
  }
  if (sizeBytes < 5000) {
    score += 0.40; // Impossibly small for a certificate
  }
  return Math.min(score, 0.99);
}
