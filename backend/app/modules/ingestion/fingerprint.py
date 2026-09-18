import hashlib
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def compute_sha256(file_path: Path, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 cryptographic hash of a file using chunked streaming.

    Reads in 64KB chunks to guarantee flat memory consumption.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def check_duplicate_hash(sha256_hash: str, db_session: Optional[Session] = None) -> Optional[str]:
    """Check if a certificate with the same SHA-256 checksum has already been registered.

    Returns the existing document_id / certificate_id if found, or None.
    """
    if db_session is None:
        return None

    try:
        # Check if certificates table exists and has file_hash column
        query = text("SELECT id FROM certificates WHERE file_hash = :hash LIMIT 1")
        result = db_session.execute(query, {"hash": sha256_hash}).scalar()
        return str(result) if result else None
    except Exception:
        # Gracefully handle unmigrated database state
        return None
