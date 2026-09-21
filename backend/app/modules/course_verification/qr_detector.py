"""Robust Multi-Pass QR Code Detection & Decoding Engine (Phase 4).

Features:
1. Multi-pass OpenCV QRCodeDetector with contrast enhancement and morphological filtering.
2. Multi-scale pyramid search for small embedded QRs on high-resolution diplomas.
3. Orientation compensation (handling rotated QRs at +/-15, +/-90, 180 degrees).
4. URL extraction and validation from decoded payload.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from app.schemas.course_certificate import QRCodeData

logger = logging.getLogger(__name__)


class QRCodeDetectorService:
    """Robust multi-pass QR detector supporting faint, rotated, and noisy certificate scans."""

    def __init__(self) -> None:
        self.detector = cv2.QRCodeDetector()

    def detect_and_decode(
        self, image_input: Union[np.ndarray, Path, str]
    ) -> QRCodeData:
        """Execute multi-pass QR detection and decoding across certificate image."""
        img = self._load_image(image_input)
        if img is None:
            return QRCodeData(error_message="Unable to load certificate image for QR detection")

        # Pass 1: Direct detection on grayscale
        res = self._detect_single_image(img)
        if res.qr_decoded:
            return res

        # Pass 2: Contrast Stretching & CLAHE (for faint / low-contrast QRs)
        clahe_img = self._apply_clahe(img)
        res = self._detect_single_image(clahe_img)
        if res.qr_decoded:
            return res

        # Pass 3: Adaptive Thresholding & Morphology
        thresh_img = self._apply_adaptive_threshold(img)
        res = self._detect_single_image(thresh_img)
        if res.qr_decoded:
            return res

        # Pass 4: Multi-Scale Pyramid (for high-resolution documents where QR is tiny)
        h, w = img.shape[:2]
        if max(h, w) > 1500:
            scale_factor = 1200.0 / max(h, w)
            resized = cv2.resize(
                img, (int(w * scale_factor), int(h * scale_factor)), interpolation=cv2.INTER_AREA
            )
            res = self._detect_single_image(resized)
            if res.qr_decoded:
                # Scale bounding box back to original coordinates
                if res.bounding_box:
                    res.bounding_box = [
                        int(v / scale_factor) for v in res.bounding_box
                    ]
                return res

        # Pass 5: Orientation Deskewing (+/- 15 deg, 90 deg, 180 deg, 270 deg)
        for angle in [90, 180, 270, 15, -15]:
            rotated = self._rotate_image(img, angle)
            res = self._detect_single_image(rotated)
            if res.qr_decoded:
                return res

        # Pass 6: Fallback to pyzbar if available in environment
        try:
            import importlib

            pyzbar_mod = importlib.import_module("pyzbar.pyzbar")
            pyzbar_decode = pyzbar_mod.decode
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            barcodes = pyzbar_decode(gray)
            for barcode in barcodes:
                if barcode.type == "QRCODE":
                    raw_text = barcode.data.decode("utf-8", errors="ignore")
                    rect = barcode.rect
                    url = self._extract_url_from_content(raw_text)
                    return QRCodeData(
                        qr_detected=True,
                        qr_decoded=True,
                        qr_content=raw_text,
                        payload=raw_text,
                        qr_url=url,
                        bounding_box=[rect.left, rect.top, rect.width, rect.height],
                        confidence=0.98,
                    )
        except (ImportError, Exception):
            pass

        # If detected but un-decodable
        if res.qr_detected:
            return QRCodeData(
                qr_detected=True,
                qr_decoded=False,
                confidence=0.50,
                error_message="QR pattern detected on certificate but payload could not be decoded",
            )

        return QRCodeData(
            qr_detected=False,
            qr_decoded=False,
            confidence=0.0,
            error_message="No QR code found on certificate",
        )

    def _detect_single_image(self, img: np.ndarray) -> QRCodeData:
        """Run OpenCV QRCodeDetector on a single image variant."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        # detectAndDecodeMulti or detectAndDecode
        decoded_info, points, _ = self.detector.detectAndDecode(gray)

        if points is not None and len(points) > 0:
            pts = points[0]
            x_coords = [p[0] for p in pts]
            y_coords = [p[1] for p in pts]
            xmin, xmax = int(min(x_coords)), int(max(x_coords))
            ymin, ymax = int(min(y_coords)), int(max(y_coords))
            bbox = [xmin, ymin, max(1, xmax - xmin), max(1, ymax - ymin)]

            if decoded_info and len(decoded_info.strip()) > 0:
                raw_text = decoded_info.strip()
                url = self._extract_url_from_content(raw_text)
                return QRCodeData(
                    qr_detected=True,
                    qr_decoded=True,
                    qr_content=raw_text,
                    payload=raw_text,
                    qr_url=url,
                    bounding_box=bbox,
                    confidence=0.95,
                )
            else:
                return QRCodeData(
                    qr_detected=True,
                    qr_decoded=False,
                    bounding_box=bbox,
                    confidence=0.40,
                )

        return QRCodeData(qr_detected=False, qr_decoded=False)

    def _extract_url_from_content(self, text: str) -> Optional[str]:
        """Extract valid HTTPS or HTTP URL from decoded QR code string."""
        m = re.search(
            r"https?://[a-zA-Z0-9\.\-_/]+(?:\.[a-zA-Z]{2,})[a-zA-Z0-9\.\-_/?=&%#]*",
            text,
        )
        return m.group(0).strip() if m else None

    def _load_image(self, input_data: Union[np.ndarray, Path, str]) -> Optional[np.ndarray]:
        """Load image into RGB numpy array."""
        if isinstance(input_data, np.ndarray):
            return input_data.copy()
        path = Path(input_data)
        if not path.exists():
            logger.error("QR detector input file does not exist: %s", path)
            return None
        img = cv2.imread(str(path))
        return img

    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _apply_adaptive_threshold(self, img: np.ndarray) -> np.ndarray:
        """Binarize faint QR patterns using Gaussian adaptive threshold."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
        )

    def _rotate_image(self, img: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image around its center."""
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
        )


# Alias
CourseQRDetector = QRCodeDetectorService
