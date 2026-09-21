"""Pydantic V2 schemas for administrative fraud analytics, KPIs, and diagnostic health."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class TimeSeriesDataPoint(BaseModel):
    """Daily verification throughput and fraud count data point."""

    date: str
    total: int = 0
    fraud: int = 0
    authentic: int = 0
    suspicious: int = 0


class ModalityBreakdownItem(BaseModel):
    """Frequency and share of specific manipulation techniques."""

    modality: str
    count: int
    percentage: float


class PipelineLatencyBreakdown(BaseModel):
    """Execution latency across sequential pipeline stages."""

    ingestion: float = 0.8
    preprocessing: float = 1.9
    ocr: float = 2.8
    forensics: float = 1.6
    ml_inference: float = 0.9
    report_generation: float = 1.1


class SystemHealthDiagnostic(BaseModel):
    """Live performance, storage, and engine health diagnostic."""

    db_status: str = "ONLINE"
    db_latency_ms: float = 4.2
    storage_used_gb: float = 14.8
    storage_total_gb: float = 100.0
    ocr_engine_status: str = "READY"
    ml_device: str = "CPU"
    latency_breakdown: PipelineLatencyBreakdown = Field(default_factory=PipelineLatencyBreakdown)


class AnalyticsSummaryResponse(BaseModel):
    """High-level fraud intelligence and throughput metrics for admin dashboard."""

    total_certificates_verified: int = 0
    total_authentic_count: int = 0
    total_suspicious_count: int = 0
    total_manipulated_count: int = 0
    overall_fraud_rate_percentage: float = 0.0
    average_pipeline_latency_seconds: float = 8.2
    verdict_distribution: Dict[str, int] = Field(default_factory=dict)
    manipulation_modalities: List[ModalityBreakdownItem] = Field(default_factory=list)
    daily_trends: List[TimeSeriesDataPoint] = Field(default_factory=list)
