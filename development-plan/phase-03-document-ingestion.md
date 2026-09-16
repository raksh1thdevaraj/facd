# Phase 03 — Document Ingestion

## 1. Purpose

Implement the document ingestion subsystem responsible for receiving, validating, sanitizing, fingerprinting, and storing academic certificate files uploaded in image (JPEG, PNG) or document (PDF) format. This phase converts incoming documents into high-resolution, standardized image files ready for downstream preprocessing and analysis while ensuring strict security against malicious file uploads.

## 2. Why This Phase Exists

Academic certificates arrive in diverse formats and qualities: multi-page PDFs, scanned JPEGs, mobile camera photos, and PNG exports. Before any computer vision, OCR, or ML model can inspect a document, the system must:
- Prove the file is safe to process (not an executable or disguised exploit).
- Verify the file is actually a readable document/image with sufficient resolution.
- Extract file-level forensic metadata (EXIF, creation tools, editing timestamps) before any processing strips it.
- Convert PDF documents into high-resolution bitmap images (300 DPI) suitable for OCR and pixel-level forensic analysis.
- Establish an immutable SHA-256 fingerprint for chain of custody and deduplication.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-ING-01** | Support upload of PDF, PNG, JPG/JPEG files up to 10MB | File upload handler, MIME validation, file size check |
| **FR-ING-02** | Convert PDF documents to high-resolution images (min 300 DPI) | `pdf2image` + Poppler rasterization pipeline with page selection |
| **FR-ING-03** | Validate file format, integrity, and minimum image dimensions (min 800x600 px) | Magic byte inspection, PIL dimension check, corruption check |
| **FR-ING-04** | Generate SHA-256 checksum and extract file metadata (size, format, timestamp, EXIF) | Streaming SHA-256 hasher, ExifTool / PIL EXIF reader, metadata parser |
| **NFR-02** | Security & Input Sanitization | Path traversal prevention, UUID storage filenames, MIME sniffing |
| **NFR-03** | Performance (< 3s ingestion) | Streaming file validation, fast in-memory checks |
| **TC-ING-01** | Valid JPEG/PNG upload test | Chip ING-12 |
| **TC-ING-02** | Valid PDF upload and 300 DPI rasterization test | Chip ING-13 |
| **TC-ING-03** | Oversized file rejection (> 10MB) | Chip ING-12 |
| **TC-ING-04** | Unsupported format rejection (EXE, DOCX, TXT) | Chip ING-12 |
| **TC-ING-05** | Corrupt/truncated file rejection | Chip ING-12 |
| **TC-ING-06** | Undersized image rejection (< 800x600 px) | Chip ING-12 |

## 4. Inputs

- Raw uploaded file binary stream (from HTTP multipart request or local CLI pipeline).
- Configuration parameters (max upload size, allowed MIME types, DPI setting, storage directory paths).

## 5. Outputs

- Standardized raw image stored on disk (`storage/uploads/{uuid}.{ext}`).
- Rasterized image stored on disk for PDFs (`storage/uploads/{uuid}_page1.png`).
- Cryptographic SHA-256 checksum string.
- Extracted raw metadata dictionary (EXIF, PDF metadata, creation software, image resolution, file size).
- Validated `IngestedDocument` Pydantic model passed to downstream processing.

## 6. Dependencies

