from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from app.modules.ocr.field_extractors.base_extractor import ExtractedField
from app.schemas.pipeline import OCRToken


class OCRVisualizer:
    """Renders high-resolution annotated verification overlays with color-coded bounding boxes."""

    # Colors in BGR
    COLOR_CONFIDENT = (118, 230, 0)  # Vibrant Green (#00E676)
    COLOR_FLAGGED = (68, 23, 255)  # Bright Red (#FF1744)
    COLOR_TOKEN = (220, 200, 180)  # Light Cyan/Gray for background tokens

    @classmethod
    def render_overlay(
        cls,
        image: np.ndarray,
        extracted_fields: Dict[str, ExtractedField],
        tokens: Optional[List[OCRToken]] = None,
        output_path: Optional[Path] = None,
        draw_tokens: bool = False,
    ) -> np.ndarray:
        """Render color-coded bounding boxes and field badges over certificate image."""
        if len(image.shape) == 2:
            canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            canvas = image.copy()

        img_h, img_w = canvas.shape[:2]

        # Draw individual tokens if requested
        if draw_tokens and tokens:
            for tok in tokens:
                p = tok.pixel_bbox
                cv2.rectangle(
                    canvas,
                    (p.x, p.y),
                    (p.x + p.width, p.y + p.height),
                    cls.COLOR_TOKEN,
                    1,
                    cv2.LINE_AA,
                )

        # Draw extracted fields
        for name, field in extracted_fields.items():
            p = field.pixel_bounding_box
            is_flagged = field.is_flagged or field.confidence < 0.70
            box_color = cls.COLOR_FLAGGED if is_flagged else cls.COLOR_CONFIDENT

            x1, y1 = max(0, p.x), max(0, p.y)
            x2, y2 = min(img_w, p.x + p.width), min(img_h, p.y + p.height)

            # Draw outer rectangle
            cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, 2, cv2.LINE_AA)

            # Draw badge tag
            label_text = f"{name} ({int(field.confidence * 100)}%)"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

            badge_y1 = max(0, y1 - text_h - 6)
            badge_y2 = y1
            badge_x2 = min(img_w, x1 + text_w + 8)

            # Badge background
            cv2.rectangle(canvas, (x1, badge_y1), (badge_x2, badge_y2), box_color, -1)
            # Badge text (white for high contrast)
            cv2.putText(
                canvas,
                label_text,
                (x1 + 4, badge_y2 - 3),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), canvas)

        return canvas
