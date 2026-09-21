"""Pydantic V2 schemas for audit logs and security event queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    """Single audit trail entry."""

    id: str
    user_id: Optional[str] = None
    certificate_id: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime


class AuditLogPaginatedList(BaseModel):
    """Paginated collection of audit log entries."""

    items: List[AuditLogItem]
    total: int
    page: int
    limit: int
    total_pages: int
