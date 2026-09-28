"""
Compatibility alias for GeminiVerifier service.
Allows importing via `app.services.gemini_verifier` or `services.geminiVerifier`.
"""

from app.services.geminiVerifier import (
    GeminiVerifier,
    get_gemini_verifier,
    verify_certificate_with_gemini,
)

__all__ = [
    "GeminiVerifier",
    "get_gemini_verifier",
    "verify_certificate_with_gemini",
]
