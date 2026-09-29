"""Lightweight Local Storage Handler for Verification History.

Persists and retrieves certificate verification audit records to/from `data/history.json`.
Provides thread-safe atomic read, append, search, pagination, and retrieval operations.
"""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Canonical paths
_SERVICES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SERVICES_DIR.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_HISTORY_FILE = DEFAULT_DATA_DIR / "history.json"


class HistoryStore:
    """Lightweight JSON-based local history persistence store."""

    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        max_records: int = 1000,
    ) -> None:
        self.file_path = (
            Path(file_path).resolve()
            if file_path
            else Path(os.environ.get("HISTORY_FILE_PATH", str(DEFAULT_HISTORY_FILE))).resolve()
        )
        self.max_records = max_records
        self._lock = threading.Lock()
        self.ensure_store_file()

    def ensure_store_file(self) -> Path:
        """Ensure parent directory and history.json ledger file exist."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
        except Exception as exc:
            logger.warning("Could not initialize history storage file %s: %s", self.file_path, exc)
        return self.file_path

    def read_all(self) -> List[Dict[str, Any]]:
        """Read and return all verification records from the JSON store."""
        with self._lock:
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data
            except Exception as exc:
                logger.warning("Failed reading history store %s: %s", self.file_path, exc)
            return []

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single verification record by unique ID."""
        records = self.read_all()
        target_id = str(record_id).strip()
        for rec in records:
            if str(rec.get("id", "")).strip() == target_id:
                return rec
        return None

    def append_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically append/prepend a verification entry into history.json.

        Thread-safe and uses atomic temporary file replacement to avoid
        data corruption during process interruptions.
        """
        with self._lock:
            self.ensure_store_file()

            # Ensure ID and timestamps
            rec_id = str(record.get("id") or uuid.uuid4())
            timestamp = record.get("timestamp") or datetime.now(timezone.utc).isoformat()

            # Normalize verdict
            verdict = str(record.get("verdict", "SUSPICIOUS")).upper().strip()
            if "AUTHENTIC" in verdict or "VERIFIED" in verdict:
                normalized_verdict = "AUTHENTIC"
            elif "FRAUD" in verdict or "REJECT" in verdict or "MANIPULATED" in verdict:
                normalized_verdict = "FRAUDULENT"
            else:
                normalized_verdict = "SUSPICIOUS"

            try:
                confidence_score = round(max(0.0, min(1.0, float(record.get("confidence_score", 0.0)))), 4)
            except (ValueError, TypeError):
                confidence_score = 0.0

            normalized_record: Dict[str, Any] = {
                "id": rec_id,
                "timestamp": timestamp,
                "original_filename": str(record.get("original_filename", "unnamed_document")),
                "document_type": str(record.get("document_type", "UNKNOWN")),
                "student_name": str(record.get("student_name", "Not Detected")),
                "identifier": str(record.get("identifier", "Not Detected")),
                "issuer": str(record.get("issuer", "Not Detected")),
                "verdict": normalized_verdict,
                "confidence_score": confidence_score,
                "qr_status": bool(record.get("qr_status", False)),
                "tampering_flags": list(record.get("tampering_flags", [])),
                "remarks": str(record.get("remarks", "")),
                "full_details": record.get("full_details", {}),
            }

            # Read existing
            entries: List[Dict[str, Any]] = []
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            entries = data
            except Exception:
                entries = []

            # Deduplicate by ID: update if present, or prepend newest
            entries = [e for e in entries if str(e.get("id")) != rec_id]
            entries.insert(0, normalized_record)

            # Cap store length
            if len(entries) > self.max_records:
                entries = entries[: self.max_records]

            # Atomic write via temp file
            dir_name = self.file_path.parent
            try:
                with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                    json.dump(entries, tf, indent=2)
                    temp_path = tf.name
                os.replace(temp_path, self.file_path)
            except Exception as exc:
                logger.error("Atomic write failed for history store: %s", exc)
                # Fallback to direct write
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2)

            return normalized_record

    def query(
        self,
        page: int = 1,
        limit: int = 20,
        order: str = "desc",
        search: Optional[str] = None,
        usn: Optional[str] = None,
        student_name: Optional[str] = None,
        verdict: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Query verification history records with filtering, sorting, and pagination."""
        all_entries = self.read_all()
        filtered: List[Dict[str, Any]] = []

        for e in all_entries:
            # Global Search across multiple candidate fields
            if search and search.strip():
                st = search.strip().lower()
                cands = [
                    str(e.get("student_name", "")).lower(),
                    str(e.get("identifier", "")).lower(),
                    str(e.get("original_filename", "")).lower(),
                    str(e.get("issuer", "")).lower(),
                ]
                if not any(st in c for c in cands):
                    continue

            # USN / identifier filter
            if usn and usn.strip():
                if usn.strip().lower() not in str(e.get("identifier", "")).lower():
                    continue

            # Student name filter
            if student_name and student_name.strip():
                if student_name.strip().lower() not in str(e.get("student_name", "")).lower():
                    continue

            # Verdict filter
            if verdict and verdict.strip() and verdict.upper() != "ALL":
                if str(e.get("verdict", "")).upper() != verdict.upper().strip():
                    continue

            # Document Type filter
            if document_type and document_type.strip() and document_type.upper() != "ALL":
                if str(e.get("document_type", "")).strip() != document_type.strip():
                    continue

            filtered.append(e)

        # Sorting
        filtered.sort(
            key=lambda x: str(x.get("timestamp", "")),
            reverse=(order.lower() != "asc"),
        )

        total = len(filtered)
        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
        offset = max(0, (page - 1) * limit)
        items = filtered[offset : offset + limit]

        return items, total, total_pages

    def delete_record(self, record_id: str) -> bool:
        """Remove a verification history record from the JSON store."""
        with self._lock:
            entries = []
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            entries = data
            except Exception:
                entries = []

            target_id = str(record_id).strip()
            new_entries = [e for e in entries if str(e.get("id", "")).strip() != target_id]

            if len(new_entries) == len(entries):
                return False

            dir_name = self.file_path.parent
            try:
                with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                    json.dump(new_entries, tf, indent=2)
                    temp_path = tf.name
                os.replace(temp_path, self.file_path)
            except Exception:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(new_entries, f, indent=2)

            return True

    def clear(self) -> int:
        """Reset history ledger to empty list. Returns deleted records count."""
        with self._lock:
            self.ensure_store_file()
            existing_count = 0
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            existing_count = len(data)
            except Exception:
                pass

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

            return existing_count


# Global singleton instance
history_store = HistoryStore()


# Functional API exports for simple imports
def get_history_store() -> HistoryStore:
    """Return the global HistoryStore singleton."""
    return history_store


def append_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Append or update a record in the local history store."""
    return history_store.append_record(record)


def read_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read past records from the local history store."""
    records = history_store.read_all()
    if limit is not None and limit > 0:
        return records[:limit]
    return records


def get_record_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve record by ID from the local history store."""
    return history_store.get_by_id(record_id)


def delete_record(record_id: str) -> bool:
    """Delete a record by ID from the local history store."""
    return history_store.delete_record(record_id)


def clear_history() -> int:
    """Clear all records from the local history store."""
    return history_store.clear()
