import re
import unicodedata
from typing import List, Optional, Tuple

from app.schemas.pipeline import OCRToken
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class FormatChecker:
    """Detects text formatting irregularities, homoglyph character substitutions,
    erratic capitalization, and ungrammatical punctuation patterns.
    """

    # Common Cyrillic homoglyphs used in Latin document spoofing
    CYRILLIC_HOMOGLYPHS = set("аеорсухАВЕКМНОРСТХІі")

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(self, tokens: List[OCRToken]) -> Tuple[float, List[AnomalousRegion]]:
        """Inspect all tokens for homoglyphs, capitalization glitches, and punctuation flaws.

        Returns:
            Tuple of (format_consistency_score [0.0, 1.0], list of anomalous regions).
        """
        if not tokens:
            return 1.0, []

        anomalies: List[AnomalousRegion] = []

        for token in tokens:
            text = token.text.strip()
            if not text:
                continue

            # 1. Homoglyph / Mixed script check
            homoglyph_region = self._check_homoglyph_substitution(token, text)
            if homoglyph_region:
                anomalies.append(homoglyph_region)
                continue

            # 2. Erratic mid-word capitalization check
            caps_region = self._check_capitalization_anomaly(token, text)
            if caps_region:
                anomalies.append(caps_region)
                continue

            # 3. Punctuation artifacts
            punct_region = self._check_punctuation_artifacts(token, text)
            if punct_region:
                anomalies.append(punct_region)

        score = max(0.0, 1.0 - min(1.0, 0.15 * len(anomalies)))
        return round(score, 3), anomalies

    def _check_homoglyph_substitution(
        self, token: OCRToken, text: str
    ) -> Optional[AnomalousRegion]:
        """Check for Cyrillic or unexpected scripts inserted into Latin words."""
        has_latin = False
        has_cyrillic = False

        for char in text:
            if "LATIN" in unicodedata.name(char, ""):
                has_latin = True
            elif char in self.CYRILLIC_HOMOGLYPHS or "CYRILLIC" in unicodedata.name(char, ""):
                has_cyrillic = True

        if has_latin and has_cyrillic:
            return AnomalousRegion(
                anomaly_type=AnomalyType.FORMAT_IRREGULARITY,
                severity=0.95,
                description=(
                    f"Homoglyph / mixed script detected in word '{text}': Cyrillic characters "
                    f"embedded in Latin text"
                ),
                bbox=token.bbox,
                pixel_bbox=token.pixel_bbox,
                token_text=text,
            )
        return None

    def _check_capitalization_anomaly(
        self, token: OCRToken, text: str
    ) -> Optional[AnomalousRegion]:
        """Detect mid-word erratic casing such as 'cOMPUTER' or 'JoHn'."""
        if len(text) < 3:
            return None

        # Check for lowercase followed immediately by uppercase inside a word: [a-z][A-Z]
        # Ignore camelCase identifiers if they are prefixed with 'e' (like e-Certificate)
        if re.search(r"[a-z][A-Z]", text):
            # Exclude McName / MacDonald / O'Connor patterns
            if not (text.startswith("Mc") or text.startswith("Mac") or text.startswith("O'")):
                return AnomalousRegion(
                    anomaly_type=AnomalyType.FORMAT_IRREGULARITY,
                    severity=0.75,
                    description=(
                        f"Erratic mid-word capitalization in '{text}' indicative of OCR typo "
                        f"or manual character replacement"
                    ),
                    bbox=token.bbox,
                    pixel_bbox=token.pixel_bbox,
                    token_text=text,
                )
        return None

    def _check_punctuation_artifacts(self, token: OCRToken, text: str) -> Optional[AnomalousRegion]:
        """Detect orphaned punctuation artifacts or invalid character repetitions."""
        # Double periods not forming a standard ellipsis
        if ".." in text and "..." not in text:
            return AnomalousRegion(
                anomaly_type=AnomalyType.FORMAT_IRREGULARITY,
                severity=0.60,
                description=f"Punctuation artifact in token '{text}': consecutive double periods",
                bbox=token.bbox,
                pixel_bbox=token.pixel_bbox,
                token_text=text,
            )

        # Unbalanced bracket within a standalone token
        if (text.count("(") != text.count(")")) and len(text) > 4:
            # Only flag if both aren't split across neighboring tokens
            pass

        return None