- **Previous phases:** Phase 01 (Project Foundation — configuration, directory layout, base exceptions).
- **System dependencies:** `poppler-utils` (for `pdftoppm` / `pdf2image`).
- **Python libraries:** `Pillow`, `pdf2image`, `python-multipart`, `pydantic`, `pytest`, `httpx`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── ingestion/
│   │       ├── __init__.py
│   │       ├── validator.py           # Magic bytes, MIME, size, dimension checks
│   │       ├── rasterizer.py          # PDF to image rasterization at 300 DPI
│   │       ├── metadata_extractor.py  # EXIF and document metadata extraction
│   │       ├── storage_manager.py     # Secure file storage, UUID mapping, path sanitation
│   │       └── service.py             # Orchestrator: IngestionService
│   ├── schemas/
│   │   └── ingestion.py               # Pydantic models: IngestedDocument, IngestionMetadata
│   └── api/
│       └── v1/
│           └── endpoints/
│               └── ingestion.py       # POST /api/v1/certificates/upload
└── tests/
    └── unit/
        ├── test_ingestion_validator.py
        ├── test_pdf_rasterizer.py
        ├── test_metadata_extractor.py
        └── test_ingestion_service.py
```

---

## 8. Implementation Chips

---

### CHIP ING-01 — File Format and MIME Type Verification

**Objective:** Validate that uploaded files match allowed MIME types (`image/jpeg`, `image/png`, `application/pdf`) by inspecting magic bytes rather than trusting the user-supplied file extension or Content-Type header.

**Why:** Attackers frequently disguise executable files or malicious scripts with `.jpg` or `.pdf` extensions. Only header signature inspection (magic bytes) reliably prevents arbitrary file execution attacks.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/ingestion/validator.py`

**Files to modify:** None

**Implementation:**
1. Define allowed MIME types and corresponding magic signatures:
   - JPEG: `FF D8 FF`
   - PNG: `89 50 4E 47 0D 0A 1A 0A`
   - PDF: `25 50 44 46` (`%PDF-`)
2. Implement `validate_file_signature(stream: BinaryIO) -> str` which reads the first 32 bytes and inspects the header.
3. Compare detected signature against the declared file extension.
4. Raise `UnsupportedFileTypeError` (HTTP 415) if signatures do not match allowed formats.
5. Rewind stream position (`stream.seek(0)`) after inspection.

**Inputs:** File binary stream or initial byte buffer.

**Outputs:** Detected MIME type string (`image/jpeg`, `image/png`, or `application/pdf`).

**Edge Cases:**
- Empty file (0 bytes) -> raises `InvalidFileError`.
- File smaller than 32 bytes -> raises `InvalidFileError`.
- Polyglot files (e.g. GIF-JPEG hybrids) -> strict match on valid headers only.

**Error Handling:**
- Raise `UnsupportedFileTypeError` if MIME is not in allowed list.
- Return explicit error message: `"Uploaded file type '{detected}' is not supported. Allowed formats: PDF, JPEG, PNG."`

**Security:** Never execute or pass the file to external command shells before signature verification.

**Testing:** Unit tests verifying valid PNG, valid JPEG, valid PDF, disguised `.exe` renamed to `.jpg`, and plain text file renamed to `.pdf`.

**Acceptance Criteria:**
- Detects JPEG, PNG, and PDF accurately.
- Rejects files with invalid signatures even if extension is `.jpg` or `.pdf`.
- Resets stream pointer to 0 after validation.

---

### CHIP ING-02 — File Size and Integrity Validation

**Objective:** Enforce maximum file size (10MB) and verify the image/PDF file is not truncated, corrupt, or unreadable.

**Why:** Large files cause Denial of Service (DoS) by memory exhaustion. Truncated or corrupt files crash downstream OCR or computer vision pipelines with unhandled decode errors.

**Dependencies:** CHIP ING-01.

**Files to modify:**
- `backend/app/modules/ingestion/validator.py`

**Implementation:**
1. Implement `validate_file_size(file_size_bytes: int, max_bytes: int = 10 * 1024 * 1024) -> None`.
   - If `file_size_bytes > max_bytes`, raise `FileTooLargeError` (HTTP 413).
   - If `file_size_bytes == 0`, raise `EmptyFileError` (HTTP 400).
