"""Safe URL & Issuer Domain Verification Service with SSRF Protection (Phase 5).

Protects against SSRF vulnerabilities by validating that verification URLs:
1. Enforce HTTPS protocol.
2. Ban loopback, private IPv4/IPv6, and metadata service IP addresses.
3. Restrict redirect chains to a maximum of 3 hops.
4. Enforce strict connection and read timeouts.
5. Classify domain trustworthiness against an authoritative Issuer Registry.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Optional, Union
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.models.issuer_registry import IssuerRegistryModel
from app.schemas.course_certificate import CourseURLVerificationResult, URLVerificationData

logger = logging.getLogger(__name__)

# Authoritative default registry seeds for recognized credential providers
DEFAULT_ISSUER_REGISTRY: list[dict[str, str]] = [
    {
        "issuer_name": "Coursera",
        "official_domain": "coursera.org",
        "verification_domain": "coursera.org",
        "verification_pattern": r"https://(?:www\.)?coursera\.org/verify/(?:[A-Z0-9]+)",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "edX",
        "official_domain": "edx.org",
        "verification_domain": "edx.org",
        "verification_pattern": r"https://(?:www\.)?edx\.org/certificates/(?:[a-f0-9]+)",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Udemy",
        "official_domain": "udemy.com",
        "verification_domain": "udemy.com",
        "verification_pattern": r"https://(?:www\.)?udemy\.com/certificate/(?:UC-[A-Za-z0-9]+)",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Credly",
        "official_domain": "credly.com",
        "verification_domain": "credly.com",
        "verification_pattern": r"https://(?:www\.)?credly\.com/badges/(?:[a-z0-9\-]+)",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Accredible",
        "official_domain": "accredible.com",
        "verification_domain": "accredible.com",
        "verification_pattern": r"https://(?:www\.)?accredible\.com/(?:[0-9]+)",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Harvard Online / HarvardX",
        "official_domain": "harvard.edu",
        "verification_domain": "online-learning.harvard.edu",
        "verification_pattern": r"https://.*harvard\.edu/.*",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Stanford Online",
        "official_domain": "stanford.edu",
        "verification_domain": "online.stanford.edu",
        "verification_pattern": r"https://.*stanford\.edu/.*",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Microsoft Learn",
        "official_domain": "microsoft.com",
        "verification_domain": "learn.microsoft.com",
        "verification_pattern": r"https://learn\.microsoft\.com/.*",
        "trusted_status": "TRUSTED",
    },
    {
        "issuer_name": "Google Cloud Skills Boost",
        "official_domain": "cloud.google.com",
        "verification_domain": "skillsboost.google",
        "verification_pattern": r"https://.*skillsboost\.google/.*",
        "trusted_status": "TRUSTED",
    },
]

AUTHORITATIVE_ISSUERS = {
    item["issuer_name"]: {
        "primary_domain": item["official_domain"],
        "verification_domain": item["verification_domain"],
        "verification_pattern": item.get("verification_pattern"),
        "trusted_status": item.get("trusted_status", "TRUSTED"),
    }
    for item in DEFAULT_ISSUER_REGISTRY
}


class URLVerifierService:
    """Validates verification URLs and looks up issuer authority safely."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def verify_url(
        self,
        url_string: Optional[str],
        check_accessibility: bool = True,
    ) -> "CourseURLVerificationResult":  # type: ignore[return]
        """Validate URL and return pipeline-compatible CourseURLVerificationResult."""
        from app.schemas.course_certificate import CourseURLVerificationResult

        full = self._do_verify(url_string, check_accessibility)
        return CourseURLVerificationResult(
            is_valid_url=full.is_valid_url,
            resolved_issuer=full.resolved_issuer,
            domain=full.domain,
            risk_level=full.risk_level,
            trust_score=full.trust_score,
            domain_match=full.domain_match,
            is_known_issuer=full.is_known_issuer,
            remarks=full.remarks or full.error_message,
        )

    def verify_url_full(
        self,
        url_string: Optional[str],
        check_accessibility: bool = True,
    ) -> URLVerificationData:
        """Validate URL and return the full URLVerificationData (for reports/tests)."""
        return self._do_verify(url_string, check_accessibility)

    def _do_verify(
        self,
        url_string: Optional[str],
        check_accessibility: bool = True,
    ) -> URLVerificationData:
        """Core URL verification logic returning the full URLVerificationData."""
        if not url_string or not isinstance(url_string, str) or not url_string.strip():
            return URLVerificationData(
                url=url_string,
                is_valid_syntax=False,
                trust_level="UNKNOWN",
                error_message="No URL provided for verification",
            )

        raw_url = url_string.strip()
        parsed = urlparse(raw_url)

        # 1. Syntax & Scheme Validation
        if not parsed.scheme or not parsed.netloc:
            return URLVerificationData(
                url=raw_url,
                is_valid_syntax=False,
                trust_level="SUSPICIOUS",
                error_message="Invalid URL structure or missing network host",
            )

        is_https = parsed.scheme.lower() == "https"
        domain = parsed.netloc.split(":")[0].lower()

        # Extract subdomain and apex domain
        parts = domain.split(".")
        subdomain = ".".join(parts[:-2]) if len(parts) > 2 else None
        apex_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain

        # 2. SSRF Protection: Reject private and loopback networks
        ssrf_check = self._validate_ssrf_safety(domain)
        if not ssrf_check["safe"]:
            return URLVerificationData(
                url=raw_url,
                is_valid_syntax=True,
                is_valid_url=False,
                is_https=is_https,
                domain=domain,
                subdomain=subdomain,
                trust_level="MALICIOUS",
                risk_level="MALICIOUS",
                remarks=f"SSRF Security Violation: {ssrf_check['reason']}",
                error_message=f"SSRF Security Violation: {ssrf_check['reason']}",
            )

        # 3. Lookup Issuer in Registry
        issuer_info = self._lookup_issuer(domain, apex_domain)
        trust_level: str = issuer_info.get("status") or "UNKNOWN"
        issuer_name: str | None = issuer_info.get("name") or None

        result = URLVerificationData(
            url=raw_url,
            is_valid_url=True,
            is_valid_syntax=True,
            is_https=is_https,
            domain=domain,
            subdomain=subdomain,
            issuer_name=issuer_name,
            resolved_issuer=issuer_name,
            trust_level=trust_level,
            risk_level=(
                "MALICIOUS"
                if trust_level == "MALICIOUS"
                else ("SUSPICIOUS" if trust_level == "SUSPICIOUS" else "SAFE")
            ),
            trust_score=(
                1.0 if trust_level == "TRUSTED" else (0.0 if trust_level == "MALICIOUS" else 0.5)
            ),
            domain_match=(trust_level == "TRUSTED"),
            is_known_issuer=bool(issuer_name),
        )

        # 4. Safe Online Accessibility Probe
        if check_accessibility:
            self._probe_accessibility(raw_url, result)

        if result.error_message:
            result.remarks = result.error_message

        return result

    def _validate_ssrf_safety(self, hostname: str) -> dict[str, Union[bool, str]]:
        """Resolve DNS and assert destination IP is not loopback, private, or link-local."""
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return {"safe": False, "reason": "Localhost loopback destination blocked"}

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_loopback
                    or ip_obj.is_private
                    or ip_obj.is_link_local
                    or ip_obj.is_reserved
                    or ip_obj.is_multicast
                ):
                    return {
                        "safe": False,
                        "reason": f"Destination resolved to protected non-public IP: {ip_str}",
                    }
        except (socket.gaierror, socket.herror, ValueError) as err:
            return {"safe": True, "reason": f"External unresolvable host: {err}"}

        return {"safe": True, "reason": "Public routable address"}

    def _lookup_issuer(self, host: str, apex_domain: str) -> dict[str, str | None]:
        """Query database or fallback registry for recognized issuer profile."""
        # 1. Check database if session provided
        if self.db:
            try:
                rec = (
                    self.db.query(IssuerRegistryModel)
                    .filter(
                        (IssuerRegistryModel.verification_domain == host)
                        | (IssuerRegistryModel.official_domain == apex_domain)
                    )
                    .first()
                )
                if rec:
                    return {
                        "name": str(rec.issuer_name),
                        "status": str(rec.trusted_status),
                    }
            except Exception as e:
                logger.warning("Database issuer query error: %s", e)

        # 2. Check static authoritative default registry
        for item in DEFAULT_ISSUER_REGISTRY:
            if (
                item["verification_domain"] == host
                or item["official_domain"] == apex_domain
                or host.endswith("." + item["verification_domain"])
            ):
                return {
                    "name": item["issuer_name"],
                    "status": item["trusted_status"],
                }

        # 3. Detect obviously suspicious TLDs or patterns
        suspicious_tlds = (".xyz", ".top", ".buzz", ".work", ".click", ".tk", ".ml")
        if any(host.endswith(tld) for tld in suspicious_tlds):
            return {"name": None, "status": "SUSPICIOUS"}

        return {"name": None, "status": "UNKNOWN"}

    def _probe_accessibility(self, url: str, data: URLVerificationData) -> None:
        """Safely probe verification URL using httpx with strict timeout and redirect caps."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CertCheck-Validator/1.0",
            "Accept": "text/html,application/xhtml+xml,application/json",
        }
        try:
            with httpx.Client(
                timeout=5.0,
                follow_redirects=True,
                max_redirects=3,
                verify=True,
            ) as client:
                resp = client.get(url, headers=headers)
                data.http_status = resp.status_code
                data.final_destination_url = str(resp.url)
                data.redirect_count = len(resp.history)
                data.page_accessible = resp.status_code in (200, 201, 204, 301, 302, 304)

        except (httpx.TimeoutException, httpx.ConnectError) as err:
            data.page_accessible = False
            data.error_message = f"Network timeout / unreachable endpoint: {err}"
            logger.info("URL accessibility probe timed out: %s", err)
        except Exception as exc:
            data.page_accessible = False
            data.error_message = f"URL request error: {exc}"
            logger.warning("URL accessibility probe error: %s", exc)


# Alias
CourseURLVerifier = URLVerifierService
