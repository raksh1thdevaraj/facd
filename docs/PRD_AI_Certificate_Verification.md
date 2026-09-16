# Product Requirements Document (PRD)
## AI-Based Detection of Fake or Manipulated Academic Certificates

**Version:** 1.0
**Date:** September 15, 2026
**Status:** Draft

---

## 1. Overview

### 1.1 Product Summary
The product is an AI-based academic certificate authenticity assessment platform that allows institutions, recruiters, and verification bodies to upload a certificate (image or PDF) and receive an automated authenticity/risk assessment. The system combines OCR, computer vision, image forensics, and machine learning to detect signs of digital manipulation and inconsistencies in certificate data, producing an interpretable risk score and verification report rather than a binary genuine/fake verdict.

### 1.2 Problem Statement
Manual certificate verification is slow, resource-intensive, and increasingly unreliable against sophisticated digital editing tools that can alter names, grades, dates, certificate numbers, signatures, and seals. Institutions, employers, and admissions offices lack an accessible, automated first-pass screening tool to flag certificates that warrant deeper investigation.

### 1.3 Goals
- Reduce manual verification effort for high-volume certificate checks (admissions, hiring, scholarships).
- Provide an interpretable, evidence-based risk score rather than an opaque pass/fail decision.
- Surface specific suspicious regions/fields so a human reviewer can quickly verify.
- Support template/record matching where institutional data is available, and fall back to general forensic analysis when it isn't.

### 1.4 Non-Goals
- The system does not claim legal or absolute proof of forgery/authenticity.
- It is not a replacement for institutional verification (e.g., direct confirmation with issuing bodies) — it is a decision-support/triage tool.
- It does not handle certificate *issuance* — only verification of already-issued documents.

---

## 2. Target Users & Personas

| Persona | Description | Primary Need |
|---|---|---|
| **University Admissions Officer** | Processes hundreds of applicant transcripts/certificates per cycle | Fast bulk screening, flag suspicious documents for manual review |
| **Corporate HR/Recruiter** | Verifies degree certificates for job candidates | Quick single-document check with clear explanation |
| **Scholarship/Grant Body** | Verifies academic records before disbursing funds | Auditable report per applicant |
| **Institution Registrar (Data Provider)** | Owns the source-of-truth records/templates | Ability to register templates/records for comparison |
| **System Administrator** | Manages platform, users, and audit logs | Access control, usage monitoring, compliance |

---

## 3. User Stories

1. As an admissions officer, I want to upload a certificate and get a risk score within seconds, so I can prioritize which applications need manual review.
2. As a recruiter, I want to see *why* a certificate was flagged (e.g., font mismatch, altered date field), so I can make an informed decision.
3. As a registrar, I want to upload our institution's official certificate templates, so the system can compare submissions against the authentic layout.
4. As an admin, I want to view an audit trail of all verifications performed, so we remain compliant with data-handling policies.
5. As a bulk user, I want to upload multiple certificates at once (batch mode), so I can screen an entire applicant cohort efficiently.
6. As any user, I want a downloadable verification report (PDF), so I can retain it as documentation of the check performed.

---

## 4. Functional Requirements (Product-Level)

### 4.1 Document Ingestion
- FR-1: Accept certificate uploads in JPG, PNG, and PDF formats.
- FR-2: Support single-document and batch (multi-document) uploads.
- FR-3: Validate file size/format and reject unsupported/corrupted files with clear error messaging.

### 4.2 Preprocessing
- FR-4: Automatically apply resizing, noise reduction, contrast enhancement, normalization, and perspective correction before analysis.
- FR-5: Allow the user to preview the preprocessed image before analysis (optional).

### 4.3 Information Extraction (OCR)
- FR-6: Extract structured fields: student name, register/roll number, course/program, marks/grades, dates, certificate/serial number, issuing institution.
- FR-7: Display extracted fields to the user with confidence scores per field.
- FR-8: Allow manual correction of misread OCR fields (human-in-the-loop).

### 4.4 Consistency & Forensic Analysis
- FR-9: Run text-consistency checks (e.g., date logic, grade-format validity, known institution naming).
- FR-10: Run image-forensic analysis to detect tampering signs (copy-paste regions, font/spacing anomalies, compression artifacts, layout misalignment, seal/signature irregularities).
- FR-11: Compare against a registered institutional template, when available.
- FR-12: Compare extracted data against stored institutional records, when available (record match/mismatch).

