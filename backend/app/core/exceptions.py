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


class UnsupportedFileTypeError(AppException):
    """Uploaded file MIME type or magic signature is not allowed."""

    def __init__(
        self,
        message: str = "Uploaded file format is not supported. Allowed formats: JPEG, PNG, PDF.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=415,
            error_code="UNSUPPORTED_FILE_TYPE",
            details=details,
        )


class FileTooLargeError(AppException):
    """Uploaded file exceeds the maximum allowed upload size."""

    def __init__(
        self,
        message: str = "File size exceeds the maximum limit.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=413,
            error_code="FILE_TOO_LARGE",
            details=details,
        )


class EmptyFileError(AppException):
    """Uploaded file has zero bytes."""

    def __init__(
        self,
        message: str = "Uploaded file is empty (0 bytes).",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="EMPTY_FILE",
            details=details,
        )


class InvalidFileError(AppException):
    """Uploaded file header or structure is invalid."""

    def __init__(
        self,
        message: str = "Uploaded file is invalid or malformed.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_FILE",
            details=details,
        )


class CorruptedFileError(AppException):
    """File cannot be decoded, is truncated, or has corrupt content."""

    def __init__(
        self,
        message: str = "File data is corrupted or truncated.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="CORRUPTED_FILE",
            details=details,
        )


class InsufficientResolutionError(AppException):
    """Image resolution does not meet minimum pixel dimensions."""

    def __init__(
        self,
        message: str = (
            "Image resolution is too low for reliable verification (minimum 800x600 px required)."
        ),
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="INSUFFICIENT_RESOLUTION",
            details=details,
        )


class EncryptedPdfError(AppException):
    """PDF is password protected or encrypted."""

    def __init__(
        self,
        message: str = (
            "Password-protected PDF files cannot be processed. Please upload an unprotected copy."
        ),
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="ENCRYPTED_PDF",
            details=details,
        )


class PDFConversionError(AppException):
    """Failed to rasterize PDF document into image format."""

    def __init__(
        self,
        message: str = "Failed to rasterize PDF pages.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="PDF_CONVERSION_ERROR",
            details=details,
        )
