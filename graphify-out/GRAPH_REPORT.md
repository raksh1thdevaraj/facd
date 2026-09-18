# Graph Report - .  (2026-09-19)

## Corpus Check
- 217 files · ~223,043 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 885 nodes · 1669 edges · 87 communities (84 shown, 3 thin omitted)
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 589 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Schemas Primitives Pipeline|Schemas Primitives Pipeline]]
- [[_COMMUNITY_Core Exceptions Ingestion|Core Exceptions Ingestion]]
- [[_COMMUNITY_Ocr Engine Easyocr|Ocr Engine Easyocr]]
- [[_COMMUNITY_Ocr Service Field|Ocr Service Field]]
- [[_COMMUNITY_Package Devdependencies Dependencies|Package Devdependencies Dependencies]]
- [[_COMMUNITY_Types Index Components|Types Index Components]]
- [[_COMMUNITY_Preprocessing Perspective Warper|Preprocessing Perspective Warper]]
- [[_COMMUNITY_Preprocessing Contrast Enhancer|Preprocessing Contrast Enhancer]]
- [[_COMMUNITY_Tsconfig Compileroptions Paths|Tsconfig Compileroptions Paths]]
- [[_COMMUNITY_Field Extractors Extractor|Field Extractors Extractor]]
- [[_COMMUNITY_Ocr Spatial Analyzer|Ocr Spatial Analyzer]]
- [[_COMMUNITY_Preprocessing Modules Base|Preprocessing Modules Base]]
- [[_COMMUNITY_Preprocessing Result Artifact|Preprocessing Result Artifact]]
- [[_COMMUNITY_Deskewer Preprocessing Rationale|Deskewer Preprocessing Rationale]]
- [[_COMMUNITY_Preprocessing Service Rationale|Preprocessing Service Rationale]]
- [[_COMMUNITY_Generate Scripts Genuine|Generate Scripts Genuine]]
- [[_COMMUNITY_Ingestion Storage Manager|Ingestion Storage Manager]]
- [[_COMMUNITY_Generate Templates Scripts|Generate Templates Scripts]]
- [[_COMMUNITY_Name Field Extractors|Name Field Extractors]]
- [[_COMMUNITY_Scripts Generate Manipulated|Scripts Generate Manipulated]]
- [[_COMMUNITY_Health Ingestion Database|Health Ingestion Database]]
- [[_COMMUNITY_Field Extractors Extractor|Field Extractors Extractor]]
- [[_COMMUNITY_Degree Field Extractors|Degree Field Extractors]]
- [[_COMMUNITY_Field Extractors Roll|Field Extractors Roll]]
- [[_COMMUNITY_Ingestion Service Rationale|Ingestion Service Rationale]]
- [[_COMMUNITY_Field Extractors Date|Field Extractors Date]]
- [[_COMMUNITY_Health Rationale Endpoint|Health Rationale Endpoint]]
- [[_COMMUNITY_Ingestion Service Rationale|Ingestion Service Rationale]]
- [[_COMMUNITY_Field Extractors Extractor|Field Extractors Extractor]]
- [[_COMMUNITY_Preprocessing Diagnostics Pipeline|Preprocessing Diagnostics Pipeline]]
- [[_COMMUNITY_Conftest Rationale Session|Conftest Rationale Session]]
- [[_COMMUNITY_Pdf Rasterizer Encrypted|Pdf Rasterizer Encrypted]]
- [[_COMMUNITY_Tsconfig Node Compileroptions|Tsconfig Node Compileroptions]]
- [[_COMMUNITY_Dataset Synthesis Rationale|Dataset Synthesis Rationale]]
- [[_COMMUNITY_Schemas Rationale Bounding|Schemas Rationale Bounding]]
- [[_COMMUNITY_Base Engine Ocr|Base Engine Ocr]]
- [[_COMMUNITY_Main Exception Handler|Main Exception Handler]]
- [[_COMMUNITY_Metadata Ingestion Extractor|Metadata Ingestion Extractor]]
- [[_COMMUNITY_Ingestion Rasterizer Rationale|Ingestion Rasterizer Rationale]]
- [[_COMMUNITY_Dataset Scripts Split|Dataset Scripts Split]]
- [[_COMMUNITY_Main Lifespan Rationale|Main Lifespan Rationale]]
- [[_COMMUNITY_Ingestion Fingerprint Modules|Ingestion Fingerprint Modules]]
- [[_COMMUNITY_Preprocessing Pipeline Preprocessingpipeline|Preprocessing Pipeline Preprocessingpipeline]]
- [[_COMMUNITY_Validate Dataset Scripts|Validate Dataset Scripts]]
- [[_COMMUNITY_Config Settings Rationale|Config Settings Rationale]]
- [[_COMMUNITY_Preprocessing Resizer Rationale|Preprocessing Resizer Rationale]]
- [[_COMMUNITY_Binarizer Binarization Ndarray|Binarizer Binarization Ndarray]]
- [[_COMMUNITY_Dataset Synthesis Rationale|Dataset Synthesis Rationale]]
- [[_COMMUNITY_Ingestion Service Path|Ingestion Service Path]]
- [[_COMMUNITY_Ingestion Metadata Extractor|Ingestion Metadata Extractor]]
- [[_COMMUNITY_Dataset Stats Scripts|Dataset Stats Scripts]]
- [[_COMMUNITY_Ocr Base Engine|Ocr Base Engine]]
- [[_COMMUNITY_Scripts Run Preprocessing|Scripts Run Preprocessing]]
- [[_COMMUNITY_Metadata Extractor Image|Metadata Extractor Image]]
- [[_COMMUNITY_Health Endpoints Api|Health Endpoints Api]]
- [[_COMMUNITY_Ocr Service Get|Ocr Service Get]]
- [[_COMMUNITY_Scripts Run Ocr|Scripts Run Ocr]]
- [[_COMMUNITY_Pkg Ai Certificate|Pkg Ai Certificate]]

