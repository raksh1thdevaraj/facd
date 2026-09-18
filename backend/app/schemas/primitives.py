from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "x_min" in data and "x1" not in data:
                data["x1"] = data["x_min"]
            if "y_min" in data and "y1" not in data:
                data["y1"] = data["y_min"]
            if "x_max" in data and "x2" not in data:
                data["x2"] = data["x_max"]
            if "y_max" in data and "y2" not in data:
                data["y2"] = data["y_max"]
        return data

    @classmethod
    def from_min_max(cls, x_min: float, y_min: float, x_max: float, y_max: float) -> "BoundingBox":
        """Construct BoundingBox from min/max coordinates."""
        return cls(x1=x_min, y1=y_min, x2=x_max, y2=y_max)

    @property
    def x_min(self) -> float:
        return self.x1

    @property
    def y_min(self) -> float:
        return self.y1

    @property
    def x_max(self) -> float:
        return self.x2

    @property
    def y_max(self) -> float:
        return self.y2


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
