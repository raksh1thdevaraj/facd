from typing import Optional

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    database: str = Field(..., description="'connected' or 'disconnected'")
    redis: Optional[str] = Field(
        default="disabled",
        description="'connected', 'disconnected', or 'disabled'",
    )
    storage: str = Field(..., description="'accessible' or 'inaccessible'")


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="'ok' or 'degraded'")
    app_name: str
    environment: str
    version: str = "0.1.0"
    services: ServiceStatus
