"""FastAPI router for Verification History and Audit Ledger Inspection."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.verification_history import (
    VerificationHistoryClearResponse,
    VerificationHistoryDetail,
    VerificationHistoryPaginatedList,
    VerificationHistorySummary,
)
from app.services.history_service import history_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Verification History"])


@router.get(
    "",
    summary="List past certificate verification summaries with filtering, sorting, and pagination",
    response_model=Union[List[VerificationHistorySummary], VerificationHistoryPaginatedList],
)
def get_verification_history(
    response: Response,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=200, description="Records per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by timestamp"),
    search: Optional[str] = Query(
        None, description="Global search by student name, USN, issuer, or filename"
    ),
    usn: Optional[str] = Query(None, description="Filter by student USN / Certificate ID"),
    student_name: Optional[str] = Query(None, description="Filter by candidate student name"),
    verdict: Optional[str] = Query(
        None, description="Filter by verdict: AUTHENTIC, SUSPICIOUS, or FRAUDULENT"
    ),
    document_type: Optional[str] = Query(
        None, description="Filter by document type (VTU_MARKSCARD, etc.)"
    ),
    format: str = Query(
        "array", pattern="^(array|paginated)$", description="Output format: 'array' or 'paginated'"
    ),
    db: Session = Depends(get_db),
) -> Union[List[VerificationHistorySummary], VerificationHistoryPaginatedList]:
    """
    Retrieve historical certificate verification records.
    Returns a clean JSON array of past verification summaries by default,
    with pagination metadata exposed via standard HTTP response headers
    (`X-Total-Count`, `X-Page`, `X-Limit`, `X-Total-Pages`).
    """
    items_raw, total, total_pages = history_service.list_history(
        db=db,
        page=page,
        limit=limit,
        order=order,
        search=search,
        usn=usn,
        student_name=student_name,
        verdict=verdict,
        document_type=document_type,
    )

    items = [VerificationHistorySummary(**it) for it in items_raw]

    # Expose pagination metadata via headers
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Total-Pages"] = str(total_pages)

    if format == "paginated":
        return VerificationHistoryPaginatedList(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    return items


@router.delete(
    "/clear",
    response_model=VerificationHistoryClearResponse,
    summary="Clear all past verification history records",
)
def clear_verification_history(
    db: Session = Depends(get_db),
) -> VerificationHistoryClearResponse:
    """Reset and clear entire verification history ledger across SQLite and local JSON storage."""
    deleted_count = history_service.clear_history(db=db)
    return VerificationHistoryClearResponse(
        success=True,
        message="Verification history cleared successfully.",
        deleted_count=deleted_count,
    )


@router.get(
    "/{history_id}",
    response_model=VerificationHistoryDetail,
    summary="Get full forensic breakdown and audit details of a specific past verification",
)
def get_verification_history_detail(
    history_id: str,
    db: Session = Depends(get_db),
) -> VerificationHistoryDetail:
    """Retrieve full verification audit dossier by record ID."""
    detail = history_service.get_history_detail(db=db, history_id=history_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record with ID '{history_id}' not found.",
        )
    return VerificationHistoryDetail(**detail)


@router.delete(
    "/{history_id}",
    summary="Delete a single verification record from history",
    response_model=Dict[str, Any],
)
def delete_verification_history_item(
    history_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a single verification record by ID."""
    deleted = history_service.delete_history_item(db=db, history_id=history_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification record with ID '{history_id}' not found.",
        )
    return {
        "success": True,
        "message": f"Verification record '{history_id}' deleted successfully.",
        "id": history_id,
    }