2. Implement streaming size verification for chunked uploads to prevent memory-filling attack before total size is known.
3. Implement `validate_image_integrity(file_path: Path) -> None`:
   - For images: Open via `PIL.Image.open(file_path)` and call `image.verify()`. Catch `UnidentifiedImageError`, `IOError`, `SyntaxError`.
   - For PDFs: Attempt to read PDF trailer using `pypdf` or `pdf2image.pdfinfo_from_path`.
4. Re-open image with `PIL.Image.open()` and run `image.transpose(Image.FLIP_TOP_BOTTOM)` or access pixel data to detect corrupted byte streams that pass `verify()`.

**Inputs:** File path or byte stream, max size threshold.

**Outputs:** Boolean `True` on success; raises descriptive validation exception on failure.

**Edge Cases:**
- File exactly 10MB (10,485,760 bytes) -> allowed.
- File 10MB + 1 byte -> rejected.
- Truncated JPEG where header exists but scan data terminates early -> caught by deep pixel decode test.

**Error Handling:**
- Raise `FileTooLargeError` with current size and limit in MB.
- Raise `CorruptedFileError` with detailed reason ("Truncated image data", "Corrupt PDF trailer").

**Testing:**
- Test 10MB boundary limits (exact, +1 byte, -1 byte).
- Test file with valid header but random zeroed payload.

**Acceptance Criteria:**
- Strictly enforces 10MB maximum limit.
- Rejects corrupt or truncated images with HTTP 400 and clear error description.

---

### CHIP ING-03 — Minimum Dimension and Resolution Verification

**Objective:** Ensure certificate images have a minimum resolution of 800 x 600 pixels to guarantee OCR readability and forensic analysis viability.

**Why:** Low-resolution thumbnails or heavily downscaled screenshots do not contain sufficient pixel density for high-confidence character recognition or clone/ELA detection.

**Dependencies:** CHIP ING-01, CHIP ING-02.

**Files to modify:**
- `backend/app/modules/ingestion/validator.py`

**Implementation:**
1. Define minimum dimensions: `MIN_WIDTH = 800`, `MIN_HEIGHT = 600`.
2. Implement `validate_dimensions(width: int, height: int) -> None`:
   - Support both landscape (`width >= 800 and height >= 600`) and portrait (`width >= 600 and height >= 800`) orientations.
   - If dimensions are below thresholds, raise `InsufficientResolutionError` (HTTP 422).
3. Extract dimensions:
   - For image files: inspect `PIL.Image.open(file_path).size`.
   - For PDF files: defer dimension check to post-rasterization (at 300 DPI, an A4 page produces ~2480 x 3508 px, naturally satisfying the limit).

**Inputs:** Image width and height integers.

**Outputs:** Normalized dimensions tuple `(width, height)`.

**Edge Cases:**
- Square certificate (e.g. 750x750) -> fails because min dimension is below 800 for the longer side.
- Very high resolution (e.g. 10000x8000) -> accepted, but flagged for downscaling in Preprocessing phase if memory limits exceed threshold.

**Error Handling:**
- Raise `InsufficientResolutionError` with message: `"Image resolution {width}x{height} is too low for verification. Minimum required resolution is 800x600 pixels."`

**Testing:**
- Test 799x599 -> rejected.
- Test 800x600 -> accepted.
- Test 600x800 (portrait) -> accepted.
- Test 1920x1080 -> accepted.

**Acceptance Criteria:**
- Accepts both portrait and landscape formats meeting 800x600 bounding constraint.
- Blocks low-resolution submissions before expensive downstream processing.

---

### CHIP ING-04 — Cryptographic SHA-256 Fingerprinting and Deduplication Check

**Objective:** Compute a secure SHA-256 hash of the uploaded document stream and check against existing records to detect exact duplicate submissions.

**Why:** The SHA-256 hash provides cryptographic non-repudiation, audit trail indexing, and allows instant cache lookup if the identical document was already analyzed.

**Dependencies:** CHIP ING-01.

**Files to create:**
- `backend/app/modules/ingestion/fingerprint.py`

