"""Security Hardening, Nginx Headers, and Secrets Isolation Tests (CHIP DEP-12).

Covers (TC-DEP-03, TC-DEP-04, TC-DEP-05).

Validates:
1. Nginx edge gateway security headers and 10MB upload limit.
2. Cryptographic secrets generator output quality.
3. Production environment refusal on insecure or short secrets.
4. GitHub Actions CI pipeline configuration integrity.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings  # noqa: E402


def test_nginx_security_headers_and_upload_limit() -> None:
    """Verify Nginx reverse proxy enforces 10MB limit and injects security headers (TC-DEP-03)."""
    nginx_conf = PROJECT_ROOT / "nginx" / "nginx.conf"
    assert nginx_conf.exists(), "nginx/nginx.conf must exist"

    content = nginx_conf.read_text(encoding="utf-8")

    # 10MB upload limit enforcement at network edge
    assert "client_max_body_size 10M;" in content, (
        "Nginx gateway must enforce client_max_body_size 10M"
    )

    # Required security headers (NFR-02)
    assert 'X-Frame-Options "DENY"' in content, "X-Frame-Options: DENY must be configured"
    assert 'X-Content-Type-Options "nosniff"' in content, (
        "X-Content-Type-Options: nosniff must be configured"
    )
    assert 'X-XSS-Protection "1; mode=block"' in content, "X-XSS-Protection must be configured"
    assert 'Referrer-Policy "strict-origin-when-cross-origin"' in content, (
        "Referrer-Policy must be configured"
    )
    assert "Content-Security-Policy" in content, "Content-Security-Policy header must be configured"
    assert "Strict-Transport-Security" in content, (
        "Strict-Transport-Security (HSTS) header must be configured"
    )


def test_secrets_generator_script() -> None:
    """Verify secrets generator creates high-entropy 256-bit hexadecimal keys (TC-DEP-04)."""
    import importlib.util

    script_path = PROJECT_ROOT / "scripts" / "generate_secrets.py"
    assert script_path.exists(), "scripts/generate_secrets.py must exist"

    spec = importlib.util.spec_from_file_location("generate_secrets", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    sec = mod.generate_production_secrets()

    assert "SECRET_KEY" in sec
    assert "REPORT_SIGNING_KEY" in sec
    assert "POSTGRES_PASSWORD" in sec

    # Hex tokens for 32 bytes produce 64 characters
    assert len(sec["SECRET_KEY"]) == 64, "SECRET_KEY must be 64 hex characters (256 bits)"
    assert len(sec["REPORT_SIGNING_KEY"]) == 64, "REPORT_SIGNING_KEY must be 64 hex characters"
    assert len(sec["POSTGRES_PASSWORD"]) >= 24, "POSTGRES_PASSWORD must be at least 24 chars"


def test_production_rejects_insecure_secrets() -> None:
    """Verify backend settings refuse startup if default or short secrets are used.

    Covers (TC-DEP-04).
    """
    insecure_keys = [
        "change_me",
        "secret",
        "default-insecure-dev-key-change-in-production-0123456789",
        "too-short",
    ]

    for key in insecure_keys:
        with pytest.raises(ValueError, match="Production security violation"):
            Settings(ENVIRONMENT="production", SECRET_KEY=key)


def test_production_accepts_valid_strong_secret() -> None:
    """Verify backend settings accept strong 64-character secret in production mode."""
    valid_key = "a" * 64
    s = Settings(ENVIRONMENT="production", SECRET_KEY=valid_key)
    assert s.SECRET_KEY == valid_key
    assert s.ENVIRONMENT == "production"


def test_github_actions_ci_workflow_structure() -> None:
    """Verify GitHub Actions CI workflow contains all required quality jobs (TC-DEP-05)."""
    ci_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), ".github/workflows/ci.yml must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = yaml.safe_load(f)

    jobs = ci_data.get("jobs", {})
    assert "lint-and-quality" in jobs, "CI must contain lint-and-quality job"
    assert "backend-tests" in jobs, "CI must contain backend-tests job"
    assert "frontend-build" in jobs, "CI must contain frontend-build job"
    assert "docker-build-test" in jobs, "CI must contain docker-build-test job"
