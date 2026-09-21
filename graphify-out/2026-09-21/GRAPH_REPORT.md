# Graph Report - AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates  (2026-09-21)

## Corpus Check
- 432 files · ~370,571 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3859 nodes · 7826 edges · 206 communities (170 shown, 23 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 704 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9c0c91f4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- institutions.py
- IngestionValidator
- test_docker_builds.py
- OCRService
- devDependencies
- ocr/__init__.py
- PerspectiveWarper
- FormatChecker
- compilerOptions
- AnomalousRegion
- ResultsPage.tsx
- to_grayscale
- admin.ts
- Deskewer
- DESIGN.md
- generate_dataset.py
- MetadataExtractor
- generate_all_templates
- TokenBuilder
- test_dataset_synthesis.py
- InstitutionRecordModel
- Software Requirements Document (SRD / SRS)
- UploadPage.tsx
- test_evaluation_metrics.py
- B.1 Module Breakdown
- schemas/certificate.py
- test_health.py
- Master Development Plan
- react
- PreprocessingService
- preprocessing/__init__.py
- PDFRasterizer
- compilerOptions
- BaselineMLService
- CertificateVisualCNN
- 8. Implementation Chips
- Part B: Test Cases Document
- Part A: Dataset Description Document
- test_jwt_tokens.py
- .verify
- GradCAMExplainer
- UserRole
- TextConsistencyService
- validate_dataset
- schemas/__init__.py
- AdaptiveBinarizer
- 8. Implementation Chips
- CoordinateMapper
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- print_dataset_stats
- test_field_extractors.py
- create_dataloaders
- .analyze
- 8. Implementation Chips
- entrypoint.sh
- 8. Implementation Chips
- test_coverage_and_reports.py
- Environment & Toolchain Specification
- database.py
- chart_generator.py
- Forensics & Algorithm Specification
- package.json
- index.ts
- ForensicConfig
- vite.config.ts
- AuthContext.tsx
- report_writer.py
- Scientific Model Evaluation & Benchmark Report (Phase 19)
- PreprocessingResult
- test_baseline_inference.py
- ai-certificate-verification-backend
- NoiseReductionFilter
- .run_pipeline
- CertificateModel
- Pipeline Data Contracts & Inter-Module Interfaces
- Dataset & Synthesis Engine Specification
- PixelBoundingBox
- CLAHEEnhancer
- deployment/__init__.py
- test_ocr_engine.py
- Test Fixtures & Mock Data Specification
- NumberedCanvas
- Product Requirements Document (PRD)
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- TierStatus
- phase-01-project-foundation.md
- dependencies
- 8. Implementation Chips
- 8. Implementation Chips
- HistoryAndAdmin.test.tsx
- WeightedLateFusion
- list_audit_logs
- backup_db.sh
- OCRToken
- Settings
- run_step
- deploy.sh
- 2. Technology Stack Breakdown
- ablation_runner.py
- docker_clean.sh
- tests/conftest.py
- .extract_tokens
- init_ssl.sh
- AI Developer Rules of Engagement & Execution Guidelines
- run_ablation_study
- AI-Based Detection of Fake or Manipulated Academic Certificates
- Environment Configuration & Secrets Specification
- scripts
- pipeline_orchestrator.py
- schemas/pipeline.py
- StudentNameExtractor
- compute_template_ssim
- CertificateIdExtractor
- .process
- BoundingBox
- Abstract
- forensics/__init__.py
- match_seal_and_logo
- .run
- config.py
- restore_db.sh
- TextLine
- AppException
- scripts/smoke_test.sh
- rules/graphify.md
- reports.py
- ingestion/service.py
- workflows/graphify.md
- explainability.py
- template_matching/service.py
- run_all_tests.sh script
- DateExtractor
- smoke_test.sh
- db_session
- test_template_endpoints.py
- TRACEABILITY_MATRIX.md
- generated_templates
- StackingMetaClassifier
- @testing-library/jest-dom
- TabularFeatureExtractor
- evaluation/__init__.py
- backend/scripts/__init__.py
- evaluate_baseline_model
- TabularDataPreprocessor
- generate_synthetic_feature_dataset
- get_inference_transforms
- export_model.py
- MultimodalFusionMLP
- ForensicAnalysisResult
- .extract_from_pil
- .predict_batch
- MLInferenceOutput
- .classify_certificate
- InstitutionModel
- FastAPI
- VerificationReportModel
- InstitutionExtractor
- 001_initial_schema.py
- FullVerificationReport
- ScoreFusionService
- .__init__
- .to_pipeline_output
- certificates.py
- e2e/conftest.py
- analytics_service.py
- create_dataset_splits
- ELAAnalyzer
- endpoints/auth.py
- create_access_token
- test_concurrent_multi_user_uploads
- test_database_migrations.py
- test_institution_endpoints_lifecycle
- test_manipulated_certificate_e2e_workflow
- test_genuine_certificate_e2e_workflow
- .log_action
- .analyze
- test_graceful_degradation_under_partial_failure
- VerificationVerdict
- CopyMoveDetector
- test_multipage_pdf_workflow

## God Nodes (most connected - your core abstractions)
1. `OCRToken` - 86 edges
2. `TextLine` - 80 edges
3. `CertificateFields` - 74 edges
4. `BoundingBox` - 64 edges
5. `PixelBoundingBox` - 62 edges
6. `TokenBuilder` - 49 edges
7. `ExtractedField` - 47 edges
8. `AnomalousRegion` - 44 edges
9. `FullVerificationReport` - 43 edges
10. `AnomalyType` - 43 edges

## Surprising Connections (you probably didn't know these)
- `BenchmarkRunner` --uses--> `WeightedLateFusion`  [INFERRED]
  ml/evaluation/benchmark_runner.py → backend/app/modules/score_fusion/late_fusion.py
- `evaluate_multimodal_models()` --uses--> `WeightedLateFusion`  [INFERRED]
  ml/scripts/evaluate_multimodal.py → backend/app/modules/score_fusion/late_fusion.py
- `evaluate_multimodal_models()` --uses--> `StackingMetaClassifier`  [INFERRED]
  ml/scripts/evaluate_multimodal.py → backend/app/modules/score_fusion/meta_classifier.py
- `train_meta_classifier()` --uses--> `StackingMetaClassifier`  [INFERRED]
  ml/scripts/train_meta_classifier.py → backend/app/modules/score_fusion/meta_classifier.py
- `evaluate_visual_model()` --uses--> `CertificateVisualCNN`  [INFERRED]
  ml/scripts/evaluate_visual_cnn.py → backend/app/modules/visual_model/network.py

## Import Cycles
- None detected.

## Communities (206 total, 23 thin omitted)

### Community 0 - "institutions.py"
Cohesion: 0.16
Nodes (22): bulk_import_records(), get_institution(), list_institutions(), get, post, Request, Session, UploadFile (+14 more)

### Community 1 - "IngestionValidator"
Cohesion: 0.13
Nodes (32): CorruptedFileError, EmptyFileError, FileTooLargeError, InsufficientResolutionError, InvalidFileError, Uploaded file MIME type or magic signature is not allowed., Uploaded file exceeds the maximum allowed upload size., Uploaded file has zero bytes. (+24 more)

### Community 2 - "test_docker_builds.py"
Cohesion: 0.17
Nodes (11): Docker Container Builds & Compose Configuration Tests (CHIP DEP-11 / TC-DEP-01,…, Verify production Docker Compose defines reverse proxy gateway and isolates…, Verify backend Dockerfile defines multi-stage build and non-root execution (TC-…, Verify frontend Dockerfile defines multi-stage build to Nginx Alpine (TC-…, Verify frontend Nginx configuration supports SPA routing and caching (FR-…, Verify Docker Compose orchestrates all 4 core services with health checks (TC-…, test_backend_dockerfile_syntax_and_structure(), test_docker_compose_production_override() (+3 more)

### Community 3 - "OCRService"
Cohesion: 0.12
Nodes (20): get_ocr_service(), OCRService, ndarray, Path, Run OCR and return canonical SPEC-02 OCROutput contract., FastAPI dependency injection provider for OCRService., Orchestrates optical character recognition, spatial layout reconstruction,…, Run complete OCR and structured field extraction pipeline for a certificate… (+12 more)

### Community 4 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, jsdom, postcss, tailwindcss, @testing-library/dom, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 5 - "ocr/__init__.py"
Cohesion: 0.08
Nodes (24): BaseOCREngine, ABC, ndarray, Path, Abstract interface defining the OCR detection and character recognition…, Name of the OCR engine backend (e.g., 'easyocr', 'pytesseract', 'mock')., Extract OCR tokens with bounding boxes and confidence scores from an image., EasyOCREngine (+16 more)

### Community 6 - "PerspectiveWarper"
Cohesion: 0.19
Nodes (14): find_document_corners(), four_point_transform(), order_points(), PerspectiveWarper, Any, ndarray, Detects document boundary corners and rectifies perspective distortion., Order 4 (x, y) coordinates consistently: top-left, top-right, bottom-right,… (+6 more)

### Community 7 - "FormatChecker"
Cohesion: 0.15
Nodes (12): FormatChecker, Detects text formatting irregularities, homoglyph character substitutions,…, Detect orphaned punctuation artifacts or invalid character repetitions., Inspect all tokens for homoglyphs, capitalization glitches, and punctuation…, Check for Cyrillic or unexpected scripts inserted into Latin words., Detect mid-word erratic casing such as 'cOMPUTER' or 'JoHn'., Detect homoglyph evasion when a Cyrillic character is embedded inside Latin…, Detect erratic casing anomaly inside a word like 'cOMPUTER'. (+4 more)

### Community 8 - "compilerOptions"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+12 more)

### Community 9 - "AnomalousRegion"
Cohesion: 0.12
Nodes (28): BaselineAlignmentAnalyzer, Detects vertical text displacement and baseline drift anomalies in lines of…, Fit baselines across text lines and identify tokens with abnormal vertical…, ConsistencyCheckItem, Combines individual typographical, spacing, formatting, and logical sub-scores…, Compute the weighted composite score, enforce veto penalties, and assemble…, ScoreAggregator, CharacterSpacingAnalyzer (+20 more)

### Community 10 - "ResultsPage.tsx"
Cohesion: 0.10
Nodes (29): CredentialsCard(), CredentialsCardProps, FindingsDossier(), FindingsDossierProps, SEVERITY_CONFIG, InteractiveViewer(), InteractiveViewerProps, ReportActions() (+21 more)

### Community 11 - "to_grayscale"
Cohesion: 0.23
Nodes (11): Any, ndarray, composite_alpha_on_white(), ensure_3channel(), ndarray, Ensure the image is a standard 3-channel BGR image array., Convert an arbitrary image array (RGBA, BGR, or Grayscale) to 2D uint8…, Convert image to CIE LAB color space. (+3 more)

### Community 12 - "admin.ts"
Cohesion: 0.14
Nodes (23): AuditDetailModal(), AuditDetailModalProps, TemplatePreviewModal(), TemplatePreviewModalProps, AdminDashboardPage(), AdminTab, AnalyticsOverview(), AuditLogsViewer() (+15 more)

### Community 13 - "Deskewer"
Cohesion: 0.20
Nodes (14): Deskewer, estimate_skew_angle(), Any, ndarray, Detects rotational skew and deskews certificate images., Detect document tilt angle within [-max_angle, +max_angle] degrees. Uses…, Rotate image by angle (in degrees) around center, expanding canvas to prevent…, rotate_image() (+6 more)

### Community 14 - "DESIGN.md"
Cohesion: 0.05
Nodes (41): 10. Responsive Breakpoint Strategy, 11. Frontend Component Architecture & Directory Layout, 12. Strict UI Implementation Rules for AI Coding Agents, 13. Screen Implementation Chips (Incremental Task Breakdown), 14. Requirements Traceability Matrix, 15. Global Acceptance Criteria & QA Checklist, 1.1 The Core Design Philosophy: "Minimal Enterprise", 1.2 Anti-AI-Slop Directives (Strict Prohibitions) (+33 more)

### Community 15 - "generate_dataset.py"
Cohesion: 0.16
Nodes (16): Verify genuine certificate rendering and bounding box calculation., test_genuine_certificate_rendering(), generate_dataset(), main(), Any, Path, Dataset Pipeline Orchestrator. Orchestrates the entire certificate synthesis…, Generate a balanced, labeled dataset of genuine and manipulated certificates. (+8 more)

### Community 16 - "MetadataExtractor"
Cohesion: 0.19
Nodes (15): MetadataExtractor, _parse_exif_date(), _parse_pdf_date(), Any, Path, Extract document metadata from PDF trailer and dictionary entries., Parse standard PDF date format, e.g. D:20240915123000+00'00'., Parse EXIF datetime string, e.g. '2024:09:15 12:30:00'. (+7 more)

### Community 17 - "generate_all_templates"
Cohesion: 0.17
Nodes (15): ImageDraw, create_guilloche_pattern(), draw_decorative_border(), generate_all_templates(), generate_seal_image(), generate_signature_image(), Any, Image (+7 more)

### Community 18 - "TokenBuilder"
Cohesion: 0.08
Nodes (40): Construct a TextLine from a list of horizontally sorted tokens., Utility factory to create a single OCRToken with exact geometry., Constructs canonical OCRToken objects from raw OCR engine outputs., TokenBuilder, FontSizeAnalyzer, Analyzes token bounding box heights to detect font size and scale mismatches., Categorize tokens into typography tiers based on line median heights., Identify tokens whose bounding box heights deviate anomalously from surrounding… (+32 more)

### Community 19 - "test_dataset_synthesis.py"
Cohesion: 0.16
Nodes (21): Verify text inpainting and replacement modification., Verify copy-move duplication operator., Verify localized JPEG quality degradation operator., test_copy_move_tampering(), test_inpaint_and_replace_tampering(), test_recompression_discrepancy(), apply_manipulation(), apply_recompression_discrepancy() (+13 more)

### Community 20 - "InstitutionRecordModel"
Cohesion: 0.07
Nodes (46): bulk_import_records(), create_record(), list_records(), Any, get, post, Session, UploadFile (+38 more)

### Community 21 - "Software Requirements Document (SRD / SRS)"
Cohesion: 0.05
Nodes (41): 10. Constraints & Limitations, 11.1 Traceability Note, 11.2 Related Document, 11. Appendix, 1.1 Purpose, 1.2 Scope, 1.3 Intended Audience, 1.4 Definitions & Abbreviations (+33 more)

### Community 22 - "UploadPage.tsx"
Cohesion: 0.12
Nodes (21): PipelineStepper(), PipelineStepperProps, STAGE_ICONS, ACCEPTED_EXTENSIONS, ACCEPTED_MIME_TYPES, FileDropzone(), FileDropzoneProps, FilePreview() (+13 more)

### Community 23 - "test_evaluation_metrics.py"
Cohesion: 0.10
Nodes (24): benchmark_results(), fixture, Unit & Benchmark Evaluation Metrics Test Suite (Phase 19 - CHIP TST-11).…, Load or run evaluation benchmark predictions on the held-out test split., TC-EVAL-01 & NFR-01: Verify overall system accuracy achieves >= 92.0%., TC-EVAL-02 & NFR-01: Verify overall system F1-score achieves >= 0.92., Verify system ROC-AUC achieves >= 0.95 on held-out test data., FR-TST-05: Proves multimodal score fusion outperforms single-branch… (+16 more)

### Community 24 - "B.1 Module Breakdown"
Cohesion: 0.05
Nodes (39): A.1 Purpose, A.2 Architectural Style, A.3 Component Overview, A.4 Suggested Technology Stack, A.5 Architecture Diagram (Deployment View), AI-Based Detection of Fake or Manipulated Academic Certificates, B.1.1 Ingestion Module, B.1.2 Preprocessing Module (+31 more)

### Community 25 - "schemas/certificate.py"
Cohesion: 0.28
Nodes (8): CertificateDetailResponse, CertificateListItem, CertificateUploadResponse, BaseModel, Pydantic V2 schemas for certificate upload, status polling, and verification…, Initial response returned upon certificate document upload., Summary item in paginated certificate history listings., Full detail view of an individual assessed certificate.

### Community 26 - "test_health.py"
Cohesion: 0.27
Nodes (9): TestClient, Verify GET /health returns valid health check payload., Verify GET /api/v1/health returns valid health check payload., Verify non-existent routes return 404., Verify GET / returns welcome payload and API information., test_404_not_found(), test_api_v1_health_endpoint(), test_root_endpoint() (+1 more)

### Community 27 - "Master Development Plan"
Cohesion: 0.06
Nodes (35): 10. Phase Summary Table, 11. Risk Mitigation, 12. Disclaimer, 1. Project Overview, 2. Final Architecture, 3.10 Development Tools, 3.1 Frontend, 3.2 Backend (+27 more)

### Community 28 - "react"
Cohesion: 0.19
Nodes (15): App(), Footer(), Navbar(), RoleGuard(), RoleGuardProps, SystemHealthBadge(), useAuth(), HomePage() (+7 more)

### Community 29 - "PreprocessingService"
Cohesion: 0.12
Nodes (21): PreprocessingArtifactManager, Path, UUID, Manages filesystem persistence of preprocessed images and audit artifacts., Save enhanced image, binarized image, and thumbnail for a certificate.…, Any, Execute diagnostic self-tests and performance benchmarks for the preprocessing…, run_preprocessing_diagnostics() (+13 more)

### Community 30 - "preprocessing/__init__.py"
Cohesion: 0.17
Nodes (14): BasePreprocessingStep, ABC, Human-readable identifier of the preprocessing step., Abstract Base Class for an atomic preprocessing pipeline transformation., PreprocessingPipeline, Sequential executor for registered preprocessing transformation steps., Register an additional transformation step., create_thumbnail() (+6 more)

### Community 31 - "PDFRasterizer"
Cohesion: 0.16
Nodes (21): EncryptedPdfError, PDFConversionError, PDF is password protected or encrypted., Failed to rasterize PDF document into image format., check_ingestion_health(), Any, Inspect the operational readiness of ingestion subsystem dependencies., is_poppler_installed() (+13 more)

### Community 32 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, types, include

### Community 33 - "BaselineMLService"
Cohesion: 0.06
Nodes (39): compute_local_contributions(), extract_feature_importances(), FeatureImportanceAnalyzer, plot_feature_importance(), Any, ndarray, Path, Feature importance analysis and local anomaly explanations for Phase 09.… (+31 more)

### Community 34 - "CertificateVisualCNN"
Cohesion: 0.08
Nodes (24): CertificateVisualCNN, Module, Tensor, Return the final convolutional layer of the backbone for Grad-CAM., Convolutional Neural Network for certificate visual manipulation…, Forward pass. Args: x: Input image tensor of shape (B, 3, H, W) Returns:…, Freeze all parameters in the convolutional backbone for Stage 1 fine-tuning., Unfreeze backbone parameters for Stage 2 fine-tuning. Args: top_blocks_only: If… (+16 more)

### Community 35 - "8. Implementation Chips"
Cohesion: 0.06
Nodes (33): 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure, 8. Implementation Chips (+25 more)

### Community 36 - "Part B: Test Cases Document"
Cohesion: 0.06
Nodes (30): A.1 Purpose, A.2 Testing Levels, A.3 Test Environment, A.4 Testing Tools (Suggested), A.5 Entry & Exit Criteria, A.6 Risk-Based Test Prioritization, AI-Based Detection of Fake or Manipulated Academic Certificates, B.10 Non-Functional Test Cases (+22 more)

### Community 37 - "Part A: Dataset Description Document"
Cohesion: 0.07
Nodes (28): A.1 Purpose, A.2 Data Sources, A.3 Dataset Composition (Indicative), A.4 Labeling Scheme, A.5 Synthetic Manipulation Generation Methodology, A.6 Data Quality Considerations, A.7 Privacy & Ethical Handling, AI-Based Detection of Fake or Manipulated Academic Certificates (+20 more)

### Community 38 - "test_jwt_tokens.py"
Cohesion: 0.19
Nodes (18): Clear all recorded failed attempts (primarily for testing and administrative…, reset_rate_limits(), get_password_hash(), Hash a plaintext password using bcrypt with 12 work factor rounds., _create_test_user(), Session, TestClient, Integration tests for JWT tokens, expiry, profiles, and rate limits (TC-USR-02,… (+10 more)

### Community 39 - ".verify"
Cohesion: 0.20
Nodes (9): load_precomputed_template_features(), ndarray, Load pre-computed keypoints coordinates and descriptors from compressed npz…, ndarray, Session, Execute dual-track template comparison and student record cross-verification.…, Session, TC-TMP-06: Register master template, save image, pre-compute features, and… (+1 more)

### Community 40 - "GradCAMExplainer"
Cohesion: 0.08
Nodes (20): GradCAMExplainer, device, ndarray, Path, Tensor, Grad-CAM (Gradient-weighted Class Activation Mapping) for visual explainability., Computes Grad-CAM heatmaps highlighting visual regions indicative of tampering., Compute Grad-CAM heatmap array of shape (H, W) normalized to [0.0, 1.0]. (+12 more)

### Community 41 - "UserRole"
Cohesion: 0.19
Nodes (13): Enforce that the authenticated user possesses one of the specified roles., require_role(), role_dependency(), is_role_authorized(), normalize_role(), Enum, str, Role-Based Access Control (RBAC) hierarchy and permissions. (+5 more)

### Community 42 - "TextConsistencyService"
Cohesion: 0.19
Nodes (10): CertificateFields, ndarray, Path, Run text consistency analysis and return canonical SPEC-02…, Orchestrates comprehensive text consistency, typographical forensics, and…, Run complete typographical forensics and logical consistency pipeline., TextConsistencyService, ndarray (+2 more)

### Community 43 - "validate_dataset"
Cohesion: 0.38
Nodes (6): main(), Any, Path, Dataset Validator. Performs comprehensive data integrity checks: 1. Verifies…, Validate dataset integrity and print detailed diagnostic report., validate_dataset()

### Community 44 - "schemas/__init__.py"
Cohesion: 0.10
Nodes (26): PredictionResult, Prediction result DTO summarizing baseline machine learning model inference., OCRResultDTO, High-level Data Transfer Object summarizing the OCR extraction results., Convert to canonical SPEC-02 OCROutput pipeline contract., OCROutput, Composite verification DTO containing visual, database, and tier assessment., Calculate a risk score on [0.0, 100.0] scale. (+18 more)

### Community 45 - "AdaptiveBinarizer"
Cohesion: 0.19
Nodes (10): AdaptiveBinarizer, Binarizes certificate image into crisp black-and-white for OCR ingestion., Path, UUID, Execute end-to-end preprocessing on an input certificate image. Saves derived…, create_document_with_text(), ndarray, Create a white document with crisp black text and background noise. (+2 more)

### Community 46 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (25): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+17 more)

### Community 47 - "CoordinateMapper"
Cohesion: 0.11
Nodes (17): CoordinateMapper, ndarray, PixelBoundingBox, Transforms bounding boxes and spatial points from processed space to raw image…, Scale and clamp processed bounding box to raw original image dimensions., Convert pixel bounding box on raw image to [0.0, 1.0] normalized coordinates., Convert normalized [0, 1] coordinates into pixel box and normalized box., Scale array of (N, 2) points from processed to raw resolution. (+9 more)

### Community 48 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (25): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+17 more)

### Community 49 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (25): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+17 more)

### Community 50 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (24): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+16 more)

### Community 51 - "print_dataset_stats"
Cohesion: 0.47
Nodes (5): main(), print_dataset_stats(), Path, Dataset Statistics Reporter. Computes and prints detailed statistics regarding…, Read metadata and print formatted summary tables.

### Community 52 - "test_field_extractors.py"
Cohesion: 0.25
Nodes (16): Find tokens strictly to the right of an anchor token on the same line., Filter lines whose vertical position falls within a normalized vertical band…, Analyzes 2D spatial layout of OCR tokens, segmenting them into lines and…, Group detected OCR tokens into horizontal text lines and sort in reading order., SpatialLayoutAnalyzer, _build_tokens_from_lines(), test_cert_id_and_qr_code_extractor(), test_date_extractor_various_formats() (+8 more)

### Community 53 - "create_dataloaders"
Cohesion: 0.08
Nodes (28): Unit tests for dataset loading and balanced sampling., Verify loading dataset from splits., Verify DataLoaders creation and batch extraction., test_certificate_dataset_loading(), test_create_dataloaders(), Dataset, CertificateImageDataset, create_dataloaders() (+20 more)

### Community 54 - ".analyze"
Cohesion: 0.40
Nodes (4): BoundingBox, ndarray, PixelBoundingBox, Extract high-pass noise residuals, compute block variances, and flag…

### Community 55 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (24): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+16 more)

### Community 57 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (24): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+16 more)

### Community 58 - "test_coverage_and_reports.py"
Cohesion: 0.12
Nodes (18): generate_markdown_matrix(), Any, Requirements & Test Case Traceability Matrix Verification Script (Phase 19).…, Audit test suite to confirm all requirement mapping targets exist., Format traceability audit into GitHub Flavored Markdown., verify_traceability(), benchmark_predictions(), fixture (+10 more)

### Community 59 - "Environment & Toolchain Specification"
Cohesion: 0.10
Nodes (19): 1. Purpose & Scope, 2.1 macOS (Darwin) Installation, 2.2 Linux / Ubuntu (Debian 12+ / Ubuntu 22.04 LTS) Installation, 2.3 Verification Commands, 2. System-Level Dependencies & Binaries, 3.1 Python Version, 3.2 Pinned `requirements.txt` / Dependency Specification, 3. Backend Python Environment (+11 more)

### Community 60 - "database.py"
Cohesion: 0.08
Nodes (35): get_current_user(), get_optional_current_user(), Session, FastAPI authentication and role-based authorization dependencies., Validate Bearer access token and resolve active user from database., Resolve user if a valid token is provided; otherwise returns None without…, FastAPI router for immutable compliance audit log inspection., decode_token() (+27 more)

### Community 61 - "chart_generator.py"
Cohesion: 0.25
Nodes (17): generate_ablation_chart(), generate_all_charts(), generate_all_evaluation_charts(), generate_category_breakdown_chart(), generate_comparative_roc_chart(), generate_confusion_matrix_chart(), generate_precision_recall_chart(), Any (+9 more)

### Community 62 - "Forensics & Algorithm Specification"
Cohesion: 0.12
Nodes (16): 1. Purpose, 2.1 Principle, 2.2 Algorithm & Mathematical Formulation, 2. Module A: Error Level Analysis (ELA), 3.1 Algorithm, 3. Module B: Copy-Move / Splicing Detection, 4.1 Principle, 4.2 Algorithm (+8 more)

### Community 63 - "package.json"
Cohesion: 0.12
Nodes (16): name, private, type, version, autoprefixer, clsx, jsdom, postcss (+8 more)

### Community 64 - "index.ts"
Cohesion: 0.12
Nodes (16): BoundingBox, CertificateFields, CheckStatus, ConsistencyCheckItem, ContributingFactor, ForensicsOutput, HealthCheckResponse, MLInferenceOutput (+8 more)

### Community 65 - "ForensicConfig"
Cohesion: 0.18
Nodes (11): NoiseAnalyzer, Analyzes high-frequency sensor noise residuals and local noise variance to…, ForensicConfig, BaseModel, Configuration parameters for Error Level Analysis, Copy-Move, and Noise…, TC-FOR-03: Detect sensor noise variance anomaly when a high-noise patch is…, Verify small or empty images do not raise exceptions., Verify that an image with uniform background noise yields noise score >= 0.90. (+3 more)

### Community 69 - "AuthContext.tsx"
Cohesion: 0.23
Nodes (11): AuthContext, AuthContextType, AuthProvider(), apiClient, failedQueue, authService, LoginCredentials, RegisterData (+3 more)

### Community 70 - "report_writer.py"
Cohesion: 0.21
Nodes (13): evaluate_categories(), format_category_table_markdown(), Any, Per-Category Forgery Performance Breakdown (CHIP TST-06). Evaluates detection…, Break down detection accuracy across forgery modalities., Format category breakdown into Markdown table., generate_evaluation_report(), generate_final_evaluation_report() (+5 more)

### Community 72 - "Scientific Model Evaluation & Benchmark Report (Phase 19)"
Cohesion: 0.14
Nodes (13): 1. Executive Summary, 2. Test Dataset Composition & Methodology, 3. Confusion Matrix & Error Classification, 4. Model Architecture Comparison (FR-TST-05), 5. Fine-Grained Forgery Modality Breakdown (FR-TST-04), 6. Subsystem Feature Ablation Study (FR-TST-06), 7. Latency and Throughput Profiling (NFR-03), 8. Conclusion & Defense Assertion (+5 more)

### Community 73 - "PreprocessingResult"
Cohesion: 0.24
Nodes (10): PreprocessingResult, Encapsulates in-memory arrays, transformation metrics, and persisted paths., Produce the canonical SPEC-02 PreprocessingOutput model., Produce the API serializable PreprocessingResultDTO., PreprocessingOutput, PreprocessingResultDTO, PreprocessingStepMetric, BaseModel (+2 more)

### Community 74 - "test_baseline_inference.py"
Cohesion: 0.15
Nodes (12): inference_engine(), fixture, Unit tests for baseline inference engine (Phase 09 - TC-MOD-04). Tests…, Returns BaselineInferenceEngine pointing to default serialized model., Verify single certificate inference latency is under 50ms over 100 runs (TC-…, Verify batch inference matches individual single predictions., Verify inference engine raises ValueError on invalid feature vector size., Verify graceful fallback heuristic when model artifact cannot be found. (+4 more)

### Community 76 - "NoiseReductionFilter"
Cohesion: 0.29
Nodes (4): NoiseReductionFilter, Any, ndarray, Edge-preserving noise reduction filter (Bilateral or Median).

### Community 78 - "CertificateModel"
Cohesion: 0.15
Nodes (17): CertificateModel, Base, Core certificate entity tracking document ingestion, lifecycle, and…, profile_pipeline(), Path, Benchmark stage execution times across provided certificate images., _create_dummy_image_bytes(), Session (+9 more)

### Community 79 - "Pipeline Data Contracts & Inter-Module Interfaces"
Cohesion: 0.17
Nodes (11): 10. Module 8: Score Fusion & Final Report DTO, 1. Overview & Data Flow Sequence, 2. Shared Primitive Types & Enums, 3. Module 1: Ingestion Output, 4. Module 2: Preprocessing Output, 5. Module 3: OCR & Information Extraction Output, 6. Module 4: Text Consistency Analysis Output, 7. Module 5: Image Forensics Output (+3 more)

### Community 80 - "Dataset & Synthesis Engine Specification"
Cohesion: 0.18
Nodes (10): 1. Purpose, 2. Directory Hierarchy, 3.1 Manipulation Type 1: Text Replacement (Field Tampering), 3.2 Manipulation Type 2: Copy-Move Cloning, 3.3 Manipulation Type 3: Splicing with Poisson Blending, 3.4 Manipulation Type 4: Compression Artifact Discrepancy, 3. Synthetic Manipulation Engine Architecture, 4. Ground-Truth Manifest Annotation Schema (+2 more)

### Community 81 - "PixelBoundingBox"
Cohesion: 0.21
Nodes (15): ForensicScoreCalculator, Aggregates Error Level Analysis, Copy-Move, and Noise consistency scores into a…, Compute composite forensic authenticity score [0.0, 1.0], assemble suspicious…, CloneMatch, Represents a pair of duplicated/cloned regions identified in a copy-move…, SuspiciousRegion, PixelBoundingBox, Absolute pixel coordinates. (+7 more)

### Community 82 - "CLAHEEnhancer"
Cohesion: 0.24
Nodes (6): CLAHEEnhancer, Any, ndarray, Contrast Limited Adaptive Histogram Equalization applied to the luminance…, test_clahe_enhances_low_contrast_image(), test_clahe_on_color_certificate()

### Community 84 - "test_ocr_engine.py"
Cohesion: 0.12
Nodes (16): ndarray, Path, Extract OCR tokens using EasyOCR., GeometricBoundingBox, Point, Any, OCRToken, Build OCRTokens from EasyOCR detection tuples: (polygon, text, confidence). (+8 more)

### Community 85 - "Test Fixtures & Mock Data Specification"
Cohesion: 0.22
Nodes (8): 1. Purpose, 2. Directory Layout for Test Fixtures, 3. Standard Synthetic Certificate Fixtures, 4.1 Mock Institutions Table (`seed_institutions.json`), 4.2 Mock Student Records (`mock_students.csv`), 4. Institutional Database Seed Data, 5. Test Assertion Tolerances & Performance Thresholds, Test Fixtures & Mock Data Specification

### Community 86 - "NumberedCanvas"
Cohesion: 0.21
Nodes (8): get_report_styles(), NumberedCanvas, Any, ReportLab stylesheet, typography, color palette, and dynamic numbered canvas., Two-pass canvas recording total page count for 'Page X of Y' footers., Draw standard running header and running footer., Build standardized publication typography stylesheet., StyleSheet1

### Community 87 - "Product Requirements Document (PRD)"
Cohesion: 0.08
Nodes (24): 10. Milestones (Indicative, Academic Project Timeline), 1.1 Product Summary, 1.2 Problem Statement, 1.3 Goals, 1.4 Non-Goals, 1. Overview, 2. Target Users & Personas, 3. User Stories (+16 more)

### Community 88 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 89 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 90 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 91 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 92 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 93 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 94 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 95 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 96 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 97 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 98 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 99 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (23): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+15 more)

### Community 100 - "TierStatus"
Cohesion: 0.09
Nodes (40): InstitutionalVetoEngine, Institutional Veto Override Engine for authoritative ground-truth rules., Applies definitive database ground-truth overrides to statistical AI scores., Apply authoritative institutional ground-truth overrides. Returns: Tuple of…, classify_tier(), Classify certificate into Tier 1, Tier 2, or Tier 3 status. Args:…, BaseModel, Enum (+32 more)

### Community 101 - "phase-01-project-foundation.md"
Cohesion: 0.09
Nodes (22): 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure, 8. Implementation Chips (+14 more)

### Community 102 - "dependencies"
Cohesion: 0.25
Nodes (8): dependencies, axios, clsx, lucide-react, react, react-dom, react-router-dom, tailwind-merge

### Community 103 - "8. Implementation Chips"
Cohesion: 0.09
Nodes (21): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+13 more)

### Community 104 - "8. Implementation Chips"
Cohesion: 0.09
Nodes (21): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+13 more)

### Community 105 - "HistoryAndAdmin.test.tsx"
Cohesion: 0.46
Nodes (4): MetricCard(), MetricCardProps, HistoryPage(), exportToCsv()

### Community 106 - "WeightedLateFusion"
Cohesion: 0.15
Nodes (13): Calculates explainable composite authenticity and risk scores via weighted…, Compute composite authenticity score [0.0, 1.0], risk score [0.0, 100.0], sub-…, WeightedLateFusion, Unit tests for Weighted Late Fusion calculations and factor breakdowns., Verify high fake probability produces low authenticity and high risk., Verify custom weights normalization and score calculation., Verify error on non-positive weights., Verify high authenticity input produces high authenticity score and low risk. (+5 more)

### Community 107 - "list_audit_logs"
Cohesion: 0.22
Nodes (10): AuditLogPaginatedList, list_audit_logs(), get, Session, AuditLogItem, AuditLogPaginatedList, BaseModel, Pydantic V2 schemas for audit logs and security event queries. (+2 more)

### Community 109 - "OCRToken"
Cohesion: 0.12
Nodes (22): ConfidenceEvaluator, CertificateFields, Evaluate fields, compute average confidence, flag low confidence, and build…, Evaluates field-level confidence scores, applies manual-review thresholds…, BaseFieldExtractor, ExtractedField, ABC, Strip surrounding punctuation, multiple spaces, and non-printable noise. (+14 more)

### Community 110 - "Settings"
Cohesion: 0.07
Nodes (25): field_validator, model_validator, Application configuration loaded from environment variables and .env file., Ensure all required runtime storage directories exist., Enforce production security constraints on secrets and keys (NFR-02)., Settings, Path, Return path to compiled PDF report if it exists. (+17 more)

### Community 111 - "run_step"
Cohesion: 0.33
Nodes (6): main(), Path, Automated All-In-One Test & Evaluation Script (CHIP TST-10). Executes the…, Run shell command with error checking and clear console output., Execute all test and evaluation phases sequentially., run_step()

### Community 113 - "2. Technology Stack Breakdown"
Cohesion: 0.17
Nodes (11): 1. Executive Summary & Architecture Overview, 2.1 Frontend Stack, 2.2 Backend API & Core Framework, 2.3 Computer Vision, OCR & Forensics Engine, 2.4 Machine Learning & Analytics, 2.5 Document Reporting & Export, 2.6 Testing, Quality Assurance & Tooling, 2. Technology Stack Breakdown (+3 more)

### Community 114 - "ablation_runner.py"
Cohesion: 0.25
Nodes (8): AblationConfig, format_ablation_table_markdown(), Any, Feature & Subsystem Ablation Study Runner (CHIP TST-07). Systematically…, Execute ablation experiments on benchmark dataset predictions., Format ablation study results into Markdown table., run_ablation_study(), TypedDict

### Community 116 - "tests/conftest.py"
Cohesion: 0.24
Nodes (9): client(), db_session(), fixture, Session, TestClient, Create test tables before tests run, tear down afterwards., Provide a transactional test database session., Provide a FastAPI TestClient with database dependency overridden. (+1 more)

### Community 117 - ".extract_tokens"
Cohesion: 0.33
Nodes (4): ndarray, Path, Return configured tokens, or generate synthetic academic certificate tokens., Generate a realistic set of academic certificate OCR tokens.

### Community 119 - "AI Developer Rules of Engagement & Execution Guidelines"
Cohesion: 0.22
Nodes (8): 1. Core Principles & Philosophy, 2. Directory Layout & Architecture Enforcement, 3. Definition of Done (DoD) per Phase, 4.1 Python Standards, 4.2 TypeScript & React Standards, 4. Coding Standards, 5. Environment & Hardware Adaptation Rules, AI Developer Rules of Engagement & Execution Guidelines

### Community 120 - "run_ablation_study"
Cohesion: 0.17
Nodes (13): Unit tests for feature ablation study (Phase 09 - TC-MOD-05). Tests domain…, Verify that run_ablation_study executes successfully and generates valid report., test_ablation_study_execution(), evaluate_feature_subset(), load_feature_groups(), Any, ndarray, Path (+5 more)

### Community 121 - "AI-Based Detection of Fake or Manipulated Academic Certificates"
Cohesion: 0.22
Nodes (8): 1. Prerequisites, 2. Backend Setup, 3. Frontend Setup, AI-Based Detection of Fake or Manipulated Academic Certificates, Architecture Overview, Project Structure, Quick Start, Verification & Quality Assurance

### Community 122 - "Environment Configuration & Secrets Specification"
Cohesion: 0.33
Nodes (5): 1. Overview, 2. Environment Variables Catalog (`.env.example`), 3. Pydantic Settings Implementation Blueprint, 4. Security Constraints, Environment Configuration & Secrets Specification

### Community 123 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 124 - "pipeline_orchestrator.py"
Cohesion: 0.12
Nodes (24): SQLAlchemy ORM model for submitted academic certificates and verification jobs., ForensicFindingModel, Base, SQLAlchemy model for storing digital image forensic findings and suspicious…, SQLAlchemy 2.0 ORM models for all 12 relational database tables., OCRFieldModel, Base, SQLAlchemy ORM model for individual academic fields extracted via OCR. (+16 more)

### Community 125 - "schemas/pipeline.py"
Cohesion: 0.11
Nodes (33): LogicalConsistencyValidator, ConsistencyCheckItem, Validates temporal chronology, calendar feasibility, numeric grade boundaries,…, Validate numeric grade / CGPA / percentage bounds and honors consistency., Perform chronological and numerical grade feasibility checks. Returns: Tuple…, Try standard date formats to parse the date string., Validate that issue dates and graduation dates are realistic and not in the…, CertificateFields (+25 more)

### Community 126 - "StudentNameExtractor"
Cohesion: 0.40
Nodes (3): Extracts student/candidate name from certificate layout., Extract student name using labeled key-value, prefix patterns, and uppercase…, StudentNameExtractor

### Community 127 - "compute_template_ssim"
Cohesion: 0.21
Nodes (14): compute_template_ssim(), evaluate_ssim_category(), ndarray, Compute global and masked Structural Similarity Index (SSIM) against master…, Categorize SSIM score into genuine, suspicious, or counterfeit., _create_base_template(), ndarray, Generate a clean base certificate image. (+6 more)

### Community 128 - "CertificateIdExtractor"
Cohesion: 0.31
Nodes (5): CertificateIdExtractor, ndarray, Detect and decode QR code using OpenCV QRCodeDetector., Extracts unique printed certificate serial numbers, folio numbers, and QR code…, Extract certificate ID through QR code detection or printed serial label…

### Community 129 - ".process"
Cohesion: 0.50
Nodes (3): Any, ndarray, Apply transformation to the input image array. Args: image: NumPy array…

### Community 130 - "BoundingBox"
Cohesion: 0.08
Nodes (16): BoundingBox, PixelBoundingBox, Compute combined normalized and pixel bounding boxes for a list of tokens., BoundingBox, PixelBoundingBox, Convert to canonical normalized BoundingBox [0.0, 1.0] and PixelBoundingBox., BoundingBox, ErrorEnvelope (+8 more)

### Community 132 - "forensics/__init__.py"
Cohesion: 0.22
Nodes (10): ForensicHeatmapGenerator, ndarray, Path, Synthesizes Error Level Analysis, Copy-Move clone regions, and Noise variance…, Create high-contrast thermal anomaly map and save annotated PNG to disk., Path, TC-FOR-05: Verify high-contrast thermal heatmap is properly generated and saved., Verify clone matches draw bounding boxes and connecting lines on the heatmap. (+2 more)

### Community 133 - "match_seal_and_logo"
Cohesion: 0.19
Nodes (15): match_seal_and_logo(), Any, ndarray, Extract university seal/logo ROI and evaluate geometric & color consistency.…, Bounding box coordinates for seal/logo/emblem in pixel dimensions., SealROI, _create_template_with_seal(), ndarray (+7 more)

### Community 134 - ".run"
Cohesion: 0.50
Nodes (3): Any, ndarray, Sequentially execute registered steps, tracking elapsed time and context.

### Community 135 - "config.py"
Cohesion: 0.14
Nodes (10): Run migrations in 'offline' mode., Run migrations in 'online' mode., run_migrations_offline(), run_migrations_online(), CleanupService, Path, Session, Orphan file garbage collection and temporary scratch space purger. (+2 more)

### Community 137 - "TextLine"
Cohesion: 0.12
Nodes (12): DegreeExtractor, Extracts degree qualification, program title, and specialization branch., Extract degree and program from lines., Extracts student roll number, registration number, USN, or enrollment ID., Extract registration / roll number via labels and strict pattern matches., RollNumberExtractor, Represents a coherent horizontal line of text reconstructed from OCR tokens., Find the immediate next text line below the anchor line within a vertical… (+4 more)

### Community 138 - "AppException"
Cohesion: 0.12
Nodes (14): AppException, ForbiddenError, NotFoundError, PipelineError, Any, Exception, Resource not found error., Input or schema validation error. (+6 more)

### Community 141 - "reports.py"
Cohesion: 0.14
Nodes (16): download_json_endpoint(), download_pdf_endpoint(), get_report_endpoint(), get, JSONResponse, Session, FastAPI router for verification report retrieval, verification, and PDF/JSON…, verify_report_integrity_endpoint() (+8 more)

### Community 143 - "ingestion/service.py"
Cohesion: 0.08
Nodes (31): post, UploadFile, Handle multipart file upload, validate integrity, and store for verification…, upload_document(), check_duplicate_hash(), compute_sha256(), Path, Session (+23 more)

### Community 145 - "explainability.py"
Cohesion: 0.06
Nodes (59): Coordinate mapping and transformation between processed and original image…, Explainability, feature attributions, and visual evidence overlay subsystem., NLGExplanationGenerator, Any, Natural Language Generation (NLG) engine for human-readable verification…, Synthesizes raw analytical findings and scores into structured natural language…, Generate executive summary paragraph for decision., Synthesize detailed finding bullets categorized by analytical domain. (+51 more)

### Community 147 - "template_matching/service.py"
Cohesion: 0.15
Nodes (17): align_to_template(), ndarray, Align query certificate image to reference template using ORB & RANSAC. Args:…, generate_visual_diff(), ndarray, Generate a composite panel: [ Master Template | Query Certificate | SSIM…, _create_sample_certificate_canvas(), ndarray (+9 more)

### Community 149 - "DateExtractor"
Cohesion: 0.38
Nodes (3): DateExtractor, Extracts and standardizes certificate issue, convocation, or examination dates., Extract and normalize certificate date to ISO YYYY-MM-DD.

### Community 151 - "db_session"
Cohesion: 0.67
Nodes (3): db_session(), fixture, In-memory SQLite test database fixture.

### Community 152 - "test_template_endpoints.py"
Cohesion: 0.25
Nodes (10): _make_dummy_image_bytes(), TestClient, Verify POST /api/v1/templates registers template and GET /api/v1/templates…, Verify GET /api/v1/templates/diagnostics returns health metrics., Verify CSV bulk import and listing via /api/v1/records., Verify POST /api/v1/records adds single student record., test_api_records_bulk_import_and_query(), test_api_single_record_create() (+2 more)

### Community 154 - "generated_templates"
Cohesion: 0.22
Nodes (9): generated_templates(), fixture, Path, Generate temporary base templates fixture., Verify templates and asset files are properly generated., Verify train/val/test splitting and manifest generation., test_dataset_splits_and_manifests(), test_template_generation() (+1 more)

### Community 155 - "StackingMetaClassifier"
Cohesion: 0.08
Nodes (22): ndarray, Path, Stacking meta-learner that predicts authenticity from multi-branch predictions., Fit meta-learner on out-of-fold branch predictions and authenticity labels., Predict probability that the certificate is authentic [0.0 = Fake, 1.0 =…, Serialize meta-classifier artifact., Load serialized meta-classifier artifact., StackingMetaClassifier (+14 more)

### Community 157 - "TabularFeatureExtractor"
Cohesion: 0.05
Nodes (42): Any, CertificateFields, ndarray, Extracts a standardized 22-dimensional float32 feature vector from upstream…, Alias mapping upstream pipeline outputs to extract()., Convenience method returning directly the 22D float32 NumPy array., Construct the 22-dimensional tabular feature vector with robust fallback…, TabularFeatureExtractor (+34 more)

### Community 162 - "evaluate_baseline_model"
Cohesion: 0.40
Nodes (5): evaluate_baseline_model(), Any, DataFrame, Path, Evaluate trained model on held-out test set, generating metrics and diagnostic…

### Community 163 - "TabularDataPreprocessor"
Cohesion: 0.14
Nodes (12): DataFrame, ndarray, Path, Load or generate train/val/test DataFrames., Preprocesses and normalizes 22-dimensional tabular certificate features., Fit scaler on training data matrix strictly., Standardize feature matrix., Serialize fitted preprocessor to disk. (+4 more)

### Community 164 - "generate_synthetic_feature_dataset"
Cohesion: 0.14
Nodes (18): Unit tests for ML model evaluation (Phase 09 - TC-MOD-02). Tests held-out test…, Verify evaluation generates metrics meeting specification and generates plots., test_evaluate_baseline_model_metrics(), Unit tests for ML model training pipeline (Phase 09 - TC-MOD-01). Tests 5-fold…, Verify that train_baseline_models trains 4 candidates with 5-fold CV and saves…, test_train_baseline_models_pipeline(), extract_and_save_dataset_features(), generate_synthetic_feature_dataset() (+10 more)

### Community 166 - "get_inference_transforms"
Cohesion: 0.13
Nodes (18): device, denormalize_image(), get_inference_transforms(), get_train_transforms(), ndarray, Tensor, Image transformation and normalization pipelines for certificate visual…, Document-safe augmentation pipeline for training. (+10 more)

### Community 168 - "export_model.py"
Cohesion: 0.32
Nodes (7): compute_sha256(), generate_manifest(), Any, Path, Model export and manifest generation script for Phase 09 ML Baseline (CHIP…, Compute sha256 checksum of a file., Generate production model manifest JSON.

### Community 169 - "MultimodalFusionMLP"
Cohesion: 0.06
Nodes (37): concatenate_features(), MultimodalFusionMLP, ndarray, Tensor, Early fusion module combining 512D visual embeddings and 22D tabular features., Concatenate 512D visual embedding and 22D tabular vector into 534D…, Deep Multi-Layer Perceptron learning joint cross-modal representations from…, Forward pass. Expects tensor of shape (B, 534) -> returns logits (B,). (+29 more)

### Community 171 - "ForensicAnalysisResult"
Cohesion: 0.12
Nodes (23): ForensicService, get_forensic_service(), ndarray, Path, Run forensics and return canonical SPEC-02 ForensicsOutput., FastAPI dependency injection provider for ForensicService., Orchestrates comprehensive classical digital image forensics: Error Level…, Run complete forensic analysis suite on the pristine uploaded certificate image. (+15 more)

### Community 172 - ".extract_from_pil"
Cohesion: 0.24
Nodes (7): Image, ndarray, Path, Tensor, Extract normalized 512D embedding from tensor of shape (1, 3, H, W) or (3, H,…, Extract normalized 512D embedding from PIL Image., Extract normalized 512D embedding directly from image file path.

### Community 175 - ".predict_batch"
Cohesion: 0.40
Nodes (3): ndarray, Perform batch inference on an (N, 22) array of features., Perform inference on a single 22-dimensional feature vector. Returns: tuple of…

### Community 179 - "MLInferenceOutput"
Cohesion: 0.08
Nodes (37): MLPredictionModel, Base, SQLAlchemy ORM model for ML manipulation predictions., SQLAlchemy model for persisting machine learning manipulation predictions., Visual feature embedding extractor for multimodal fusion., Extracts 512-dimensional L2-normalized visual feature embeddings from…, VisualEmbeddingExtractor, Deep learning visual tampering classification module. (+29 more)

### Community 180 - ".classify_certificate"
Cohesion: 0.47
Nodes (4): Any, Session, Convenience method returning canonical SPEC-02 pipeline contract schema., Extract features, run inference, calculate local contributions, and return full…

### Community 181 - "InstitutionModel"
Cohesion: 0.08
Nodes (41): create_template(), get_template(), list_templates(), Any, get, post, Session, UploadFile (+33 more)

### Community 183 - "FastAPI"
Cohesion: 0.08
Nodes (25): get_detailed_health(), get_health(), get_ingestion_health(), get, Session, Probe the health of the FastAPI service and its dependencies (Database,…, Probe the health of document ingestion dependencies (PDF renderers, disk…, Perform diagnostic health checks across database, storage, and ML models. (+17 more)

### Community 184 - "VerificationReportModel"
Cohesion: 0.26
Nodes (11): Base, SQLAlchemy ORM model for final verification decisions and reports., SQLAlchemy model persisting final multimodal verification decisions., VerificationReportModel, Session, TestClient, Integration tests for admin fraud analytics, system health, and history…, test_admin_analytics_summary() (+3 more)

### Community 185 - "InstitutionExtractor"
Cohesion: 0.40
Nodes (3): InstitutionExtractor, Extracts issuing university or college name from the header region of the…, Extract institution name from header lines (top 40% of document).

### Community 188 - "FullVerificationReport"
Cohesion: 0.05
Nodes (71): CertificateFields, FileMetadata, FullVerificationReport, SubsystemScoreItem, VisualEvidencePaths, Report assembler harvesting outputs across all pipeline analytical stages., Assembles inputs from all analytical pipeline phases into…, Harvest outputs across pipeline and construct FullVerificationReport. (+63 more)

### Community 189 - "ScoreFusionService"
Cohesion: 0.08
Nodes (25): Any, ndarray, Session, Convenience method returning canonical SPEC-02 pipeline output contract., Production service coordinating multimodal fusion, veto overrides, and final…, Run multimodal score fusion, apply veto overrides, and generate final verdict., ScoreFusionService, main() (+17 more)

### Community 193 - "certificates.py"
Cohesion: 0.08
Nodes (33): delete_certificate(), get_certificate_details(), get_certificate_status(), list_certificates(), BackgroundTasks, get, post, Request (+25 more)

### Community 195 - "e2e/conftest.py"
Cohesion: 0.29
Nodes (9): genuine_sample_path(), manipulated_sample_path(), fixture, Path, Test fixtures for End-to-End integration test suite., Path to known genuine certificate image., Path to known manipulated certificate image., Generate a clean 3-page academic transcript PDF. (+1 more)

### Community 198 - "analytics_service.py"
Cohesion: 0.16
Nodes (23): get_analytics_summary(), get_system_diagnostic_health(), get, Session, FastAPI router for administrative fraud analytics, KPI metrics, and system…, AnalyticsSummaryResponse, ModalityBreakdownItem, PipelineLatencyBreakdown (+15 more)

### Community 199 - "create_dataset_splits"
Cohesion: 0.29
Nodes (5): create_dataset_splits(), Any, Path, Dataset Splitter & Ground Truth Manifest Generator. Partitions generated…, Split samples into train, val, and test partitions with out-of-distribution…

### Community 202 - "ELAAnalyzer"
Cohesion: 0.13
Nodes (17): ELAAnalyzer, BoundingBox, Image, ndarray, Path, PixelBoundingBox, Compute ELA differential error curve across multiple JPEG quality levels., Performs Error Level Analysis (ELA) to detect JPEG compression inconsistencies… (+9 more)

### Community 205 - "endpoints/auth.py"
Cohesion: 0.07
Nodes (52): change_password(), _check_rate_limit(), _clear_failed_attempts(), get_current_user_profile(), login(), logout(), get, post (+44 more)

### Community 207 - "create_access_token"
Cohesion: 0.17
Nodes (19): create_access_token(), create_refresh_token(), Create a signed, stateless JWT access token (default expiry: 15 minutes)., Create a signed JWT refresh token with unique JTI (default expiry: 7 days)., _create_user(), Session, TestClient, Integration tests for RBAC enforcement and token revocation (TC-USR-03, TC-… (+11 more)

### Community 213 - "test_concurrent_multi_user_uploads"
Cohesion: 0.29
Nodes (6): Path, Session, TestClient, Concurrent multi-user upload and execution stress test (TC-E2E-05)., TC-E2E-05: Process multiple concurrent certificate uploads without race…, test_concurrent_multi_user_uploads()

### Community 214 - "test_database_migrations.py"
Cohesion: 0.40
Nodes (4): Path, Integration test for Alembic migrations and 12-table schema creation (TC-…, Verify Alembic applies all migrations and creates all 12 tables (TC-API-01)., test_alembic_migrations_apply_cleanly()

### Community 215 - "test_institution_endpoints_lifecycle"
Cohesion: 0.40
Nodes (4): TestClient, Integration tests for institution onboarding and bulk CSV records endpoints., Verify university registration, listing, and bulk CSV student record import., test_institution_endpoints_lifecycle()

### Community 216 - "test_manipulated_certificate_e2e_workflow"
Cohesion: 0.29
Nodes (6): Path, Session, TestClient, End-to-End manipulated certificate verification workflow test (TC-E2E-02)., TC-E2E-02: Full workflow from upload of forged certificate to…, test_manipulated_certificate_e2e_workflow()

### Community 219 - "test_genuine_certificate_e2e_workflow"
Cohesion: 0.29
Nodes (6): Path, Session, TestClient, End-to-End full genuine certificate verification workflow test (TC-E2E-01)., TC-E2E-01: Full workflow from upload of genuine document to authentic verdict…, test_genuine_certificate_e2e_workflow()

### Community 223 - ".log_action"
Cohesion: 0.10
Nodes (20): Verify a plaintext password against its bcrypt hash in constant time., Enforce password complexity requirements (NFR-02). Rules: - Minimum 8…, validate_password_strength(), verify_password(), AuditLogModel, Base, Immutable audit trail recording all security, verification, and administrative…, Any (+12 more)

### Community 224 - ".analyze"
Cohesion: 0.50
Nodes (3): ndarray, Compute stroke width metrics across tokens and flag weight discrepancies.…, Estimate the mean stroke width of characters within a token's bounding box.

### Community 225 - "test_graceful_degradation_under_partial_failure"
Cohesion: 0.25
Nodes (7): Path, Session, TestClient, Graceful degradation and fault-tolerant fallback recovery test (TC-E2E-04)., TC-E2E-04: Graceful degradation when template matching encounters simulated…, test_graceful_degradation_under_partial_failure(), patch

### Community 227 - "VerificationVerdict"
Cohesion: 0.08
Nodes (49): Multimodal score fusion and decision subsystem., Weighted late fusion engine blending branch probabilities and sub-scores., Stacking Meta-Classifier for multimodal probability blending., Production orchestrator service for multimodal score fusion and verdict…, Verdict determination and confidence calibration engine., Classifies authenticity scores into canonical project verdicts with calibrated…, Categorize authenticity score into Verdict, RiskBand, Confidence, and Rationale., VerdictEngine (+41 more)

### Community 229 - "CopyMoveDetector"
Cohesion: 0.14
Nodes (15): CopyMoveDetector, ndarray, Detects duplicated or cloned elements (seals, stamps, signatures, text patches)…, Cluster displacement vectors using DBSCAN and verify transformation via RANSAC., Detect copy-move forgery clusters and return authenticity score and clone…, Extract SIFT keypoints and descriptors with automatic fallback to ORB., Match descriptors against themselves and filter out self-matches and nearby…, _draw_complex_stamp() (+7 more)

### Community 230 - "test_multipage_pdf_workflow"
Cohesion: 0.29
Nodes (6): Path, Session, TestClient, End-to-End multi-page PDF upload and page-1 rasterization verification test…, TC-E2E-03: Multi-page PDF upload, high-resolution page-1 rasterization, and…, test_multipage_pdf_workflow()

## Knowledge Gaps
- **862 isolated node(s):** `entrypoint.sh script`, `ai-certificate-verification-backend`, `run_all_tests.sh script`, `smoke_test.sh script`, `name` (+857 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2155 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CertificateFields` connect `schemas/pipeline.py` to `.verify`, `AnomalousRegion`, `TextConsistencyService`, `schemas/__init__.py`, `OCRToken`, `.run_pipeline`, `pipeline_orchestrator.py`, `explainability.py`, `template_matching/service.py`, `InstitutionRecordModel`, `InstitutionModel`, `ScoreFusionService`, `FullVerificationReport`, `TabularFeatureExtractor`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `VerificationPipelineOrchestrator` connect `pipeline_orchestrator.py` to `BaselineMLService`, `certificates.py`, `OCRService`, `TextConsistencyService`, `ForensicAnalysisResult`, `schemas/__init__.py`, `endpoints/auth.py`, `CertificateModel`, `.run_pipeline`, `explainability.py`, `MLInferenceOutput`, `InstitutionModel`, `schemas/pipeline.py`, `ScoreFusionService`, `FullVerificationReport`, `PreprocessingService`, `PDFRasterizer`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `OCRToken` connect `OCRToken` to `CertificateIdExtractor`, `BoundingBox`, `OCRService`, `ocr/__init__.py`, `FormatChecker`, `TextLine`, `AnomalousRegion`, `TokenBuilder`, `DateExtractor`, `TextConsistencyService`, `schemas/__init__.py`, `test_field_extractors.py`, `InstitutionExtractor`, `PixelBoundingBox`, `test_ocr_engine.py`, `.analyze`, `.extract_tokens`, `schemas/pipeline.py`, `StudentNameExtractor`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `OCRToken` (e.g. with `BaseOCREngine` and `ConfidenceEvaluator`) actually correct?**
  _`OCRToken` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `TextLine` (e.g. with `BaseFieldExtractor` and `CertificateIdExtractor`) actually correct?**
  _`TextLine` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `CertificateFields` (e.g. with `TabularFeatureExtractor` and `ConfidenceEvaluator`) actually correct?**
  _`CertificateFields` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `BoundingBox` (e.g. with `CopyMoveDetector` and `ELAAnalyzer`) actually correct?**
  _`BoundingBox` has 17 INFERRED edges - model-reasoned connections that need verification._