**Implementation:**
1. Implement `compute_sha256(file_path: Path, chunk_size: int = 65536) -> str`:
   - Read file in 64KB chunks to maintain flat memory usage even for 10MB files.
   - Update `hashlib.sha256()`.
   - Return hex digest string (64 characters).
2. Implement `check_duplicate_hash(sha256_hash: str, db_session: Session) -> Optional[Certificate]`:
   - Query `certificate` table for matching `file_hash`.
   - If match found, return existing certificate record for reference or duplicate notification.

**Inputs:** File path on disk.

**Outputs:** Lowercase 64-character SHA-256 hexadecimal string.

**Edge Cases:**
- Identical visual content saved with 1 byte of differing metadata produces a different hash -> expected behavior for cryptographic hash. (Visual deduplication is handled in Template Matching).
- Same file uploaded twice by same user -> flagged as duplicate with option to view existing report.

**Security:** Hash must be computed directly from the sanitized stored file on disk, not raw unverified network buffers.

**Testing:**
- Verify hash against known external tool (`shasum -a 256 <file>`).
- Verify streaming chunking produces identical result to in-memory hash.

**Acceptance Criteria:**
- Memory consumption remains under 1MB during hashing of 10MB files.
- Returns accurate SHA-256 string.

---

### CHIP ING-05 — Document Metadata and EXIF Extraction

**Objective:** Extract all file-level and image-level metadata, including EXIF tags, creation dates, camera/scanner models, editing software signatures, and GPS coordinates (if present).

**Why:** Fraudulent certificates are often edited using Adobe Photoshop, Canva, GIMP, or online PDF editors. These tools frequently leave software signature strings and mismatched timestamps in the metadata, providing immediate forensic clues.

**Dependencies:** CHIP ING-01.

**Files to create:**
- `backend/app/modules/ingestion/metadata_extractor.py`

**Implementation:**
1. Implement `extract_image_metadata(file_path: Path) -> dict`:
   - Use `PIL.Image.open(file_path)._getexif()` to retrieve raw EXIF tags.
   - Map numeric EXIF tags to human-readable names using `PIL.ExifTags.TAGS`.
   - Extract key forensic fields:
     - `Software` / `ProcessingSoftware` (e.g. "Adobe Photoshop 2024", "Canva", "GIMP")
     - `DateTimeOriginal`, `DateTimeDigitized`, `DateTime`
     - `Make` / `Model` (camera or scanner hardware)
     - `Orientation`
     - `ColorSpace`
2. Implement `extract_pdf_metadata(file_path: Path) -> dict`:
   - Use `pypdf.PdfReader` to extract `reader.metadata`:
     - `/Producer` (e.g. "macOS Quartz PDFContext", "iText", "ReportLab")
     - `/Creator` (e.g. "Microsoft Word", "Canva", "Adobe Illustrator")
     - `/CreationDate`, `/ModDate`
3. Normalize timestamps to ISO 8601 UTC.
4. Flag suspicious indicators:
   - `software_indicates_editing: bool` (True if software contains "photoshop", "gimp", "paint", "canva", "illustrator").
   - `metadata_stripped: bool` (True if standard camera/scanner tags are completely absent).
   - `creation_modification_mismatch: bool` (True if ModDate is significantly later than CreationDate).

**Inputs:** Path to stored image or PDF file.

**Outputs:** Structured `MetadataExtractionResult` containing:
- `raw_metadata`: Dict[str, Any]
- `software`: Optional[str]
- `creation_date`: Optional[datetime]
- `modification_date`: Optional[datetime]
- `has_exif`: bool
- `suspicious_indicators`: List[str]

**Edge Cases:**
- No EXIF present (common in web-downloaded or screenshot images) -> `has_exif=False`, return clean empty structure without exceptions.
- Malformed or corrupt EXIF tag -> skip invalid tag and log warning; do not fail ingestion.

