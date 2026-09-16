# Implementation & Testing Documents
## AI-Based Detection of Fake or Manipulated Academic Certificates

**Version:** 1.0
**Date:** September 15, 2026
**Status:** Draft

This document consolidates the Test Plan, Test Cases Document, and Evaluation Report, building on the PRD, SRD, Design Documents, and ML/Data-Specific Documents already produced for this project.

---

# Part A: Test Plan

## A.1 Purpose
Defines the overall testing strategy for the system — what will be tested, at what level, using what environment and tools — to ensure all functional and non-functional requirements from the SRD are verified before final submission/demo.

## A.2 Testing Levels

| Level | Scope | Owner |
|---|---|---|
| Unit Testing | Individual functions/modules (OCR field mapper, forensic checks, score fusion logic, etc.) | Developer per module |
| Integration Testing | Interaction between modules (e.g., OCR → Text-Consistency → Score Fusion) | Dev team |
| System Testing | End-to-end pipeline: upload → report generation | QA / whole team |
| Model Evaluation Testing | ML classifier performance on held-out test set | ML component owner |
| Usability Testing | UI walkthroughs with a non-technical user (e.g., a peer acting as admissions officer) | UI owner |
| Regression Testing | Re-run core test cases after any module update/model retraining | Whole team |

## A.3 Test Environment

| Component | Setup |
|---|---|
| Backend | Local/staging server running API + processing workers |
| Database | Isolated test PostgreSQL instance (not production data) |
| Test Data | Dataset test split (Part A of ML/Data Docs) + a small set of manually curated edge-case files |
| Browsers | Chrome, Firefox (minimum) for UI testing |
| Model | Latest trained model version, tagged for the test run |

## A.4 Testing Tools (Suggested)

| Purpose | Tool |
|---|---|
| Unit/integration testing (Python) | `pytest` |
| API testing | Postman / `pytest` with `httpx` |
| UI testing (optional) | Manual walkthroughs, or Selenium/Playwright if automated |
| ML evaluation | scikit-learn metrics (`classification_report`, `confusion_matrix`) |
| Load/batch testing | Simple script uploading N documents concurrently |

## A.5 Entry & Exit Criteria

| | Criteria |
|---|---|
| **Entry** | All modules implemented and individually unit-tested; test dataset finalized; test environment set up |
| **Exit** | All critical/high-priority test cases pass; no open blocking defects; model evaluation metrics meet the minimum thresholds defined in Part C |

## A.6 Risk-Based Test Prioritization

| Priority | Focus Area | Rationale |
|---|---|---|
| Critical | Upload → Report generation (end-to-end happy path) | Core value proposition |
| Critical | ML classification correctness on test set | Determines credibility of the tool |
| High | OCR field extraction accuracy | Feeds every downstream module |
| High | Score fusion logic (correct weighting/combination) | Determines final output correctness |
| Medium | Template/record matching (optional module) | Only active when data available |
| Medium | Batch upload handling | Secondary use case |
| Low | Admin analytics dashboard | Supporting feature, not core pipeline |

---

# Part B: Test Cases Document

Each test case is mapped to a functional requirement ID from the SRD for traceability.

## B.1 Ingestion Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-ING-01 | FR-ING-01 | Upload valid JPG/PNG/PDF | Valid certificate file | File accepted, job created |
| TC-ING-02 | FR-ING-02 | Upload oversized file | File exceeding max size limit | Rejected with clear size-limit error |
| TC-ING-03 | FR-ING-03 | Upload corrupted file | Deliberately corrupted image | Rejected with clear error message, no crash |
| TC-ING-04 | FR-ING-04 | Batch upload | 10 certificates at once | All 10 accepted, individual job IDs created |

## B.2 Preprocessing Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-PRE-01 | FR-PRE-01–03 | Preprocess low-quality scan | Noisy, low-contrast image | Output image visibly cleaner; OCR confidence improves vs. raw input |
| TC-PRE-02 | FR-PRE-04 | Skewed photo correction | Certificate photographed at an angle | Output image deskewed/aligned |
| TC-PRE-03 | FR-PRE-05 | Multi-page PDF input | 2-page PDF certificate | Each page rasterized and processed separately |

