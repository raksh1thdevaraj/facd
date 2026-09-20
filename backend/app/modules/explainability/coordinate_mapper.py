"""Coordinate mapping and transformation between processed and original image spaces."""

from __future__ import annotations

from typing import Tuple

import numpy as np

from app.schemas.explainability import NormalizedBox
from app.schemas.primitives import PixelBoundingBox


class CoordinateMapper:
    """Transforms bounding boxes and spatial points from processed space to raw image resolution."""

    def __init__(
        self,
        orig_width: int,
        orig_height: int,
        proc_width: int = 512,
        proc_height: int = 512,
        rotation_degrees: float = 0.0,
    ) -> None:
        self.orig_width = max(1, orig_width)
        self.orig_height = max(1, orig_height)
        self.proc_width = max(1, proc_width)
        self.proc_height = max(1, proc_height)
        self.rotation_degrees = rotation_degrees

        self.scale_x = self.orig_width / float(self.proc_width)
        self.scale_y = self.orig_height / float(self.proc_height)

    def map_box(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> PixelBoundingBox:
        """Scale and clamp processed bounding box to raw original image dimensions."""
        raw_x = int(round(x * self.scale_x))
        raw_y = int(round(y * self.scale_y))
        raw_w = int(round(width * self.scale_x))
        raw_h = int(round(height * self.scale_y))

        # Clamp boundaries
        raw_x = max(0, min(raw_x, self.orig_width - 1))
        raw_y = max(0, min(raw_y, self.orig_height - 1))
        raw_w = max(1, min(raw_w, self.orig_width - raw_x))
        raw_h = max(1, min(raw_h, self.orig_height - raw_y))

        return PixelBoundingBox(x=raw_x, y=raw_y, width=raw_w, height=raw_h)

    def to_normalized_box(self, box: PixelBoundingBox) -> NormalizedBox:
        """Convert pixel bounding box on raw image to [0.0, 1.0] normalized coordinates."""
        nx = max(0.0, min(1.0, box.x / float(self.orig_width)))
        ny = max(0.0, min(1.0, box.y / float(self.orig_height)))
        nw = max(0.0, min(1.0 - nx, box.width / float(self.orig_width)))
        nh = max(0.0, min(1.0 - ny, box.height / float(self.orig_height)))
        return NormalizedBox(x=round(nx, 4), y=round(ny, 4), w=round(nw, 4), h=round(nh, 4))

    def map_normalized(
        self,
        nx: float,
        ny: float,
        nw: float,
        nh: float,
    ) -> Tuple[PixelBoundingBox, NormalizedBox]:
        """Convert normalized [0, 1] coordinates into pixel box and normalized box."""
        px = int(round(nx * self.orig_width))
        py = int(round(ny * self.orig_height))
        pw = int(round(nw * self.orig_width))
        ph = int(round(nh * self.orig_height))

        px = max(0, min(px, self.orig_width - 1))
        py = max(0, min(py, self.orig_height - 1))
        pw = max(1, min(pw, self.orig_width - px))
        ph = max(1, min(ph, self.orig_height - py))

        pbox = PixelBoundingBox(x=px, y=py, width=pw, height=ph)
        nbox = NormalizedBox(
            x=round(nx, 4),
            y=round(ny, 4),
            w=round(nw, 4),
            h=round(nh, 4),
        )
        return pbox, nbox

    def map_points(self, points: np.ndarray) -> np.ndarray:
        """Scale array of (N, 2) points from processed to raw resolution."""
        pts = np.asarray(points, dtype=np.float32).copy()
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError(f"Expected points shape (N, 2), got {pts.shape}")
        pts[:, 0] = np.clip(pts[:, 0] * self.scale_x, 0, self.orig_width - 1)
        pts[:, 1] = np.clip(pts[:, 1] * self.scale_y, 0, self.orig_height - 1)
        return np.round(pts).astype(np.int32)
