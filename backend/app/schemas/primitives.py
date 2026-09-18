from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class BoundingBox(BaseModel):
    """Normalized coordinates: 0.0 to 1.0 relative to image width and height."""
    x1: float = Field(..., ge=0.0, le=1.0, description="Top-left X (0.0 to 1.0)")
    y1: float = Field(..., ge=0.0, le=1.0, description="Top-left Y (0.0 to 1.0)")
    x2: float = Field(..., ge=0.0, le=1.0, description="Bottom-right X (0.0 to 1.0)")
    y2: float = Field(..., ge=0.0, le=1.0, description="Bottom-right Y (0.0 to 1.0)")


class PixelBoundingBox(BaseModel):
    """Absolute pixel coordinates."""
    x: int = Field(..., ge=0, description="Top-left X in pixels")
    y: int = Field(..., ge=0, description="Top-left Y in pixels")
    width: int = Field(..., gt=0, description="Box width in pixels")
    height: int = Field(..., gt=0, description="Box height in pixels")


class ErrorEnvelope(BaseModel):
    """Standardized API error envelope response."""
    status_code: int
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
