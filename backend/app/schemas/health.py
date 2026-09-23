from typing import Optional

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    database: str = Field(..., description="'connected' or 'disconnected'")
    redis: Optional[str] = Field(
        default="disabled",
        description="'connected', 'disconnected', or 'disabled'",
    )
    storage: str = Field(..., description="'accessible' or 'inaccessible'")


class LightweightHealthResponse(BaseModel):
    status: str = Field(..., description="'healthy' or 'degraded'")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    db_connected: bool = Field(..., description="Database connection status")
    model_engine: str = Field(default="online", description="'online' or 'offline'")
    latency_ms: float = Field(..., description="Observed ping latency in milliseconds")


class HealthCheckResponse(BaseModel):
    status: str = Field(default="healthy", description="'healthy', 'ok' or 'degraded'")
    app_name: str
    environment: str
    version: str = "0.1.0"
    services: ServiceStatus

