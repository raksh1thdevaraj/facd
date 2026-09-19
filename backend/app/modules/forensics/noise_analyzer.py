import math
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.schemas.forensics import ForensicConfig
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class NoiseAnalyzer:
    """Analyzes high-frequency sensor noise residuals and local noise variance
    to expose spliced patches originating from different cameras or document scanners.
    """

    def __init__(self, config: Optional[ForensicConfig] = None):
        self.config = config or ForensicConfig()

    def analyze(
        self,
        image: np.ndarray,
    ) -> Tuple[np.ndarray, float, List[BoundingBox], List[PixelBoundingBox]]:
        """Extract high-pass noise residuals, compute block variances, and flag inconsistencies.

        Returns:
            Tuple of:
            - noise_variance_map: np.ndarray (normalized [0, 255] visualization map)
            - noise_inconsistency_score: float [0.0, 1.0] (1.0 = uniform noise, 0.0 = splice)
            - tampered_bboxes: List[BoundingBox]
            - tampered_pixel_bboxes: List[PixelBoundingBox]
        """
        if image is None or image.size == 0:
            return np.zeros((100, 100), dtype=np.uint8), 1.0, [], []

        img_h, img_w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        gray_f = gray.astype(np.float32)

        # Step 1: Extract noise residual via median filtering
        smooth = cv2.medianBlur(gray, 3).astype(np.float32)
        residual = gray_f - smooth

        bs = self.config.noise_block_size
        rows = img_h // bs
        cols = img_w // bs

        if rows == 0 or cols == 0:
            return np.zeros((img_h, img_w), dtype=np.uint8), 1.0, [], []

        block_variances = np.zeros((rows, cols), dtype=np.float32)

        for r in range(rows):
            for c in range(cols):
                patch = residual[r * bs : (r + 1) * bs, c * bs : (c + 1) * bs]
                block_variances[r, c] = float(np.var(patch))

        # Normalize block variance map into full resolution [0, 255] array
        var_min = float(np.min(block_variances))
        var_max = float(np.max(block_variances))
        denom = max(1e-5, var_max - var_min)
        norm_grid = ((block_variances - var_min) / denom * 255.0).astype(np.uint8)
        full_noise_map = cv2.resize(norm_grid, (img_w, img_h), interpolation=cv2.INTER_NEAREST)

        # Step 2: Anomaly detection using robust statistics (Median & MAD)
        flat_vars = block_variances.flatten()
        med_var = float(np.median(flat_vars))
        mad = float(np.median(np.abs(flat_vars - med_var)))
        robust_mad = max(0.5, mad)

        # Flag blocks with noise variance exceeding median by > 3.0 * MAD
        abs_dev = np.abs(block_variances - med_var)
        threshold = self.config.noise_mad_multiplier * robust_mad
        anomalous_blocks = abs_dev > threshold

        num_anomalous = int(np.sum(anomalous_blocks))
        total_blocks = rows * cols
        anomalous_ratio = num_anomalous / max(1, total_blocks)

        noise_score = math.exp(-anomalous_ratio * 8.0)
        noise_score = max(0.0, min(1.0, noise_score))

        # Step 3: Extract bounding boxes around clustered anomaly blocks
        norm_bboxes: List[BoundingBox] = []
        pixel_bboxes: List[PixelBoundingBox] = []

        mask = (anomalous_blocks.astype(np.uint8)) * 255
        if np.count_nonzero(mask) > 0:
            # Group contiguous blocks
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            dilated = cv2.dilate(mask, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) < 1.0:
                    continue
                bx, by, bw, bh = cv2.boundingRect(cnt)

                px = int(bx * bs)
                py = int(by * bs)
                pw = int(bw * bs)
                ph = int(bh * bs)

                pix_box = PixelBoundingBox(
                    x=px,
                    y=py,
                    width=max(4, min(img_w - px, pw)),
                    height=max(4, min(img_h - py, ph)),
                )
                norm_box = BoundingBox(
                    x1=max(0.0, min(1.0, px / img_w)),
                    y1=max(0.0, min(1.0, py / img_h)),
                    x2=max(0.0, min(1.0, (px + pw) / img_w)),
                    y2=max(0.0, min(1.0, (py + ph) / img_h)),
                )
                pixel_bboxes.append(pix_box)
                norm_bboxes.append(norm_box)

        return full_noise_map, round(noise_score, 4), norm_bboxes, pixel_bboxes