## B.3 OCR Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-OCR-01 | FR-OCR-01 | Extract all key fields | Clear genuine certificate | Name, register number, course, marks, dates, cert number all extracted correctly |
| TC-OCR-02 | FR-OCR-02 | Confidence scoring | Certificate with one blurry field | Blurry field shows lower confidence than clear fields |
| TC-OCR-03 | FR-OCR-03 | Manual correction flow | Low-confidence field flagged | User can edit field; corrected value used downstream |

## B.4 Text-Consistency Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-TXT-01 | FR-TXT-01 | Invalid date logic | Issue date before enrollment date | Flagged as inconsistency |
| TC-TXT-02 | FR-TXT-02 | Invalid grade format | Grade outside expected scheme (e.g., "Z+") | Flagged as anomaly |
| TC-TXT-03 | FR-TXT-03 | Unknown institution name | Institution name not matching any known record | Flagged for review |

## B.5 Forensics Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-FOR-01 | FR-FOR-01 | Clone/copy-paste detection | Synthetically cloned region sample | Cloned region correctly flagged with bounding box |
| TC-FOR-02 | FR-FOR-02 | Font/spacing anomaly | Sample with mismatched font in one field | Anomaly detected in that field |
| TC-FOR-03 | FR-FOR-03 | Compression artifact detection | Sample with locally re-saved region | ELA-style check flags the edited region |
| TC-FOR-04 | FR-FOR-04 | Layout misalignment | Sample with shifted field position | Alignment deviation score above threshold |
| TC-FOR-05 | FR-FOR-05 | Signature/seal tamper | Sample with swapped signature | Irregularity flagged in signature region |
| TC-FOR-06 | — | Genuine sample (negative control) | Unaltered genuine certificate | No forensic flags raised (or only low-severity/expected noise) |

## B.6 Template/Record Matching Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-TPL-01 | FR-TPL-01 | Register template | Upload institution template | Template stored and linked to institution |
| TC-TPL-02 | FR-TPL-02 | Template match — genuine | Genuine certificate matching registered template | High similarity score, status "match" |
| TC-TPL-03 | FR-TPL-02 | Template match — altered layout | Certificate with shifted layout | Lower similarity score, status "mismatch" |
| TC-TPL-04 | FR-TPL-03 | Record verification | Certificate fields vs. stored record (matching) | Status "record match" |
| TC-TPL-05 | FR-TPL-04 | No template available | Certificate from unregistered institution | Module skipped gracefully; pipeline continues |

## B.7 ML/DL Classification Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-ML-01 | FR-ML-01 | Classify genuine sample | Genuine test-set certificate | Low manipulation probability |
| TC-ML-02 | FR-ML-01 | Classify manipulated sample | Manipulated test-set certificate | High manipulation probability |
| TC-ML-03 | FR-ML-04 | Model version logging | Any prediction | Model version recorded with prediction |
| TC-ML-04 | FR-ML-02 | Explanation output | Manipulated sample | Top contributing factors returned (non-empty) |

## B.8 Score Fusion & Reporting Module

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-SCR-01 | FR-SCR-01–02 | Fused score computation | Sample with mixed signals (1 forensic flag, ML score 0.3) | Final score/band reflects weighted combination, not just one signal |
| TC-SCR-02 | FR-SCR-03 | Report content completeness | Any processed certificate | Report includes score, findings list, contributing factors |
| TC-SCR-03 | FR-SCR-04 | Region highlighting | Certificate with flagged forensic region | Flagged region visually highlighted in report image |
| TC-SCR-04 | FR-SCR-05 | PDF export | Any generated report | Downloadable PDF matches on-screen report content |

## B.9 User & Access Management

