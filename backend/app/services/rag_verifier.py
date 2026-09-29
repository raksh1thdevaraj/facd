"""RAG-Based Ground-Truth Cross-Verification Engine.

Cross-examines extracted certificate OCR/visual data and decoded QR/URL payloads
against authoritative institutional schemas (VTU CBCS grading regulations,
Coursera verification specs, NPTEL/Swayam criteria, and Unacademy formats).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Search paths for schema knowledge files
SCHEMA_PATHS = [
    Path(__file__).parent.parent / "rag_knowledge",
    Path(__file__).parent.parent.parent.parent / "rag_knowledge",
    Path.cwd() / "rag_knowledge",
    Path.cwd() / "backend" / "app" / "rag_knowledge",
]


def _load_json_schema(filename: str, fallback_default: Dict[str, Any]) -> Dict[str, Any]:
    """Search for and load schema JSON file, returning fallback if not found."""
    for base_dir in SCHEMA_PATHS:
        candidate = base_dir / filename
        if candidate.is_file():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to parse schema %s: %s", candidate, e)
    return fallback_default


# Authoritative fallback schemas
DEFAULT_VTU_SCHEMA = {
    "schema_name": "VTU_CBCS_GRADING_SCHEMA",
    "document_type": "VTU_MARKSCARD",
    "authority": "Visvesvaraya Technological University",
    "aliases": ["VTU", "VISVESVARAYA TECHNOLOGICAL UNIVERSITY", "VTU BELAGAVI", "VTU BELGAUM", "JNANA SANGAMA"],
    "usn_pattern": r"^[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}$",
    "grading_rules": {
        "O": {"name": "Outstanding", "grade_points": 10, "min_marks": 90, "max_marks": 100},
        "A+": {"name": "Excellent", "grade_points": 9, "min_marks": 80, "max_marks": 89},
        "A": {"name": "Very Good", "grade_points": 8, "min_marks": 70, "max_marks": 79},
        "B+": {"name": "Good", "grade_points": 7, "min_marks": 60, "max_marks": 69},
        "B": {"name": "Above Average", "grade_points": 6, "min_marks": 55, "max_marks": 59},
        "C": {"name": "Average", "grade_points": 5, "min_marks": 50, "max_marks": 54},
        "P": {"name": "Pass", "grade_points": 4, "min_marks": 40, "max_marks": 49},
        "F": {"name": "Fail", "grade_points": 0, "min_marks": 0, "max_marks": 39},
    },
    "official_domains": ["vtu.ac.in", "results.vtu.ac.in", "exam.vtu.ac.in", "universitysolutions.in"],
}

DEFAULT_COURSE_PROVIDERS = {
    "document_type": "ONLINE_COURSE_CERTIFICATE",
    "providers": [
        {
            "provider_id": "COURSERA",
            "name": "Coursera Inc.",
            "aliases": ["COURSERA", "COURSERA.ORG", "COURSERA INC"],
            "official_domains": ["coursera.org"],
            "verification_url_patterns": [
                r"^https?://(www\.)?coursera\.org/verify/(specialization/)?[A-Z0-9]+",
                r"^coursera\.org/verify/(specialization/)?[A-Z0-9]+",
                r"coursera\.org/verify/",
            ],
            "certificate_id_pattern": r"^[A-Z0-9]{10,24}$",
        },
        {
            "provider_id": "NPTEL",
            "name": "NPTEL / Swayam",
            "aliases": ["NPTEL", "SWAYAM", "IIT", "IISc", "NATIONAL PROGRAMME ON TECHNOLOGY ENHANCED LEARNING"],
            "official_domains": ["nptel.ac.in", "archive.nptel.ac.in", "swayam.gov.in"],
            "verification_url_patterns": [r"^https?://(www\.)?(archive\.)?nptel\.ac\.in/.*", r"^https?://(www\.)?swayam\.gov\.in/.*"],
            "certificate_id_pattern": r"^NPTEL\d{2}[A-Z]{2}\d{2}[A-Z0-9]+$",
        },
        {
            "provider_id": "UNACADEMY",
            "name": "Unacademy",
            "aliases": ["UNACADEMY"],
            "official_domains": ["unacademy.com"],
            "verification_url_patterns": [r"^https?://(www\.)?unacademy\.com/.*"],
            "certificate_id_pattern": r"^[A-Z0-9\-]+$",
        },
    ],
}


class RAGSchemaVerifier:
    """Evaluates certificate data against institutional ground-truth schemas."""

    def __init__(self) -> None:
        self.vtu_schema = _load_json_schema("vtu_schema.json", DEFAULT_VTU_SCHEMA)
        self.course_schema = _load_json_schema("course_providers_schema.json", DEFAULT_COURSE_PROVIDERS)

    def detect_document_type(
        self,
        issuer: Optional[str] = None,
        raw_text: Optional[str] = None,
        certificate_type: Optional[str] = None,
        qr_url: Optional[str] = None,
    ) -> str:
        """Classify document into 'VTU_MARKSCARD' or 'ONLINE_COURSE_CERTIFICATE'."""
        text_corpus = f"{issuer or ''} {raw_text or ''} {qr_url or ''}".upper()

        # Check for Course Providers
        course_keywords = ["COURSERA", "NPTEL", "SWAYAM", "UNACADEMY", "UDEMY", "EDX", "COURSE COMPLETION", "COURSE CERTIFICATE"]
        if any(kw in text_corpus for kw in course_keywords) or certificate_type == "course_certificate":
            if not any(vtu_kw in text_corpus for vtu_kw in ["VTU", "VISVESVARAYA", "MARKS CARD", "SEMESTER GRADE"]):
                return "ONLINE_COURSE_CERTIFICATE"

        # Check for VTU / Academic Markscard
        vtu_keywords = ["VTU", "VISVESVARAYA", "MARKS CARD", "SGPA", "CGPA", "USN", "SEMESTER"]
        if any(kw in text_corpus for kw in vtu_keywords) or certificate_type in ["marks_card", "markscard"]:
            return "VTU_MARKSCARD"

        # Default fallback based on certificate_type
        if certificate_type == "course_certificate":
            return "ONLINE_COURSE_CERTIFICATE"
        return "VTU_MARKSCARD"

    def get_schema_prompt_context(
        self, certificate_type: Optional[str] = None, text_hint: Optional[str] = None
    ) -> str:
        """Generate schema rules text for augmenting the Gemini prompt based on detected issuer."""
        doc_type = self.detect_document_type(
            issuer=text_hint, raw_text=text_hint, certificate_type=certificate_type
        )
        if doc_type == "VTU_MARKSCARD":
            grading_str = ", ".join(
                f"{g}: {info.get('grade_points')} pts ({info.get('min_marks')}-{info.get('max_marks')})"
                for g, info in self.vtu_schema.get("grading_rules", {}).items()
            )
            domains_str = ", ".join(self.vtu_schema.get("official_domains", []))
            authority_str = self.vtu_schema.get("authority", "Visvesvaraya Technological University")
            usn_pattern_str = self.vtu_schema.get("usn_pattern", r"^[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}$")
            return f"""
