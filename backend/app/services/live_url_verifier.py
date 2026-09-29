"""
Live Institutional URL Cross-Verification Engine (Web Scraping & Truth-Check).
Detects identity-swapped fake certificates by querying live accredited databases
(Coursera, NPTEL, edX, etc.) and verifying the genuine credential holder.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class LiveURLVerifier:
    """Performs live network truth-checks against institutional verification portals."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @staticmethod
    def sanitize_url(raw_url: str) -> str:
        """Strip OCR-introduced whitespace and extraneous punctuation from URLs."""
        if not raw_url:
            return ""

        s = raw_url.strip()
        # Remove common trailing punctuation
        s = s.rstrip(".,;:)]}>\"'")

        # Collapse OCR whitespace in common domains and paths
        # e.g., 'cour  ser a.or  g /v er if y /ST4861' -> 'coursera.org/verify/ST4861'
        domain_fixes = [
            (r"cour\s*ser\s*a", "coursera"),
            (r"np\s*tel", "nptel"),
            (r"ed\s*x", "edx"),
            (r"ver\s*if\s*y", "verify"),
            (r"spe\s*cia\s*li\s*za\s*tion", "specialization"),
            (r"cer\s*ti\s*fi\s*cate", "certificate"),
            (r"\.or\s*g", ".org"),
            (r"\.ac\s*\.\s*in", ".ac.in"),
            (r"\.edu", ".edu"),
            (r"\.com", ".com"),
            (r"\.gov\s*\.\s*in", ".gov.in"),
        ]
        for pattern, repl in domain_fixes:
            s = re.sub(pattern, repl, s, flags=re.IGNORECASE)

        # Remove spaces around URL delimiters
        s = re.sub(r"\s*([:/?.=&_])\s*", r"\1", s)

        # Remove any internal spaces in path or query
        if "://" in s:
            scheme, rest = s.split("://", 1)
            rest = re.sub(r"\s+", "", rest)
            s = f"{scheme}://{rest}"
        else:
            s = re.sub(r"\s+", "", s)
            if re.match(r"^(?:www\.)?(?:coursera|nptel|edx|swayam|vtu)", s, re.I):
                s = "https://" + s

        s = re.sub(r"(verify/(?:specialization/)?[A-Za-z0-9]+?)[Cc]ourser[a-z]*$", r"\1", s)
        return s.strip().rstrip(".,;:)]}>\"'")

    @staticmethod
    def extract_token_from_url(url: str) -> Optional[str]:
        """Extract verification token/code from URL."""
        if not url:
            return None
        # Coursera patterns
        coursera_match = re.search(
            r"coursera\.org/verify/(?:specialization/)?([A-Za-z0-9]+)", url, re.I
        )
        if coursera_match:
            tok = coursera_match.group(1).strip()
            return re.sub(r"[Cc]ourser[a-z]*$", "", tok)

        # NPTEL patterns
        nptel_match = re.search(r"nptel\.ac\.in/noc/Ecertificate/\?q=([A-Za-z0-9]+)", url, re.I)
        if nptel_match:
            return nptel_match.group(1).strip()

        # edX patterns
        edx_match = re.search(r"edx\.org/certificates?/([A-Za-z0-9]+)", url, re.I)
        if edx_match:
            return edx_match.group(1).strip()

        # Fallback to last path segment
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            last = path_parts[-1]
            if last.lower() not in ["verify", "specialization", "certificate", "records", "view"]:
                return last
        return None

    def _scrape_coursera_page(self, html: str, final_url: str) -> Dict[str, Any]:
        """Parse Coursera verification page HTML to extract official learner record."""
        soup = BeautifulSoup(html, "html.parser")
        text_lower = html.lower()

        # Check for 404 / Missing Certificate Indicators
        missing_indicators = [
            "we couldn't find that certificate",
            "couldn't find that certificate",
            "we couldn't find",
            "page not found",
            "invalid certificate",
        ]
        for indicator in missing_indicators:
            if indicator in text_lower:
                return {
                    "is_found": False,
                    "learner_name": None,
                    "course_title": None,
                    "issue_date": None,
                    "reason": "Certificate verification URL does not exist on Coursera servers (404/Not Found)",
                }

        # Check if the page is missing accomplishments content
        if "completed by" not in text_lower and "accomplishment" not in text_lower and "specialization" not in text_lower:
            return {
                "is_found": False,
                "learner_name": None,
                "course_title": None,
                "issue_date": None,
                "reason": "No valid credential record found on Coursera verification portal",
            }

        # 1. Extract Learner Name
        learner_name: Optional[str] = None

        # Method A: Look for container with "Completed by"
        for el in soup.find_all(lambda t: t.name in ["h3", "p", "div", "span"] and "completed by" in t.get_text().lower()):
            strongs = el.find_all("strong")
            if strongs:
                candidate = strongs[0].get_text(strip=True)
                if candidate and len(candidate) < 80:
                    learner_name = candidate
                    break
            # Fallback regex inside element text
            el_text = el.get_text(strip=True)
            m = re.search(r"completed by\s*([A-Za-z0-9\s\.\-_]+)", el_text, re.I)
            if m:
                learner_name = m.group(1).strip()
                break

        # Method B: Check h3 tags if not found yet
        if not learner_name:
            for h in soup.find_all("h3"):
                h_text = h.get_text(strip=True)
                if "completed by" in h_text.lower():
                    clean = re.sub(r"completed by", "", h_text, flags=re.I).strip()
                    if clean and len(clean) < 80:
                        learner_name = clean
                        break

        # 2. Extract Course Title
        course_title: Optional[str] = None
        for h in soup.find_all(["h1", "h2", "h3"]):
            h_text = h.get_text(strip=True)
            if not h_text:
                continue
            if any(
                skip in h_text.lower()
                for skip in [
                    "what you will learn",
                    "skills you will gain",
                    "skills",
                    "professional certificates",
                    "courses & specializations",
                    "career resources",
                    "coursera",
                    "community",
                    "more",
                    "completed by",
                    "what an interesting discovery",
                ]
            ):
                continue
            if len(h_text) > 4 and len(h_text) < 120:
                course_title = h_text
                break

        # 3. Extract Issue Date
        issue_date: Optional[str] = None
        date_pattern = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
        date_match = re.search(date_pattern, html, re.I)
        if date_match:
            issue_date = date_match.group(0).strip()

        return {
            "is_found": bool(learner_name or course_title),
            "learner_name": learner_name,
            "course_title": course_title,
            "issue_date": issue_date,
            "reason": None if learner_name else "Unable to parse learner name from Coursera page",
        }

    def _scrape_nptel_page(self, html: str, final_url: str) -> Dict[str, Any]:
        """Parse NPTEL verification portal HTML."""
        soup = BeautifulSoup(html, "html.parser")
        text_lower = html.lower()

        if "not found" in text_lower or "invalid" in text_lower or "no records" in text_lower:
            return {
                "is_found": False,
                "learner_name": None,
                "course_title": None,
                "issue_date": None,
                "reason": "Certificate roll number not found in NPTEL official registry",
            }

        learner_name = None
        course_title = None

        # Look for table rows or definitions containing Name / Course
        for row in soup.find_all(["tr", "div", "p"]):
            text = row.get_text(separator=" ", strip=True)
            if "name" in text.lower() and not learner_name:
                m = re.search(r"name\s*[:\-]\s*([A-Za-z\s\.]+)", text, re.I)
                if m:
                    learner_name = m.group(1).strip()
            if "course" in text.lower() and not course_title:
                m = re.search(r"course(?:\s+name)?\s*[:\-]\s*([A-Za-z0-9\s\.\-_]+)", text, re.I)
                if m:
                    course_title = m.group(1).strip()

        return {
            "is_found": bool(learner_name or course_title),
            "learner_name": learner_name,
            "course_title": course_title,
            "issue_date": None,
            "reason": None if learner_name else "Parsed NPTEL registry entry",
        }

    def verify_live_url(
        self,
        url: str,
        visual_student_name: Optional[str] = None,
        visual_course_title: Optional[str] = None,
        raw_document_text: Optional[str] = None,
        timeout: float = 12.0,
    ) -> Dict[str, Any]:
        """Execute live HTTP GET verification against institutional portal and cross-check identity.

        Hierarchy: Official Issuer Web Database > Visual OCR > Forensic Image Artifacts.
        """
        clean_url = self.sanitize_url(url)
        if not clean_url:
            return {
                "executed": False,
                "error": "No valid verification URL provided",
                "is_valid": False,
                "url_status": "NO_URL",
            }

        parsed = urlparse(clean_url)
        domain = parsed.netloc.lower()

        provider = "GENERIC"
        if "coursera.org" in domain:
            provider = "COURSERA"
        elif "nptel.ac.in" in domain:
            provider = "NPTEL"
        elif "edx.org" in domain:
            provider = "EDX"

        token = self.extract_token_from_url(clean_url)
        logger.info(
            "Executing live URL truth-check: %s (Provider: %s, Token: %s)",
            clean_url,
            provider,
            token,
        )

        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                follow_redirects=True,
                timeout=timeout,
            ) as client:
                resp = client.get(clean_url)
                http_status = resp.status_code
                final_url = str(resp.url)
                html_body = resp.text
        except httpx.TimeoutException:
            logger.warning("Live URL verification timed out for %s", clean_url)
            return {
                "executed": True,
                "sanitized_url": clean_url,
                "provider": provider,
                "token": token,
                "url_status": "TIMEOUT",
                "http_status_code": 408,
                "is_valid": True,  # Neutral on network timeout: do not falsely penalize if offline
                "is_mismatch": False,
                "mismatch_flag": None,
                "reason": "Live institutional server check timed out; falling back to visual & cryptographic checks",
                "verdict": "SUSPICIOUS",
                "confidence_score": 0.85,
            }
        except Exception as net_err:
            logger.warning("Live URL network error for %s: %s", clean_url, net_err)
            return {
                "executed": True,
                "sanitized_url": clean_url,
                "provider": provider,
                "token": token,
                "url_status": "NETWORK_ERROR",
                "http_status_code": 0,
                "is_valid": True,
                "is_mismatch": False,
                "mismatch_flag": None,
                "reason": f"Network check unable to reach verification server: {str(net_err)}",
                "verdict": "SUSPICIOUS",
                "confidence_score": 0.85,
            }

        # -------------------------------------------------------------
        # Evaluate HTTP Status & Content
        # -------------------------------------------------------------
        if http_status == 404:
            logger.warning("Institutional verification URL returned 404: %s", clean_url)
            return {
                "executed": True,
                "sanitized_url": clean_url,
                "provider": provider,
                "token": token,
                "url_status": "INVALID_URL_404",
                "http_status_code": 404,
                "is_valid": False,
                "is_mismatch": True,
                "mismatch_flag": "INVALID_URL_404",
                "verdict": "FRAUDULENT",
                "confidence_score": 0.05,
                "reason": "Certificate verification URL does not exist on issuer servers (404 Not Found)",
                "discrepancy_details": (
                    f"The printed verification URL ({clean_url}) returned 404 Not Found "
                    f"on the official {provider} infrastructure. This indicates a counterfeit link."
                ),
            }

        if http_status != 200:
            return {
                "executed": True,
                "sanitized_url": clean_url,
                "provider": provider,
                "token": token,
                "url_status": f"HTTP_{http_status}",
                "http_status_code": http_status,
                "is_valid": False,
                "is_mismatch": True,
                "mismatch_flag": "HTTP_ERROR",
                "verdict": "SUSPICIOUS",
                "confidence_score": 0.40,
                "reason": f"Verification server responded with HTTP {http_status}",
            }

        # Scrape and parse provider portal
        scraped: Dict[str, Any] = {}
        if provider == "COURSERA":
            scraped = self._scrape_coursera_page(html_body, final_url)
        elif provider == "NPTEL":
            scraped = self._scrape_nptel_page(html_body, final_url)
        else:
            scraped = {
                "is_found": True,
                "learner_name": None,
                "course_title": None,
                "issue_date": None,
                "reason": "Generic accredited domain reached with 200 OK",
            }

        if not scraped.get("is_found"):
            logger.warning("Scraper found no certificate record on 200 OK page: %s", clean_url)
            return {
                "executed": True,
                "sanitized_url": clean_url,
                "provider": provider,
                "token": token,
                "url_status": "INVALID_URL_404",
                "http_status_code": 404,
                "is_valid": False,
                "is_mismatch": True,
                "mismatch_flag": "INVALID_URL_404",
                "verdict": "FRAUDULENT",
                "confidence_score": 0.05,
                "reason": scraped.get("reason") or "Certificate verification record does not exist on issuer servers",
                "discrepancy_details": (
                    f"The official {provider} portal confirmed no credential record exists for ID '{token}'."
                ),
            }

        web_registered_name = scraped.get("learner_name")
        web_course_title = scraped.get("course_title")
        web_issue_date = scraped.get("issue_date")

        # -------------------------------------------------------------
        # Truth Engine: Cross-Check Visual OCR against Live Web Data
        # -------------------------------------------------------------
        name_similarity = 100.0
        is_name_mismatch = False
        mismatch_flag: Optional[str] = None
        discrepancy_details: Optional[str] = None

        if web_registered_name and visual_student_name:
            v_name_clean = visual_student_name.strip()
            w_name_clean = web_registered_name.strip()

            token_sort = fuzz.token_sort_ratio(v_name_clean.lower(), w_name_clean.lower())
            direct_ratio = fuzz.ratio(v_name_clean.lower(), w_name_clean.lower())
            name_similarity = round(max(token_sort, direct_ratio), 1)

            if name_similarity < 85.0:
                is_name_mismatch = True
                mismatch_flag = "IDENTITY_MISMATCH_FRAUD"
                discrepancy_details = (
                    f"Critical Discrepancy: Certificate displays '{visual_student_name}', "
                    f"but {provider} registry records this credential ID under '{web_registered_name}'."
                )
                logger.error(
                    "IDENTITY MISMATCH DETECTED: Visual='%s' vs Live Registry='%s' (Similarity: %s%%)",
                    visual_student_name,
                    web_registered_name,
                    name_similarity,
                )

        course_similarity = 100.0
        is_course_mismatch = False
        if web_course_title:
            w_course_clean = web_course_title.strip()
            # If the web course title appears directly in document text, it is confirmed authentic
            if raw_document_text and (
                w_course_clean.lower() in raw_document_text.lower()
                or fuzz.partial_ratio(w_course_clean.lower(), raw_document_text.lower()) >= 80.0
            ):
                course_similarity = 100.0
                is_course_mismatch = False
            elif visual_course_title:
                v_course_clean = visual_course_title.strip()
                c_score = fuzz.token_set_ratio(v_course_clean.lower(), w_course_clean.lower())
                course_similarity = round(c_score, 1)

                if course_similarity < 65.0:
                    is_course_mismatch = True
                    if not mismatch_flag:
                        mismatch_flag = "COURSE_MISMATCH_FRAUD"
                        discrepancy_details = (
                            f"Critical Discrepancy: Certificate course title '{visual_course_title}' "
                            f"does not match issuer registry title '{web_course_title}'."
                        )

        # -------------------------------------------------------------
        # Decision Synthesis (Official Web Database is Truth Authority)
        # -------------------------------------------------------------
        if is_name_mismatch or is_course_mismatch:
            verdict = "FRAUDULENT"
            confidence_score = 0.05
            is_valid = False
            reason = discrepancy_details or "Registry data mismatch"
        else:
            verdict = "AUTHENTIC"
            confidence_score = 0.99
            is_valid = True
            reason = (
                f"Live {provider} registry verified: Credential ID '{token}' matches registered learner '{web_registered_name}'"
                if web_registered_name
                else f"Live {provider} registry reached with 200 OK status"
            )

        return {
            "executed": True,
            "sanitized_url": clean_url,
            "provider": provider,
            "token": token,
            "url_status": "VERIFIED_200",
            "http_status_code": 200,
            "is_valid": is_valid,
            "is_mismatch": is_name_mismatch or is_course_mismatch,
            "mismatch_flag": mismatch_flag,
            "web_registered_name": web_registered_name,
            "web_course_title": web_course_title,
            "web_issue_date": web_issue_date,
            "visual_student_name": visual_student_name,
            "visual_course_title": visual_course_title,
            "name_similarity": name_similarity,
            "course_similarity": course_similarity,
            "verdict": verdict,
            "confidence_score": confidence_score,
            "reason": reason,
            "discrepancy_details": discrepancy_details,
        }


# Global singleton instance
_live_verifier: Optional[LiveURLVerifier] = None


def get_live_url_verifier() -> LiveURLVerifier:
    global _live_verifier
    if _live_verifier is None:
        _live_verifier = LiveURLVerifier()
    return _live_verifier