## God Nodes (most connected - your core abstractions)
1. `ExtractedField` - 52 edges
2. `BaseFieldExtractor` - 48 edges
3. `TextLine` - 44 edges
4. `BoundingBox` - 42 edges
5. `PixelBoundingBox` - 36 edges
6. `BaseOCREngine` - 26 edges
7. `InvalidFileError` - 24 edges
8. `OCRService` - 24 edges
9. `BasePreprocessingStep` - 24 edges
10. `StudentNameExtractor` - 22 edges

## Surprising Connections (you probably didn't know these)
- `generate_synthetic_record()` --calls--> `datetime`  [INFERRED]
  ml/scripts/generate_genuine.py → backend/app/modules/ingestion/metadata_extractor.py
- `AppException` --uses--> `AppException`  [INFERRED]
  backend/app/main.py → backend/app/core/exceptions.py
- `BinaryIO` --uses--> `InvalidFileError`  [INFERRED]
  backend/app/modules/ingestion/storage_manager.py → backend/app/core/exceptions.py
- `ndarray` --uses--> `BaseOCREngine`  [INFERRED]
  backend/app/modules/ocr/easyocr_engine.py → backend/app/modules/ocr/base_engine.py
- `OCRToken` --uses--> `BaseOCREngine`  [INFERRED]
  backend/app/modules/ocr/easyocr_engine.py → backend/app/modules/ocr/base_engine.py

## Import Cycles
- 1-file cycle: `backend/app/main.py -> backend/app/main.py`
- 1-file cycle: `backend/app/modules/ingestion/storage_manager.py -> backend/app/modules/ingestion/storage_manager.py`
- 1-file cycle: `backend/app/modules/preprocessing/artifact_manager.py -> backend/app/modules/preprocessing/artifact_manager.py`
- 1-file cycle: `backend/app/modules/ingestion/metadata_extractor.py -> backend/app/modules/ingestion/metadata_extractor.py`
- 1-file cycle: `backend/app/modules/preprocessing/service.py -> backend/app/modules/preprocessing/service.py`

## Communities (87 total, 3 thin omitted)

### Community 0 - "Schemas Primitives Pipeline"
Cohesion: 0.07
Nodes (55): ExtractedField, OCRToken, OCRToken, TextLine, OCROutput, OCRToken, Any, BaseModel (+47 more)

### Community 1 - "Core Exceptions Ingestion"
Cohesion: 0.06
Nodes (38): Any, BinaryIO, Path, Path, AppException, CorruptedFileError, EmptyFileError, EncryptedPdfError (+30 more)

