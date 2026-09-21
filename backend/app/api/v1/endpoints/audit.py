"""FastAPI router for immutable compliance audit log inspection."""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.audit_log import AuditLogModel
from app.models.user import AppUserModel
from app.schemas.audit import AuditLogItem, AuditLogPaginatedList

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogPaginatedList,
    summary="List immutable system audit logs with pagination and filters",
)
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, description="Filter by action name"),
    certificate_id: Optional[str] = Query(None, description="Filter by certificate UUID"),
    db: Session = Depends(get_db),
    current_user: AppUserModel = Depends(require_admin),
) -> AuditLogPaginatedList:
    query = db.query(AuditLogModel)

    if action:
        query = query.filter(AuditLogModel.action == action.upper())
    if certificate_id:
        query = query.filter(AuditLogModel.certificate_id == certificate_id)

    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLogModel.created_at)).offset(offset).limit(limit).all()

    items = [
        AuditLogItem(
            id=log.id,
            user_id=log.user_id,
            certificate_id=log.certificate_id,
            action=log.action,
            ip_address=log.ip_address,
            details=log.details_json or {},
            created_at=log.created_at,
        )
        for log in logs
    ]

    total_pages = max(1, math.ceil(total / limit))
    return AuditLogPaginatedList(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
