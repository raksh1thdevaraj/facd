"""FastAPI router for administrative fraud analytics, KPI metrics, and system diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.admin import AnalyticsSummaryResponse, SystemHealthDiagnostic
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin", tags=["Administration & Analytics"])


@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get high-level fraud intelligence and aggregate throughput KPIs",
)
def get_analytics_summary(
    bypass_cache: bool = False,
    db: Session = Depends(get_db),
) -> AnalyticsSummaryResponse:
    return AnalyticsService.get_summary(db=db, bypass_cache=bypass_cache)


@router.get(
    "/system/health",
    response_model=SystemHealthDiagnostic,
    summary="Get diagnostic health metrics for database, disk storage, and pipeline latency",
)
def get_system_diagnostic_health(
    db: Session = Depends(get_db),
) -> SystemHealthDiagnostic:
    return AnalyticsService.get_system_health(db=db)
