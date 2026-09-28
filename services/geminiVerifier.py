# ruff: noqa: N999
"""
Dedicated Google Gemini Vision Verifier module.
Matches specification path: `services/geminiVerifier.py`.
"""

import sys
from pathlib import Path

# Ensure backend is on sys.path
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent if _current_dir.name == "services" else _current_dir
_backend_dir = _root_dir / "backend"

for p in [str(_backend_dir), str(_root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

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
