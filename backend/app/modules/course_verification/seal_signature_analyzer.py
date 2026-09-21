"""Signature and Institutional Seal Presence & Integrity Analyzer (Phase 8).

Analyzes the lower signatory and authentication zones of course certificates to evaluate:
1. Handwritten signature presence, stroke density, and continuity.
2. Institutional seal or crest geometry (circular contours, color saturation).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from app.schemas.course_certificate import SealSignatureResult

logger = logging.getLogger(__name__)


class SealSignatureAnalyzer:
    """Evaluates signature presence and institutional seal validity."""

    def analyze(self, image_input: Union[np.ndarray, Path, str]) -> SealSignatureResult:
        """Scan certificate image for signature strokes and circular seal crests."""
        img = self._load_image(image_input)
        if img is None:
            return SealSignatureResult(details=["Unable to load image for signature/seal analysis."])

        h, w = img.shape[:2]
        details: list[str] = []

        # Analyze lower 35% of certificate (typical signatory zone)
        lower_zone = img[int(h * 0.65) :, :]

        # 1. Signature Stroke Analysis
        sig_detected, sig_score = self._analyze_signature_strokes(lower_zone)
        if sig_detected:
            details.append(
                f"Handwritten or digital signature detected with stroke confidence {int(sig_score * 100)}%."
            )
        else:
            details.append("No distinct signature strokes detected in signatory zone.")

        # 2. Institutional Seal / Emblem Analysis
        seal_detected, seal_score = self._analyze_seal_crest(img)
        if seal_detected:
            details.append(
                f"Institutional seal / emblem detected with structural confidence {int(seal_score * 100)}%."
            )
        else:
            details.append("No circular or embossed institutional seal detected (common in online course badges).")

        return SealSignatureResult(
            signature_detected=sig_detected,
            signature_score=round(sig_score, 4),
            seal_detected=seal_detected,
            seal_score=round(seal_score, 4),
            details=details,
        )

    def _analyze_signature_strokes(self, roi: np.ndarray) -> tuple[bool, float]:
        """Detect dynamic handwritten stroke variations and connected components."""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        # Inverse binary threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Morphological gradient to isolate edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(thresh, cv2.MORPH_GRADIENT, kernel)

        # Connected component analysis
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh)

        signature_candidates = 0
        total_pixels = 0

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            w_box = stats[i, cv2.CC_STAT_WIDTH]
            h_box = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = w_box / max(1, h_box)

            # Signatures typically have elongated horizontal cursive aspect ratios
            if 150 < area < 15000 and 1.8 < aspect < 8.0:
                signature_candidates += 1
                total_pixels += area

        if signature_candidates >= 1 and total_pixels > 300:
            score = min(1.0, 0.65 + 0.10 * signature_candidates)
            return True, float(score)

        return False, 0.20

    def _analyze_seal_crest(self, img: np.ndarray) -> tuple[bool, float]:
        """Detect circular crests using Hough Circle transform and color concentration."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        blurred = cv2.medianBlur(gray, 5)

        # Detect circular contours
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=100,
            param1=50,
            param2=40,
            minRadius=25,
            maxRadius=150,
        )

        if circles is not None and len(circles[0]) > 0:
            return True, 0.85

        # Check saturated color contours (e.g. gold, dark blue, or red seals)
        if len(img.shape) == 3:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # High saturation mask
            sat_mask = cv2.inRange(hsv, (0, 70, 50), (180, 255, 255))
            contours, _ = cv2.findContours(sat_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 1000 < area < 40000:
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
                    # High circularity
                    if len(approx) > 6:
                        return True, 0.75

        return False, 0.15

    def _load_image(self, input_data: Union[np.ndarray, Path, str]) -> Optional[np.ndarray]:
        if isinstance(input_data, np.ndarray):
            return input_data.copy()
        path = Path(input_data)
        if not path.exists():
            return None
        return cv2.imread(str(path))


# Alias
CourseSealSignatureAnalyzer = SealSignatureAnalyzer
