"""Verification History and Audit Log Service.

Manages persistent storage and querying of verification records across SQLite
and the lightweight local JSON ledger (`data/history.json`).
Supports asynchronous non-blocking recording and resilient failover.
"""

from __future__ import annotations

import json
import logging
import math
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.verification_history import VerificationHistoryModel

logger = logging.getLogger(__name__)

# Canonical path to local JSON ledger
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LEDGER_DIR = PROJECT_ROOT / "data"
LEDGER_FILE = LEDGER_DIR / "history.json"


def _ensure_ledger_file() -> None:
    """Ensure data directory and history.json ledger file exist."""
    try:
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        if not LEDGER_FILE.exists():
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
    except Exception as exc:
        logger.warning("Could not initialize ledger file %s: %s", LEDGER_FILE, exc)


from services.historyStore import history_store


class VerificationHistoryService:
    """Service encapsulating database and ledger persistence for verification history."""

    @staticmethod
    def _append_to_json_ledger(record: Dict[str, Any]) -> None:
        """Atomically append/prepend a verification entry into data/history.json."""
        try:
            history_store.append_record(record)
        except Exception as exc:
            logger.warning("Failed to append verification record to JSON ledger: %s", exc)

    @staticmethod
    def _read_from_json_ledger() -> List[Dict[str, Any]]:
        """Read all verification records from data/history.json."""
        try:
            return history_store.read_all()
        except Exception as exc:
            logger.warning("Failed to read from JSON ledger: %s", exc)
        return []

    @classmethod
    def record_verification(
        cls,
        original_filename: str,
        document_type: str,
        verdict: str,
        confidence_score: float,
        student_name: str = "Not Detected",
        identifier: str = "Not Detected",
        issuer: str = "Not Detected",
        qr_status: bool = False,
        tampering_flags: Optional[List[str]] = None,
        remarks: str = "",
        full_details: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
        timestamp_iso: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Persist a completed verification synchronously or within current session."""
        rec_id = record_id or str(uuid.uuid4())
        now_dt = datetime.now(timezone.utc)
        now_iso = timestamp_iso or now_dt.isoformat()
        flags = list(tampering_flags) if tampering_flags else []
        conf = max(0.0, min(1.0, float(confidence_score)))

        normalized_verdict = verdict.upper().strip()
        if normalized_verdict not in {"AUTHENTIC", "SUSPICIOUS", "FRAUDULENT"}:
            if "AUTHENTIC" in normalized_verdict or "VERIFIED" in normalized_verdict:
                normalized_verdict = "AUTHENTIC"
            elif (
                "FRAUD" in normalized_verdict
                or "REJECT" in normalized_verdict
                or "MANIPULATED" in normalized_verdict
            ):
                normalized_verdict = "FRAUDULENT"
            else:
                normalized_verdict = "SUSPICIOUS"

        record_dict = {
            "id": rec_id,
            "timestamp": now_iso,
            "original_filename": original_filename,
            "document_type": document_type,
            "student_name": student_name or "Not Detected",
            "identifier": identifier or "Not Detected",
            "issuer": issuer or "Not Detected",
            "verdict": normalized_verdict,
            "confidence_score": round(conf, 4),
            "qr_status": bool(qr_status),
            "tampering_flags": flags,
            "remarks": remarks or "",
            "full_details": full_details or {},
        }

        # 1. Update SQLite
        owns_session = False
        session = db
        if session is None:
            session = SessionLocal()
            owns_session = True

        try:
            # Check existing record
            existing = session.query(VerificationHistoryModel).filter_by(id=rec_id).first()
            if existing:
                existing.original_filename = original_filename
                existing.document_type = document_type
                existing.student_name = record_dict["student_name"]
                existing.identifier = record_dict["identifier"]
                existing.issuer = record_dict["issuer"]
                existing.verdict = normalized_verdict
                existing.confidence_score = conf
                existing.qr_status = bool(qr_status)
                existing.tampering_flags = flags
                existing.remarks = remarks or ""
                existing.full_details = full_details or {}
            else:
                new_model = VerificationHistoryModel(
                    id=rec_id,
                    timestamp=now_dt,
                    timestamp_iso=now_iso,
                    original_filename=original_filename,
                    document_type=document_type,
                    student_name=record_dict["student_name"],
                    identifier=record_dict["identifier"],
                    issuer=record_dict["issuer"],
                    verdict=normalized_verdict,
                    confidence_score=conf,
                    qr_status=bool(qr_status),
                    tampering_flags=flags,
                    remarks=remarks or "",
                    full_details=full_details or {},
                )
                session.add(new_model)
            session.commit()
        except Exception as db_err:
            session.rollback()
            logger.warning(
                "Could not save verification history record %s to database: %s", rec_id, db_err
            )
        finally:
            if owns_session:
                session.close()

        # 2. Update local JSON ledger
        cls._append_to_json_ledger(record_dict)

        return record_dict

    @classmethod
    def record_verification_async(cls, **kwargs: Any) -> None:
        """Spawn a non-blocking background thread to persist the verification record."""
        # Remove any non-thread-safe active DB session so thread creates its own
        kwargs_copy = dict(kwargs)
        kwargs_copy["db"] = None

        def _worker() -> None:
            try:
                cls.record_verification(**kwargs_copy)
            except Exception as exc:
                logger.warning("Background record_verification failed: %s", exc)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    @classmethod
    def list_history(
        cls,
        db: Session,
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
        try:
            query = db.query(VerificationHistoryModel)

            # Global Search across candidate fields
            if search and search.strip():
                s = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        VerificationHistoryModel.student_name.ilike(s),
                        VerificationHistoryModel.identifier.ilike(s),
                        VerificationHistoryModel.original_filename.ilike(s),
                        VerificationHistoryModel.issuer.ilike(s),
                    )
                )

            # Specific column filters
            if usn and usn.strip():
                query = query.filter(VerificationHistoryModel.identifier.ilike(f"%{usn.strip()}%"))
            if student_name and student_name.strip():
                query = query.filter(
                    VerificationHistoryModel.student_name.ilike(f"%{student_name.strip()}%")
                )
            if verdict and verdict.strip() and verdict.upper() != "ALL":
                query = query.filter(VerificationHistoryModel.verdict == verdict.upper().strip())
            if document_type and document_type.strip() and document_type.upper() != "ALL":
                query = query.filter(
                    VerificationHistoryModel.document_type == document_type.strip()
                )

            total = query.count()

            # Sorting
            if order.lower() == "asc":
                query = query.order_by(asc(VerificationHistoryModel.timestamp))
            else:
                query = query.order_by(desc(VerificationHistoryModel.timestamp))

            # Pagination
            offset = max(0, (page - 1) * limit)
            records = query.offset(offset).limit(limit).all()

            items = [r.to_summary_dict() for r in records]
            total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

            return items, total, total_pages

        except Exception as exc:
            logger.warning(
                "Database query for verification history failed, falling back to JSON ledger: %s",
                exc,
            )
            return cls._list_from_json_ledger(
                page=page,
                limit=limit,
                order=order,
                search=search,
                usn=usn,
                student_name=student_name,
                verdict=verdict,
                document_type=document_type,
            )

    @classmethod
    def _list_from_json_ledger(
        cls,
        page: int = 1,
        limit: int = 20,
        order: str = "desc",
        search: Optional[str] = None,
        usn: Optional[str] = None,
        student_name: Optional[str] = None,
        verdict: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Fallback query handler reading directly from data/history.json."""
        all_entries = cls._read_from_json_ledger()
        filtered = []

        for e in all_entries:
            # Search
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

            # USN
            if usn and usn.strip():
                if usn.strip().lower() not in str(e.get("identifier", "")).lower():
                    continue

            # Student Name
            if student_name and student_name.strip():
                if student_name.strip().lower() not in str(e.get("student_name", "")).lower():
                    continue

            # Verdict
            if verdict and verdict.strip() and verdict.upper() != "ALL":
                if str(e.get("verdict", "")).upper() != verdict.upper().strip():
                    continue

            # Document Type
            if document_type and document_type.strip() and document_type.upper() != "ALL":
                if str(e.get("document_type", "")) != document_type.strip():
                    continue

            summary = {
                "id": e.get("id"),
                "timestamp": e.get("timestamp"),
                "original_filename": e.get("original_filename"),
                "document_type": e.get("document_type"),
                "student_name": e.get("student_name"),
                "identifier": e.get("identifier"),
                "issuer": e.get("issuer"),
                "verdict": e.get("verdict"),
                "confidence_score": round(float(e.get("confidence_score", 0.0)), 4),
                "qr_status": bool(e.get("qr_status")),
                "tampering_flags": e.get("tampering_flags", []),
                "remarks": e.get("remarks", ""),
            }
            filtered.append(summary)

        # Sort
        filtered.sort(
            key=lambda x: str(x.get("timestamp", "")),
            reverse=(order.lower() != "asc"),
        )

        total = len(filtered)
        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
        offset = max(0, (page - 1) * limit)
        items = filtered[offset : offset + limit]

        return items, total, total_pages

    @classmethod
    def get_history_detail(cls, db: Session, history_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete forensic breakdown for a specific historical record."""
        # 1. Try SQLite
        try:
            record = (
                db.query(VerificationHistoryModel)
                .filter(VerificationHistoryModel.id == history_id)
                .first()
            )
            if record:
                return record.to_detail_dict()
        except Exception as exc:
            logger.warning("Error querying VerificationHistoryModel for %s: %s", history_id, exc)

        # 2. Fallback to JSON ledger
        entries = cls._read_from_json_ledger()
        for e in entries:
            if e.get("id") == history_id:
                return {
                    "id": e.get("id"),
                    "timestamp": e.get("timestamp"),
                    "original_filename": e.get("original_filename"),
                    "document_type": e.get("document_type"),
                    "student_name": e.get("student_name"),
                    "identifier": e.get("identifier"),
                    "issuer": e.get("issuer"),
                    "verdict": e.get("verdict"),
                    "confidence_score": round(float(e.get("confidence_score", 0.0)), 4),
                    "qr_status": bool(e.get("qr_status")),
                    "tampering_flags": e.get("tampering_flags", []),
                    "remarks": e.get("remarks", ""),
                    "full_details": e.get("full_details", {}),
                }

        return None

    @classmethod
    def delete_history_item(cls, db: Session, history_id: str) -> bool:
        """Remove a verification history record from both SQLite and JSON ledger."""
        deleted = False

        # 1. Delete from SQLite
        try:
            record = (
                db.query(VerificationHistoryModel)
                .filter(VerificationHistoryModel.id == history_id)
                .first()
            )
            if record:
                db.delete(record)
                db.commit()
                deleted = True
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to delete record %s from database: %s", history_id, exc)

        # 2. Delete from JSON ledger
        try:
            if history_store.delete_record(history_id):
                deleted = True
        except Exception as exc:
            logger.warning("Failed to delete record %s from JSON ledger: %s", history_id, exc)

        return deleted

    @classmethod
    def clear_history(cls, db: Session) -> int:
        """Clear all historical verification records from SQLite and JSON ledger."""
        count = 0

        # 1. Clear SQLite table
        try:
            count = db.query(VerificationHistoryModel).delete()
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to truncate verification_history table: %s", exc)

        # 2. Reset JSON ledger
        try:
            history_store.clear()
        except Exception as exc:
            logger.warning("Failed to clear JSON ledger: %s", exc)

        return count


# Singleton instance
history_service = VerificationHistoryService()