**Testing:**
- Test with known Photoshop-edited JPEG (verifies `Software` detection).
- Test with clean scanned certificate.
- Test with screenshot having stripped metadata.
- Test with PDF created from Microsoft Word vs Canva.

**Acceptance Criteria:**
- Extracts all available EXIF and PDF tags.
- Flags graphic editing software signatures without causing unhandled errors.

---

### CHIP ING-06 — PDF Document Rasterization Pipeline

**Objective:** Convert uploaded PDF certificates into high-resolution PNG images at 300 DPI with page validation and multi-page handling.

**Why:** Downstream analysis (OCR, pixel forensics, CNN features) operates on raster images. A 300 DPI rasterization ensures fine print, university seals, micro-text, and security borders are rendered at forensic resolution.

**Dependencies:** CHIP ING-01, CHIP ING-02.

**Files to create:**
- `backend/app/modules/ingestion/rasterizer.py`

**Implementation:**
1. Implement `rasterize_pdf(pdf_path: Path, output_dir: Path, dpi: int = 300, max_pages: int = 3) -> List[Path]`:
   - Use `pdf2image.convert_from_path(pdf_path, dpi=dpi, fmt="png", thread_count=2)`.
   - Restrict to first `max_pages` (academic certificates are almost always 1 page; transcripts may be up to 3 pages).
   - Save each page to `output_dir / f"{pdf_path.stem}_page_{page_num}.png"`.
   - Return list of generated image paths.
2. Validate output raster image dimensions:
   - Ensure generated PNG has width >= 2000 and height >= 1400 (standard for 300 DPI A4/Letter).
3. Implement timeout safeguard:
   - Wrap rasterization call with 15-second process timeout to prevent PDF decompression bomb attacks.

**Inputs:** PDF file path, target DPI (default 300), output directory.

**Outputs:** List of `Path` objects pointing to generated 300 DPI PNG images.

**Edge Cases:**
- Multi-page PDF: Rasterize up to `max_pages` pages, log page count. Primary analysis targets Page 1.
- Password-protected PDF: Catch `PDFPasswordIncorrect` and raise `EncryptedPdfError` (HTTP 422).
- PDF with vector text only vs scanned image container: Both rendered cleanly to raster bitmap.

**Error Handling:**
- Raise `PDFConversionError` if Poppler fails or process times out.
- Raise `EncryptedPdfError` with message `"Password-protected PDF files cannot be processed. Please upload an unprotected copy."`

**Testing:**
- Test standard 1-page certificate PDF -> outputs 1 high-res PNG.
- Test 5-page PDF -> rasterizes first 3 pages and logs warning.
- Test password-protected PDF -> cleanly returns HTTP 422 error.

**Acceptance Criteria:**
- Rasterizes PDF at 300 DPI within 3.0 seconds for single-page certificate.
- Produces valid PNG image files compatible with Pillow and OpenCV.

---

### CHIP ING-07 — Secure File Storage Manager

**Objective:** Manage filesystem persistence of raw uploaded files and intermediate images using randomized UUID names, strict directory isolation, and path traversal prevention.

