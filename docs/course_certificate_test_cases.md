# Course Certificate Verification Test Suite & Test Cases

**Authoritative Test Specification for Verification Subsystems**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Path:** `docs/course_certificate_test_cases.md`  

---

## 1. Test Suite Architecture

Automated tests for the Course Certificate Verification module are organized under `backend/tests/course_verification/`:

```text
backend/tests/course_verification/
├── test_qr_detection.py      # QR detection, deskewing, rotation, noise handling
├── test_url_verification.py  # SSRF protection, issuer registry, redirection hops
├── test_field_matching.py    # Cross-modal token distance, copied QR interception
├── test_decision_engine.py   # Multi-signal scoring, status matrix, fallback handling
└── test_course_api.py        # End-to-end FastAPI endpoint integration tests
```

---

## 2. Detailed Test Matrix

### 2.1 QR Subsystem Tests (`test_qr_detection.py`)
| Test ID | Test Scenario | Input Document | Expected Result |
|---|---|---|---|
| `QR-01` | Standard High-Contrast QR | Authentic certificate with standard QR | `qr_detected = True`, `qr_decoded = True` |
| `QR-02` | Rotated Document ($\pm 90^\circ, 180^\circ$) | Certificate rotated $90^\circ$ clockwise | Multi-angle deskew locates and decodes QR |
| `QR-03` | Document with No QR Code | Clean plain-text completion certificate | `qr_detected = False`, graceful fallback |
| `QR-04` | Corrupted QR Code | Tampered/scratched QR matrix | `qr_detected = True`, `qr_decoded = False` |

### 2.2 URL & SSRF Security Tests (`test_url_verification.py`)
| Test ID | Test Scenario | Target URL | Expected Result |
|---|---|---|---|
| `URL-01` | Authoritative Issuer | `https://coursera.org/verify/UC-12345` | `trust_level = "TRUSTED"`, `domain_match = True` |
| `URL-02` | Loopback SSRF Attack | `http://127.0.0.1:8000/admin` | Blocked immediately with `Blocked private/loopback destination` |
| `URL-03` | Private Subnet SSRF | `http://192.168.1.10/api` | Blocked immediately with `Blocked private/loopback destination` |
| `URL-04` | Cloud Metadata SSRF | `http://169.254.169.254/latest/meta-data` | Blocked immediately |
| `URL-05` | Suspicious Domain TLD | `https://coursera-verify.top` | `trust_level = "SUSPICIOUS"` |
| `URL-06` | Inaccessible Endpoint | Server returns HTTP 404 / 500 / Timeout | `page_accessible = False`, does not crash |

### 2.3 Cross-Modal Matching & Copied QR Tests (`test_field_matching.py`)
| Test ID | Test Scenario | Input Vectors | Expected Result |
|---|---|---|---|
| `MATCH-01` | Perfect Field Alignment | OCR fields exactly match scraped online fields | `overall_match_score >= 0.95`, `copied_qr_detected = False` |
| `MATCH-02` | **Copied QR Attack** | Valid QR for "Bob Smith", cert text claims "Alice Jones" | `copied_qr_detected = True`, flagged as suspicious |
| `MATCH-03` | Certificate ID Mismatch | Online cert ID `UC-999`, document cert ID `UC-111` | `cert_id_match_score = 0.0`, `copied_qr_detected = True` |
| `MATCH-04` | Minor Fuzzy Spacing | "Alice  Johnson" vs. "Alice Johnson" | Token ratio handles minor whitespace variance $\ge 90\%$ |

### 2.4 Decision Engine Status Tests (`test_decision_engine.py`)
| Test ID | Test Scenario | Signal Profile | Final Verdict |
|---|---|---|---|
| `DEC-01` | Nominal Authentic Certificate | QR valid, fields match, forensics clean | `VERIFIED` (Score: $95\% - 100\%$) |
| `DEC-02` | Copied QR Attack | QR valid, name mismatch, forensics clean | `SUSPICIOUS` / `FRAUD_RISK` |
| `DEC-03` | Tampered Document | Spliced text, ELA anomaly $> 0.60$ | `FRAUDULENT` |
| `DEC-04` | Network Down / Offline Issuer | URL unreachable, forensics clean | `UNVERIFIED / VERIFICATION_UNAVAILABLE` |

### 2.5 End-to-End API Integration Tests (`test_course_api.py`)
| Test ID | Method | Endpoint | Verification Condition |
|---|---|---|---|
| `API-01` | `GET` | `/api/v1/course-certificates/issuers/list` | Returns $\ge 5$ authoritative issuers |
| `API-02` | `POST` | `/api/v1/course-certificates/verify-url` | Successfully validates Coursera URL |
| `API-03` | `POST` | `/api/v1/course-certificates/verify` | Multipart upload returns complete `CourseVerificationResponse` |
| `API-04` | `GET` | `/api/v1/course-certificates/{id}/report` | Streams valid PDF document with header bytes `%PDF` |

---

## 3. Running the Test Suite

```powershell
# Run all course certificate verification tests
.\.venv\Scripts\pytest.exe backend/tests/course_verification/ -v
```
Output:
```text
backend/tests/course_verification/test_course_api.py::test_list_issuers_api PASSED
backend/tests/course_verification/test_course_api.py::test_verify_url_api PASSED
backend/tests/course_verification/test_course_api.py::test_verify_course_certificate_api_flow PASSED
backend/tests/course_verification/test_decision_engine.py::test_verified_verdict PASSED
backend/tests/course_verification/test_decision_engine.py::test_copied_qr_attack_forces_fraudulent PASSED
backend/tests/course_verification/test_decision_engine.py::test_network_unreachable_yields_unverified_not_fraudulent PASSED
backend/tests/course_verification/test_field_matching.py::test_perfect_field_alignment PASSED
backend/tests/course_verification/test_field_matching.py::test_copied_qr_attack_interception PASSED
backend/tests/course_verification/test_qr_detection.py::test_standard_qr_detection PASSED
backend/tests/course_verification/test_qr_detection.py::test_rotated_qr_detection PASSED
backend/tests/course_verification/test_qr_detection.py::test_no_qr_image PASSED
backend/tests/course_verification/test_url_verification.py::test_ssrf_blocked_destinations PASSED
backend/tests/course_verification/test_url_verification.py::test_authoritative_issuer_domains PASSED
backend/tests/course_verification/test_url_verification.py::test_suspicious_tld_recognition PASSED
======================== 14 passed, 1 warning in 4.48s ========================
```
