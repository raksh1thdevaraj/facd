"""Course Certificate Information Extraction Engine (Phase 3).

Reuses existing OCR services while applying targeted linguistic heuristics,
pattern matching, and token position analysis to extract course, credential,
candidate, and signatory fields into a normalized JSON payload.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from app.modules.ocr.service import OCRService
from app.schemas.course_certificate import NormalizedCertificateData

logger = logging.getLogger(__name__)


class CourseCertificateExtractor:
    """Extracts normalized certificate data fields from image or OCR tokens."""

    def __init__(self, ocr_service: Optional[OCRService] = None) -> None:
        self.ocr_service = ocr_service or OCRService()

    def extract_from_image(
        self,
        image_input: Union[np.ndarray, Path, str],
        certificate_id_hint: Optional[str] = None,
    ) -> NormalizedCertificateData:
        """Run OCR on the image and extract normalized course certificate fields."""
        doc_id = certificate_id_hint or str(uuid.uuid4())
        ocr_output = self.ocr_service.process_document(
            document_id=doc_id,
            image_or_path=image_input,
        )
        # OCRResultDTO uses raw_extracted_text and average_ocr_confidence
        raw_text: str = getattr(ocr_output, "raw_extracted_text", "") or ""
        mean_conf: float = float(getattr(ocr_output, "average_ocr_confidence", 0.85))

        return self.extract_from_text(raw_text, ocr_confidence=mean_conf)

    def extract_from_text(
        self,
        text: str,
        tokens: Optional[list[Any]] = None,
        ocr_confidence: float = 0.85,
    ) -> NormalizedCertificateData:
        """Extract structured course fields from raw OCR text and token bounding boxes."""
        cleaned_text = re.sub(r"\s+", " ", text).strip()

        candidate_name = self._extract_candidate_name(cleaned_text, text)
        course_name = self._extract_course_name(cleaned_text, text)
        cert_id = self._extract_cert_id(cleaned_text)
        issuer = self._extract_issuer(cleaned_text)
        issue_date = self._extract_date(cleaned_text)
        grade = self._extract_grade(cleaned_text)
        duration = self._extract_duration(cleaned_text)
        instructor = self._extract_instructor(cleaned_text)
        url = self._extract_url(cleaned_text)

        return NormalizedCertificateData(
            candidate_name=candidate_name,
            course_name=course_name,
            certificate_id=cert_id,
            credential_id=cert_id,
            registration_id=cert_id,
            issuer=issuer,
            institution=issuer,
            organization=issuer,
            issue_date=issue_date,
            completion_date=issue_date,
            expiry_date=None,
            grade=grade,
            score=grade,
            duration=duration,
            instructor=instructor,
            signatory=instructor,
            verification_url=url,
            qr_content=None,
            ocr_confidence=round(float(ocr_confidence), 4),
        )

    def _extract_candidate_name(self, cleaned: str, raw: str) -> Optional[str]:
        """Extract candidate/student name following certification intro clauses."""
        patterns = [
            r"(?:this\s+is\s+to\s+certify\s+that|certifies\s+that|proudly\s+presented\s+to|awarded\s+to|conferred\s+upon)\s+([A-Z][a-zA-Z\s\.\-]{2,40})(?:\s+has|\s+for|\s+in|\n|$)",
            r"(?:student\s+name|candidate\s+name|recipient|name)\s*[:\-]?\s*([A-Z][a-zA-Z\s\.\-]{2,40})",
        ]
        for pat in patterns:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                # Exclude obvious false positive stop phrases
                if not any(
                    x in val.lower()
                    for x in ["successfully", "completed", "completion", "master", "course"]
                ):
                    return val

        # Fallback: scan lines for standalone capitalized names
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if re.search(
                r"(certify\s+that|presented\s+to|awarded\s+to)", line, re.IGNORECASE
            ) and i + 1 < len(lines):
                cand = lines[i + 1].strip()
                if 2 <= len(cand.split()) <= 4 and re.match(r"^[A-Z][a-zA-Z\s\.\-]+$", cand):
                    return cand

        return None

    def _extract_course_name(self, cleaned: str, raw: str) -> Optional[str]:
        """Extract course or certification title."""
        patterns = [
            r"(?:completed\s+(?:the\s+)?(?:course|program|specialization|curriculum|track|training|bootcamp)\s+(?:in|on|titled|of)?)\s*[:\"']?([A-Za-z0-9\s,\-\:]{3,60})[\"']?(?:\s+with|\s+on|\s+at|\s+dated|\.|\n|$)",
            r"(?:course\s+name|course\s+title|program)\s*[:\-]\s*([A-Za-z0-9\s,\-\:]{3,60})",
            r"(?:mastery\s+in|certificate\s+of\s+completion\s+in)\s+([A-Za-z0-9\s,\-\:]{3,60})",
        ]
        for pat in patterns:
            m = re.search(pat, cleaned, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if len(val) > 3 and not val.lower().startswith("with "):
                    return val.split(" with ")[0].strip()

        return None

    def _extract_cert_id(self, text: str) -> Optional[str]:
        """Extract unique certificate ID or credential alphanumeric code."""
        patterns = [
            r"(?:certificate\s+id|credential\s+id|verification\s+code|cert\s+id|registration\s+no|id)\s*[:#\-]?\s*([A-Za-z0-9\-_]{6,36})",
            r"\b([A-Z0-9]{3,5}-[A-Z0-9]{4,8}-[A-Z0-9]{4,8})\b",
            r"\b(UC-[A-Za-z0-9]{8,16})\b",  # Coursera / Udemy pattern
            r"\b(CRT-[A-Za-z0-9]{6,16})\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_issuer(self, text: str) -> Optional[str]:
        """Extract organization, institute or online platform issuer."""
        known_issuers = [
            "Coursera",
            "edX",
            "Udemy",
            "HarvardX",
            "Stanford Online",
            "MITx",
            "Google Cloud",
            "AWS Training",
            "Microsoft Learn",
            "DeepLearning.AI",
            "Credly",
            "Accredible",
            "Trailhead",
            "DataCamp",
            "Codecademy",
        ]
        for issuer in known_issuers:
            if re.search(rf"\b{re.escape(issuer)}\b", text, re.IGNORECASE):
                return issuer

        # Generic pattern
        m = re.search(
            r"(?:issued\s+by|organization|institution|offered\s+by)\s*[:\-]?\s*([A-Za-z0-9\s\.\-]{3,40})",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract completion or issue date in standardized format."""
        patterns = [
            r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
            r"\b(\d{4}[-/.]\d{2}[-/.]\d{2})\b",
            r"\b(\d{2}[-/.]\d{2}[-/.]\d{4})\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_grade(self, text: str) -> Optional[str]:
        """Extract score or grade if declared on certificate."""
        patterns = [
            r"(?:grade\s+achieved|grade|score)\s*[:\-]?\s*([A-Z][+]?|\d{1,3}(?:\.\d{1,2})?\s*%)",
            r"\b(with\s+honors|with\s+distinction|grade\s*:\s*[A-Z])\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract course duration if declared."""
        m = re.search(
            r"\b(\d{1,3}\s*(?:hours?|hrs?|weeks?|months?|credits?))\b", text, re.IGNORECASE
        )
        return m.group(1).strip() if m else None

    def _extract_instructor(self, text: str) -> Optional[str]:
        """Extract instructor or authorized signatory name."""
        patterns = [
            r"(?:instructor|professor|director|authorized\s+signatory|signed\s+by)\s*[:\-]?\s*([A-Z][a-zA-Z\s\.\-]{3,35})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract verification URL if printed explicitly in text."""
        m = re.search(
            r"https?://(?:www\.)?[a-zA-Z0-9\.\-_/]+\.(?:com|org|edu|io|net|gov)/[a-zA-Z0-9\.\-_/?=&%]+",
            text,
        )
        return m.group(0).strip() if m else None

    def extract_fields(
        self,
        raw_text: str,
        ocr_confidence: float = 0.85,
        qr_payload: Optional[str] = None,
        resolved_issuer: Optional[str] = None,
    ) -> Any:
        """Adapter method returning CourseExtractedFields for unified pipeline."""
        from app.schemas.course_certificate import CourseExtractedFields

        norm = self.extract_from_text(raw_text, ocr_confidence=ocr_confidence)
        issuer = norm.issuer or resolved_issuer
        return CourseExtractedFields(
            candidate_name=norm.candidate_name,
            course_name=norm.course_name,
            certificate_id=norm.certificate_id,
            issue_date=norm.issue_date,
            issuer=issuer,
            ocr_confidence=round(float(ocr_confidence), 4),
            grade=norm.grade,
            signatory=norm.instructor,
            raw_text=raw_text,
        )


# Alias
CourseExtractor = CourseCertificateExtractor
