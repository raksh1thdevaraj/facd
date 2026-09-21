# Graph Report - AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates  (2026-09-21)

## Corpus Check
- 421 files · ~367,440 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3810 nodes · 7781 edges · 212 communities (182 shown, 16 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 703 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f0514d26`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FeatureVector
- IngestionValidator
- TemplateVerificationService
- OCRService
- devDependencies
- ocr/__init__.py
- PerspectiveWarper
- TokenBuilder
- compilerOptions
- AnomalousRegion
- ResultsPage.tsx
- to_grayscale
- admin.ts
- Deskewer
- DESIGN.md
- generate_dataset.py
- datetime
- generate_all_templates
- TextLine
- test_dataset_synthesis.py
- InstitutionRecordModel
- Software Requirements Document (SRD / SRS)
- UploadPage.tsx
- test_evaluation_metrics.py
- B.1 Module Breakdown
- ._validate_dates
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
- register_institution_template
- GradCAMExplainer
- UserRole
- .analyze
- validate_dataset
- fallback_handler.py
- AdaptiveBinarizer
- 8. Implementation Chips
- CoordinateMapper
- 8. Implementation Chips
- 8. Implementation Chips
- 8. Implementation Chips
- print_dataset_stats
- test_field_extractors.py
- create_dataloaders
- verify_student_record
- 8. Implementation Chips
- train_visual_cnn
- 8. Implementation Chips
- test_coverage_and_reports.py
- Environment & Toolchain Specification
- AppUserModel
- chart_generator.py
- Forensics & Algorithm Specification
- package.json
- index.ts
- NoiseAnalyzer
- vite.config.ts
- AuthContext.tsx
- report_writer.py
- Scientific Model Evaluation & Benchmark Report (Phase 19)
- PreprocessingResult
- test_baseline_inference.py
- ai-certificate-verification-backend
- NoiseReductionFilter
- .run_pipeline
- test_certificate_endpoints.py
- Pipeline Data Contracts & Inter-Module Interfaces
- Dataset & Synthesis Engine Specification
- PixelBoundingBox
- CLAHEEnhancer
- evaluate_multimodal.py
- EasyOCREngine
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
- .analyze
- OCRToken
- Settings
- run_step
- 2. Technology Stack Breakdown
- ablation_runner.py
- TesseractOCREngine
- tests/conftest.py
- .extract_tokens
- app_exception_handler
- AI Developer Rules of Engagement & Execution Guidelines
- run_ablation_study
- AI-Based Detection of Fake or Manipulated Academic Certificates
- Environment Configuration & Secrets Specification
- scripts
- pipeline_orchestrator.py
- AnomalyType
- StudentNameExtractor
- compute_template_ssim
- CertificateIdExtractor
- .process
- BoundingBox
- Abstract
- ForensicHeatmapGenerator
- match_seal_and_logo
- .run
- cleanup_service.py
- upload_certificate
- DegreeExtractor
- AppException
- RollNumberExtractor
- rules/graphify.md
- .build_story
- run_template_diagnostics
- ingestion/service.py
- workflows/graphify.md
- explainability.py
- trained_rf
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
- schemas/__init__.py
- evaluation/__init__.py
- backend/scripts/__init__.py
- evaluate_baseline_model
- TabularDataPreprocessor
- generate_synthetic_feature_dataset
- visual_model/__init__.py
- export_model.py
- ScoreFusionService
- ForensicAnalysisResult
- VisualEmbeddingExtractor
- .predict_batch
- MLInferenceOutput
- .classify_certificate
- InstitutionModel
- ExtractedFieldDTO
- database.py
- CertificateModel
- InstitutionExtractor
- 001_initial_schema.py
- .render_overlay
- CertificateFields
- test_api_report_endpoints_lifecycle
- export_visual_model.py
- .__init__
- .to_pipeline_output
- task_runner.py
- .to_pipeline_output
- e2e/conftest.py
- analytics_service.py
- create_dataset_splits
- primitives.py
- endpoints/auth.py
- security.py
- test_concurrent_multi_user_uploads
- test_database_migrations.py
- test_institution_endpoints_lifecycle
- test_manipulated_certificate_e2e_workflow
- test_genuine_certificate_e2e_workflow
- .log_action
- TextConsistencyConfig
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
- `evaluate_multimodal_models()` --uses--> `MultimodalFusionMLP`  [INFERRED]
  ml/scripts/evaluate_multimodal.py → backend/app/modules/score_fusion/early_fusion.py
- `train_early_fusion_mlp()` --uses--> `MultimodalFusionMLP`  [INFERRED]
  ml/scripts/train_early_fusion_mlp.py → backend/app/modules/score_fusion/early_fusion.py
- `BenchmarkRunner` --uses--> `WeightedLateFusion`  [INFERRED]
  ml/evaluation/benchmark_runner.py → backend/app/modules/score_fusion/late_fusion.py
- `evaluate_multimodal_models()` --uses--> `WeightedLateFusion`  [INFERRED]
  ml/scripts/evaluate_multimodal.py → backend/app/modules/score_fusion/late_fusion.py
- `evaluate_multimodal_models()` --uses--> `StackingMetaClassifier`  [INFERRED]
  ml/scripts/evaluate_multimodal.py → backend/app/modules/score_fusion/meta_classifier.py

## Import Cycles
- None detected.

## Communities (212 total, 16 thin omitted)

### Community 0 - "FeatureVector"
Cohesion: 0.10
Nodes (18): FeatureVector, Any, BaseModel, ndarray, Standardized 22-dimensional tabular feature vector extracted across upstream…, Convert pydantic feature model into ordered float32 NumPy array of shape (22,)., Alias for to_numpy()., Convert pydantic model to dictionary of feature name -> float. (+10 more)

### Community 1 - "IngestionValidator"
Cohesion: 0.13
Nodes (32): CorruptedFileError, EmptyFileError, FileTooLargeError, InsufficientResolutionError, InvalidFileError, Uploaded file MIME type or magic signature is not allowed., Uploaded file exceeds the maximum allowed upload size., Uploaded file has zero bytes. (+24 more)

### Community 2 - "TemplateVerificationService"
Cohesion: 0.20
Nodes (8): ndarray, Session, Orchestrator for visual template matching and student record verification., Execute dual-track template comparison and student record cross-verification.…, TemplateVerificationService, Session, FR-TPL-04: Graceful execution when neither template nor record is registered., test_service_graceful_fallback_no_template_no_record()

### Community 3 - "OCRService"
Cohesion: 0.12
Nodes (22): EngineFactory, Factory for selecting and instantiating OCR engines with graceful degradation., Create or retrieve the requested OCR engine with automatic fallback., Query availability status for all known OCR backends., get_ocr_service(), OCRService, ndarray, Path (+14 more)

### Community 4 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, jsdom, postcss, tailwindcss, @testing-library/dom, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 5 - "ocr/__init__.py"
Cohesion: 0.11
Nodes (18): BaseOCREngine, ABC, ndarray, Path, Abstract interface defining the OCR detection and character recognition…, Name of the OCR engine backend (e.g., 'easyocr', 'pytesseract', 'mock')., Extract OCR tokens with bounding boxes and confidence scores from an image., MockOCREngine (+10 more)

### Community 6 - "PerspectiveWarper"
Cohesion: 0.19
Nodes (14): find_document_corners(), four_point_transform(), order_points(), PerspectiveWarper, Any, ndarray, Detects document boundary corners and rectifies perspective distortion., Order 4 (x, y) coordinates consistently: top-left, top-right, bottom-right,… (+6 more)

### Community 7 - "TokenBuilder"
Cohesion: 0.12
Nodes (27): Utility factory to create a single OCRToken with exact geometry., Constructs canonical OCRToken objects from raw OCR engine outputs., TokenBuilder, FormatChecker, Detects text formatting irregularities, homoglyph character substitutions,…, Detect homoglyph evasion when a Cyrillic character is embedded inside Latin…, Detect erratic casing anomaly inside a word like 'cOMPUTER'., Verify that normally formatted words yield format consistency score 1.0. (+19 more)

### Community 8 - "compilerOptions"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+12 more)

### Community 9 - "AnomalousRegion"
Cohesion: 0.14
Nodes (16): Detect orphaned punctuation artifacts or invalid character repetitions., Inspect all tokens for homoglyphs, capitalization glitches, and punctuation…, Check for Cyrillic or unexpected scripts inserted into Latin words., Detect mid-word erratic casing such as 'cOMPUTER' or 'JoHn'., get_text_consistency_service(), FastAPI dependency injection provider for TextConsistencyService., Orchestrates comprehensive text consistency, typographical forensics, and…, TextConsistencyService (+8 more)

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

### Community 16 - "datetime"
Cohesion: 0.19
Nodes (16): MetadataExtractor, _parse_exif_date(), _parse_pdf_date(), Any, Path, Extract document metadata from PDF trailer and dictionary entries., Parse standard PDF date format, e.g. D:20240915123000+00'00'., Parse EXIF datetime string, e.g. '2024:09:15 12:30:00'. (+8 more)

### Community 17 - "generate_all_templates"
Cohesion: 0.17
Nodes (15): ImageDraw, create_guilloche_pattern(), draw_decorative_border(), generate_all_templates(), generate_seal_image(), generate_signature_image(), Any, Image (+7 more)

### Community 18 - "TextLine"
Cohesion: 0.11
Nodes (27): Represents a coherent horizontal line of text reconstructed from OCR tokens., Find the immediate next text line below the anchor line within a vertical…, Construct a TextLine from a list of horizontally sorted tokens., TextLine, BaselineAlignmentAnalyzer, Detects vertical text displacement and baseline drift anomalies in lines of…, Fit baselines across text lines and identify tokens with abnormal vertical…, FontSizeAnalyzer (+19 more)

### Community 19 - "test_dataset_synthesis.py"
Cohesion: 0.16
Nodes (21): Verify text inpainting and replacement modification., Verify copy-move duplication operator., Verify localized JPEG quality degradation operator., test_copy_move_tampering(), test_inpaint_and_replace_tampering(), test_recompression_discrepancy(), apply_manipulation(), apply_recompression_discrepancy() (+13 more)

### Community 20 - "InstitutionRecordModel"
Cohesion: 0.11
Nodes (28): bulk_import_records(), create_record(), list_records(), Any, get, post, Session, UploadFile (+20 more)

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

### Community 25 - "._validate_dates"
Cohesion: 0.24
Nodes (6): ConsistencyCheckItem, Validate numeric grade / CGPA / percentage bounds and honors consistency., Perform chronological and numerical grade feasibility checks. Returns: Tuple…, Try standard date formats to parse the date string., Validate that issue dates and graduation dates are realistic and not in the…, date

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
Cohesion: 0.14
Nodes (18): PreprocessingArtifactManager, Path, UUID, Manages filesystem persistence of preprocessed images and audit artifacts., Save enhanced image, binarized image, and thumbnail for a certificate.…, Any, Execute diagnostic self-tests and performance benchmarks for the preprocessing…, run_preprocessing_diagnostics() (+10 more)

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
Cohesion: 0.07
Nodes (35): compute_local_contributions(), extract_feature_importances(), FeatureImportanceAnalyzer, plot_feature_importance(), Any, ndarray, Path, Feature importance analysis and local anomaly explanations for Phase 09.… (+27 more)

### Community 34 - "CertificateVisualCNN"
Cohesion: 0.10
Nodes (19): CertificateVisualCNN, Module, Tensor, Return the final convolutional layer of the backbone for Grad-CAM., Convolutional Neural Network for certificate visual manipulation…, Forward pass. Args: x: Input image tensor of shape (B, 3, H, W) Returns:…, Freeze all parameters in the convolutional backbone for Stage 1 fine-tuning., Unfreeze backbone parameters for Stage 2 fine-tuning. Args: top_blocks_only: If… (+11 more)

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
Cohesion: 0.22
Nodes (16): Clear all recorded failed attempts (primarily for testing and administrative…, reset_rate_limits(), _create_test_user(), Session, TestClient, Integration tests for JWT tokens, expiry, profiles, and rate limits (TC-USR-02,…, Verify 5 failed login attempts trigger HTTP 429 Too Many Requests (CHIP USR-10)., Verify POST /api/v1/auth/login issues valid access and refresh tokens (TC-… (+8 more)

### Community 39 - "register_institution_template"
Cohesion: 0.24
Nodes (10): load_precomputed_template_features(), Any, ndarray, Session, Load pre-computed keypoints coordinates and descriptors from compressed npz…, Register and index master template, persisting image and precomputed features.…, register_institution_template(), Session (+2 more)

### Community 40 - "GradCAMExplainer"
Cohesion: 0.11
Nodes (15): GradCAMExplainer, device, ndarray, Path, Tensor, Computes Grad-CAM heatmaps highlighting visual regions indicative of tampering., Compute Grad-CAM heatmap array of shape (H, W) normalized to [0.0, 1.0]., Blend computed heatmap with the raw BGR certificate image. (+7 more)

### Community 41 - "UserRole"
Cohesion: 0.19
Nodes (13): Enforce that the authenticated user possesses one of the specified roles., require_role(), role_dependency(), is_role_authorized(), normalize_role(), Enum, str, Role-Based Access Control (RBAC) hierarchy and permissions. (+5 more)

### Community 42 - ".analyze"
Cohesion: 0.22
Nodes (8): CertificateFields, ndarray, Path, Run text consistency analysis and return canonical SPEC-02…, Run complete typographical forensics and logical consistency pipeline., ndarray, Path, Draw anomaly bounding boxes and descriptive tags onto the certificate image.

### Community 43 - "validate_dataset"
Cohesion: 0.38
Nodes (6): main(), Any, Path, Dataset Validator. Performs comprehensive data integrity checks: 1. Verifies…, Validate dataset integrity and print detailed diagnostic report., validate_dataset()

### Community 44 - "fallback_handler.py"
Cohesion: 0.11
Nodes (24): PredictionResult, Prediction result DTO summarizing baseline machine learning model inference., OCRResultDTO, High-level Data Transfer Object summarizing the OCR extraction results., TemplateMatchOutput, Convert to canonical SPEC-02 TemplateMatchOutput contract., Composite verification DTO containing visual, database, and tier assessment., Calculate a risk score on [0.0, 100.0] scale. (+16 more)

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
Cohesion: 0.12
Nodes (18): Unit tests for dataset loading and balanced sampling., Verify loading dataset from splits., Verify DataLoaders creation and batch extraction., test_certificate_dataset_loading(), test_create_dataloaders(), Dataset, CertificateImageDataset, create_dataloaders() (+10 more)

### Community 54 - "verify_student_record"
Cohesion: 0.16
Nodes (18): _extract_numeric_cgpa(), _extract_year_from_text(), Session, Extract a 4-digit year (1950-2099) from date or general text., Extract numeric GPA/CGPA or percentage from grade string., Query institutional records database and cross-verify extracted student…, verify_student_record(), Session (+10 more)

### Community 55 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (24): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+16 more)

### Community 56 - "train_visual_cnn"
Cohesion: 0.20
Nodes (10): evaluate_epoch(), Any, DataLoader, device, Module, Path, Two-stage transfer learning training script for certificate visual CNN model., Evaluate model on validation loader, returning loss and classification metrics. (+2 more)

### Community 57 - "8. Implementation Chips"
Cohesion: 0.08
Nodes (24): 10. Phase Completion Checklist, 1. Purpose, 2. Why This Phase Exists, 3. Requirements Covered, 4. Inputs, 5. Outputs, 6. Dependencies, 7. Files and Folder Structure (+16 more)

### Community 58 - "test_coverage_and_reports.py"
Cohesion: 0.12
Nodes (18): generate_markdown_matrix(), Any, Requirements & Test Case Traceability Matrix Verification Script (Phase 19).…, Audit test suite to confirm all requirement mapping targets exist., Format traceability audit into GitHub Flavored Markdown., verify_traceability(), benchmark_predictions(), fixture (+10 more)

### Community 59 - "Environment & Toolchain Specification"
Cohesion: 0.10
Nodes (19): 1. Purpose & Scope, 2.1 macOS (Darwin) Installation, 2.2 Linux / Ubuntu (Debian 12+ / Ubuntu 22.04 LTS) Installation, 2.3 Verification Commands, 2. System-Level Dependencies & Binaries, 3.1 Python Version, 3.2 Pinned `requirements.txt` / Dependency Specification, 3. Backend Python Environment (+11 more)

### Community 60 - "AppUserModel"
Cohesion: 0.13
Nodes (21): get_current_user(), get_optional_current_user(), Session, FastAPI authentication and role-based authorization dependencies., Validate Bearer access token and resolve active user from database., Resolve user if a valid token is provided; otherwise returns None without…, get_current_user_profile(), get (+13 more)

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

### Community 65 - "NoiseAnalyzer"
Cohesion: 0.16
Nodes (12): NoiseAnalyzer, BoundingBox, ndarray, PixelBoundingBox, Analyzes high-frequency sensor noise residuals and local noise variance to…, Extract high-pass noise residuals, compute block variances, and flag…, TC-FOR-03: Detect sensor noise variance anomaly when a high-noise patch is…, Verify small or empty images do not raise exceptions. (+4 more)

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
Nodes (9): PreprocessingResult, Encapsulates in-memory arrays, transformation metrics, and persisted paths., Produce the canonical SPEC-02 PreprocessingOutput model., Produce the API serializable PreprocessingResultDTO., PreprocessingResultDTO, PreprocessingStepMetric, BaseModel, Execution timing and status for an individual pipeline step. (+1 more)

### Community 74 - "test_baseline_inference.py"
Cohesion: 0.15
Nodes (12): inference_engine(), fixture, Unit tests for baseline inference engine (Phase 09 - TC-MOD-04). Tests…, Returns BaselineInferenceEngine pointing to default serialized model., Verify single certificate inference latency is under 50ms over 100 runs (TC-…, Verify batch inference matches individual single predictions., Verify inference engine raises ValueError on invalid feature vector size., Verify graceful fallback heuristic when model artifact cannot be found. (+4 more)

### Community 76 - "NoiseReductionFilter"
Cohesion: 0.18
Nodes (7): NoiseReductionFilter, Any, ndarray, Edge-preserving noise reduction filter (Bilateral or Median)., Construct the sequence of image transformation steps., PreprocessingConfig, Configuration parameters for the preprocessing pipeline stages.

### Community 78 - "test_certificate_endpoints.py"
Cohesion: 0.23
Nodes (11): _create_dummy_image_bytes(), Session, TestClient, Integration tests for certificate management REST endpoints (TC-API-02)., Verify POST /upload returns HTTP 202 and status endpoint returns job state (TC-…, Verify paginated listing and detailed retrieval of certificates., Verify DELETE /certificates/{id} deletes certificate record., test_certificate_deletion() (+3 more)

### Community 79 - "Pipeline Data Contracts & Inter-Module Interfaces"
Cohesion: 0.17
Nodes (11): 10. Module 8: Score Fusion & Final Report DTO, 1. Overview & Data Flow Sequence, 2. Shared Primitive Types & Enums, 3. Module 1: Ingestion Output, 4. Module 2: Preprocessing Output, 5. Module 3: OCR & Information Extraction Output, 6. Module 4: Text Consistency Analysis Output, 7. Module 5: Image Forensics Output (+3 more)

### Community 80 - "Dataset & Synthesis Engine Specification"
Cohesion: 0.18
Nodes (10): 1. Purpose, 2. Directory Hierarchy, 3.1 Manipulation Type 1: Text Replacement (Field Tampering), 3.2 Manipulation Type 2: Copy-Move Cloning, 3.3 Manipulation Type 3: Splicing with Poisson Blending, 3.4 Manipulation Type 4: Compression Artifact Discrepancy, 3. Synthetic Manipulation Engine Architecture, 4. Ground-Truth Manifest Annotation Schema (+2 more)

### Community 81 - "PixelBoundingBox"
Cohesion: 0.15
Nodes (18): Cluster displacement vectors using DBSCAN and verify transformation via RANSAC., Compute composite forensic authenticity score [0.0, 1.0], assemble suspicious…, CloneMatch, Represents a pair of duplicated/cloned regions identified in a copy-move…, SuspiciousRegion, PixelBoundingBox, Absolute pixel coordinates., TC-FOR-04: Test composite scoring formula, bounds [0.0, 1.0], and veto… (+10 more)

### Community 82 - "CLAHEEnhancer"
Cohesion: 0.24
Nodes (6): CLAHEEnhancer, Any, ndarray, Contrast Limited Adaptive Histogram Equalization applied to the luminance…, test_clahe_enhances_low_contrast_image(), test_clahe_on_color_certificate()

### Community 83 - "evaluate_multimodal.py"
Cohesion: 0.12
Nodes (18): evaluate_multimodal_models(), Any, Benchmark multimodal fusion strategies against held-out test dataset., Evaluate Early, Late, and Stacking Fusion methods on test dataset., generate_multimodal_features(), ndarray, Path, Train the 534D Multimodal Early Fusion MLP. (+10 more)

### Community 84 - "EasyOCREngine"
Cohesion: 0.13
Nodes (11): EasyOCREngine, ndarray, Path, Thread-safe singleton OCR engine wrapper around EasyOCR., Initialize EasyOCR Reader with CPU/GPU safety., Extract OCR tokens using EasyOCR., Any, OCRToken (+3 more)

### Community 85 - "Test Fixtures & Mock Data Specification"
Cohesion: 0.22
Nodes (8): 1. Purpose, 2. Directory Layout for Test Fixtures, 3. Standard Synthetic Certificate Fixtures, 4.1 Mock Institutions Table (`seed_institutions.json`), 4.2 Mock Student Records (`mock_students.csv`), 4. Institutional Database Seed Data, 5. Test Assertion Tolerances & Performance Thresholds, Test Fixtures & Mock Data Specification

### Community 86 - "NumberedCanvas"
Cohesion: 0.39
Nodes (4): NumberedCanvas, Any, Two-pass canvas recording total page count for 'Page X of Y' footers., Draw standard running header and running footer.

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
Cohesion: 0.12
Nodes (18): Weighted late fusion engine blending branch probabilities and sub-scores., Calculates explainable composite authenticity and risk scores via weighted…, Compute composite authenticity score [0.0, 1.0], risk score [0.0, 100.0], sub-…, WeightedLateFusion, BaseModel, Normalized sub-scores across analytical branches [0.0 = Fake, 1.0 = Genuine]., SubScoresBreakdown, Unit tests for Weighted Late Fusion calculations and factor breakdowns. (+10 more)

### Community 107 - "list_audit_logs"
Cohesion: 0.22
Nodes (10): AuditLogPaginatedList, list_audit_logs(), get, Session, AuditLogItem, AuditLogPaginatedList, BaseModel, Pydantic V2 schemas for audit logs and security event queries. (+2 more)

### Community 108 - ".analyze"
Cohesion: 0.25
Nodes (8): BoundingBox, Image, ndarray, Path, PixelBoundingBox, Compute ELA differential error curve across multiple JPEG quality levels., Helper to safely convert input image to PIL RGB Image., Compute Error Level Analysis map, ELA authenticity score, and candidate…

### Community 109 - "OCRToken"
Cohesion: 0.15
Nodes (19): ConfidenceEvaluator, Evaluates field-level confidence scores, applies manual-review thresholds…, BaseFieldExtractor, ExtractedField, ABC, Strip surrounding punctuation, multiple spaces, and non-printable noise., Represents a successfully extracted academic certificate field with spatial and…, Abstract base class for all entity field extractors. (+11 more)

### Community 110 - "Settings"
Cohesion: 0.18
Nodes (7): field_validator, Application configuration loaded from environment variables and .env file., Ensure all required runtime storage directories exist., Settings, Path, Return path to compiled PDF report if it exists., BaseSettings

### Community 111 - "run_step"
Cohesion: 0.33
Nodes (6): main(), Path, Automated All-In-One Test & Evaluation Script (CHIP TST-10). Executes the…, Run shell command with error checking and clear console output., Execute all test and evaluation phases sequentially., run_step()

### Community 113 - "2. Technology Stack Breakdown"
Cohesion: 0.17
Nodes (11): 1. Executive Summary & Architecture Overview, 2.1 Frontend Stack, 2.2 Backend API & Core Framework, 2.3 Computer Vision, OCR & Forensics Engine, 2.4 Machine Learning & Analytics, 2.5 Document Reporting & Export, 2.6 Testing, Quality Assurance & Tooling, 2. Technology Stack Breakdown (+3 more)

### Community 114 - "ablation_runner.py"
Cohesion: 0.25
Nodes (8): AblationConfig, format_ablation_table_markdown(), Any, Feature & Subsystem Ablation Study Runner (CHIP TST-07). Systematically…, Execute ablation experiments on benchmark dataset predictions., Format ablation study results into Markdown table., run_ablation_study(), TypedDict

### Community 115 - "TesseractOCREngine"
Cohesion: 0.22
Nodes (6): ndarray, Path, OCR engine wrapper around PyTesseract with graceful binary discovery., Check if pytesseract and tesseract executable are present on the system., Extract OCR tokens using PyTesseract., TesseractOCREngine

### Community 116 - "tests/conftest.py"
Cohesion: 0.24
Nodes (9): client(), db_session(), fixture, Session, TestClient, Create test tables before tests run, tear down afterwards., Provide a transactional test database session., Provide a FastAPI TestClient with database dependency overridden. (+1 more)

### Community 117 - ".extract_tokens"
Cohesion: 0.33
Nodes (4): ndarray, Path, Return configured tokens, or generate synthetic academic certificate tokens., Generate a realistic set of academic certificate OCR tokens.

### Community 118 - "app_exception_handler"
Cohesion: 0.32
Nodes (8): app_exception_handler(), generic_exception_handler(), Exception, JSONResponse, Request, Handle custom application exceptions and format into standard error envelopes., Catch-all unhandled exception handler., exception_handler

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
Nodes (23): SQLAlchemy ORM model for submitted academic certificates and verification jobs., ForensicFindingModel, Base, SQLAlchemy model for storing digital image forensic findings and suspicious…, SQLAlchemy 2.0 ORM models for all 12 relational database tables., OCRFieldModel, Base, SQLAlchemy ORM model for individual academic fields extracted via OCR. (+15 more)

### Community 125 - "AnomalyType"
Cohesion: 0.11
Nodes (32): LogicalConsistencyValidator, Validates temporal chronology, calendar feasibility, numeric grade boundaries,…, ConsistencyCheckItem, Combines individual typographical, spacing, formatting, and logical sub-scores…, Compute the weighted composite score, enforce veto penalties, and assemble…, ScoreAggregator, ConsistencyCheckItem, CheckStatus (+24 more)

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
Nodes (17): BoundingBox, PixelBoundingBox, Compute combined normalized and pixel bounding boxes for a list of tokens., BoundingBox, PixelBoundingBox, Convert to canonical normalized BoundingBox [0.0, 1.0] and PixelBoundingBox., Create an anomalous region spanning the two interacting tokens., BoundingBox (+9 more)

### Community 132 - "ForensicHeatmapGenerator"
Cohesion: 0.23
Nodes (10): ForensicHeatmapGenerator, ndarray, Path, Synthesizes Error Level Analysis, Copy-Move clone regions, and Noise variance…, Create high-contrast thermal anomaly map and save annotated PNG to disk., Path, TC-FOR-05: Verify high-contrast thermal heatmap is properly generated and saved., Verify clone matches draw bounding boxes and connecting lines on the heatmap. (+2 more)

### Community 133 - "match_seal_and_logo"
Cohesion: 0.19
Nodes (15): match_seal_and_logo(), Any, ndarray, Extract university seal/logo ROI and evaluate geometric & color consistency.…, Bounding box coordinates for seal/logo/emblem in pixel dimensions., SealROI, _create_template_with_seal(), ndarray (+7 more)

### Community 134 - ".run"
Cohesion: 0.50
Nodes (3): Any, ndarray, Sequentially execute registered steps, tracking elapsed time and context.

### Community 135 - "cleanup_service.py"
Cohesion: 0.25
Nodes (6): CleanupService, Path, Session, Orphan file garbage collection and temporary scratch space purger., Purges orphaned temporary uploads, rasterized images, and scratch artifacts…, Scan and purge temporary files older than max_age_hours. Returns total number…

### Community 136 - "upload_certificate"
Cohesion: 0.25
Nodes (8): delete_certificate(), BackgroundTasks, post, Request, UploadFile, upload_certificate(), CertificateUploadResponse, delete

### Community 137 - "DegreeExtractor"
Cohesion: 0.39
Nodes (3): DegreeExtractor, Extracts degree qualification, program title, and specialization branch., Extract degree and program from lines.

### Community 138 - "AppException"
Cohesion: 0.12
Nodes (14): AppException, ForbiddenError, NotFoundError, PipelineError, Any, Exception, Resource not found error., Input or schema validation error. (+6 more)

### Community 139 - "RollNumberExtractor"
Cohesion: 0.36
Nodes (3): Extracts student roll number, registration number, USN, or enrollment ID., Extract registration / roll number via labels and strict pattern matches., RollNumberExtractor

### Community 141 - ".build_story"
Cohesion: 0.15
Nodes (10): _fit_image(), Any, Image, Path, Load image from path and scale proportionally to fit within max bounds., Construct the flowable story sequence for ReportLab., get_report_styles(), ReportLab stylesheet, typography, color palette, and dynamic numbered canvas. (+2 more)

### Community 142 - "run_template_diagnostics"
Cohesion: 0.29
Nodes (7): Any, Run diagnostics on template storage, cached descriptors, and database latency., template_diagnostics(), Any, Session, Execute health checks on template storage, descriptor cache, and database index…, run_template_diagnostics()

### Community 143 - "ingestion/service.py"
Cohesion: 0.08
Nodes (31): post, UploadFile, Handle multipart file upload, validate integrity, and store for verification…, upload_document(), check_duplicate_hash(), compute_sha256(), Path, Session (+23 more)

### Community 145 - "explainability.py"
Cohesion: 0.05
Nodes (63): Coordinate mapping and transformation between processed and original image…, Explainability, feature attributions, and visual evidence overlay subsystem., NLGExplanationGenerator, Any, Natural Language Generation (NLG) engine for human-readable verification…, Synthesizes raw analytical findings and scores into structured natural language…, Generate executive summary paragraph for decision., Synthesize detailed finding bullets categorized by analytical domain. (+55 more)

### Community 146 - "trained_rf"
Cohesion: 0.67
Nodes (3): fixture, Fixture returning a fitted random forest model on synthetic features., trained_rf()

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

### Community 157 - "schemas/__init__.py"
Cohesion: 0.12
Nodes (24): Any, CertificateFields, ndarray, Extracts a standardized 22-dimensional float32 feature vector from upstream…, Alias mapping upstream pipeline outputs to extract()., Convenience method returning directly the 22D float32 NumPy array., Construct the 22-dimensional tabular feature vector with robust fallback…, TabularFeatureExtractor (+16 more)

### Community 162 - "evaluate_baseline_model"
Cohesion: 0.40
Nodes (5): evaluate_baseline_model(), Any, DataFrame, Path, Evaluate trained model on held-out test set, generating metrics and diagnostic…

### Community 163 - "TabularDataPreprocessor"
Cohesion: 0.14
Nodes (12): DataFrame, ndarray, Path, Load or generate train/val/test DataFrames., Preprocesses and normalizes 22-dimensional tabular certificate features., Fit scaler on training data matrix strictly., Standardize feature matrix., Serialize fitted preprocessor to disk. (+4 more)

### Community 164 - "generate_synthetic_feature_dataset"
Cohesion: 0.14
Nodes (18): Unit tests for ML model evaluation (Phase 09 - TC-MOD-02). Tests held-out test…, Verify evaluation generates metrics meeting specification and generates plots., test_evaluate_baseline_model_metrics(), Unit tests for ML model training pipeline (Phase 09 - TC-MOD-01). Tests 5-fold…, Verify that train_baseline_models trains 4 candidates with 5-fold CV and saves…, test_train_baseline_models_pipeline(), extract_and_save_dataset_features(), generate_synthetic_feature_dataset() (+10 more)

### Community 166 - "visual_model/__init__.py"
Cohesion: 0.13
Nodes (19): Grad-CAM (Gradient-weighted Class Activation Mapping) for visual explainability., Deep learning visual tampering classification module., denormalize_image(), get_inference_transforms(), get_train_transforms(), ndarray, Tensor, Image transformation and normalization pipelines for certificate visual… (+11 more)

### Community 168 - "export_model.py"
Cohesion: 0.32
Nodes (7): compute_sha256(), generate_manifest(), Any, Path, Model export and manifest generation script for Phase 09 ML Baseline (CHIP…, Compute sha256 checksum of a file., Generate production model manifest JSON.

### Community 169 - "ScoreFusionService"
Cohesion: 0.05
Nodes (52): Base, SQLAlchemy ORM model for final verification decisions and reports., SQLAlchemy model persisting final multimodal verification decisions., VerificationReportModel, concatenate_features(), MultimodalFusionMLP, ndarray, Tensor (+44 more)

### Community 171 - "ForensicAnalysisResult"
Cohesion: 0.11
Nodes (24): ForensicService, get_forensic_service(), ndarray, Path, Run forensics and return canonical SPEC-02 ForensicsOutput., FastAPI dependency injection provider for ForensicService., Orchestrates comprehensive classical digital image forensics: Error Level…, Run complete forensic analysis suite on the pristine uploaded certificate image. (+16 more)

### Community 172 - "VisualEmbeddingExtractor"
Cohesion: 0.11
Nodes (17): device, Image, ndarray, Path, Tensor, Visual feature embedding extractor for multimodal fusion., Extracts 512-dimensional L2-normalized visual feature embeddings from…, Extract normalized 512D embedding from tensor of shape (1, 3, H, W) or (3, H,… (+9 more)

### Community 175 - ".predict_batch"
Cohesion: 0.40
Nodes (3): ndarray, Perform batch inference on an (N, 22) array of features., Perform inference on a single 22-dimensional feature vector. Returns: tuple of…

### Community 179 - "MLInferenceOutput"
Cohesion: 0.09
Nodes (33): MLPredictionModel, Base, SQLAlchemy ORM model for ML manipulation predictions., SQLAlchemy model for persisting machine learning manipulation predictions., Path, Session, Production service for deep learning visual certificate classification., Convenience method returning canonical SPEC-02 pipeline contract schema. (+25 more)

### Community 180 - ".classify_certificate"
Cohesion: 0.47
Nodes (4): Any, Session, Convenience method returning canonical SPEC-02 pipeline contract schema., Extract features, run inference, calculate local contributions, and return full…

### Community 181 - "InstitutionModel"
Cohesion: 0.08
Nodes (47): bulk_import_records(), get_institution(), list_institutions(), get, post, Request, Session, UploadFile (+39 more)

### Community 182 - "ExtractedFieldDTO"
Cohesion: 0.33
Nodes (5): CertificateFields, Evaluate fields, compute average confidence, flag low confidence, and build…, ExtractedFieldDTO, BaseModel, Structured representation of an extracted academic certificate entity.

### Community 183 - "database.py"
Cohesion: 0.08
Nodes (29): Run migrations in 'offline' mode., Run migrations in 'online' mode., run_migrations_offline(), run_migrations_online(), FastAPI router for immutable compliance audit log inspection., get_detailed_health(), get_health(), get_ingestion_health() (+21 more)

### Community 184 - "CertificateModel"
Cohesion: 0.22
Nodes (13): CertificateModel, Base, Core certificate entity tracking document ingestion, lifecycle, and…, profile_pipeline(), Path, Benchmark stage execution times across provided certificate images., Session, TestClient (+5 more)

### Community 185 - "InstitutionExtractor"
Cohesion: 0.40
Nodes (3): InstitutionExtractor, Extracts issuing university or college name from the header region of the…, Extract institution name from header lines (top 40% of document).

### Community 187 - ".render_overlay"
Cohesion: 0.50
Nodes (3): ndarray, Path, Render color-coded bounding boxes and field badges over certificate image.

### Community 188 - "CertificateFields"
Cohesion: 0.04
Nodes (90): download_json_endpoint(), download_pdf_endpoint(), get_report_endpoint(), get, JSONResponse, Session, FastAPI router for verification report retrieval, verification, and PDF/JSON…, verify_report_integrity_endpoint() (+82 more)

### Community 189 - "test_api_report_endpoints_lifecycle"
Cohesion: 0.50
Nodes (4): Session, TestClient, Verify GET /api/v1/reports/{id}, /json, /pdf, and /verify endpoints (TC-REP-05)., test_api_report_endpoints_lifecycle()

### Community 190 - "export_visual_model.py"
Cohesion: 0.50
Nodes (3): export_and_optimize(), Export and optimize Certificate Visual CNN for production deployment., Export TorchScript model, quantized model, and benchmark CPU latency.

### Community 193 - "task_runner.py"
Cohesion: 0.15
Nodes (13): AsyncTaskRunner, FastAPIBackgroundTaskRunner, get_task_runner(), ABC, Any, BackgroundTasks, Asynchronous task runner interface and FastAPI BackgroundTasks execution…, Abstract interface for dispatching asynchronous verification pipeline jobs. (+5 more)

### Community 195 - "e2e/conftest.py"
Cohesion: 0.29
Nodes (9): genuine_sample_path(), manipulated_sample_path(), fixture, Path, Test fixtures for End-to-End integration test suite., Path to known genuine certificate image., Path to known manipulated certificate image., Generate a clean 3-page academic transcript PDF. (+1 more)

### Community 198 - "analytics_service.py"
Cohesion: 0.16
Nodes (23): get_analytics_summary(), get_system_diagnostic_health(), get, Session, FastAPI router for administrative fraud analytics, KPI metrics, and system…, AnalyticsSummaryResponse, ModalityBreakdownItem, PipelineLatencyBreakdown (+15 more)

### Community 199 - "create_dataset_splits"
Cohesion: 0.29
Nodes (5): create_dataset_splits(), Any, Path, Dataset Splitter & Ground Truth Manifest Generator. Partitions generated…, Split samples into train, val, and test partitions with out-of-distribution…

### Community 202 - "primitives.py"
Cohesion: 0.18
Nodes (14): ELAAnalyzer, Performs Error Level Analysis (ELA) to detect JPEG compression inconsistencies…, ForensicScoreCalculator, Aggregates Error Level Analysis, Copy-Move, and Noise consistency scores into a…, ForensicConfig, Configuration parameters for Error Level Analysis, Copy-Move, and Noise…, Enum, Path (+6 more)

### Community 205 - "endpoints/auth.py"
Cohesion: 0.07
Nodes (50): change_password(), _check_rate_limit(), _clear_failed_attempts(), login(), logout(), post, Request, Session (+42 more)

### Community 207 - "security.py"
Cohesion: 0.12
Nodes (25): create_access_token(), create_refresh_token(), get_password_hash(), Cryptographic security utilities: bcrypt password hashing and JWT issuance., Hash a plaintext password using bcrypt with 12 work factor rounds., Create a signed, stateless JWT access token (default expiry: 15 minutes)., Create a signed JWT refresh token with unique JTI (default expiry: 7 days)., Database seeding script initializing default institutions and test users (CHIP… (+17 more)

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
Cohesion: 0.09
Nodes (24): Verify a plaintext password against its bcrypt hash in constant time., Enforce password complexity requirements (NFR-02). Rules: - Minimum 8…, validate_password_strength(), verify_password(), Any, Session, Record an audit entry into the database. Args: db: Active SQLAlchemy database…, Session (+16 more)

### Community 224 - "TextConsistencyConfig"
Cohesion: 0.14
Nodes (8): ndarray, Analyzes character stroke widths using Stroke Width Transform and distance…, Compute stroke width metrics across tokens and flag weight discrepancies.…, Estimate the mean stroke width of characters within a token's bounding box., StrokeWidthAnalyzer, BaseModel, Configuration thresholds for typographical and textual consistency checks., TextConsistencyConfig

### Community 225 - "test_graceful_degradation_under_partial_failure"
Cohesion: 0.25
Nodes (7): Path, Session, TestClient, Graceful degradation and fault-tolerant fallback recovery test (TC-E2E-04)., TC-E2E-04: Graceful degradation when template matching encounters simulated…, test_graceful_degradation_under_partial_failure(), patch

### Community 227 - "VerificationVerdict"
Cohesion: 0.08
Nodes (45): get_certificate_details(), get_certificate_status(), list_certificates(), get, Session, FastAPI router for certificate document upload, status polling, and…, Verdict determination and confidence calibration engine., Classifies authenticity scores into canonical project verdicts with calibrated… (+37 more)

### Community 229 - "CopyMoveDetector"
Cohesion: 0.15
Nodes (14): CopyMoveDetector, ndarray, Detects duplicated or cloned elements (seals, stamps, signatures, text patches)…, Detect copy-move forgery clusters and return authenticity score and clone…, Extract SIFT keypoints and descriptors with automatic fallback to ORB., Match descriptors against themselves and filter out self-matches and nearby…, _draw_complex_stamp(), ndarray (+6 more)

### Community 230 - "test_multipage_pdf_workflow"
Cohesion: 0.29
Nodes (6): Path, Session, TestClient, End-to-End multi-page PDF upload and page-1 rasterization verification test…, TC-E2E-03: Multi-page PDF upload, high-resolution page-1 rasterization, and…, test_multipage_pdf_workflow()

## Knowledge Gaps
- **855 isolated node(s):** `ai-certificate-verification-backend`, `run_all_tests.sh script`, `smoke_test.sh script`, `name`, `private` (+850 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2122 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CertificateFields` connect `CertificateFields` to `TemplateVerificationService`, `OCRService`, `AnomalousRegion`, `.analyze`, `fallback_handler.py`, `OCRToken`, `.run_pipeline`, `PixelBoundingBox`, `template_matching/service.py`, `test_api_report_endpoints_lifecycle`, `AnomalyType`, `verify_student_record`, `ExtractedFieldDTO`, `InstitutionModel`, `._validate_dates`, `pipeline_orchestrator.py`, `schemas/__init__.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `OCRToken` connect `OCRToken` to `CertificateIdExtractor`, `BoundingBox`, `OCRService`, `ocr/__init__.py`, `TokenBuilder`, `DegreeExtractor`, `AnomalousRegion`, `RollNumberExtractor`, `TextLine`, `DateExtractor`, `schemas/__init__.py`, `.analyze`, `fallback_handler.py`, `test_field_extractors.py`, `ExtractedFieldDTO`, `InstitutionExtractor`, `.render_overlay`, `PixelBoundingBox`, `EasyOCREngine`, `TextConsistencyConfig`, `TesseractOCREngine`, `.extract_tokens`, `StudentNameExtractor`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `CertificateVisualCNN` connect `CertificateVisualCNN` to `visual_model/__init__.py`, `GradCAMExplainer`, `VisualEmbeddingExtractor`, `MLInferenceOutput`, `create_dataloaders`, `train_visual_cnn`, `export_visual_model.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `OCRToken` (e.g. with `BaseOCREngine` and `ConfidenceEvaluator`) actually correct?**
  _`OCRToken` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `TextLine` (e.g. with `BaseFieldExtractor` and `CertificateIdExtractor`) actually correct?**
  _`TextLine` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `CertificateFields` (e.g. with `TabularFeatureExtractor` and `ConfidenceEvaluator`) actually correct?**
  _`CertificateFields` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `BoundingBox` (e.g. with `CopyMoveDetector` and `ELAAnalyzer`) actually correct?**
  _`BoundingBox` has 17 INFERRED edges - model-reasoned connections that need verification._