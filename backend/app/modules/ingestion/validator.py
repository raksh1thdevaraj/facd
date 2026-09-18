from pathlib import Path
from typing import BinaryIO, Optional, Tuple

import pypdf
import pypdf.errors
from PIL import Image, UnidentifiedImageError

from app.core.exceptions import (
    CorruptedFileError,
    EmptyFileError,
    EncryptedPdfError,
    FileTooLargeError,
    InsufficientResolutionError,
    InvalidFileError,
    UnsupportedFileTypeError,
)

# Magic bytes definitions
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_PDF = b"%PDF-"

# Resolution constraints
MIN_RES_LONG = 800
MIN_RES_SHORT = 600


class IngestionValidator:
    """Validates file format, magic signatures, file size, integrity, and dimensions."""

    @staticmethod
    def validate_file_signature(stream: BinaryIO, declared_filename: Optional[str] = None) -> str:
        """Inspect the initial bytes of the stream to verify file type against allowed MIME types.

        Resets stream pointer to 0 before returning.
        """
        try:
            stream.seek(0)
            header = stream.read(32)
            stream.seek(0)
        except Exception as exc:
            raise InvalidFileError(f"Unable to read file header: {exc}") from exc

        if not header or len(header) == 0:
            raise EmptyFileError("Uploaded file is empty (0 bytes).")

        if len(header) < 4:
            raise InvalidFileError("File header is too short to determine file type.")

        if header.startswith(MAGIC_JPEG):
            return "image/jpeg"
        elif header.startswith(MAGIC_PNG):
            return "image/png"
        elif header.startswith(MAGIC_PDF):
            return "application/pdf"

        # Check if malicious executable or text was passed
        file_hint = f" for '{declared_filename}'" if declared_filename else ""
        raise UnsupportedFileTypeError(
            f"Uploaded file signature{file_hint} is not supported. Allowed formats: JPEG, PNG, PDF."
        )

    @staticmethod
    def validate_file_size(file_size_bytes: int, max_bytes: int = 10 * 1024 * 1024) -> None:
        """Enforce file size limits: Reject 0-byte and oversized files."""
        if file_size_bytes == 0:
            raise EmptyFileError("Uploaded file is empty (0 bytes).")
        if file_size_bytes > max_bytes:
            max_mb = max_bytes / (1024 * 1024)
            cur_mb = file_size_bytes / (1024 * 1024)
            raise FileTooLargeError(
                f"File size ({cur_mb:.2f}MB) exceeds the maximum limit of {max_mb:.0f}MB."
            )

    @staticmethod
    def validate_image_integrity(
        file_path: Path, mime_type: Optional[str] = None
    ) -> Tuple[int, int]:
        """Verify image or PDF can be opened and decoded without corruption.

        Returns (width, height) for image files, or (0, 0) for PDF files.
        """
        if not file_path.exists():
            raise InvalidFileError(f"Target file does not exist: {file_path}")

        ext = file_path.suffix.lower()

        if ext == ".pdf" or mime_type == "application/pdf":
            try:
                reader = pypdf.PdfReader(str(file_path))
                if reader.is_encrypted:
                    raise EncryptedPdfError(
                        "Password-protected PDF files cannot be processed. "
                        "Please upload an unprotected copy."
                    )
                page_count = len(reader.pages)
                if page_count == 0:
                    raise CorruptedFileError("PDF file contains no pages.")
                # Verify first page can be parsed
                _ = reader.pages[0].mediabox
                return 0, 0
            except EncryptedPdfError:
                raise
            except pypdf.errors.FileNotDecryptedError as exc:
                raise EncryptedPdfError(
                    "Password-protected PDF files cannot be processed. "
                    "Please upload an unprotected copy."
                ) from exc
            except (pypdf.errors.PdfReadError, Exception) as exc:
                raise CorruptedFileError(f"Corrupt or invalid PDF file: {exc}") from exc

        # Image integrity check
        try:
            with Image.open(file_path) as img:
                img.verify()

            # Deep inspection: re-open and force raster decode to catch truncated scanlines
            with Image.open(file_path) as img:
                img.load()
                width, height = img.size
                return width, height
        except UnidentifiedImageError as exc:
            raise CorruptedFileError(f"Cannot identify image file format: {exc}") from exc
        except (IOError, SyntaxError, OSError, ValueError) as exc:
            raise CorruptedFileError(f"Corrupted or truncated image data: {exc}") from exc

    @staticmethod
    def validate_dimensions(
        width: int,
        height: int,
        min_width: int = MIN_RES_SHORT,
        min_height: int = MIN_RES_LONG,
    ) -> Tuple[int, int]:
        """Validate that image meets minimum resolution (800x600) in portrait or landscape."""
        is_landscape = width >= MIN_RES_LONG and height >= MIN_RES_SHORT
        is_portrait = width >= MIN_RES_SHORT and height >= MIN_RES_LONG

        if not (is_landscape or is_portrait):
            raise InsufficientResolutionError(
                f"Image resolution {width}x{height} is too low for verification. "
                f"Minimum required resolution is 800x600 pixels (or 600x800 for portrait)."
            )
        return width, height