**Why:** Storing files using original user-supplied filenames introduces directory traversal vulnerabilities (`../../etc/passwd`), filename collisions, and arbitrary script execution risks on the host filesystem.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/ingestion/storage_manager.py`

**Implementation:**
1. Implement `StorageManager` class configured with base directories:
   - `storage/uploads/raw/`
   - `storage/uploads/rasterized/`
   - `storage/preprocessed/`
   - `storage/reports/`
2. Implement `save_upload_stream(file_stream: BinaryIO, original_filename: str, mime_type: str) -> StorageRecord`:
   - Generate secure UUID v4 identifier: `certificate_id = uuid.uuid4()`.
   - Sanitize extension from `original_filename` using `re.sub(r'[^a-zA-Z0-9]', '', ext)`.
   - Construct absolute path: `target_path = raw_dir / f"{certificate_id}.{safe_ext}"`.
   - Ensure path resolves strictly within `raw_dir` via `target_path.resolve().is_relative_to(raw_dir)`.
   - Stream write bytes to disk with file permissions `0o640`.
3. Implement cleanup utility `delete_certificate_files(certificate_id: UUID) -> None` for GDPR/privacy compliance.

**Inputs:** Raw upload stream, original filename, MIME type.

**Outputs:** `StorageRecord` containing `certificate_id`, `stored_file_path`, `original_filename`, `file_extension`.

**Security:**
- Strip all path characters (`/`, `\`, `..`, null bytes) from original filenames.
- Apply strict non-executable file permissions.

**Testing:**
- Test directory traversal attempt (`../../../evil.sh`) -> saved as `{uuid}.sh` in target dir, traversal defeated.
- Test concurrent uploads with identical filename -> saved with unique UUIDs, no collisions.

**Acceptance Criteria:**
- All stored files use UUID v4 filenames.
- Files cannot be written outside the configured storage directory.

---

### CHIP ING-08 — Ingestion Schemas and Domain Models

**Objective:** Define Pydantic v2 schemas and dataclasses for all ingestion inputs, outputs, validation status, and metadata structures.

**Why:** Strict type boundaries prevent runtime errors across API endpoints, service layers, and downstream pipeline modules.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/schemas/ingestion.py`

**Implementation:**
1. Define `IngestionStatus(str, Enum)`: `SUCCESS`, `VALIDATION_FAILED`, `CORRUPTED`, `UNSUPPORTED_FORMAT`.
2. Define `MetadataModel(BaseModel)`:
   - `file_size_bytes: int`
   - `mime_type: str`
   - `original_filename: str`
   - `sha256_checksum: str`
   - `image_width: int`
   - `image_height: int`
   - `software_signature: Optional[str] = None`
   - `creation_date: Optional[datetime] = None`
   - `suspicious_indicators: List[str] = []`
3. Define `IngestedDocument(BaseModel)`:
   - `certificate_id: UUID`
   - `original_file_path: Path`
   - `working_image_path: Path` (rasterized PNG if PDF, or verified image path)
   - `format: str`
   - `is_pdf: bool`
   - `page_count: int`
   - `metadata: MetadataModel`
   - `created_at: datetime`

**Inputs:** Raw extraction dictionaries.

**Outputs:** Validated Pydantic models with auto-serialization.

**Testing:** Unit tests verifying valid serialization, default values, and rejection of negative dimensions or sizes.

**Acceptance Criteria:**
- Models validate all inputs strictly.
- Compatible with FastAPI OpenAPI generation.

---

### CHIP ING-09 — Document Ingestion Orchestrator Service

**Objective:** Unify format validation, size checking, integrity testing, storage persistence, SHA-256 fingerprinting, metadata extraction, and PDF rasterization into a single `DocumentIngestionService`.

**Why:** A single service entry point encapsulates all ingestion logic, allowing it to be called identically from the FastAPI HTTP endpoint, CLI scripts, and background worker queues.

**Dependencies:** CHIP ING-01 through CHIP ING-08.

**Files to create:**
- `backend/app/modules/ingestion/service.py`

**Implementation:**
1. Implement `DocumentIngestionService`:
   ```python
   class DocumentIngestionService:
       def __init__(self, storage: StorageManager, validator: IngestionValidator):
           self.storage = storage
           self.validator = validator

       def ingest(self, file_stream: BinaryIO, original_filename: str, client_ip: str) -> IngestedDocument:
           # 1. Inspect magic bytes & MIME
           # 2. Check size limits
           # 3. Save raw file to storage with UUID
           # 4. Verify integrity & dimensions
           # 5. Compute SHA-256 hash
           # 6. Extract EXIF / document metadata
           # 7. If PDF, rasterize to 300 DPI PNG
           # 8. Return IngestedDocument model
   ```