AUTHORITATIVE VTU CBCS INSTITUTIONAL REFERENCE SCHEMA & ARITHMETIC RULES:
- Target Authority: {authority_str}
- USN Format: {usn_pattern_str} (10-char alphanumeric: 1-4 region code + 2-letter college code + 2-digit year + 2-letter branch + 3-digit roll)
- Regional Centers: 1=Bengaluru, 2=Belagavi, 3=Kalaburagi, 4=Mysuru
- CBCS Grading Rules: {grading_str}
- SGPA Formula: sum(Ci * Gi) / sum(Ci), where Ci is subject credit and Gi is grade point. Typical semester credits = 20-24.
- Official Accredited Domains: {domains_str}

Cross-Examination Tasks:
1. Does the calculated SGPA match the listed individual marks/grades and credits mathematically?
2. Does the USN match standard 10-char VTU CBCS syntax and a valid regional center digit (1-4)?
3. Does the verification URL (if any) resolve to an accredited VTU domain?
4. Flag any arithmetic contradictions or schema non-compliances.
"""
        else:
            prov_summaries = []
            for p in self.course_schema.get("providers", []):
                p_domains = ", ".join(p.get("official_domains", []))
                p_id_pat = p.get("certificate_id_pattern", "N/A")
                prov_summaries.append(
                    f"- {p.get('name')}: Official domains: {p_domains}; ID Pattern: {p_id_pat}"
                )
            prov_text = "\n".join(prov_summaries)
            return f"""
