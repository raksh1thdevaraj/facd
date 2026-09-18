import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from app.config import settings
from app.core.exceptions import InvalidFileError


@dataclass
class StorageRecord:
    certificate_id: UUID
    stored_file_path: Path
    original_filename: str
    file_extension: str


class StorageManager:
    """Manages secure filesystem persistence with UUID filenames and path traversal defense."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
    ):
        self.base_dir = (base_dir or settings.STORAGE_BASE_DIR).resolve()
        self.raw_dir = (self.base_dir / "uploads" / "raw").resolve()
        self.rasterized_dir = (self.base_dir / "uploads" / "rasterized").resolve()
        self.preprocessed_dir = (self.base_dir / "preprocessed").resolve()
        self.reports_dir = (self.base_dir / "reports").resolve()

        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Create storage directory tree if missing."""
        for d in [
            self.raw_dir,
            self.rasterized_dir,
            self.preprocessed_dir,
            self.reports_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename_and_ext(filename: str) -> tuple[str, str]:
        """Strip dangerous path characters and extract clean alphanumeric extension."""
        # Strip directory traversal characters, null bytes, slashes
        clean_basename = Path(filename).name
        clean_basename = clean_basename.replace("\x00", "").strip()

        ext = Path(clean_basename).suffix.lower().lstrip(".")
        safe_ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:8]
        if not safe_ext:
            safe_ext = "bin"

        return clean_basename, safe_ext

    def save_upload_stream(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        certificate_id: Optional[UUID] = None,
    ) -> StorageRecord:
        """Stream write uploaded bytes to disk under a secure UUID filename."""
        cert_id = certificate_id or uuid.uuid4()
        clean_orig_name, safe_ext = self.sanitize_filename_and_ext(original_filename)

        target_path = (self.raw_dir / f"{cert_id}.{safe_ext}").resolve()

        # Path traversal guard
        if not target_path.is_relative_to(self.raw_dir):
            raise InvalidFileError("Path traversal detected in upload filename.")

        try:
            file_stream.seek(0)
            with open(target_path, "wb") as f:
                while chunk := file_stream.read(65536):
                    f.write(chunk)

            # Set POSIX file permissions (owner read/write, group read)
            os.chmod(target_path, 0o640)
        except Exception as exc:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise InvalidFileError(f"Failed to persist file to disk: {exc}") from exc

        return StorageRecord(
            certificate_id=cert_id,
            stored_file_path=target_path,
            original_filename=clean_orig_name,
            file_extension=f".{safe_ext}",
        )

    def delete_certificate_files(self, certificate_id: UUID) -> None:
        """Clean up all files associated with a certificate ID across all storage directories."""
        cert_prefix = str(certificate_id)
        for directory in [
            self.raw_dir,
            self.rasterized_dir,
            self.preprocessed_dir,
            self.reports_dir,
        ]:
            if not directory.exists():
                continue
            for item in directory.glob(f"{cert_prefix}*"):
                try:
                    if item.is_file():
                        item.unlink(missing_ok=True)
                except Exception:
                    pass