2. Add execution timing log: Record elapsed milliseconds from upload receipt to completed ingestion.
3. Emit structured audit log on both success and failure.

**Inputs:** File stream, original filename string, client IP address.

**Outputs:** Complete `IngestedDocument` instance ready for pipeline ingestion.

**Error Handling:**
- If any step fails, clean up temporarily stored raw files to avoid orphan files on disk.
- Re-raise structured domain exceptions.

**Testing:**
- End-to-end unit test with sample JPEG, PNG, and PDF.
- Cleanup test verifying no orphan files remain if verification fails midway.

**Acceptance Criteria:**
- Completes full ingestion in < 2.0s for 5MB file.
- Cleans up scratch files on failure.

---

### CHIP ING-10 — FastAPI Document Upload Endpoint

**Objective:** Implement the HTTP endpoint `POST /api/v1/certificates/upload` accepting multipart form data with progress tracking and OpenAPI documentation.

**Why:** Provides the frontend and API clients with a secure, standard HTTP interface to submit certificates for verification.

**Dependencies:** CHIP ING-09.

**Files to create:**
- `backend/app/api/v1/endpoints/ingestion.py`

**Files to modify:**
- `backend/app/api/v1/router.py` (register ingestion router)

**Implementation:**
1. Create endpoint:
   ```python
   @router.post("/certificates/upload", response_model=IngestedDocumentResponse, status_code=status.HTTP_201_CREATED)
   async def upload_certificate(
       file: UploadFile = File(..., description="Certificate file (PDF, JPEG, or PNG up to 10MB)"),
       service: DocumentIngestionService = Depends(get_ingestion_service),
       current_user: Optional[User] = Depends(get_optional_user),
   ):
   ```
2. Stream `file.file` directly to the service to keep API server memory consumption flat.
3. Handle exceptions with mapped HTTP status codes:
   - `UnsupportedFileTypeError` -> 415
   - `FileTooLargeError` -> 413
   - `InvalidFileError`, `CorruptedFileError` -> 400
   - `InsufficientResolutionError` -> 422
4. Return standardized JSON response with `certificate_id`, `sha256_checksum`, `file_format`, `resolution`, and processing status.

**Inputs:** Multipart form request containing `file`.

**Outputs:** JSON response with HTTP 201 and `IngestedDocumentResponse`.

**Testing:** Integration tests using `httpx.AsyncClient` testing successful upload and all error status codes.

**Acceptance Criteria:**
- Returns HTTP 201 on valid submission.
- Returns clear JSON error payloads with correct HTTP status codes on validation failures.

---

### CHIP ING-11 — Ingestion Pipeline Health and Metrics

**Objective:** Expose diagnostic health checks for ingestion dependencies (`poppler-utils`, disk write access, temp storage space) and track upload metrics.

**Why:** If Poppler is missing or disk storage is full, the entire system fails. Proactive health checks ensure operations teams catch infrastructure issues immediately.

**Dependencies:** CHIP ING-06, CHIP ING-07.

**Files to create:**
- `backend/app/modules/ingestion/health.py`

**Implementation:**
1. Implement `check_ingestion_health() -> dict`:
   - Verify `pdftoppm` executable exists in system `$PATH`.
   - Verify write permissions and available free disk space (> 2GB free) in `storage/`.
   - Return status dictionary `{"poppler_available": bool, "storage_writable": bool, "disk_free_gb": float}`.
2. Hook into `/api/v1/health` endpoint.

**Acceptance Criteria:**
- Reports accurate status of Poppler and storage subsystem.

---

### CHIP ING-12 — Unit Tests: File Validation and Edge Cases

**Objective:** Implement comprehensive unit tests for all file validation rules (MIME, size, dimension, corruption).

**Dependencies:** CHIP ING-01, CHIP ING-02, CHIP ING-03.

**Files to create:**
- `backend/tests/unit/test_ingestion_validator.py`

