"""Centralized audit logging service for immutable compliance tracking."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLogModel

logger = logging.getLogger(__name__)


class AuditService:
    """Service recording operations to the immutable audit_logs database table."""

    @classmethod
    def log_action(
        cls,
        db: Session,
        action: str,
        user_id: Optional[str] = None,
        certificate_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[AuditLogModel]:
        """Record an audit entry into the database.

        Args:
            db: Active SQLAlchemy database session.
            action: Action identifier (e.g. CERTIFICATE_UPLOADED, REPORT_DOWNLOADED).
            user_id: Optional user initiating the action.
            certificate_id: Optional certificate ID related to the action.
            ip_address: Client IP address.
            details: Contextual metadata dictionary.

        Returns:
            Created AuditLogModel instance, or None if logging failed.
        """
        try:
            record = AuditLogModel(
                user_id=user_id,
                certificate_id=certificate_id,
                action=action,
                ip_address=ip_address,
                details_json=details or {},
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except Exception as e:
            db.rollback()
            logger.warning("Failed to record audit log for action %s: %s", action, e)
            return None
