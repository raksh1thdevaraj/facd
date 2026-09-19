from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from app.schemas.text_consistency import AnomalousRegion, AnomalyType


class TextAnomalyVisualizer:
    """Renders color-coded semi-transparent overlays and callouts on certificate images
    to visually explain detected typographical and logical anomalies.
    """

    # BGR Color palette for high-contrast anomaly visualization
    COLOR_MAP = {
        AnomalyType.BASELINE_DRIFT: (255, 229, 0),  # Cyan
        AnomalyType.FONT_SIZE_MISMATCH: (0, 214, 255),  # Yellow
        AnomalyType.STROKE_WEIGHT_DISCREPANCY: (251, 64, 224),  # Magenta
        AnomalyType.SPACING_IRREGULARITY: (0, 109, 255),  # Orange
        AnomalyType.FORMAT_IRREGULARITY: (0, 165, 255),  # Amber
        AnomalyType.LOGICAL_CONTRADICTION: (0, 0, 213),  # Red
    }

    @classmethod
    def render_overlay(
        cls,
        image: Optional[np.ndarray],
        anomalies: List[AnomalousRegion],
        output_path: Path,
    ) -> Path:
        """Draw anomaly bounding boxes and descriptive tags onto the certificate image."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if image is None or image.size == 0:
            # Create neutral white canvas if image is not provided
            canvas = np.full((1200, 1600, 3), 255, dtype=np.uint8)
        else:
            canvas = image.copy()
            if len(canvas.shape) == 2:
                canvas = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

        h, w = canvas.shape[:2]
        overlay = canvas.copy()

        for anomaly in anomalies:
            color = cls.COLOR_MAP.get(anomaly.anomaly_type, (0, 0, 255))

            # Derive pixel coordinates
            if anomaly.pixel_bbox:
                px = max(0, min(w - 1, anomaly.pixel_bbox.x))
                py = max(0, min(h - 1, anomaly.pixel_bbox.y))
                pw = max(4, min(w - px, anomaly.pixel_bbox.width))
                ph = max(4, min(h - py, anomaly.pixel_bbox.height))
                pt1 = (px, py)
                pt2 = (px + pw, py + ph)
            else:
                x1 = int(anomaly.bbox.x1 * w)
                y1 = int(anomaly.bbox.y1 * h)
                x2 = int(anomaly.bbox.x2 * w)
                y2 = int(anomaly.bbox.y2 * h)
                pt1 = (max(0, x1), max(0, y1))
                pt2 = (min(w - 1, x2), min(h - 1, y2))

            # 1. Semi-transparent filled rectangle
            cv2.rectangle(overlay, pt1, pt2, color, -1)

            # 2. Solid border
            cv2.rectangle(canvas, pt1, pt2, color, 2)

            # 3. Label tag
            tag_text = f"{anomaly.anomaly_type.value}: {int(anomaly.severity * 100)}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            thickness = 1
            (tw, th), _ = cv2.getTextSize(tag_text, font, font_scale, thickness)

            tag_y1 = max(0, pt1[1] - th - 6)
            tag_y2 = pt1[1]
            tag_x2 = min(w, pt1[0] + tw + 8)

            cv2.rectangle(canvas, (pt1[0], tag_y1), (tag_x2, tag_y2), color, -1)
            cv2.putText(
                canvas,
                tag_text,
                (pt1[0] + 4, tag_y2 - 3),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )

        # Blend semi-transparent overlay (alpha = 0.30)
        cv2.addWeighted(overlay, 0.30, canvas, 0.70, 0, canvas)

        # Save to disk
        cv2.imwrite(str(output_path), canvas)
        return output_path