**Implementation:**
1. Implement `test_valid_jpeg_accepted()`
2. Implement `test_valid_png_accepted()`
3. Implement `test_file_exceeding_10mb_rejected()` (TC-ING-03)
4. Implement `test_disguised_executable_rejected()` (TC-ING-04)
5. Implement `test_corrupt_jpeg_payload_rejected()` (TC-ING-05)
6. Implement `test_undersized_image_rejected()` (TC-ING-06)
7. Implement `test_empty_file_rejected()`

**Acceptance Criteria:**
- 100% test pass rate across all validator test cases.

---

### CHIP ING-13 — Unit Tests: PDF Rasterization and Metadata Extraction

**Objective:** Implement automated tests for PDF rasterization at 300 DPI and EXIF/metadata extraction accuracy.

**Dependencies:** CHIP ING-05, CHIP ING-06.

**Files to create:**
- `backend/tests/unit/test_pdf_rasterizer.py`
- `backend/tests/unit/test_metadata_extractor.py`

**Implementation:**
1. Generate test synthetic 1-page PDF fixture.
2. Test `rasterize_pdf` generates 300 DPI image with dimensions matching expected A4 pixel grid.
3. Test `extract_image_metadata` correctly detects Photoshop software tag on synthetic test image.
4. Test `extract_pdf_metadata` extracts Creator and Producer tags.

**Acceptance Criteria:**
- Confirms 300 DPI rasterization and metadata tag extraction.

---

### CHIP ING-14 — Integration Test: Ingestion API Endpoint

**Objective:** Test `POST /api/v1/certificates/upload` endpoint end-to-end with real multipart HTTP requests.

**Dependencies:** CHIP ING-10.

**Files to create:**
- `backend/tests/integration/test_ingestion_api.py`

**Implementation:**
1. Test valid PNG upload -> returns 201 Created and valid `certificate_id`.
2. Test valid PDF upload -> returns 201 Created, confirms rasterized PNG generated.
3. Test 15MB file upload -> returns 413 Payload Too Large.
4. Test `.txt` file upload -> returns 415 Unsupported Media Type.

**Acceptance Criteria:**
- All API test cases pass with correct HTTP status codes and response schemas.

---

## 9. Implementation Order and Dependencies

```
CHIP ING-01 (MIME & Magic Bytes)
    ↓
CHIP ING-02 (Size & Integrity)
    ↓
CHIP ING-03 (Resolution 800x600)
    ↓
CHIP ING-04 (SHA-256 Fingerprint) ──┐
    ↓                               │
CHIP ING-05 (Metadata / EXIF)      │
    ↓                               │
CHIP ING-06 (PDF Rasterization)     │
    ↓                               │
CHIP ING-07 (Secure Storage) ◄──────┘
    ↓
CHIP ING-08 (Schemas & Models)
    ↓
CHIP ING-09 (Ingestion Service)
    ↓
CHIP ING-10 (FastAPI Endpoint)
    ↓
CHIP ING-11 (Health & Diagnostics)
    ↓
CHIP ING-12, ING-13, ING-14 (Unit & Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Magic byte inspection validates JPEG, PNG, and PDF files reliably.
- [ ] 10MB maximum file size strictly enforced with streaming checks.
- [ ] Minimum 800x600 resolution verified for all images.
- [ ] SHA-256 checksum generated via streaming buffer without memory spikes.
- [ ] Metadata extraction identifies EXIF tags and flags editing software signatures.
- [ ] PDF rasterization generates 300 DPI PNG images via Poppler within 3 seconds.
- [ ] File storage uses secure UUID v4 paths with path traversal protections.
- [ ] `POST /api/v1/certificates/upload` returns standardized JSON with HTTP 201.
- [ ] Test cases TC-ING-01 through TC-ING-06 automated and passing.
- [ ] Orphan files cleaned up automatically if ingestion errors occur.
