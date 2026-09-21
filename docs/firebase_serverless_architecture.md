# Production Serverless & Security Architecture: Firebase Cloud Functions v2, Firestore, App Check

**System:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Target Project:** `certcheck-60f6c`  
**Web App ID:** `1:607869238844:web:c68a96b8440f500075cd39`  
**Storage Bucket:** `certcheck-60f6c.firebasestorage.app`  

---

## 1. Firestore Data Model & Entity Schemas

All collections adhere to a normalized, audit-compliant document structure with strict immutability for forensic verdict histories.

### 1.1 Collection: `users`
**Path:** `/users/{uid}`

| Field | Type | Description |
|---|---|---|
| `uid` | `string` | Primary Key matching Firebase Authentication UID. |
| `email` | `string` | User email address. |
| `role` | `string` | One of `'student'`, `'institution_verifier'`, `'admin'`. |
| `organization` | `string` | University, employer, or institutional verification body. |
| `createdAt` | `Timestamp` | Server timestamp of account initialization. |
| `updatedAt` | `Timestamp` | Server timestamp of last profile modification. |

### 1.2 Collection: `certificates`
**Path:** `/certificates/{certificateId}`

| Field | Type | Description |
|---|---|---|
| `docId` | `string` | Unique Certificate Identifier (UUIDv4). |
| `uploaderUid` | `string` | UID of the user who uploaded the certificate. |
| `storagePath` | `string` | Canonical GCS object path (`certificates/{userId}/{certificateId}/{fileName}`). |
| `fileHash` | `string` | Hex-encoded SHA-256 digest to prevent duplicate/tamper uploads. |
| `originalFileName` | `string` | Client filename. |
| `mimeType` | `string` | One of `'application/pdf'`, `'image/png'`, `'image/jpeg'`. |
| `fileSizeBytes` | `number` | File size (strictly <= 10MB). |
| `status` | `string` | State: `'queued'`, `'processing'`, `'verified'`, `'flagged_fraud'`. |
| `uploadTimestamp` | `Timestamp` | Timestamp when file was ingested. |
| `updatedAt` | `Timestamp` | Timestamp of latest state transition. |
| `reviewedBy` | `string` \| `null` | UID of human verifier (if manual review occurred). |
| `reviewNotes` | `string` \| `null` | Auditor justifications for manual confirmations/overturns. |
| `reviewedAt` | `Timestamp` \| `null` | Timestamp of human audit review. |

### 1.3 Collection: `fraud_reports`
**Path:** `/fraud_reports/{certificateId}`  
*Confidentiality constraint:* Read access is strictly restricted to `institution_verifier` and `admin`. Students cannot inspect fraud vector logic.

| Field | Type | Description |
|---|---|---|
| `certificateId` | `string` | References parent `certificates` document ID. |
| `fraudScore` | `number` | Aggregate probability score from 0.0 (genuine) to 1.0 (fraudulent). |
| `tamperingFlags` | `map` | Boolean flags: `font_mismatch`, `stamp_forged`, `metadata_anomaly`, `ocr_text_mismatch`, `ela_anomaly_detected`, `copy_move_detected`. |
| `detectedAnomalies` | `array<map>` | Granular anomalies with `category`, `description`, `confidence`, and optional `boundingBox`. |
| `verifiedByModelVersion` | `string` | AI model version tag (e.g., `v2.4-hybrid-ela-ocr`). |
| `timestamp` | `Timestamp` | Time analysis completed. |
| `manualOverturn` | `map` \| `null` | Record of human reviewer adjustments (`overturnedBy`, `originalStatus`, `newStatus`, `reason`, `timestamp`). |

### 1.4 Collection: `audit_logs`
**Path:** `/audit_logs/{autoId}`  
*Immutability constraint:* Append-only collection. Direct client writes are disallowed; written exclusively by Cloud Functions and Admin SDK.

| Field | Type | Description |
|---|---|---|
| `timestamp` | `Timestamp` | Precise ISO/Server timestamp. |
| `actorUid` | `string` | User UID or `"SYSTEM_AI_WORKER"`. |
| `action` | `string` | E.g., `CERTIFICATE_UPLOADED`, `AI_ANALYSIS_STARTED`, `AI_ANALYSIS_COMPLETED`, `FLAGGED_AS_FRAUD`, `VERIFIED_AUTHENTIC`, `MANUAL_REVIEW_SUBMITTED`. |
| `certificateId` | `string` | Associated certificate document ID. |
| `ipAddress` | `string` | Client IPv4/IPv6 or internal Cloud Functions marker. |
| `metadata` | `map` | Contextual parameters (hashes, score deltas, model versions). |

---

## 2. Serverless AI Processing Pipeline (Cloud Functions v2)

