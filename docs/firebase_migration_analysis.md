# Technical Architectural Analysis: Migration to Firebase Ecosystem

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Target:** Firebase Authentication, Cloud Firestore & Firebase Storage Migration  
**Document Path:** `docs/firebase_migration_analysis.md`  
**Date:** September 21, 2026  

---

## 1. Executive Summary

This document establishes the audit, gap analysis, data mapping, and step-by-step migration architecture required to transition the project from its current localized storage (SQLite / SQLAlchemy / Local Disk / JWT Bearer) to **Google Firebase**:
- **Authentication**: Firebase Authentication (Client SDK on React Frontend, Token Verification on FastAPI Backend via `firebase-admin`).
- **Database**: Cloud Firestore (Replacing SQLite relational tables with structured NoSQL collections, indexes, and document references).
- **Storage**: Firebase Storage (Replacing local `storage/uploads`, `storage/reports`, and `uploads/` directories with secure, bucket-isolated object paths).
- **ML Services**: Preserved intact (FastAPI/PyTorch/LightGBM/EasyOCR services continue computing forensic and model metrics without interruption).

---

## 2. Current Architecture Audit

### 2.1 Technology Stack Matrix
| Component | Existing Implementation | Target Firebase Implementation |
|---|---|---|
| **Frontend UI** | React 18, Vite 5, TypeScript 5, TailwindCSS 3.4 | React 18 + Firebase Web SDK v10 (Modular) |
| **Client Auth State** | LocalStorage JWT access/refresh tokens, `AuthContext` | `onAuthStateChanged` Firebase Auth observer + ID Token refresh |
| **Backend Framework** | Python 3.11, FastAPI 0.110, Pydantic V2 | FastAPI 0.110 + `firebase-admin` Python SDK |
| **Backend Auth Validation**| `python-jose` verifying local HS256 JWT tokens in `backend/app/api/deps.py` | `firebase_admin.auth.verify_id_token()` resolving Firebase UID & Claims |
| **Primary Database** | SQLite (`dev.db`), SQLAlchemy 2.0 ORM (14 models) | Google Cloud Firestore (Document Collections) |
| **File Storage** | Local filesystem (`storage/uploads`, `storage/reports`, `storage/templates`) | Google Firebase Storage (`gs://certcheck-60f6c.firebasestorage.app`) |
| **Forensics & ML** | ELA, Copy-Move, ResNet visual model, LightGBM/Logistic Regression tabular models | Reused intact, input stream sourced from Firebase Storage download URLs |

### 2.2 Existing User Roles & Authorization Hierarchy
From `backend/app/core/rbac.py` and `frontend/src/types/auth.ts`:
- **`ADMIN`** (Aliases: `admin`, `administrator`): Unrestricted access to user management, institution registries, fraud audit logs, template registration, and global analytics.
- **`INSTITUTION_VERIFIER`** (Aliases: `verifier`, `registrar`, `auditor`): Authorized to upload bulk institutional records, inspect academic certificates, view forensic overlays, and manage templates.
- **`PUBLIC_USER`** (Aliases: `user`, `student`, `guest`): Authorized to upload single course/academic certificates, preview verification reports, and inspect verification history.

---

## 3. Detailed Data & Entity Migration Mapping

### 3.1 Relational Tables to Firestore Collections
The existing SQLite database contains 14 tables. The target Firestore schema maps them into structured, document-oriented collections:

| SQLite Table | Target Firestore Collection | Document ID Convention | Key Document Fields |
|---|---|---|---|
| `app_users` | `users/` | Firebase Auth UID (`auth.uid`) | `email`, `fullName`, `role` (`ADMIN`/`INSTITUTION_VERIFIER`/`PUBLIC_USER`), `institutionId`, `isActive`, `emailVerified`, `createdAt`, `updatedAt` |
| `institutions` | `institutions/` | `inst_{uuid}` | `name`, `code`, `domain`, `country`, `isVerified`, `createdAt` |
| `certificates` | `certificates/` | `cert_{uuid}` | `certificateId`, `userId`, `storagePath`, `fileUrl`, `fileType`, `issuerId`, `extractedData`, `verificationStatus`, `tamperingScore`, `createdAt` |
| `course_certificate_verifications` | `course_verifications/` | `course_cert_{uuid}` | `userId`, `certificateId`, `storagePath`, `fileUrl`, `extractedFields`, `qrData`, `urlVerification`, `fieldComparison`, `tamperingAnalysis`, `authenticityScore`, `fraudRiskScore`, `finalStatus`, `createdAt` |
| `issuer_registry` | `issuers/` | `issuer_{name_slug}` | `issuerName`, `officialDomain`, `verificationDomain`, `trustedStatus`, `verificationPattern`, `createdAt` |
| `verification_reports` | `reports/` | `report_{uuid}` | `certificateId`, `verificationId`, `pdfStoragePath`, `pdfDownloadUrl`, `verdict`, `hmacSignature`, `generatedAt` |
| `audit_logs` | `audit_logs/` | `audit_{uuid}` | `userId`, `action`, `resourceId`, `ipAddress`, `timestamp`, `details` |
| `institution_records` | `academic_records/` | `rec_{cert_id}` | `studentName`, `degree`, `major`, `graduationDate`, `institutionId`, `gpa` |
| `institution_templates` | `templates/` | `tmpl_{uuid}` | `institutionId`, `name`, `storagePath`, `featureVectorPath`, `isActive` |

