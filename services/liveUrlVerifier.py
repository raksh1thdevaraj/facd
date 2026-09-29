"""
Shim exporter for LiveURLVerifier to support root-level services/ imports.
"""

from app.services.live_url_verifier import LiveURLVerifier, get_live_url_verifier

__all__ = ["LiveURLVerifier", "get_live_url_verifier"]