| TC ID | Requirement | Test Description | Input | Expected Result |
|---|---|---|---|---|
| TC-USR-01 | FR-USR-01 | Role-based access | Verifier attempts to access admin dashboard | Access denied |
| TC-USR-02 | FR-USR-02 | Verification history | User views past uploads | History list matches actual past verifications |
| TC-USR-03 | FR-USR-03 | Admin analytics | Admin views dashboard | Correct counts of processed/flagged certificates shown |
| TC-USR-04 | FR-USR-04 | Audit logging | Any user action (upload, view, export) | Corresponding audit log entry created |

## B.10 Non-Functional Test Cases

| TC ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TC-NFR-01 | NFR-01 | Single-certificate latency | End-to-end analysis completes within target time (e.g., ≤30s) |
| TC-NFR-02 | NFR-02 | Batch scalability | 100-document batch job completes without failure |
| TC-NFR-03 | NFR-03 | Graceful failure on bad input | Malformed file does not crash the system; clean error returned |
| TC-NFR-04 | NFR-04 | Data encryption | Uploaded files encrypted in transit (HTTPS) and at rest |
| TC-NFR-05 | NFR-06 | Usability walkthrough | Non-technical test user completes upload-to-report flow without assistance |

---

# Part C: Evaluation Report (Template)

> This section is a **template/structure** to be filled in once the model is trained and tested — it defines exactly what results need to be captured and how they should be presented for the final project report.

## C.1 Evaluation Setup

| Item | Value |
|---|---|
| Test set size | *(to be filled — e.g., N genuine + N manipulated samples)* |
| Model version evaluated | *(e.g., v1.0)* |
| Classification threshold used | *(e.g., 0.5 probability cutoff)* |
| Hardware used | *(e.g., CPU/GPU spec)* |

## C.2 Overall Performance Metrics

| Metric | Result |
|---|---|
| Accuracy | *(to be filled)* |
| Precision | *(to be filled)* |
| Recall | *(to be filled)* |
| F1-score | *(to be filled)* |

## C.3 Confusion Matrix (Template)

|  | Predicted: Genuine | Predicted: Manipulated |
|---|---|---|
| **Actual: Genuine** | TN = ___ | FP = ___ |
| **Actual: Manipulated** | FN = ___ | TP = ___ |

## C.4 Per-Manipulation-Type Detection Rate

| Manipulation Type | Recall (Detection Rate) |
|---|---|
| Name altered | *(to be filled)* |
| Marks altered | *(to be filled)* |
| Date altered | *(to be filled)* |
| Certificate number altered | *(to be filled)* |
| Signature altered | *(to be filled)* |
| Seal altered | *(to be filled)* |

## C.5 Ablation Study

| Model Variant | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Tabular-only (rule/forensic features) | | | | |
| Visual-only (CNN on image) | | | | |
| Fused (tabular + visual) | | | | |

*Purpose: demonstrates whether combining signals genuinely improves detection over any single signal source — directly supports the PRD's justification for a multi-signal fusion approach.*

## C.6 Error Analysis
- **False positives (genuine flagged as manipulated):** *(list example cases and likely cause — e.g., poor scan quality, unusual but legitimate formatting)*
- **False negatives (manipulated missed):** *(list example cases and likely cause — e.g., very subtle edits, manipulation type underrepresented in training data)*

## C.7 Usability Feedback Summary
- Time-to-decision with vs. without the tool *(qualitative/quantitative observation from usability testing)*
- Reviewer agreement with system-flagged reasons *(from Part A.6 usability testing)*

## C.8 Conclusions & Limitations
- Summary of how well the system meets the success metrics defined in the PRD (Section 7).
- Known limitations (e.g., dataset size, format coverage, subtlety of undetected forgeries).
- Recommendations for future improvement (e.g., expand dataset, add more institution templates, active-learning loop from reviewer corrections).

---

## D. Traceability Note
Every test case above is mapped to its corresponding SRD functional requirement ID, and the Evaluation Report structure directly reflects the Evaluation Plan defined in SRD Section 9 and the Success Metrics defined in PRD Section 7. Once filled in with actual results, this document (Part C) becomes a core section of the Final Project Report.