### Community 2 - "Ocr Engine Easyocr"
Cohesion: 0.05
Nodes (28): ndarray, OCRToken, Path, BaseOCREngine, ndarray, OCRToken, Path, ndarray (+20 more)

### Community 3 - "Ocr Service Field"
Cohesion: 0.12
Nodes (25): BaseOCREngine, ndarray, OCROutput, Path, GradeExtractor, Extracts CGPA, GPA, percentage, and graduation division/class., InstitutionExtractor, Extracts issuing university or college name from the header region of the certif (+17 more)

### Community 4 - "Package Devdependencies Dependencies"
Cohesion: 0.07
Nodes (27): dependencies, axios, clsx, lucide-react, react, react-dom, react-router-dom, tailwind-merge (+19 more)

### Community 5 - "Types Index Components"
Cohesion: 0.09
Nodes (21): Header(), SystemHealthBadge(), apiClient, checkHealth(), App(), BoundingBox, CertificateFields, CheckStatus (+13 more)

### Community 6 - "Preprocessing Perspective Warper"
Cohesion: 0.12
Nodes (21): ndarray, Any, ndarray, composite_alpha_on_white(), ensure_3channel(), Ensure the image is a standard 3-channel BGR image array., Convert an arbitrary image array (RGBA, BGR, or Grayscale) to 2D uint8 Grayscale, Convert image to CIE LAB color space. (+13 more)

### Community 7 - "Preprocessing Contrast Enhancer"
Cohesion: 0.13
Nodes (13): BasePreprocessingStep, CLAHEEnhancer, Contrast Limited Adaptive Histogram Equalization applied to the luminance channe, NoiseReductionFilter, Edge-preserving noise reduction filter (Bilateral or Median)., PerspectiveWarper, Detects document boundary corners and rectifies perspective distortion., Construct the sequence of image transformation steps. (+5 more)

### Community 8 - "Tsconfig Compileroptions Paths"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+13 more)

### Community 9 - "Field Extractors Extractor"
Cohesion: 0.15
Nodes (15): ExtractedField, ndarray, OCRToken, TextLine, ExtractedField, ndarray, OCRToken, Path (+7 more)

### Community 10 - "Ocr Spatial Analyzer"
Cohesion: 0.14
Nodes (14): ExtractedField, OCRToken, TextLine, OCRToken, Extract grade, CGPA, or class division from text lines., Represents a coherent horizontal line of text reconstructed from OCR tokens., Find tokens strictly to the right of an anchor token on the same line., Find the immediate next text line below the anchor line within a vertical distan (+6 more)

### Community 11 - "Preprocessing Modules Base"
Cohesion: 0.11
Nodes (15): Any, ndarray, Any, ndarray, Any, ndarray, Any, ndarray (+7 more)

### Community 12 - "Preprocessing Result Artifact"
Cohesion: 0.14
Nodes (14): Path, PreprocessingResult, UUID, Save enhanced image, binarized image, and thumbnail for a certificate., PreprocessingResult, Encapsulates in-memory arrays, transformation metrics, and persisted paths., Produce the canonical SPEC-02 PreprocessingOutput model., Produce the API serializable PreprocessingResultDTO. (+6 more)

### Community 13 - "Deskewer Preprocessing Rationale"
Cohesion: 0.19
Nodes (14): Any, ndarray, ndarray, Deskewer, estimate_skew_angle(), Detects rotational skew and deskews certificate images., Detect document tilt angle within [-max_angle, +max_angle] degrees.      Uses pr, Rotate image by angle (in degrees) around center, expanding canvas to prevent cl (+6 more)

### Community 14 - "Preprocessing Service Rationale"
Cohesion: 0.18
Nodes (14): Path, PreprocessingResult, UUID, PreprocessingArtifactManager, Manages filesystem persistence of preprocessed images and audit artifacts., AdaptiveBinarizer, Binarizes certificate image into crisp black-and-white for OCR ingestion., get_preprocessing_service() (+6 more)

### Community 15 - "Generate Scripts Genuine"
Cohesion: 0.15
Nodes (16): Any, Path, Any, Image, Path, generate_dataset(), main(), Dataset Pipeline Orchestrator.  Orchestrates the entire certificate synthesis li (+8 more)

