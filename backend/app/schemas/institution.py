"""Pydantic V2 schemas for institution onboarding, template management, and bulk record imports."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InstitutionCreate(BaseModel):
    """Schema for registering a new university or certification authority."""

    name: str = Field(..., description="Full official university name")
    code: str = Field(..., description="Unique institution code (e.g. MIT, STANFORD)")
    contact_email: Optional[str] = Field(default=None, description="Registrar contact email")


class InstitutionResponse(BaseModel):
    """Institution details with registered counts."""

    id: str
    name: str
    code: str
    contact_email: Optional[str] = None
    is_active: bool
    template_count: int = 0
    record_count: int = 0
    created_at: datetime


class InstitutionPaginatedList(BaseModel):
    """Paginated collection of registered universities."""

    items: List[InstitutionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class BulkRecordImportResponse(BaseModel):
    """Response returned upon bulk student record CSV/JSON upload."""

    institution_id: str
    imported_count: int
    status: str = "SUCCESS"
    message: str
