# ruff: noqa: N999
"""
Google Gemini Vision Forensic Verification Service.

Provides multimodal forensic document analysis using the official Google Gen AI SDK
(`google-genai`), evaluating:
1. Extracted Entities (USN/Registration No, Candidate Name, CGPA/Score, Issuing Institution).
2. Forgery Indicators (Font mismatch, text baseline shifts, patch compression artifacts, splicing).
3. Arithmetic Consistency (Calculation of semester credits, grades, CGPA/SGPA for marks cards).
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import cv2
import numpy as np

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    genai: Any = None
    types: Any = None
    APIError: Any = Exception
    ClientError: Any = Exception
    ServerError: Any = Exception

from app.config import settings

logger = logging.getLogger(__name__)

# Fallback sequence of Gemini vision models in case of model deprecation or capacity spikes
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.0-flash-exp",
]

DEFAULT_INSTITUTIONAL_SCHEMA_RULES = """
AUTHORITATIVE INSTITUTIONAL REFERENCE SCHEMA & LOGICAL AUDIT:
1. VTU CBCS & NEP ENGINEERING MARKS CARD RULES (Visvesvaraya Technological University):
   - USN Pattern: Strictly 10-character alphanumeric: [1-4][A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{3}.
     * Region digit: 1=Bengaluru, 2=Belagavi, 3=Kalaburagi, 4=Mysuru.
     * 2-letter College Code: e.g. MS (MSRIT), RV (RVCE), BM (BMSCE), PE (PESIT), DS (DSCE), BI (BIT), SI (SIT), NI (NIE), GA (GAT).
     * 2-digit Admission Year: e.g. 19, 20, 21, 22, 23, 24.
     * 2-letter Branch Identifier: e.g. CS, IS, EC, EE, ME, CV, AI, CD.
     * 3-digit Candidate Roll Sequence: 001 to 999.
   - Letter Grade to Grade Point Mapping (VTU CBCS / Autonomous):
     * O (Outstanding): 10 grade points (Marks range 90-100)
     * A+ (Excellent): 9 grade points (Marks range 80-89)
     * A (Very Good): 8 grade points (Marks range 70-79)
     * B+ (Good): 7 grade points (Marks range 60-69)
     * B (Above Average): 6 grade points (Marks range 55-59)
     * C (Average): 5 grade points (Marks range 50-54)
     * P (Pass): 4 grade points (Marks range 40-49)
     * F (Fail): 0 grade points (Marks range 0-39)
   - Deterministic SGPA Formula:
     SGPA = sum(Credits_i * GradePoints_i) / sum(Credits_i)
     Tolerance: Delta = |Printed_SGPA - Calculated_SGPA| <= 0.01.
     Any Delta > 0.01 is definitive mathematical manipulation and MUST be flagged as FRAUDULENT.
   - Semester Total Credits: Typically 18.0 to 24.0 credits per regular semester.
   - Institutional Seals & Watermarks:
     * Visvesvaraya Technological University circular heraldic crest at top-center.
     * Official seal & signature of "Registrar (Evaluation)".
     * Embedded guilloche background pattern / micro-line border security.
   - Typographic & Digital Tampering Vectors:
     * Flag any font family substitution (e.g. Courier or Arial injected over standard tabular font).
     * Flag any vertical baseline displacement or digit misalignments.
     * Flag localized compression noise, rectangular pixel halos, or clone stamps around grades or CGPA.
"""

FORENSIC_PROMPT_TEMPLATE = """
You are an authoritative senior document forensics examiner specializing in the authenticity
assessment of academic credentials, university marks cards, and official certificates.

Analyze the attached certificate document image with rigorous forensic scrutiny.

Conduct an exhaustive forensic review across the following core dimensions:
1. EXTRACTED VISUAL ENTITIES:
   - Extract actual candidate / student name visible on document (return null if not legible).
   - Extract USN, Registration Number, or Certificate ID visible on document (return null if not legible).
   - Extract CGPA, SGPA, Percentage, or Final Grade visible on document.
   - Extract Issuing University, College, or Certificate Authority visible on document.
   - Extract Degree Program, Specialization, Course Title, or Branch.
   - Extract Issue Date or Completion Year visible on document.

2. FORGERY INDICATORS:
   - Font Mismatch: Detect mismatched font families, inconsistent weights, differing stroke thicknesses, or irregular kerning.
   - Text Baseline Shifts: Detect vertical displacement, staggered letters, tilted baselines, or floating characters in text fields (especially names, grades, and dates).
   - Patch Compression Artifacts: Detect localized JPEG blockiness, rectangular boundary compression halos, clone stamping traces, or blur patches surrounding altered text.
   - Splicing / Digital Overlay: Detect pasted text boxes, inconsistent background grain/noise, or mismatched paper texture.

3. ARITHMETIC CONSISTENCY & SCHEMA CROSS-EXAMINATION:
   - For marks cards and grade sheets, compute whether subject credits, grade points, and component scores mathematically align with the stated SGPA/CGPA or Total Marks using the institutional schema rules below.
   - Verify whether stated award or percentage matches institutional grading tiers.
   - Flag any mathematical contradiction, out-of-range percentage, or impossible grade point calculation.
   - Does the certificate format, ID pattern, or verification URL match official institutional standards?

{schema_rules_section}

Context hints:
- Expected Student Name (if provided for cross-check): "{expected_student_name}"
- Expected Registration No (if provided for cross-check): "{expected_reg_no}"
- Declared Certificate Type: "{certificate_type}"

You MUST respond strictly with a valid JSON object matching this schema without any markdown formatting:
{{
  "entities": {{
    "student_name": "<string or null>",
    "registration_no": "<string or null>",
    "cgpa_or_score": "<string or null>",
    "issuing_institution": "<string or null>",
    "degree_or_program": "<string or null>",
    "issue_date": "<string or null>"
  }},
  "forgery_indicators": {{
    "font_mismatch": <true or false>,
    "text_baseline_shift": <true or false>,
    "patch_compression_artifacts": <true or false>,
    "splicing_detected": <true or false>,
    "details": "<detailed forensic observations on typography, baselines, and pixel compression>"
  }},
  "arithmetic_consistency": {{
    "is_consistent": <true or false>,
    "details": "<mathematical evaluation of scores and grade points>"
  }},
  "schema_validation": {{
    "schema_matched": <true or false>,
    "discrepancies": ["<anomaly details or empty>"]
  }},
  "is_authentic": <true or false>,
  "confidence_score": <float between 0.00 and 1.00>,
  "verdict": "<'VERIFIED' | 'SUSPICIOUS' | 'REJECTED'>",
  "forensic_summary": "<succinct analytical summary of findings>"
}}
"""


class GeminiVerifier:
    """Multimodal document forensic verifier powered by Google Gemini Vision."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_ms: int = 30000,
    ) -> None:
        self._explicitly_disabled = False
        if api_key is not None:
            self.api_key = api_key.strip()
            if not self.api_key:
                self._explicitly_disabled = True
        else:
            self.api_key = (
                getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY", "")
            ).strip()

        if model is not None:
            self.primary_model = model.strip()
        else:
            self.primary_model = (
                getattr(settings, "GEMINI_MODEL", None)
                or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            ).strip()

        self.timeout_ms = timeout_ms
        self._client: Optional[Any] = None

        if (
            GOOGLE_GENAI_AVAILABLE
            and genai is not None
            and types is not None
            and self.api_key
        ):
            try:
                self._client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=self.timeout_ms),
                )
                logger.info("GeminiVerifier initialized with model '%s'", self.primary_model)
            except Exception as init_err:
                logger.warning("Failed to initialize Google Gen AI Client: %s", init_err)
                self._client = None
        else:
            if not GOOGLE_GENAI_AVAILABLE:
                logger.warning("google-genai SDK is not installed in the current environment.")
            elif not self.api_key:
                logger.info(
                    "GEMINI_API_KEY is not set. Gemini Vision verification will degrade gracefully."
                )

    @property
    def is_available(self) -> bool:
        """Returns True if the SDK is available and an API key is configured."""
        return bool(GOOGLE_GENAI_AVAILABLE and self.api_key and self._client is not None)

    def _prepare_image_bytes(
        self, image_input: Union[bytes, str, Path, np.ndarray]
    ) -> tuple[bytes, str]:
        """Convert input to raw bytes and identify appropriate MIME type."""
        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.is_file():
                raise FileNotFoundError(f"Certificate image file not found: {path}")
            mime_type, _ = mimetypes.guess_type(str(path))
            mime_type = mime_type or "image/png"
            with open(path, "rb") as f:
                data = f.read()
            return data, mime_type

        if isinstance(image_input, np.ndarray):
            # Encode OpenCV BGR ndarray to PNG format in-memory
            success, buffer = cv2.imencode(".png", image_input)
            if not success:
                raise ValueError("Failed to encode image array to PNG bytes.")
            return buffer.tobytes(), "image/png"

        if isinstance(image_input, bytes):
            # Detect mime type from magic bytes
            if image_input.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif image_input.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif image_input.startswith(b"%PDF"):
                mime = "application/pdf"
            elif image_input.startswith(b"RIFF") and b"WEBP" in image_input[:16]:
                mime = "image/webp"
            else:
                mime = "image/png"
            return image_input, mime

        raise TypeError(f"Unsupported image_input type: {type(image_input)}")

    def verify(
        self,
        image_input: Union[bytes, str, Path, np.ndarray],
        certificate_type: str = "marks_card",
        expected_student_name: Optional[str] = None,
        expected_reg_no: Optional[str] = None,
        schema_rules_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute deep forensic document analysis on certificate image.

        Args:
            image_input: Image bytes, file path, Path object, or OpenCV BGR numpy array.
            certificate_type: Type of document ("marks_card" or "course_certificate").
            expected_student_name: Optional candidate name for cross-validation.
            expected_reg_no: Optional student/registration ID for cross-validation.
            schema_rules_context: Optional institutional schema rules context for RAG validation.

        Returns:
            Structured dictionary with entities, forgery indicators, arithmetic consistency,
            authenticity verdict, and confidence score.
        """
        # Dynamic client recovery if key exists in env/settings but client wasn't initialized
        if (
            self._client is None
            and not getattr(self, "_explicitly_disabled", False)
            and GOOGLE_GENAI_AVAILABLE
            and genai is not None
            and types is not None
        ):
            active_key = (
                self.api_key
                or os.getenv("GEMINI_API_KEY", "")
                or getattr(settings, "GEMINI_API_KEY", "")
                or ""
            ).strip()
            if active_key:
                self.api_key = active_key
                try:
                    self._client = genai.Client(
                        api_key=self.api_key,
                        http_options=types.HttpOptions(timeout=self.timeout_ms),
                    )
                    logger.info("Dynamically initialized Gemini Client with model '%s'", self.primary_model)
                except Exception as dyn_err:
                    logger.warning("Dynamic Gemini Client init failed: %s", dyn_err)

        # Guard: Check availability
        if not self.is_available or types is None:
            return {
                "success": False,
                "status": "SKIPPED",
                "is_authentic": None,
                "confidence_score": 0.0,
                "verdict": "UNVERIFIED",
                "entities": {
                    "student_name": None,
                    "registration_no": None,
                    "cgpa_or_score": None,
                    "issuing_institution": None,
                    "degree_or_program": None,
                    "issue_date": None,
                },
                "forgery_indicators": {
                    "font_mismatch": False,
                    "text_baseline_shift": False,
                    "patch_compression_artifacts": False,
                    "splicing_detected": False,
                    "details": "Multimodal Vision check skipped (API key not configured or client uninitialized).",
                },
                "arithmetic_consistency": {
                    "is_consistent": True,
                    "details": "Arithmetic consistency check skipped.",
                },
                "schema_validation": {
                    "schema_matched": True,
                    "discrepancies": [],
                },
                "forensic_summary": "Multimodal Vision API is not configured. Local forensic pipeline used.",
                "model_used": None,
                "error": "GEMINI_API_KEY_NOT_CONFIGURED"
                if not self.api_key
                else "CLIENT_INIT_FAILED",
            }

        try:
            img_bytes, mime_type = self._prepare_image_bytes(image_input)
        except Exception as prep_err:
            logger.error("Failed to prepare image for Gemini verifier: %s", prep_err)
            return {
                "success": False,
                "status": "ERROR",
                "is_authentic": None,
                "confidence_score": 0.0,
                "verdict": "ERROR",
                "error": f"IMAGE_PREPARATION_ERROR: {str(prep_err)}",
                "forensic_summary": "Failed to read or encode uploaded certificate image.",
            }

        schema_rules = schema_rules_context or DEFAULT_INSTITUTIONAL_SCHEMA_RULES
        prompt = FORENSIC_PROMPT_TEMPLATE.format(
            expected_student_name=expected_student_name or "N/A",
            expected_reg_no=expected_reg_no or "N/A",
            certificate_type=certificate_type,
            schema_rules_section=schema_rules,
        )

        image_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,  # Low temperature for deterministic forensic analysis
        )

        # Build candidate model priority queue starting with configured model
        models_to_try: List[str] = [self.primary_model]
        for m in CANDIDATE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        last_error: Optional[Exception] = None
        response_text: Optional[str] = None
        model_used: Optional[str] = None

        for model_name in models_to_try:
            try:
                logger.info("Attempting Gemini Vision inspection with model '%s'...", model_name)
                response = self._client.models.generate_content(  # type: ignore
                    model=model_name,
                    contents=[image_part, prompt],
                    config=gen_config,
                )
                if response and response.text:
                    response_text = response.text
                    model_used = model_name
                    logger.info("Gemini Vision verification succeeded with model '%s'", model_name)
                    break
            except Exception as api_err:
                last_error = api_err
                err_msg = str(api_err)
                logger.warning(
                    "Gemini Vision call failed for model '%s': %s",
                    model_name,
                    err_msg[:120],
                )
                # If 404 (model deprecated / not found), 429 (quota rate-limit), or 503 (demand spike), proceed to next candidate
                if (
                    "404" in err_msg
                    or "503" in err_msg
                    or "429" in err_msg
                    or "RESOURCE_EXHAUSTED" in err_msg
                    or "NOT_FOUND" in err_msg
                    or "UNAVAILABLE" in err_msg
                ):
                    continue
                # For auth or permissions issues, break early
                if "401" in err_msg or "403" in err_msg or "PERMISSION_DENIED" in err_msg:
                    break

        if not response_text:
            logger.error("Gemini Vision calls exhausted with error: %s", last_error)
            return {
                "success": False,
                "status": "DEGRADED",
                "is_authentic": None,
                "confidence_score": 0.0,
                "verdict": "UNVERIFIED",
                "entities": {
                    "student_name": None,
                    "registration_no": None,
                    "cgpa_or_score": None,
                    "issuing_institution": None,
                    "degree_or_program": None,
                    "issue_date": None,
                },
                "forgery_indicators": {
                    "font_mismatch": False,
                    "text_baseline_shift": False,
                    "patch_compression_artifacts": False,
                    "splicing_detected": False,
                    "details": f"Multimodal Vision service temporarily unavailable: {str(last_error)}",
                },
                "arithmetic_consistency": {
                    "is_consistent": True,
                    "details": "Arithmetic check unavailable during service degradation.",
                },
                "schema_validation": {
                    "schema_matched": True,
                    "discrepancies": [],
                },
                "forensic_summary": (
                    "Multimodal Vision service experienced high demand or temporary network outage. "
                    "Verification gracefully fell back to local deterministic pipeline."
                ),
                "model_used": None,
                "error": str(last_error),
            }

        # Parse structured JSON output
        try:
            # Clean possible accidental wrappers
            cleaned_json = response_text.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()

            parsed: Dict[str, Any] = json.loads(cleaned_json)
        except Exception as json_err:
            logger.error(
                "Failed to parse Gemini JSON output: %s. Raw: %s", json_err, response_text[:300]
            )
            return {
                "success": False,
                "status": "PARSE_ERROR",
                "raw_response": response_text[:500],
                "error": f"JSON_PARSE_ERROR: {str(json_err)}",
                "forensic_summary": "Gemini response could not be parsed into expected JSON schema.",
            }

        # Normalize parsed output into consistent contract
        entities = parsed.get("entities", {})
        forgery_indicators = parsed.get("forgery_indicators", {})
        arithmetic = parsed.get("arithmetic_consistency", {})
        schema_val = parsed.get("schema_validation", {})

        is_authentic = bool(parsed.get("is_authentic", False))
        confidence_val = float(parsed.get("confidence_score", 0.85 if is_authentic else 0.20))
        verdict = str(parsed.get("verdict", "VERIFIED" if is_authentic else "SUSPICIOUS")).upper()

        return {
            "success": True,
            "status": "COMPLETED",
            "model_used": model_used,
            "is_authentic": is_authentic,
            "confidence_score": round(confidence_val, 4),
            "verdict": verdict,
            "entities": {
                "student_name": entities.get("student_name"),
                "registration_no": entities.get("registration_no"),
                "cgpa_or_score": entities.get("cgpa_or_score"),
                "issuing_institution": entities.get("issuing_institution"),
                "degree_or_program": entities.get("degree_or_program"),
                "issue_date": entities.get("issue_date"),
            },
            "forgery_indicators": {
                "font_mismatch": bool(forgery_indicators.get("font_mismatch", False)),
                "text_baseline_shift": bool(forgery_indicators.get("text_baseline_shift", False)),
                "patch_compression_artifacts": bool(
                    forgery_indicators.get("patch_compression_artifacts", False)
                ),
                "splicing_detected": bool(forgery_indicators.get("splicing_detected", False)),
                "details": forgery_indicators.get(
                    "details", "No visible typographic or compression irregularities detected."
                ),
            },
            "arithmetic_consistency": {
                "is_consistent": bool(arithmetic.get("is_consistent", True)),
                "details": arithmetic.get("details", "Marks card calculations are consistent."),
            },
            "schema_validation": {
                "schema_matched": bool(schema_val.get("schema_matched", True)),
                "discrepancies": schema_val.get("discrepancies", []),
            },
            "forensic_summary": parsed.get(
                "forensic_summary", "Document analyzed with Multimodal Vision Forensic Engine."
            ),
        }


# Singleton instance
_gemini_verifier: Optional[GeminiVerifier] = None


def get_gemini_verifier() -> GeminiVerifier:
    """Retrieve or initialize the global GeminiVerifier instance."""
    global _gemini_verifier
    if _gemini_verifier is None:
        _gemini_verifier = GeminiVerifier()
    return _gemini_verifier


def verify_certificate_with_gemini(
    image_input: Union[bytes, str, Path, np.ndarray],
    certificate_type: str = "marks_card",
    expected_student_name: Optional[str] = None,
    expected_reg_no: Optional[str] = None,
    schema_rules_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience helper function to verify a certificate with Gemini Vision."""
    verifier = get_gemini_verifier()
    return verifier.verify(
        image_input=image_input,
        certificate_type=certificate_type,
        expected_student_name=expected_student_name,
        expected_reg_no=expected_reg_no,
        schema_rules_context=schema_rules_context,
    )
