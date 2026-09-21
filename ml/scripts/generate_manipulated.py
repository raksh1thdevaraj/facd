"""Synthetic Certificate Tampering Engine.

Implements 5 core forensic tampering transformations:
1. Text Inpainting & Replacement (with matched and font-mismatched styling)
2. Copy-Move / Digit Duplication with edge smoothing
3. Splicing with Poisson & Alpha Blending (seals/signatures)
4. Local Re-compression Quality Mismatch (JPEG ELA artifacts)
5. Perspective Skew & Scanner Noise Perturbations
"""

from __future__ import annotations

import io
import random
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def inpaint_and_replace_text(
    img: np.ndarray,
    target_box: dict[str, int],
    new_text: str,
    font_mismatched: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Inpaint a target text region and render replacement text over the clean background."""
    x = target_box["x"]
    y = target_box["y"]
    w = target_box["width"]
    h = target_box["height"]

    img_h, img_w = img.shape[:2]
    # Bound check
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(10, min(w, img_w - x))
    h = max(10, min(h, img_h - y))

    # 1. Create Inpainting mask for target bounding box
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    mask[y : y + h, x : x + w] = 255

    # 2. Inpaint using Telea / Navier-Stokes algorithm
    inpainted = cv2.inpaint(img, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # 3. Render replacement text
    pil_img = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.load_default()

    # Font mismatch / baseline shift simulation
    draw_x = x + 4
    draw_y = y + (4 if not font_mismatched else 7)
    text_color = (25, 25, 25) if not font_mismatched else (45, 45, 50)

    draw.text((draw_x, draw_y), new_text, fill=text_color, font=font)

    result_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    tamper_info = {
        "technique": "INPAINT_AND_REPLACE",
        "new_value": new_text,
        "font_mismatched": font_mismatched,
        "bbox_pixel": {"x": x, "y": y, "width": w, "height": h},
        "bbox_normalized": {
            "x1": round(x / img_w, 4),
            "y1": round(y / img_h, 4),
            "x2": round((x + w) / img_w, 4),
            "y2": round((y + h) / img_h, 4),
        },
    }
    return result_bgr, tamper_info


def copy_move_tampering(
    img: np.ndarray,
    source_box: dict[str, int],
    target_x: int,
    target_y: int,
    smooth_edge: bool = True,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Copy a source image patch and duplicate it over a target position."""
    img_h, img_w = img.shape[:2]
    sx, sy, sw, sh = (
        source_box["x"],
        source_box["y"],
        source_box["width"],
        source_box["height"],
    )

    # Bound check
    sx = max(0, min(sx, img_w - 1))
    sy = max(0, min(sy, img_h - 1))
    sw = max(5, min(sw, img_w - sx))
    sh = max(5, min(sh, img_h - sy))

    tx = max(0, min(target_x, img_w - sw))
    ty = max(0, min(target_y, img_h - sh))

    output = img.copy()
    patch = img[sy : sy + sh, sx : sx + sw].copy()

    if smooth_edge:
        # Subtle feathering along patch border
        patch = cv2.GaussianBlur(patch, (3, 3), 0.5)

    output[ty : ty + sh, tx : tx + sw] = patch

    tamper_info = {
        "technique": "COPY_MOVE",
        "source_bbox_pixel": {"x": sx, "y": sy, "width": sw, "height": sh},
        "bbox_pixel": {"x": tx, "y": ty, "width": sw, "height": sh},
        "bbox_normalized": {
            "x1": round(tx / img_w, 4),
            "y1": round(ty / img_h, 4),
            "x2": round((tx + sw) / img_w, 4),
            "y2": round((ty + sh) / img_h, 4),
        },
    }
    return output, tamper_info


def splice_seal_or_signature(
    img: np.ndarray,
    splice_asset_path: Path,
    target_pos: tuple[int, int],
    target_size: tuple[int, int],
    use_poisson: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Splice an external seal or signature with alpha or Poisson blending."""
    img_h, img_w = img.shape[:2]
    tx, ty = target_pos
    tw, th = target_size

    tx = max(0, min(tx, img_w - tw))
    ty = max(0, min(ty, img_h - th))

    asset_pil = Image.open(splice_asset_path).convert("RGBA")
    asset_pil = asset_pil.resize((tw, th), Image.Resampling.LANCZOS)
    asset_np = np.array(asset_pil)

    output = img.copy()
    rgb_asset = cv2.cvtColor(asset_np[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha_mask = asset_np[:, :, 3]

    if use_poisson and cv2.countNonZero(alpha_mask) > 100:
        center = (tx + tw // 2, ty + th // 2)
        try:
            output = cv2.seamlessClone(
                rgb_asset, output, alpha_mask, center, cv2.NORMAL_CLONE
            )
        except (cv2.error, ValueError):
            # Fallback to standard alpha blend
            for c in range(3):
                output[ty : ty + th, tx : tx + tw, c] = (
                    (alpha_mask / 255.0) * rgb_asset[:, :, c]
                    + (1.0 - alpha_mask / 255.0) * output[ty : ty + th, tx : tx + tw, c]
                ).astype(np.uint8)
    else:
        for c in range(3):
            output[ty : ty + th, tx : tx + tw, c] = (
                (alpha_mask / 255.0) * rgb_asset[:, :, c]
                + (1.0 - alpha_mask / 255.0) * output[ty : ty + th, tx : tx + tw, c]
            ).astype(np.uint8)

    tamper_info = {
        "technique": "SPLICING",
        "asset_used": splice_asset_path.name,
        "bbox_pixel": {"x": tx, "y": ty, "width": tw, "height": th},
        "bbox_normalized": {
            "x1": round(tx / img_w, 4),
            "y1": round(ty / img_h, 4),
            "x2": round((tx + tw) / img_w, 4),
            "y2": round((ty + th) / img_h, 4),
        },
    }
    return output, tamper_info


def apply_recompression_discrepancy(
    img: np.ndarray,
    target_box: dict[str, int],
    low_q: int = 65,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Save a local patch with low quality JPEG and paste back to create ELA compression noise."""
    img_h, img_w = img.shape[:2]
    x, y, w, h = (
        target_box["x"],
        target_box["y"],
        target_box["width"],
        target_box["height"],
    )

    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(10, min(w, img_w - x))
    h = max(10, min(h, img_h - y))

    patch = img[y : y + h, x : x + w]
    patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
    pil_patch = Image.fromarray(patch_rgb)

    buffer = io.BytesIO()
    pil_patch.save(buffer, format="JPEG", quality=low_q)
    buffer.seek(0)
    recompressed_patch = np.array(Image.open(buffer))
    recompressed_bgr = cv2.cvtColor(recompressed_patch, cv2.COLOR_RGB2BGR)

    output = img.copy()
    output[y : y + h, x : x + w] = recompressed_bgr

    tamper_info = {
        "technique": "RECOMPRESSION_DISCREPANCY",
        "quality_factor": low_q,
        "bbox_pixel": {"x": x, "y": y, "width": w, "height": h},
        "bbox_normalized": {
            "x1": round(x / img_w, 4),
            "y1": round(y / img_h, 4),
            "x2": round((x + w) / img_w, 4),
            "y2": round((y + h) / img_h, 4),
        },
    }
    return output, tamper_info


def apply_manipulation(
    genuine_img: Image.Image,
    field_boxes: dict[str, Any],
    assets_dir: Path,
    manipulation_type: str | None = None,
) -> tuple[Image.Image, list[dict[str, Any]], list[str]]:
    """Select and execute one or more tamper transformations on a genuine certificate."""
    img_cv = cv2.cvtColor(np.array(genuine_img), cv2.COLOR_RGB2BGR)
    img_h, img_w = img_cv.shape[:2]

    types = [
        "TEXT_REPLACEMENT",
        "COPY_MOVE",
        "SEAL_SIGNATURE_SPLICE",
        "RECOMPRESSION",
    ]
    chosen_type = manipulation_type or random.choice(types)

    applied_types = [chosen_type]
    manipulated_regions = []

    if chosen_type == "TEXT_REPLACEMENT":
        # Target CGPA/Grade or Student Name
        target_field = random.choice(
            ["grade_or_marks", "student_name", "certificate_number"]
        )
        if target_field in field_boxes:
            box = field_boxes[target_field]["bbox_pixel"]
            if target_field == "grade_or_marks":
                new_val = "First Class with Distinction (CGPA 9.95 / 10.0)"
            elif target_field == "student_name":
                new_val = "ALEXANDER HAMILTON"
            else:
                new_val = "CERT-24-999999"

            img_cv, info = inpaint_and_replace_text(
                img_cv, box, new_val, font_mismatched=True
            )
            info["region_id"] = f"REG_{len(manipulated_regions) + 1:02d}"
            info["field_affected"] = target_field
            info["original_value"] = field_boxes[target_field]["value"]
            info["tampered_value"] = new_val
            manipulated_regions.append(info)

    elif chosen_type == "COPY_MOVE":
        # Clone marks or date digit
        target_field = random.choice(["grade_or_marks", "register_number"])
        if target_field in field_boxes:
            box = field_boxes[target_field]["bbox_pixel"]
            clone_x = max(10, box["x"] + random.randint(40, 120))
            clone_y = box["y"]
            img_cv, info = copy_move_tampering(img_cv, box, clone_x, clone_y)
            info["region_id"] = f"REG_{len(manipulated_regions) + 1:02d}"
            info["field_affected"] = target_field
            manipulated_regions.append(info)

    elif chosen_type == "SEAL_SIGNATURE_SPLICE":
        # Splice foreign seal or signature
        seals = list((assets_dir / "seals").glob("*.png"))
        if seals:
            splice_seal = random.choice(seals)
            target_pos = (img_w // 2 - 110, img_h - 340)
            img_cv, info = splice_seal_or_signature(
                img_cv, splice_seal, target_pos, (220, 220), use_poisson=True
            )
            info["region_id"] = f"REG_{len(manipulated_regions) + 1:02d}"
            info["field_affected"] = "institutional_seal"
            manipulated_regions.append(info)

    elif chosen_type == "RECOMPRESSION":
        # Local ELA discrepancy on certificate number or degree
        target_field = random.choice(["course_degree", "certificate_number"])
        if target_field in field_boxes:
            box = field_boxes[target_field]["bbox_pixel"]
            img_cv, info = apply_recompression_discrepancy(img_cv, box, low_q=60)
            info["region_id"] = f"REG_{len(manipulated_regions) + 1:02d}"
            info["field_affected"] = target_field
            manipulated_regions.append(info)

    # Convert back to PIL Image
    final_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    return final_pil, manipulated_regions, applied_types