AUTHORITATIVE ONLINE COURSE CREDENTIAL REFERENCE SCHEMA & SPECIFICATIONS:
{prov_text}

Cross-Examination Tasks:
1. Verify whether the Certificate ID format conforms to official provider specification (e.g. Coursera 10-24 char alphanumeric, NPTEL NPTEL<year><discipline>...).
2. Verify whether verification URL points to an accredited provider domain (coursera.org/verify, nptel.ac.in/noc, unacademy.com/certificate).
3. Verify if percentage or completion grade matches stated honors/criteria (e.g. NPTEL Elite >= 60%, Elite+Gold >= 90%).
4. Flag any visual inconsistencies, unaccredited redirect domains, or format discrepancies.
"""

    def cross_verify(
        self,
        extracted_data: Dict[str, Any],
        qr_verification: Dict[str, Any],
        raw_text: Optional[str] = None,
        certificate_type: Optional[str] = None,
        gemini_arithmetic: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform end-to-end RAG logical cross-verification.

        Returns:
            Dict conforming to:
            {
                "document_type": "VTU_MARKSCARD" | "ONLINE_COURSE_CERTIFICATE",
                "schema_matched": bool,
                "arithmetic_valid": bool,
                "anomalies_detected": List[str],
                "mismatch_report": str,
            }
        """
        student_name = (extracted_data.get("student_name") or "").strip()
        identifier = (extracted_data.get("identifier") or extracted_data.get("reg_no") or "").strip()
        issuer = (extracted_data.get("issuer") or extracted_data.get("institution_name") or "").strip()
        score_or_cgpa = (extracted_data.get("score_or_cgpa") or extracted_data.get("sgpa") or "").strip()

        qr_url = qr_verification.get("payload_or_url") or qr_verification.get("url") or ""
        qr_detected = bool(qr_verification.get("detected") or qr_verification.get("qr_present"))

        doc_type = self.detect_document_type(
            issuer=issuer,
            raw_text=raw_text,
            certificate_type=certificate_type,
            qr_url=qr_url,
        )

        anomalies: List[str] = []
        schema_matched = True
        arithmetic_valid = True

        if doc_type == "VTU_MARKSCARD":
            schema_matched, arithmetic_valid, vtu_anomalies = self._verify_vtu_marks_card(
                identifier=identifier,
                issuer=issuer,
                score_or_cgpa=score_or_cgpa,
                raw_text=raw_text or "",
                qr_url=qr_url,
                gemini_arithmetic=gemini_arithmetic,
            )
            anomalies.extend(vtu_anomalies)
        else:
            schema_matched, arithmetic_valid, course_anomalies = self._verify_online_course(
                identifier=identifier,
                issuer=issuer,
                score_or_cgpa=score_or_cgpa,
                raw_text=raw_text or "",
                qr_url=qr_url,
            )
            anomalies.extend(course_anomalies)

        # Cross-examine QR payload vs Extracted Text (Cryptographic Payload Check)
        if qr_detected and qr_url:
            conflict, conflict_reason = self._check_qr_payload_conflict(
                qr_url=qr_url,
                student_name=student_name,
                identifier=identifier,
            )
            if conflict:
                anomalies.append(f"FRAUD_DATA_MISMATCH: {conflict_reason}")
                schema_matched = False

        mismatch_report = "; ".join(anomalies) if anomalies else "All institutional schema and arithmetic rules fully validated."

        return {
            "document_type": doc_type,
            "schema_matched": schema_matched and len(anomalies) == 0,
            "arithmetic_valid": arithmetic_valid,
            "anomalies_detected": anomalies,
            "mismatch_report": mismatch_report,
        }

    def _verify_vtu_marks_card(
        self,
        identifier: str,
        issuer: str,
        score_or_cgpa: str,
        raw_text: str,
        qr_url: str,
        gemini_arithmetic: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, bool, List[str]]:
        """Cross-examine against VTU CBCS schema."""
        anomalies: List[str] = []
        schema_matched = True
        arithmetic_valid = True

        usn_regex = self.vtu_schema.get("usn_pattern", r"^[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}$")

        # 1. USN Pattern Verification
        if identifier:
            clean_usn = identifier.replace(" ", "").upper()
            if not re.match(usn_regex, clean_usn):
                # Check if it looks like an academic roll number but violates VTU standard
                anomalies.append(
                    f"USN '{identifier}' violates standard VTU CBCS format (Expected 10-char regex: {usn_regex})"
                )
                schema_matched = False
        else:
            # Check if USN exists anywhere in raw text
            found_usn = re.search(r"\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b", raw_text.upper())
            if not found_usn and len(raw_text) > 100:
                anomalies.append("No valid VTU USN (University Seat Number) detected on marks card")
                schema_matched = False

        # 2. Score / SGPA Range & Arithmetic Consistency
        if score_or_cgpa:
            try:
                # Extract float
                match = re.search(r"(\d+\.?\d*)", score_or_cgpa)
                if match:
                    val = float(match.group(1))
                    if val > 10.0 or val < 0.0:
                        anomalies.append(f"Stated SGPA/CGPA {val} is outside standard VTU scale (0.00 - 10.00)")
                        arithmetic_valid = False
            except Exception:
                pass

        # 3. Gemini Arithmetic Consistency Integration
        if gemini_arithmetic:
            if gemini_arithmetic.get("is_consistent") is False:
                details = gemini_arithmetic.get("details", "Marks calculation does not match stated grade points.")
                anomalies.append(f"Arithmetic Inconsistency: {details}")
                arithmetic_valid = False

        # 4. QR / Institutional Domain Whitelist
        if qr_url:
            allowed_domains = self.vtu_schema.get("official_domains", [])
            domain_match = any(d.lower() in qr_url.lower() for d in allowed_domains)
            if not domain_match and qr_url.startswith(("http://", "https://")):
                anomalies.append(f"Verification URL '{qr_url}' does not point to an accredited VTU domain ({', '.join(allowed_domains)})")
                schema_matched = False

        return schema_matched, arithmetic_valid, anomalies

    def _verify_online_course(
        self,
        identifier: str,
        issuer: str,
        score_or_cgpa: str,
        raw_text: str,
        qr_url: str,
    ) -> Tuple[bool, bool, List[str]]:
        """Cross-examine against Coursera / NPTEL / Unacademy schemas."""
        anomalies: List[str] = []
        schema_matched = True
        arithmetic_valid = True

        providers = self.course_schema.get("providers", [])
        combined_text = f"{issuer} {raw_text} {qr_url}".upper()

        matched_provider = None
        for prov in providers:
            if any(alias.upper() in combined_text for alias in prov.get("aliases", [])):
                matched_provider = prov
                break
            if any(dom.lower() in qr_url.lower() for dom in prov.get("official_domains", [])):
                matched_provider = prov
                break

        if matched_provider:
            prov_id = matched_provider["provider_id"]
            # Validate URL pattern if QR/URL is present
            if qr_url:
                patterns = matched_provider.get("verification_url_patterns", [])
                valid_url = any(re.search(pat, qr_url, re.IGNORECASE) for pat in patterns)
                if not valid_url and qr_url.startswith(("http://", "https://")):
                    anomalies.append(
                        f"URL '{qr_url}' does not conform to official {prov_id} verification URL format"
                    )
                    schema_matched = False

            # Validate Certificate ID pattern if identifier present
            cert_pat = matched_provider.get("certificate_id_pattern")
            if identifier and cert_pat:
                if not re.search(cert_pat, identifier):
                    anomalies.append(
                        f"Certificate ID '{identifier}' does not match standard {prov_id} ID pattern"
                    )
                    schema_matched = False

            # Validate Score / Award Criteria for NPTEL
            if prov_id == "NPTEL" and score_or_cgpa:
                try:
                    num_match = re.search(r"(\d+)", score_or_cgpa)
                    if num_match:
                        score_val = int(num_match.group(1))
                        if score_val < 0 or score_val > 100:
                            anomalies.append(f"NPTEL percentage {score_val}% is invalid (expected 0 - 100%)")
                            arithmetic_valid = False
                        if "ELITE + GOLD" in combined_text and score_val < 90:
                            anomalies.append(f"Contradiction: Certificate claims 'Elite + Gold' but score is {score_val}% (< 90%)")
                            arithmetic_valid = False
                        elif "ELITE + SILVER" in combined_text and (score_val < 75 or score_val >= 90):
                            anomalies.append(f"Contradiction: Certificate claims 'Elite + Silver' but score is {score_val}% (expected 75-89%)")
                            arithmetic_valid = False
                except Exception:
                    pass

        return schema_matched, arithmetic_valid, anomalies

    def _check_qr_payload_conflict(
        self,
        qr_url: str,
        student_name: str,
        identifier: str,
    ) -> Tuple[bool, str]:
        """Check if embedded query params or URL paths contradict front document text."""
        qr_lower = qr_url.lower()

        # Check for mismatched certificate identifier in URL path or query
        if identifier and len(identifier) >= 5:
            # If URL has an ID segment like /verify/ABCDEF12345 or /verify/specialization/ABCDEF12345
            url_match = re.search(
                r"(?:/verify/(?:specialization/)?|/certificate/|id=|q=)([A-Za-z0-9\-_]+)",
                qr_url,
                re.IGNORECASE,
            )
            url_id = ""
            if url_match:
                candidate = url_match.group(1).upper()
                if candidate not in {"SPECIALIZATION", "CERTIFICATE", "VERIFY", "INDEX"}:
                    url_id = candidate

            if not url_id:
                # Fallback to extracting the trailing alphanumeric token from URL
                tokens = [
                    t.upper()
                    for t in re.findall(r"[A-Za-z0-9]{8,24}", qr_url)
                    if t.upper() not in {"SPECIALIZATION", "CERTIFICATE", "VERIFY", "COURSERA", "HTTP", "HTTPS"}
                ]
                if tokens:
                    url_id = tokens[-1]

            if url_id:
                id_clean = identifier.upper().replace(" ", "").replace("-", "")
                if url_id != id_clean and id_clean not in url_id and url_id not in id_clean:
                    # Potential mismatch only if both are distinct high-entropy codes
                    if len(url_id) >= 6 and len(id_clean) >= 6:
                        return True, f"Embedded QR certificate ID '{url_id}' contradicts document identifier '{identifier}'"

        return False, ""


_verifier_instance: Optional[RAGSchemaVerifier] = None


def get_rag_verifier() -> RAGSchemaVerifier:
    """Singleton getter for RAG schema verifier."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = RAGSchemaVerifier()
    return _verifier_instance
