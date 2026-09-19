from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from app.schemas.forensics import CloneMatch


class ForensicHeatmapGenerator:
    """Synthesizes Error Level Analysis, Copy-Move clone regions, and Noise variance
    into a unified thermal forensic heatmap overlay.
    """

    @classmethod
    def generate_composite_heatmap(
        cls,
        raw_image: Optional[np.ndarray],
        ela_map: Optional[np.ndarray],
        clone_matches: List[CloneMatch],
        noise_map: Optional[np.ndarray],
        output_path: Path,
    ) -> Path:
        """Create high-contrast thermal anomaly map and save annotated PNG to disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if raw_image is None or raw_image.size == 0:
            canvas = np.full((1200, 1600, 3), 255, dtype=np.uint8)
        else:
            canvas = raw_image.copy()
            if len(canvas.shape) == 2:
                canvas = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

        img_h, img_w = canvas.shape[:2]

        # 1. Prepare ELA intensity layer
        if ela_map is not None and ela_map.size > 0:
            if len(ela_map.shape) == 3:
                gray_ela = cv2.cvtColor(ela_map, cv2.COLOR_RGB2GRAY)
            else:
                gray_ela = ela_map
            gray_ela_resized = cv2.resize(gray_ela, (img_w, img_h))
            ela_norm = gray_ela_resized.astype(np.float32) / 255.0
        else:
            ela_norm = np.zeros((img_h, img_w), dtype=np.float32)

        # 2. Prepare Noise variance layer
        if noise_map is not None and noise_map.size > 0:
            noise_resized = cv2.resize(noise_map, (img_w, img_h))
            noise_norm = noise_resized.astype(np.float32) / 255.0
        else:
            noise_norm = np.zeros((img_h, img_w), dtype=np.float32)

        # 3. Prepare Clone mask layer
        clone_mask = np.zeros((img_h, img_w), dtype=np.float32)
        for clone in clone_matches:
            sp = clone.source_pixel_bbox
            tp = clone.target_pixel_bbox
            cv2.rectangle(clone_mask, (sp.x, sp.y), (sp.x + sp.width, sp.y + sp.height), 1.0, -1)
            cv2.rectangle(clone_mask, (tp.x, tp.y), (tp.x + tp.width, tp.y + tp.height), 1.0, -1)

        # 4. Multi-detector weighted fusion
        combined = (0.40 * ela_norm) + (0.35 * clone_mask) + (0.25 * noise_norm)
        combined = np.clip(combined, 0.0, 1.0)

        # Smooth thermal transitions
        blurred = cv2.GaussianBlur(combined, (21, 21), 5.0)
        heatmap_gray = np.uint8(np.clip(blurred * 255.0, 0, 255))
        heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)

        # 5. Blend thermal map with original image (65% base + 35% heatmap)
        blended = cv2.addWeighted(canvas, 0.65, heatmap_color, 0.35, 0)

        # 6. Annotate detected copy-move pairs with cyan links and bounding boxes
        for clone in clone_matches:
            sp = clone.source_pixel_bbox
            tp = clone.target_pixel_bbox

            # Source bounding box (Green)
            cv2.rectangle(
                blended,
                (sp.x, sp.y),
                (sp.x + sp.width, sp.y + sp.height),
                (0, 255, 0),
                2,
            )
            # Cloned target bounding box (Red)
            cv2.rectangle(
                blended,
                (tp.x, tp.y),
                (tp.x + tp.width, tp.y + tp.height),
                (0, 0, 255),
                2,
            )

            # Center-to-center connecting vector (Cyan)
            c1 = (sp.x + sp.width // 2, sp.y + sp.height // 2)
            c2 = (tp.x + tp.width // 2, tp.y + tp.height // 2)
            cv2.line(blended, c1, c2, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(blended, c1, 4, (0, 255, 0), -1)
            cv2.circle(blended, c2, 4, (0, 0, 255), -1)

        cv2.imwrite(str(output_path), blended)
        return output_path
