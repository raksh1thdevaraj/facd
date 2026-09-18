from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for all domain-specific application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(
        self,
        message: str = "Requested resource was not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    """Input or schema validation error."""

    def __init__(
        self,
        message: str = "Invalid input or parameter payload",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class PipelineError(AppException):
    """Verification pipeline execution error."""

    def __init__(
        self,
        message: str = "Error encountered during verification pipeline execution",
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        full_details = details or {}
        if stage:
            full_details["stage"] = stage
        super().__init__(
            message=message,
            status_code=500,
            error_code="PIPELINE_ERROR",
            details=full_details,
        )


class UnauthorizedError(AppException):
    """Authentication or authorization failure."""

    def __init__(
        self,
        message: str = "Invalid credentials or unauthorized access",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenError(AppException):
    """Access forbidden due to insufficient role/permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions to perform this action",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details,
        )
