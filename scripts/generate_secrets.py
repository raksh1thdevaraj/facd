#!/usr/bin/env python3
"""Cryptographic Secrets Generator for Production Deployment (CHIP DEP-05).

Generates high-entropy cryptographic keys and passwords for production isolation:
1. SECRET_KEY (256-bit / 64 hex characters)
2. REPORT_SIGNING_KEY (256-bit / 64 hex characters)
3. POSTGRES_PASSWORD (256-bit URL-safe token)
"""

from __future__ import annotations

import secrets


def generate_production_secrets() -> dict[str, str]:
    """Generate cryptographically secure random keys using secrets module."""
    secret_key = secrets.token_hex(32)
    report_signing_key = secrets.token_hex(32)
    postgres_password = secrets.token_urlsafe(24)

    return {
        "SECRET_KEY": secret_key,
        "REPORT_SIGNING_KEY": report_signing_key,
        "POSTGRES_PASSWORD": postgres_password,
    }


def main() -> None:
    """Print generated secrets to stdout in dotenv format."""
    sec = generate_production_secrets()
    print(
        "# =============================================================================="
    )
    print("# Cryptographically Generated Production Secrets (NFR-02)")
    print("# DO NOT COMMIT THESE VALUES TO SOURCE CONTROL")
    print(
        "# =============================================================================="
    )
    for k, v in sec.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
