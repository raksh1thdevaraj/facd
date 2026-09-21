# Course Certificate Verification REST API Reference

**Interactive API Documentation & Endpoint Specification**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Base Path:** `/api/v1/course-certificates`  

---

## 1. Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/course-certificates/verify` | Upload certificate file and execute end-to-end verification |
| `GET` | `/api/v1/course-certificates/{id}` | Retrieve complete audit record and signal data by ID |
| `GET` | `/api/v1/course-certificates/{id}/report` | Download official publication-grade verification PDF |
| `GET` | `/api/v1/course-certificates/{id}/qr` | Retrieve QR code detection data and decoded URL |
| `GET` | `/api/v1/course-certificates/{id}/online-verification` | Retrieve live online record and comparison metrics |
| `GET` | `/api/v1/course-certificates/issuers/list` | List recognized authoritative credential issuers |
| `POST` | `/api/v1/course-certificates/issuers` | Register a new authoritative credential issuer |
| `POST` | `/api/v1/course-certificates/verify-url` | Standalone validation of a verification URL |
| `POST` | `/api/v1/course-certificates/ml/ocr` | Standalone ML OCR field extraction from certificate image |
| `POST` | `/api/v1/course-certificates/ml/qr` | Standalone ML QR code detection & decoding |
| `POST` | `/api/v1/course-certificates/ml/tampering` | Standalone ML document pixel tampering analysis |
| `POST` | `/api/v1/course-certificates/ml/score` | Standalone ML risk scoring from feature vector |

---

## 2. Endpoint Details

### 2.1 Verify Certificate
`POST /api/v1/course-certificates/verify`

**Request:** `multipart/form-data`
- `file`: Binary file (PDF, PNG, JPG, JPEG, WEBP, up to 10MB)

**Response:** `200 OK`
```json
{
  "verification_id": "c4828bbb-7adf-4e46-8bdb-982b8523a796",
  "certificate_id": "UC-12345678",
  "filename": "certificate_alice.png",
  "verified_at": "2026-09-21T21:49:16.430000",
  "decision": {
    "status": "VERIFIED",
    "overall_authenticity_score": 96.5,
    "fraud_risk_score": 3.5,
    "decision_reasons": [
      "Official issuer verification succeeded at coursera.org.",
      "Certificate ID matches online registration record.",
      "Candidate name matches online registration record.",
      "Document forensics show no signs of manipulation."
    ],
    "risk_factors": [],
    "signal_scores": {
      "online_issuer_score": 25.0,
      "field_matching_score": 25.0,
      "document_integrity_score": 20.0,
      "qr_verification_score": 15.0,
      "issuer_domain_trust_score": 10.0,
      "signature_seal_score": 1.5
    }
  },
  "extracted_fields": {
    "candidate_name": "Alice Johnson",
    "course_name": "Machine Learning Specialization",
    "certificate_id": "UC-12345678",
    "issue_date": "2026-05-14",
    "issuer": "Coursera",
    "ocr_confidence": 0.95
  },
  "qr_result": {
    "qr_detected": true,
    "qr_decoded": true,
    "payload": "https://coursera.org/verify/UC-12345678"
  },
  "url_result": {
    "is_valid_url": true,
    "domain": "coursera.org",
    "risk_level": "SAFE",
    "trust_score": 1.0,
    "domain_match": true,
    "is_known_issuer": true
  },
  "comparison_result": {
    "name_match_score": 1.0,
    "course_match_score": 1.0,
    "cert_id_match_score": 1.0,
    "date_match_score": 1.0,
    "overall_match_score": 1.0,
    "copied_qr_detected": false
  },
  "forensic_result": {
    "tampering_detected": false,
    "tampering_probability": 0.04,
    "copy_move_detected": false,
    "noise_inconsistency_score": 0.05
  },
  "seal_signature_result": {
    "signature_detected": true,
    "seal_detected": false,
    "signature_score": 0.85,
    "seal_score": 0.0,
    "details": ["Signature detected with stroke confidence 85%."]
  }
}
```

### 2.2 Download Verification Audit PDF Report
`GET /api/v1/course-certificates/{id}/report`

**Response:** `200 OK`
- `Content-Type`: `application/pdf`
- `Content-Disposition`: `attachment; filename="course_verification_report_UC-12345678.pdf"`

### 2.3 Standalone URL Verification
`POST /api/v1/course-certificates/verify-url`

**Request:** `application/json`
```json
{
  "url": "https://coursera.org/verify/UC-12345678"
}
```

**Response:** `200 OK`
```json
{
  "url": "https://coursera.org/verify/UC-12345678",
  "is_valid_url": true,
  "is_valid_syntax": true,
  "is_https": true,
  "domain": "coursera.org",
  "resolved_issuer": "Coursera",
  "trust_level": "TRUSTED",
  "risk_level": "SAFE",
  "trust_score": 1.0,
  "domain_match": true,
  "is_known_issuer": true,
  "page_accessible": true,
  "http_status": 200,
  "redirect_count": 2,
  "final_destination_url": "https://www.coursera.org/account/accomplishments/verify/UC-12345678"
}
```