### 4.5 Scoring & Reporting
- FR-13: Combine all analysis signals into a single authenticity/risk score (e.g., 0–100 or Low/Medium/High risk band).
- FR-14: Generate a human-readable report showing: overall score, per-field findings, flagged/suspicious regions (visually highlighted on the certificate image), and contributing factors.
- FR-15: Allow the report to be exported/downloaded (PDF).
- FR-16: Store verification history per user/organization for later retrieval.

### 4.6 Administration
- FR-17: Role-based access (Admin, Institution/Registrar, Verifier/Reviewer).
- FR-18: Template and record management interface for registrars.
- FR-19: Usage dashboard/analytics for admins (volume, flagged rate, etc.).

---

## 5. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Single-certificate analysis should complete within a target time (e.g., under 15–30 seconds) |
| Scalability | Support batch processing of at least 100 documents per job |
| Availability | Web interface targeted at high uptime for institutional use during peak admission/hiring cycles |
| Security | Encrypted storage and transmission of uploaded documents and extracted personal data |
| Privacy | Compliance with applicable data-protection norms (e.g., minimal retention, consent for storage) |
| Usability | Non-technical staff (admissions/HR) should be able to use the tool without training |
| Explainability | Every risk score must be accompanied by human-interpretable reasons, not a black-box number |
| Portability | Web-based, accessible from standard browsers without special plugins |

---

## 6. Scope

### 6.1 In Scope (Phase 1 / Academic Project Scope)
- Web-based upload and analysis interface.
- OCR-based field extraction for common certificate formats.
- Image-forensic tampering detection.
- ML/DL-based classification model trained on genuine and synthetically manipulated samples.
- Risk-score generation and interpretable report.
- Basic template/record comparison (where sample institutional data is provided).
- Evaluation using accuracy, precision, recall, F1-score, and confusion matrix on a controlled dataset.

### 6.2 Out of Scope (Phase 1)
- Real-time integration with external/national degree-verification registries.
- Blockchain-based certificate issuance or verification.
- Legal certification of results (the tool is advisory, not a legal authority).
- Multi-language OCR beyond the primary language(s) targeted in the initial dataset.
- Mobile native applications (web-responsive only in Phase 1).

---

## 7. Success Metrics

- **Model performance:** Accuracy, Precision, Recall, F1-score, and confusion matrix on held-out genuine vs. manipulated test data (target thresholds to be defined during evaluation phase).
- **Usability:** Time taken by a reviewer to reach a decision, with vs. without the tool (target: significant reduction).
- **Adoption (if piloted):** Number of certificates processed, number of institutions/organizations onboarded.
- **Explainability quality:** Reviewer agreement rate with system-flagged reasons (qualitative feedback).

---

## 8. Assumptions & Constraints

- A labeled dataset of genuine and synthetically manipulated certificates is available or can be constructed for training/evaluation.
- Institutional templates/records, when used, are provided voluntarily by the institution and are assumed accurate.
- The system is a decision-support tool; final authenticity determination remains a human/institutional responsibility.
- Initial scope targets certificates in a defined structural format (e.g., typical Indian academic mark-sheets/degree certificates) rather than arbitrary global formats.

---

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Limited/imbalanced training data for manipulated samples | Poor model generalization | Use synthetic manipulation generation + data augmentation |
| False positives flagging genuine certificates | Loss of trust in tool | Present risk scores with confidence + explanation, not binary verdicts |
| OCR errors on low-quality scans | Incorrect field extraction | Preprocessing pipeline + human-in-the-loop correction |
| Sophisticated forgeries evading forensic checks | Missed detections | Combine multiple independent signal sources (text + visual + template) |
| Data privacy concerns with storing certificates | Compliance risk | Encryption, access control, defined retention policy |

---

## 10. Milestones (Indicative, Academic Project Timeline)

1. **Phase 1:** Requirements finalization, dataset collection/synthesis, preprocessing pipeline.
2. **Phase 2:** OCR extraction module + text-consistency checks.
3. **Phase 3:** Image-forensics module + ML/DL classification model.
4. **Phase 4:** Score fusion, report generation, web interface integration.
5. **Phase 5:** Evaluation (accuracy/precision/recall/F1/confusion matrix), documentation, final demo.