---

## 4. Storage Bucket Structure & Access Partitioning

Target Bucket: `certcheck-60f6c.firebasestorage.app`

```text
gs://certcheck-60f6c.firebasestorage.app/
├── certificates/
│   └── {userId}/
│       └── {certificateId}/
│           ├── original.pdf (or .png / .jpg)
│           ├── rasterized/
│           │   └── page_001.png
│           ├── forensics/
│           │   ├── ela_heatmap.png
│           │   └── qr_crop.png
│           └── reports/
│               └── audit_report.pdf
├── templates/
│   └── {institutionId}/
│       └── {templateId}.png
└── public/
    └── sample_specimens/
```

---

## 5. Security & Rule Architecture

### 5.1 Cloud Firestore Rules Philosophy
1. **Zero Anonymous Access**: Public reads/writes strictly rejected (`request.auth != null`).
2. **Owner-Isolated Reads & Writes**: Users can only read and create records where `resource.data.userId == request.auth.uid`.
3. **Immutability of Role & Fraud Decisions**:
   - `request.resource.data.role` cannot be altered by normal client requests.
   - Verification scores (`authenticityScore`, `finalStatus`, `tamperingProbability`) can ONLY be written by authenticated backend services (via Firebase Admin SDK).
4. **Admin Inheritance**: Users possessing `request.auth.token.role == 'ADMIN'` inherit global read/query capabilities.

### 5.2 Storage Security Rules Philosophy
- File uploads constrained to `request.auth.uid` folder path.
- Content type validated: `request.resource.contentType.matches('application/pdf|image/png|image/jpeg|image/webp')`.
- Max upload size: 15MB.

---

## 6. Components Requiring Modification vs. Remaining Unchanged

### 6.1 Files to Modify
1. **Frontend**:
   - `frontend/package.json`: Add `firebase`.
   - `frontend/src/config/firebase.ts`: Initialize Firebase Client SDK with user's provided credentials.
   - `frontend/src/services/authService.ts`: Replace Axios login/register with `signInWithEmailAndPassword`, `createUserWithEmailAndPassword`, `signOut`, `sendPasswordResetEmail`.
   - `frontend/src/context/AuthContext.tsx`: Subscribe to `onAuthStateChanged`, attach Firebase ID Token to outgoing requests.
   - `frontend/src/services/api.ts`: Add Axios interceptor injecting `Authorization: Bearer <firebaseIdToken>`.
   - `frontend/src/services/courseCertificateService.ts`: Upload to Firebase Storage and post storage reference to backend.
2. **Backend**:
   - `backend/pyproject.toml`: Add `firebase-admin>=6.5.0`.
   - `backend/app/config.py`: Add Firebase project configuration settings (`FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_PATH`).
   - `backend/app/core/firebase.py`: Reusable Firebase Admin SDK initializer and token verifier.
   - `backend/app/api/deps.py`: Update `get_current_user` to verify Firebase ID tokens using `firebase_admin.auth.verify_id_token`.
   - `backend/app/services/firestore_service.py`: Abstraction layer reading/writing Firestore collections for users, certificates, and audit logs.
   - `backend/app/services/firebase_storage_service.py`: Upload/download service for certificate media.
3. **Rules & Documentation**:
   - `firestore.rules`: Security rules enforcing authorization and immutability.
   - `storage.rules`: Storage rules restricting upload paths and mime types.
   - `firestore.indexes.json`: Composite index definitions for certificate queries.
   - `docs/firebase_setup.md`: Comprehensive setup and operational runbook.

### 6.2 Files That Must Remain Unchanged
- **ML Classifiers & Models**: `ml/scripts/train_course_cert_model.py`, `ml/models/course_cert_classifier.joblib`.
- **Forensics Algorithms**: `backend/app/modules/forensics/` (ELA, copy-move block matching, Laplacian noise analysis).
- **QR & OCR Detection**: `backend/app/modules/course_verification/qr_detector.py`, `backend/app/modules/ocr/`.
- **UI Design System**: All Tailwind styling, components, cards, navigation bar layouts, and page visuals.

---

## 7. Migration Execution Plan & Phased Strategy

1. **Phase 1**: Analysis & Setup Documentation (`docs/firebase_migration_analysis.md`, `docs/firebase_setup.md`).
2. **Phase 2**: Firebase Infrastructure Configuration (`firestore.rules`, `storage.rules`, `firestore.indexes.json`).
3. **Phase 3**: Frontend Firebase Integration (`firebase.ts`, `authService.ts`, `AuthContext.tsx`, `api.ts`).
4. **Phase 4**: Backend Firebase Admin SDK (`firebase.py`, `deps.py`, `firestore_service.py`, `firebase_storage_service.py`).
5. **Phase 5**: SQLite-to-Firestore Data Migration Scripts (`migration/export_sqlite_to_firestore.py`).
6. **Phase 6**: Verification & Security Testing (Auth, Storage, Course Certificate end-to-end flow).