Implemented in [`functions/src/index.ts`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/functions/src/index.ts) using Node.js 20 and TypeScript:

### 2.1 Storage Trigger: `processCertificateUpload` (`onObjectFinalized`)
1. **Trigger Condition:** Fired on object creation matching `certificates/{userId}/{certificateId}/{fileName}`.
2. **Pre-flight Validation:** Validates MIME type (`application/pdf`, `image/png`, `image/jpeg`) and strictly enforces the <= 10MB ceiling.
3. **Checksumming:** Streams the file buffer and computes the SHA-256 hash. Queries Firestore to flag duplicate tamper uploads.
4. **Status Queuing:** Updates `certificates/{certificateId}` to `status: 'processing'`.
5. **Inference Dispatch:** Generates a short-lived signed URL (15 minutes) or streams the payload to the AI inference endpoint (`AI_INFERENCE_ENDPOINT`).
6. **Atomic Persistence:** Executes a Firestore batch write:
   - Updates `certificates/{certificateId}` status to `'verified'` or `'flagged_fraud'`.
   - Populates `fraud_reports/{certificateId}` with complete signals and anomaly coordinates.
   - Appends an immutable record to `audit_logs`.

### 2.2 HTTPS Callable: `verifyCertificateManualReview` (`onCall`)
1. **Authentication Enforcement:** Rejects unauthenticated callers.
2. **Role Verification:** Queries caller's custom claims or Firestore `users/{uid}` document to ensure the user possesses the `institution_verifier` or `admin` role.
3. **Transaction Execution:** Transactionally updates `certificates/{certificateId}` and adds the overturn justification to `fraud_reports/{certificateId}`.
4. **Audit Logging:** Inserts a tamper-evident audit record documenting the actor, old state, new state, and review notes.

---

## 3. Granular Firebase Security Rules

### 3.1 Cloud Storage Security Rules ([`storage.rules`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/storage.rules))
- Authenticated uploads only.
- Strict size enforcement: `request.resource.size <= 10 * 1024 * 1024` (10MB).
- Strict MIME filtering: `request.resource.contentType in ['image/jpeg', 'image/png', 'application/pdf']`.
- Path isolation: Users can only read and write inside `/certificates/{userId}/{certificateId}/{fileName}`.
- Immutable uploads: `allow update, delete: if false;` prevents clients from tampering with or deleting forensic evidence.

### 3.2 Cloud Firestore Security Rules ([`firestore.rules`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/firestore.rules))
- `certificates`: Read access restricted to document owner, verifiers, and admins. Initial creation allowed with `status: 'queued'`. Client updates and state changes are disallowed (`allow update: if false;`).
- `fraud_reports`: Read access strictly restricted to verifiers and admins. Direct client writes disallowed (`allow write: if false;`).
- `audit_logs`: Read-only for verifiers and admins; write disallowed for clients (`allow write: if false;`).

---

## 4. Abuse Prevention & Firebase App Check

### 4.1 Web App Check (reCAPTCHA Enterprise)
Configured in [`frontend/src/config/appCheck.ts`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/frontend/src/config/appCheck.ts) and mounted in [`frontend/src/main.tsx`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/frontend/src/main.tsx):

```typescript
import { initializeAppCheck, ReCaptchaEnterpriseProvider } from "firebase/app-check";
import { app } from "./firebase";

export const initAppCheck = () => {
  if (import.meta.env.DEV) {
    self.FIREBASE_APPCHECK_DEBUG_TOKEN = true;
  }
  const siteKey = import.meta.env.VITE_RECAPTCHA_ENTERPRISE_SITE_KEY;
  if (!siteKey) return null;
  return initializeAppCheck(app, {
    provider: new ReCaptchaEnterpriseProvider(siteKey),
    isTokenAutoRefreshEnabled: true,
  });
};
```

### 4.2 Android Play Integrity (Mobile Clients)
For Android mobile apps, App Check can be activated with Play Integrity:
```kotlin
Firebase.appCheck.installAppCheckProviderFactory(
    PlayIntegrityAppCheckProviderFactory.getInstance()
)
```

---

## 5. Deployment Commands & Runbook

Deploy all rules, indexes, and Cloud Functions using the latest Firebase CLI:

```bash
# 1. Build and verify Cloud Functions TypeScript
cd functions && npm run build && cd ..

# 2. Deploy Firestore Rules and Storage Rules
npx -y firebase-tools@latest deploy --only firestore:rules,storage --project certcheck-60f6c

# 3. Deploy Composite Indexes
npx -y firebase-tools@latest deploy --only firestore:indexes --project certcheck-60f6c

# 4. Deploy Cloud Functions v2 (Storage trigger + Callable)
npx -y firebase-tools@latest deploy --only functions --project certcheck-60f6c
```