### Community 16 - "Ingestion Storage Manager"
Cohesion: 0.17
Nodes (10): BinaryIO, Path, UUID, Manages secure filesystem persistence with UUID filenames and path traversal def, Create storage directory tree if missing., Strip dangerous path characters and extract clean alphanumeric extension., Stream write uploaded bytes to disk under a secure UUID filename., Clean up all files associated with a certificate ID across all storage directori (+2 more)

### Community 17 - "Generate Templates Scripts"
Cohesion: 0.17
Nodes (15): ImageDraw, Any, Image, Path, create_guilloche_pattern(), draw_decorative_border(), generate_all_templates(), generate_seal_image() (+7 more)

### Community 18 - "Name Field Extractors"
Cohesion: 0.31
Nodes (6): ExtractedField, OCRToken, TextLine, Extracts student/candidate name from certificate layout., Extract student name using labeled key-value, prefix patterns, and uppercase lay, StudentNameExtractor

### Community 19 - "Scripts Generate Manipulated"
Cohesion: 0.24
Nodes (13): Any, Image, ndarray, Path, apply_manipulation(), apply_recompression_discrepancy(), inpaint_and_replace_text(), Synthetic Certificate Tampering Engine.  Implements 5 core forensic tampering tr (+5 more)

### Community 20 - "Health Ingestion Database"
Cohesion: 0.18
Nodes (8): get_db(), FastAPI dependency for obtaining a database session., Session, Any, get_ingestion_health(), Probe the health of document ingestion dependencies (PDF renderers, disk storage, check_ingestion_health(), Inspect the operational readiness of ingestion subsystem dependencies.

### Community 21 - "Field Extractors Extractor"
Cohesion: 0.18
Nodes (9): ExtractedField, OCRToken, TextLine, BaseFieldExtractor, Strip surrounding punctuation, multiple spaces, and non-printable noise., Abstract base class for all entity field extractors., Name of the target field (e.g. 'student_name', 'register_number')., Check if any label pattern approximately appears in the line text using RapidFuz (+1 more)

### Community 22 - "Degree Field Extractors"
Cohesion: 0.29
Nodes (6): ExtractedField, OCRToken, TextLine, DegreeExtractor, Extracts degree qualification, program title, and specialization branch., Extract degree and program from lines.

### Community 23 - "Field Extractors Roll"
Cohesion: 0.27
Nodes (6): ExtractedField, OCRToken, TextLine, Extracts student roll number, registration number, USN, or enrollment ID., Extract registration / roll number via labels and strict pattern matches., RollNumberExtractor

### Community 24 - "Ingestion Service Rationale"
Cohesion: 0.27
Nodes (9): BinaryIO, IngestedDocument, MetadataExtractor, Extracts forensic metadata from image and PDF files., PDFRasterizer, Rasterizes PDF documents into 300 DPI high-resolution PNG images.      Supports, Process an uploaded certificate stream end-to-end.          Cleans up any create, IngestionValidator (+1 more)

### Community 25 - "Field Extractors Date"
Cohesion: 0.25
Nodes (6): ExtractedField, OCRToken, TextLine, DateExtractor, Extracts and standardizes certificate issue, convocation, or examination dates., Extract and normalize certificate date to ISO YYYY-MM-DD.

### Community 26 - "Health Rationale Endpoint"
Cohesion: 0.27
Nodes (9): TestClient, Verify GET /health returns valid health check payload., Verify GET /api/v1/health returns valid health check payload., Verify non-existent routes return 404., Verify GET / returns welcome payload and API information., test_404_not_found(), test_api_v1_health_endpoint(), test_root_endpoint() (+1 more)

### Community 27 - "Ingestion Service Rationale"
Cohesion: 0.33
Nodes (9): DocumentIngestionService, Handle multipart file upload, validate integrity, and store for verification pip, upload_document(), IngestedDocumentResponse, DocumentIngestionService, get_ingestion_service(), Dependency provider for FastAPI route handlers., Orchestrates document validation, storage, fingerprinting, metadata, and rasteri (+1 more)

### Community 28 - "Field Extractors Extractor"
Cohesion: 0.38
Nodes (9): _build_tokens_from_lines(), test_cert_id_and_qr_code_extractor(), test_date_extractor_various_formats(), test_degree_extractor(), test_grade_extractor(), test_institution_extractor(), test_roll_number_extractor_usn_and_labeled(), test_student_name_extractor_labeled() (+1 more)

### Community 29 - "Preprocessing Diagnostics Pipeline"
Cohesion: 0.28
Nodes (7): Any, Path, Execute diagnostic self-tests and performance benchmarks for the preprocessing s, run_preprocessing_diagnostics(), compute_sha256(), test_end_to_end_preprocessing_under_5s(), test_preprocessing_diagnostics()

### Community 30 - "Conftest Rationale Session"
Cohesion: 0.25
Nodes (8): Session, TestClient, client(), db_session(), Create test tables before tests run, tear down afterwards., Provide a transactional test database session., Provide a FastAPI TestClient with database dependency overridden., setup_test_db()

### Community 31 - "Pdf Rasterizer Encrypted"
Cohesion: 0.44
Nodes (8): Path, create_encrypted_pdf(), create_test_pdf(), Helper to generate a clean multi-page test PDF using ReportLab., Helper to encrypt a PDF using pypdf., test_encrypted_pdf_raises_encrypted_error(), test_rasterize_multipage_pdf_respects_max_pages(), test_rasterize_single_page_pdf()

### Community 32 - "Tsconfig Node Compileroptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, types, include

### Community 33 - "Dataset Synthesis Rationale"
Cohesion: 0.25
Nodes (8): copy_move_tampering(), Copy a source image patch and duplicate it over a target position., Verify text inpainting and replacement modification., Verify copy-move duplication operator., Verify localized JPEG quality degradation operator., test_copy_move_tampering(), test_inpaint_and_replace_tampering(), test_recompression_discrepancy()

### Community 34 - "Schemas Rationale Bounding"
Cohesion: 0.22
Nodes (8): Verify normalized bounding box coordinates must be 0.0 to 1.0., Verify absolute pixel coordinates., Verify IngestionOutput instantiation., Verify full Report DTO model composition and validation., test_bounding_box_validation(), test_ingestion_output_model(), test_pixel_bounding_box_validation(), test_score_fusion_and_verification_report_dto()

### Community 35 - "Base Engine Ocr"
Cohesion: 0.29
Nodes (4): ABC, BaseOCREngine, Abstract interface defining the OCR detection and character recognition contract, Name of the OCR engine backend (e.g., 'easyocr', 'pytesseract', 'mock').

### Community 36 - "Main Exception Handler"
Cohesion: 0.29
Nodes (8): app_exception_handler(), generic_exception_handler(), Handle custom application exceptions and format into standard error envelopes., Catch-all unhandled exception handler., AppException, Exception, JSONResponse, Request

### Community 37 - "Metadata Ingestion Extractor"
Cohesion: 0.39
Nodes (5): Any, Path, Extract document metadata from PDF trailer and dictionary entries., Dispatch metadata extraction based on MIME type or extension., Extract EXIF tags, software strings, and camera hardware signatures from images.

### Community 38 - "Ingestion Rasterizer Rationale"
Cohesion: 0.29
Nodes (6): Path, PDFConversionError, Failed to rasterize PDF document into image format., is_poppler_installed(), Convert up to max_pages pages of a PDF to high-resolution PNG images.          S, Check if the poppler pdftoppm executable is available on system PATH.

### Community 39 - "Dataset Scripts Split"
Cohesion: 0.25
Nodes (7): Any, Path, create_dataset_splits(), Dataset Splitter & Ground Truth Manifest Generator.  Partitions generated sample, Split samples into train, val, and test partitions with out-of-distribution isol, Verify train/val/test splitting and manifest generation., test_dataset_splits_and_manifests()

### Community 40 - "Main Lifespan Rationale"
Cohesion: 0.33
Nodes (3): lifespan(), Lifespan context manager for startup and shutdown events., FastAPI

### Community 41 - "Ingestion Fingerprint Modules"
Cohesion: 0.29
Nodes (6): Path, Session, check_duplicate_hash(), compute_sha256(), Compute the SHA-256 cryptographic hash of a file using chunked streaming.      R, Check if a certificate with the same SHA-256 checksum has already been registere

### Community 42 - "Preprocessing Pipeline Preprocessingpipeline"
Cohesion: 0.33
Nodes (4): BasePreprocessingStep, PreprocessingPipeline, Sequential executor for registered preprocessing transformation steps., Register an additional transformation step.

### Community 43 - "Validate Dataset Scripts"
Cohesion: 0.38
Nodes (6): Any, Path, main(), Dataset Validator.  Performs comprehensive data integrity checks: 1. Verifies im, Validate dataset integrity and print detailed diagnostic report., validate_dataset()

### Community 45 - "Config Settings Rationale"
Cohesion: 0.33
Nodes (4): Application configuration loaded from environment variables and .env file., Ensure all required runtime storage directories exist., Settings, BaseSettings

### Community 46 - "Preprocessing Resizer Rationale"
Cohesion: 0.40
Nodes (5): ndarray, create_thumbnail(), normalize_resolution(), Standardize image dimensions within [min_long_edge, max_long_edge] preserving as, Generate a lightweight web thumbnail preview preserving aspect ratio.

### Community 47 - "Binarizer Binarization Ndarray"
Cohesion: 0.47
Nodes (5): ndarray, create_document_with_text(), Create a white document with crisp black text and background noise., test_adaptive_binarization_polarity(), test_otsu_binarization()

### Community 48 - "Dataset Synthesis Rationale"
Cohesion: 0.33
Nodes (6): Path, TempPathFactory, generated_templates(), Generate temporary base templates fixture., Verify templates and asset files are properly generated., test_template_generation()

### Community 49 - "Ingestion Service Path"
Cohesion: 0.53
Nodes (5): Path, test_ingest_valid_pdf_document(), test_ingest_valid_png_document(), test_orphan_file_cleanup_on_failure(), test_path_traversal_filename_sanitization()

### Community 50 - "Ingestion Metadata Extractor"
Cohesion: 0.47
Nodes (5): datetime, _parse_exif_date(), _parse_pdf_date(), Parse standard PDF date format, e.g. D:20240915123000+00'00'., Parse EXIF datetime string, e.g. '2024:09:15 12:30:00'.

### Community 51 - "Dataset Stats Scripts"
Cohesion: 0.47
Nodes (5): Path, main(), print_dataset_stats(), Dataset Statistics Reporter.  Computes and prints detailed statistics regarding, Read metadata and print formatted summary tables.

### Community 53 - "Ocr Base Engine"
Cohesion: 0.40
Nodes (4): ndarray, OCRToken, Path, Extract OCR tokens with bounding boxes and confidence scores from an image.

### Community 54 - "Scripts Run Preprocessing"
Cohesion: 0.50
Nodes (4): ndarray, create_comparison_image(), main(), Create a side-by-side composite [Original | Enhanced | Binarized].

### Community 55 - "Metadata Extractor Image"
Cohesion: 0.60
Nodes (4): Path, test_clean_image_metadata_extraction(), test_image_with_photoshop_software_detected(), test_pdf_metadata_extraction()

### Community 56 - "Health Endpoints Api"
Cohesion: 0.83
Nodes (4): Session, get_health(), Probe the health of the FastAPI service and its dependencies (Database, Storage), HealthCheckResponse

## Knowledge Gaps
- **92 isolated node(s):** `Session`, `Path`, `Session`, `Any`, `ndarray` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Ingestion Metadata Extractor` to `Schemas Primitives Pipeline`, `Ingestion Service Rationale`, `Dataset Scripts Split`, `Generate Scripts Genuine`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `InvalidFileError` connect `Core Exceptions Ingestion` to `Ingestion Storage Manager`, `Preprocessing Service Rationale`, `Preprocessing Contrast Enhancer`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `OCRService` connect `Ocr Service Field` to `Ocr Engine Easyocr`, `Base Engine Ocr`, `Field Extractors Extractor`, `Ocr Spatial Analyzer`, `Name Field Extractors`, `Field Extractors Extractor`, `Degree Field Extractors`, `Field Extractors Roll`, `Ocr Service Get`, `Scripts Run Ocr`, `Field Extractors Date`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `ExtractedField` (e.g. with `ExtractedField` and `OCRToken`) actually correct?**
  _`ExtractedField` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `BaseFieldExtractor` (e.g. with `ExtractedField` and `ndarray`) actually correct?**
  _`BaseFieldExtractor` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `TextLine` (e.g. with `OCRToken` and `TextLine`) actually correct?**
  _`TextLine` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `BoundingBox` (e.g. with `OCRToken` and `TextLine`) actually correct?**
  _`BoundingBox` has 33 INFERRED edges - model-reasoned connections that need verification._