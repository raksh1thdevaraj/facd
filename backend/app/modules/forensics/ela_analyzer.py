import io
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance

from app.schemas.forensics import ForensicConfig
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class ELAAnalyzer:
    """Performs Error Level Analysis (ELA) to detect JPEG compression inconsistencies
    and localized digital image splicing.
    """

    def __init__(self, config: Optional[ForensicConfig] = None):
        self.config = config or ForensicConfig()

    def analyze(
        self,
        image_or_path: Union[np.ndarray, Path, str],
        quality: Optional[int] = None,
    ) -> Tuple[np.ndarray, float, List[BoundingBox], List[PixelBoundingBox]]:
        """Compute Error Level Analysis map, ELA authenticity score, and candidate tampered regions.

        Returns:
            Tuple of:
            - ela_image_rgb: np.ndarray (amplified ELA visualization image)
            - ela_score: float [0.0, 1.0] (1.0 = pristine/uniform, 0.0 = heavy compression anomaly)
            - tampered_bboxes: List[BoundingBox] (normalized coordinates)
            - tampered_pixel_bboxes: List[PixelBoundingBox]
        """
        q = quality or self.config.ela_quality
        pil_img = self._load_pil_image(image_or_path)
        img_w, img_h = pil_img.size

        # Save temporary recompressed JPEG in-memory
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=q)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")

        # Compute absolute difference
        diff = ImageChops.difference(pil_img, recompressed)

        # Dynamic amplification
        extrema = diff.getextrema()
        max_diff = max(ex[1] for ex in extrema) if extrema else 0
        scale = 255.0 / max_diff if max_diff > 0 else 1.0
        scale = min(scale, 25.0)  # Bound amplification

        enhanced = ImageEnhance.Brightness(diff).enhance(scale)
        ela_np = np.array(enhanced, dtype=np.uint8)

        # Quantify localized compression variance across grid blocks
        gray_ela = cv2.cvtColor(ela_np, cv2.COLOR_RGB2GRAY)
        bs = self.config.ela_block_size

        block_means: List[float] = []
        rows = img_h // bs
        cols = img_w // bs

        grid_matrix = np.zeros((rows, cols), dtype=np.float32)

        for r in range(rows):
            for c in range(cols):
                block = gray_ela[r * bs : (r + 1) * bs, c * bs : (c + 1) * bs]
                m = float(np.mean(block))
                block_means.append(m)
                grid_matrix[r, c] = m

        if not block_means:
            return ela_np, 1.0, [], []

        variance = float(np.var(block_means))
        ela_score = math.exp(-variance / self.config.ela_variance_threshold)
        ela_score = max(0.0, min(1.0, ela_score))

        # Detect outlier blocks exceeding global mean + 2.8 std
        global_mean = float(np.mean(block_means))
        global_std = float(np.std(block_means))
        threshold = global_mean + 2.8 * global_std

        anomaly_mask = np.uint8((grid_matrix > threshold) & (grid_matrix > 15.0)) * 255

        # Group contiguous anomaly blocks
        norm_bboxes: List[BoundingBox] = []
        pixel_bboxes: List[PixelBoundingBox] = []

        if np.count_nonzero(anomaly_mask) > 0:
            contours, _ = cv2.findContours(anomaly_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) < 1.0:
                    continue
                bx, by, bw, bh = cv2.boundingRect(cnt)

                # Scale back to full image pixel coordinates
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

        if pixel_bboxes:
            outlier_ratio = np.count_nonzero(anomaly_mask) / float(rows * cols)
            penalty = min(0.60, 0.15 * len(pixel_bboxes) + outlier_ratio * 4.0)
            ela_score = max(0.10, ela_score * (1.0 - penalty))

        return ela_np, round(ela_score, 4), norm_bboxes, pixel_bboxes

    def multi_quality_ela_curve(
        self,
        image_or_path: Union[np.ndarray, Path, str],
        qualities: Optional[List[int]] = None,
    ) -> Dict[str, Union[Dict[int, float], int]]:
        """Compute ELA differential error curve across multiple JPEG quality levels."""
        qs = qualities or self.config.ela_qualities
        pil_img = self._load_pil_image(image_or_path)

        curve: Dict[int, float] = {}
        for q in qs:
            buffer = io.BytesIO()
            pil_img.save(buffer, format="JPEG", quality=q)
            buffer.seek(0)
            recompressed = Image.open(buffer).convert("RGB")
            diff = ImageChops.difference(pil_img, recompressed)
            mean_diff = float(np.mean(np.array(diff)))
            curve[q] = round(mean_diff, 3)

        # Inflection point: quality level with lowest recompression delta
        estimated_quality = min(curve.keys(), key=lambda k: curve[k])

        return {
            "error_curve": curve,
            "estimated_original_quality": estimated_quality,
        }

    def _load_pil_image(self, image_or_path: Union[np.ndarray, Path, str]) -> Image.Image:
        """Helper to safely convert input image to PIL RGB Image."""
        if isinstance(image_or_path, (str, Path)):
            img_path = Path(image_or_path)
            if not img_path.exists():
                raise FileNotFoundError(f"Image not found: {img_path}")
            return Image.open(str(img_path)).convert("RGB")
        elif isinstance(image_or_path, np.ndarray):
            if len(image_or_path.shape) == 2:
                rgb = cv2.cvtColor(image_or_path, cv2.COLOR_GRAY2RGB)
            elif image_or_path.shape[2] == 4:
                rgb = cv2.cvtColor(image_or_path, cv2.COLOR_BGRA2RGB)
            else:
                rgb = cv2.cvtColor(image_or_path, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        else:
            raise TypeError(f"Unsupported image type: {type(image_or_path)}")
