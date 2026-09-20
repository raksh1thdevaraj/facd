"""Multi-layer visual evidence renderer generating unified composite anomaly overlays."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

import cv2
import numpy as np
from PIL import Image

from app.schemas.explainability import UnifiedAnomalyBox


class UnifiedOverlayRenderer:
    """Renders composite visual evidence dossiers onto raw certificate canvases."""

    COLOR_MAP = {
        "CRITICAL": (0, 0, 213),  # Red in BGR
        "MAJOR": (0, 140, 255),  # Orange in BGR
        "WARNING": (0, 215, 255),  # Yellow in BGR
        "INFO": (0, 200, 0),  # Green in BGR
        "CLONE": (255, 255, 0),  # Cyan in BGR
        "TEXT": (0, 0, 220),  # Red in BGR
        "OCR": (0, 165, 255),  # Amber in BGR
    }

    def render(
        self,
        raw_image_path: Union[str, Path],
        output_path: Union[str, Path],
        anomalies: List[UnifiedAnomalyBox],
        heatmap_overlay_path: Optional[Union[str, Path]] = None,
        heatmap_array: Optional[np.ndarray] = None,
    ) -> Path:
        """Render multi-layer visual evidence composite and save to output_path."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        raw_bgr = cv2.imread(str(raw_image_path))
        if raw_bgr is None:
            with Image.open(raw_image_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                raw_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        h, w = raw_bgr.shape[:2]
        canvas = raw_bgr.copy()

        # =========================================================================
        # Layer 1: Semi-Transparent Heatmap
        # =========================================================================
        if heatmap_overlay_path and Path(heatmap_overlay_path).exists():
            heat_img = cv2.imread(str(heatmap_overlay_path))
            if heat_img is not None:
                heat_resized = cv2.resize(heat_img, (w, h))
                canvas = cv2.addWeighted(canvas, 0.75, heat_resized, 0.25, 0)
        elif heatmap_array is not None:
            heat_norm = np.clip(heatmap_array, 0.0, 1.0)
            heat_resized = cv2.resize(heat_norm, (w, h))
            heat_uint8 = np.uint8(255 * heat_resized)
            colored_cam = cv2.applyColorMap(heat_uint8, cv2.COLORMAP_JET)
            canvas = cv2.addWeighted(canvas, 0.75, colored_cam, 0.25, 0)

        # =========================================================================
        # Layer 2 & 3: Bounding Boxes with Pill Labels
        # =========================================================================
        for anom in anomalies:
            b = anom.box
            color = self.COLOR_MAP.get(anom.severity.value, (0, 0, 255))
            if anom.category in self.COLOR_MAP:
                color = self.COLOR_MAP[anom.category]

            # Draw outer rectangle
            cv2.rectangle(canvas, (b.x, b.y), (b.x + b.width, b.y + b.height), color, 3)

            # Draw label pill above box
            label_text = anom.label or anom.category
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1
            (tw, th), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

            pill_y1 = max(0, b.y - th - 8)
            pill_y2 = max(th + 8, b.y)
            pill_x2 = min(w, b.x + tw + 10)

            # Filled pill background
            cv2.rectangle(canvas, (b.x, pill_y1), (pill_x2, pill_y2), color, -1)
            # Text inside pill
            cv2.putText(
                canvas,
                label_text,
                (b.x + 5, pill_y2 - baseline - 2),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

        # =========================================================================
        # Layer 5: Dark Legend Banner at Canvas Bottom
        # =========================================================================
        banner_h = max(40, int(h * 0.05))
        overlay_banner = canvas.copy()
        cv2.rectangle(overlay_banner, (0, h - banner_h), (w, h), (20, 20, 20), -1)
        canvas = cv2.addWeighted(canvas, 0.2, overlay_banner, 0.8, 0)

        # Legend items
        legend_items = [
            ("Tampering Anomaly", (0, 0, 213)),
            ("Warning / OCR Flag", (0, 165, 255)),
            ("Cloned Patch", (255, 255, 0)),
            ("Authentic Marker", (0, 200, 0)),
        ]

        x_offset = 20
        y_center = h - int(banner_h / 2)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, min(0.6, w / 1600.0))

        for text, col in legend_items:
            cv2.circle(canvas, (x_offset + 8, y_center), 6, col, -1)
            cv2.putText(
                canvas,
                text,
                (x_offset + 22, y_center + 4),
                font,
                font_scale,
                (240, 240, 240),
                1,
                cv2.LINE_AA,
            )
            (tw, _), _ = cv2.getTextSize(text, font, font_scale, 1)
            x_offset += tw + 45

        cv2.imwrite(str(out_p), canvas)
        return out_p
