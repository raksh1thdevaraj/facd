# Cloud Firestore Schema & Data Modeling

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Architecture:** NoSQL Document Store with Relational Synchronization  

---

## 1. Collections Overview

| Collection Name | Document ID | Access Level | Description |
|---|---|---|---|
| `users` | User UID (`request.auth.uid`) | Owner Read/Write (Role Restricted), Verifier/Admin Read | Forensic analysts, verifiers, admins, and student accounts. |
| `certificates` | UUIDv4 (`cert_id`) | Owner Read/Create, Verifier/Admin Read/Write | Uploaded academic certificates, status, hash, and metadata. |
| `course_verifications` | UUIDv4 (`verification_id`) | Owner Read, Verifier/Admin Read/Write | Course certificate authenticity verdicts, QR data, forensics, tampering metrics. |
| `audit_logs` | Auto-ID | Verifier/Admin Read-Only | Append-only tamper-evident security audit trail. |

---

## 2. Document Schemas

### 2.1 Collection: `users`
Path: `/users/{userId}`

```json
{
  "id": "u4W78K3x9P...",
  "email": "analyst@university.edu",
  "username": "analyst_john",
  "full_name": "John Doe",
  "role": "INSTITUTION_VERIFIER",
  "institution_id": "inst-101-harvard",
  "is_active": true,
  "created_at": "2026-09-21T18:30:00.000Z",
  "updated_at": "2026-09-21T18:30:00.000Z"
}
```

### 2.2 Collection: `certificates`
Path: `/certificates/{certId}`

```json
{
  "id": "e8a7c2e1-4b72-4cfb-a78b-0123456789ab",
  "user_id": "u4W78K3x9P...",
  "file_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
  "original_filename": "mit_computer_science_degree.pdf",
  "file_size": 245100,
  "mime_type": "application/pdf",
  "job_status": "COMPLETED",
  "job_progress": 100,
  "authenticity_score": 96.5,
  "final_status": "VERIFIED",
  "created_at": "2026-09-21T19:00:00.000Z",
  "updated_at": "2026-09-21T19:01:15.000Z"
}
```

### 2.3 Collection: `course_verifications`
Path: `/course_verifications/{verificationId}`

```json
{
  "id": "cv-7d2e-4b91-81f0-a1b2c3d4e5f6",
  "user_id": "u4W78K3x9P...",
  "file_hash": "f6e5d4c3b2a1...",
  "original_filename": "coursera_machine_learning.pdf",
  "issuer": "Coursera / Stanford Online",
  "verification_url": "https://coursera.org/verify/ABC123XYZ",
  "authenticity_score": 98.2,
  "fraud_risk_score": 1.8,
  "final_status": "VERIFIED",
  "evidence_summary": {
    "decision_reasons": [
      "Official certificate verification URL cryptographically matched online registry.",
      "No copy-move or splicing tampering detected via ELA and frequency analysis."
    ],
    "risk_factors": [],
    "signal_scores": {
      "qr_validity": 1.0,
      "online_match": 1.0,
      "forensic_integrity": 0.98,
      "font_consistency": 0.95
    }
  },
  "created_at": "2026-09-21T19:05:00.000Z"
}
```

### 2.4 Collection: `audit_logs`
Path: `/audit_logs/{logId}`

```json
{
  "action": "CERTIFICATE_VERIFIED",
  "certificate_id": "e8a7c2e1-4b72-4cfb-a78b-0123456789ab",
  "user_id": "u4W78K3x9P...",
  "ip_address": "192.168.1.100",
  "timestamp": "2026-09-21T19:01:15.000Z",
  "details": {
    "verdict": "VERIFIED",
    "score": 96.5
  }
}
```
