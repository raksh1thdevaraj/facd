"""Firestore database service for certificates, verification records, and user management."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.firebase import get_firestore_client

logger = logging.getLogger(__name__)


class FirestoreService:
    """Encapsulates document operations on Cloud Firestore collections."""

    USERS_COLLECTION = "users"
    CERTIFICATES_COLLECTION = "certificates"
    VERIFICATIONS_COLLECTION = "verifications"
    COURSE_VERIFICATIONS_COLLECTION = "course_verifications"
    AUDIT_LOGS_COLLECTION = "audit_logs"

    def __init__(self):
        self._db = get_firestore_client()

    @property
    def is_available(self) -> bool:
        """Returns True if Firestore client is initialized and reachable."""
        return self._db is not None

    def save_verification(self, verification_id: str, data: Dict[str, Any]) -> bool:
        """Save an immutable marks card verification audit record to Firestore."""
        if not self.is_available:
            return False
        try:
            doc_ref = self._db.collection(self.VERIFICATIONS_COLLECTION).document(verification_id)
            payload = {
                "id": verification_id,
                "timestamp": data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "fileName": data.get("fileName") or data.get("filename") or "document.pdf",
                "fileUrl": data.get("fileUrl") or data.get("file_url") or "",
                "studentName": data.get("studentName") or data.get("student_name") or "STUDENT CANDIDATE",
                "usn": data.get("usn") or data.get("reg_no") or "UNKNOWN",
                "collegeCode": data.get("collegeCode") or data.get("college_code") or "VTU",
                "sgpaListed": float(data.get("sgpaListed") or data.get("sgpa") or 0.0),
                "sgpaCalculated": float(data.get("sgpaCalculated") or data.get("calculated_sgpa") or 0.0),
                "arithmeticDiscrepancy": bool(data.get("arithmeticDiscrepancy", False)),
                "tamperingScore": float(data.get("tamperingScore") or data.get("tampering_score") or 0.0),
                "verdict": data.get("verdict") or "SUSPICIOUS",
                "forensicReport": data.get("forensicReport") or data.get("forensic_report") or "",
            }
            doc_ref.set(payload, merge=True)
            return True
        except Exception as exc:
            logger.error("Failed to save verification %s in Firestore: %s", verification_id, exc)
            return False

    def get_verification(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """Fetch verification audit record by ID from Firestore."""
        if not self.is_available:
            return None
        try:
            doc = self._db.collection(self.VERIFICATIONS_COLLECTION).document(verification_id).get()
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
        except Exception as exc:
            logger.error("Failed to get verification %s from Firestore: %s", verification_id, exc)
            return None

    def list_verifications(
        self, limit: int = 50, verdict: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List verification records from Firestore sorted by timestamp descending."""
        if not self.is_available:
            return []
        try:
            coll = self._db.collection(self.VERIFICATIONS_COLLECTION)
            if verdict and verdict != "ALL":
                q = coll.where("verdict", "==", verdict).order_by("timestamp", direction="DESCENDING").limit(limit)
            else:
                q = coll.order_by("timestamp", direction="DESCENDING").limit(limit)
            return [{"id": d.id, **d.to_dict()} for d in q.stream()]
        except Exception as exc:
            logger.error("Failed to list verifications from Firestore: %s", exc)
            return []

    def upsert_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Upsert a user document in Firestore."""
        if not self.is_available:
            return False
        try:
            doc_ref = self._db.collection(self.USERS_COLLECTION).document(user_id)
            payload = {**data}
            if "updated_at" not in payload:
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            doc_ref.set(payload, merge=True)
            return True
        except Exception as exc:
            logger.error("Failed to upsert user %s in Firestore: %s", user_id, exc)
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile from Firestore by UID."""
        if not self.is_available:
            return None
        try:
            doc = self._db.collection(self.USERS_COLLECTION).document(user_id).get()
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
        except Exception as exc:
            logger.error("Failed to get user %s from Firestore: %s", user_id, exc)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Query user by email in Firestore."""
        if not self.is_available:
            return None
        try:
            query = (
                self._db.collection(self.USERS_COLLECTION)
                .where("email", "==", email.lower())
                .limit(1)
            )
            docs = list(query.stream())
            if docs:
                return {"id": docs[0].id, **docs[0].to_dict()}
            return None
        except Exception as exc:
            logger.error("Failed to query user by email %s in Firestore: %s", email, exc)
            return None

    def save_certificate(self, cert_id: str, data: Dict[str, Any]) -> bool:
        """Save or update a certificate document in Firestore."""
        if not self.is_available:
            return False
        try:
            doc_ref = self._db.collection(self.CERTIFICATES_COLLECTION).document(cert_id)
            payload = {**data}
            if "updated_at" not in payload:
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            doc_ref.set(payload, merge=True)
            return True
        except Exception as exc:
            logger.error("Failed to save certificate %s in Firestore: %s", cert_id, exc)
            return False

    def get_certificate(self, cert_id: str) -> Optional[Dict[str, Any]]:
        """Fetch certificate by ID from Firestore."""
        if not self.is_available:
            return None
        try:
            doc = self._db.collection(self.CERTIFICATES_COLLECTION).document(cert_id).get()
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
        except Exception as exc:
            logger.error("Failed to get certificate %s from Firestore: %s", cert_id, exc)
            return None

    def list_certificates_for_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List certificates owned by a user from Firestore."""
        if not self.is_available:
            return []
        try:
            query = (
                self._db.collection(self.CERTIFICATES_COLLECTION)
                .where("user_id", "==", user_id)
                .limit(limit)
            )
            return [{"id": d.id, **d.to_dict()} for d in query.stream()]
        except Exception as exc:
            logger.error("Failed to list certificates for user %s: %s", user_id, exc)
            return []

    def save_course_verification(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Save a course verification report to Firestore."""
        if not self.is_available:
            return False
        try:
            doc_ref = self._db.collection(self.COURSE_VERIFICATIONS_COLLECTION).document(record_id)
            payload = {**data}
            if "updated_at" not in payload:
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            doc_ref.set(payload, merge=True)
            return True
        except Exception as exc:
            logger.error("Failed to save course verification %s to Firestore: %s", record_id, exc)
            return False

    def get_course_verification(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch course verification record by ID from Firestore."""
        if not self.is_available:
            return None
        try:
            doc = (
                self._db.collection(self.COURSE_VERIFICATIONS_COLLECTION).document(record_id).get()
            )
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
        except Exception as exc:
            logger.error("Failed to get course verification %s from Firestore: %s", record_id, exc)
            return None

    def log_audit_event(self, event_data: Dict[str, Any]) -> bool:
        """Record an audit trail event in Firestore."""
        if not self.is_available:
            return False
        try:
            payload = {
                **event_data,
                "timestamp": event_data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            }
            self._db.collection(self.AUDIT_LOGS_COLLECTION).add(payload)
            return True
        except Exception as exc:
            logger.error("Failed to log audit event in Firestore: %s", exc)
            return False


firestore_service = FirestoreService()
