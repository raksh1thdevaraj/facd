# Requirements & Test Traceability Matrix

**Audit Status:** 43/43 Requirements Verified (100.0%)

| Req ID | Description | Phase | Test Cases | Test File | Status |
|---|---|---|---|---|---|
| `FR-ING-01` | Multi-format certificate document ingestion (JPG, PNG, PDF) | Phase 03 | TC-ING-01, TC-ING-02 | `test_ingestion_api.py` | ✅ PASSED |
| `FR-ING-02` | File format, dimensions, and size limit validation | Phase 03 | TC-ING-03, TC-ING-04 | `test_ingestion_validator.py` | ✅ PASSED |
| `FR-ING-03` | Strict rejection and logging of corrupted/unsupported files | Phase 03 | TC-ING-05 | `test_ingestion_api.py` | ✅ PASSED |
| `FR-ING-04` | Batch certificate upload support | Phase 03 | TC-ING-06 | `test_ingestion_service.py` | ✅ PASSED |
| `FR-PRE-01` | Adaptive resolution scaling and DPI normalization | Phase 04 | TC-PRE-01 | `test_preprocessing_pipeline.py` | ✅ PASSED |
| `FR-PRE-02` | Document denoising and background artifact suppression | Phase 04 | TC-PRE-02 | `test_contrast_enhancer.py` | ✅ PASSED |
| `FR-PRE-03` | Contrast normalization and binarization | Phase 04 | TC-PRE-03 | `test_binarizer.py` | ✅ PASSED |
| `FR-PRE-04` | Automatic deskewing and perspective rectification | Phase 04 | TC-PRE-04, TC-PRE-05 | `test_deskewer.py` | ✅ PASSED |
| `FR-PRE-05` | PDF vector-to-raster conversion via pypdfium2/poppler | Phase 04 | TC-PRE-06 | `test_pdf_rasterizer.py` | ✅ PASSED |
| `FR-OCR-01` | Structured field extraction from academic certificates | Phase 05 | TC-OCR-01, TC-OCR-02 | `test_field_extractors.py` | ✅ PASSED |
| `FR-OCR-02` | Character and field-level confidence scoring | Phase 05 | TC-OCR-03 | `test_confidence_evaluator.py` | ✅ PASSED |
| `FR-OCR-03` | Confidence threshold filtering and fallback degradation | Phase 05 | TC-OCR-04 | `test_ocr_service.py` | ✅ PASSED |
| `FR-OCR-04` | Printed and semi-structured text recognition support | Phase 05 | TC-OCR-05 | `test_ocr_engine.py` | ✅ PASSED |
| `FR-TXT-01` | Date chronological order and lifespan logic validation | Phase 06 | TC-TXT-01 | `test_logical_validator.py` | ✅ PASSED |
| `FR-TXT-02` | Grade, GPA, and marks formatting integrity validation | Phase 06 | TC-TXT-02 | `test_format_checker.py` | ✅ PASSED |
| `FR-TXT-03` | Institution name validation and fuzzy alias matching | Phase 06 | TC-TXT-03 | `test_text_consistency_service.py` | ✅ PASSED |
| `FR-TXT-04` | Certificate serial number regex format checking | Phase 06 | TC-TXT-04 | `test_format_checker.py` | ✅ PASSED |
| `FR-FOR-01` | Copy-move cloning detection using SIFT/ORB keypoints | Phase 07 | TC-FOR-01 | `test_copy_move_detector.py` | ✅ PASSED |
| `FR-FOR-02` | Font size, stroke width, and spacing anomaly detection | Phase 07 | TC-FOR-02 | `test_stroke_width_analyzer.py` | ✅ PASSED |
| `FR-FOR-03` | Error Level Analysis (ELA) JPEG compression forensics | Phase 07 | TC-FOR-03 | `test_ela_analyzer.py` | ✅ PASSED |
| `FR-FOR-04` | Baseline alignment and inter-token spacing validation | Phase 07 | TC-FOR-04 | `test_baseline_checker.py` | ✅ PASSED |
| `FR-FOR-05` | Institutional seal and official stamp presence/integrity check | Phase 07 | TC-FOR-05 | `test_seal_matcher.py` | ✅ PASSED |
| `FR-TPL-01` | Institutional master certificate template registration | Phase 08 | TC-TPL-01 | `test_template_registration.py` | ✅ PASSED |
| `FR-TPL-02` | Structural similarity (SSIM) & visual layout comparison | Phase 08 | TC-TPL-02 | `test_ssim_evaluator.py` | ✅ PASSED |
| `FR-TPL-03` | Authoritative student ground-truth record verification | Phase 08 | TC-TPL-03 | `test_record_verifier.py` | ✅ PASSED |
| `FR-TPL-04` | Graceful fallback when no institutional template exists | Phase 08 | TC-TPL-04 | `test_tier_classifier.py` | ✅ PASSED |
| `FR-ML-01` | Supervised tabular ML classification model (Random Forest/HistGBM) | Phase 09 | TC-ML-01 | `test_baseline_inference.py` | ✅ PASSED |
| `FR-ML-02` | Continuous authenticity probability and confidence scoring | Phase 09 | TC-ML-02 | `test_ml_service.py` | ✅ PASSED |
| `FR-ML-03` | Deep Learning visual CNN branch (EfficientNet-B0) | Phase 10 | TC-DL-01 | `test_visual_network.py` | ✅ PASSED |
| `FR-ML-04` | Model versioning and metadata logging in evaluation reports | Phase 09 | TC-ML-03 | `test_model_evaluation.py` | ✅ PASSED |
| `FR-SCR-01` | Weighted multimodal score fusion (Early / Late / Stacking) | Phase 11 | TC-FUS-01 | `test_score_fusion_service.py` | ✅ PASSED |
| `FR-SCR-02` | Categorical risk band mapping (AUTHENTIC, SUSPICIOUS, MANIPULATED) | Phase 11 | TC-FUS-02 | `test_verdict_engine.py` | ✅ PASSED |
| `FR-SCR-03` | Institutional veto override rules engine | Phase 11 | TC-FUS-03 | `test_veto_rules.py` | ✅ PASSED |
| `FR-SCR-04` | Visual explainability overlays and bounding box annotations | Phase 12 | TC-EXP-01 | `test_unified_overlay.py` | ✅ PASSED |
| `FR-SCR-05` | Cryptographically signed, downloadable PDF verification report | Phase 13 | TC-REP-01 | `test_report_service.py` | ✅ PASSED |
| `FR-USR-01` | Role-based access control (Admin, Verifier, Auditor, Public) | Phase 15 | TC-ADM-01 | `test_admin_endpoints.py` | ✅ PASSED |
| `FR-USR-02` | Historical verification query and multi-parameter filtering | Phase 17 | TC-ADM-02 | `test_admin_endpoints.py` | ✅ PASSED |
| `FR-USR-03` | System analytics and throughput metrics dashboard | Phase 17 | TC-ADM-03 | `test_admin_endpoints.py` | ✅ PASSED |
| `FR-USR-04` | Immutable security and operational audit logging | Phase 15 | TC-AUD-01 | `test_audit_logging.py` | ✅ PASSED |
| `NFR-01` | Verification Accuracy: Overall Accuracy >= 92%, F1 >= 0.92 | Phase 19 | TC-EVAL-01, TC-EVAL-02 | `test_evaluation_metrics.py` | ✅ PASSED |
| `NFR-02` | Batch processing throughput and concurrent load resilience | Phase 18 | TC-E2E-05 | `e2e/test_concurrent_load.py` | ✅ PASSED |
| `NFR-03` | End-to-end turnaround latency <= 15 seconds per certificate | Phase 18 | TC-E2E-01 | `e2e/test_full_genuine_flow.py` | ✅ PASSED |
| `NFR-04` | Fault tolerance and graceful degradation under partial failures | Phase 18 | TC-E2E-04 | `e2e/test_graceful_degradation.py` | ✅ PASSED |