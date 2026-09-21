"""Genuine Certificate Generator.

Populates base certificate templates with realistic synthetic student records,
renders text fields, composites seals and signatures, and returns ground truth bounding boxes.
"""

from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path
from typing import Any

from faker import Faker
from PIL import Image, ImageDraw, ImageFont

fake = Faker()
Faker.seed(42)
random.seed(42)

DEGREE_PROGRAMS = [
    "Bachelor of Science in Computer Science",
    "Bachelor of Engineering in Mechanical Engineering",
    "Bachelor of Technology in Information Technology",
    "Bachelor of Science in Electrical Engineering",
    "Master of Science in Artificial Intelligence",
    "Master of Business Administration",
    "Bachelor of Arts in Economics",
    "Master of Technology in Data Science",
]

GRADE_DISTINCTIONS = [
    "First Class with Distinction (CGPA 9.42 / 10.0)",
    "First Class with Distinction (CGPA 8.85 / 10.0)",
    "First Class (CGPA 8.15 / 10.0)",
    "First Class (CGPA 7.60 / 10.0)",
    "Second Class Upper Division (CGPA 6.90 / 10.0)",
    "Grade A+ (Distinction)",
    "Grade A (Outstanding)",
    "Grade B+ (Merit)",
]


def generate_synthetic_record() -> dict[str, str]:
    """Generate a realistic, consistent synthetic student record."""
    grad_year = random.randint(2018, 2025)
    month = random.choice([5, 6, 7, 11])
    day = random.randint(10, 28)
    from datetime import timezone

    issue_date = datetime(grad_year, month, day, tzinfo=timezone.utc).strftime(
        "%B %d, %Y"
    )
    cert_year_short = str(grad_year)[-2:]

    return {
        "student_name": fake.name().upper(),
        "register_number": f"REG{grad_year}{random.randint(10000, 99999)}",
        "certificate_number": f"CERT-{cert_year_short}-{random.randint(100000, 999999)}",
        "course_degree": random.choice(DEGREE_PROGRAMS),
        "grade_or_marks": random.choice(GRADE_DISTINCTIONS),
        "issue_date": f"Given on this {issue_date}",
    }


def render_genuine_certificate(
    template_meta: dict[str, Any],
    record: dict[str, str],
    raw_dir: Path,
    assets_dir: Path,
) -> tuple[Image.Image, dict[str, Any]]:
    """Render text and graphic assets onto a base template, computing exact bounding boxes."""
    template_path = raw_dir / template_meta["filename"]
    base_img = Image.open(template_path).convert("RGBA")
    width, height = base_img.size

    # Composite Seal
    seal_anchor = template_meta["seal_anchor"]
    seal_path = assets_dir / "seals" / template_meta["seal_file"]
    if seal_path.exists():
        seal_img = Image.open(seal_path).convert("RGBA")
        seal_img = seal_img.resize(
            (seal_anchor["size"], seal_anchor["size"]), Image.Resampling.LANCZOS
        )
        base_img.paste(seal_img, (seal_anchor["x"], seal_anchor["y"]), mask=seal_img)

    # Composite Left Signature
    sig_l_anchor = template_meta["sig_left_anchor"]
    sig_l_path = assets_dir / "signatures" / template_meta["sig_left_file"]
    if sig_l_path.exists():
        sig_l_img = Image.open(sig_l_path).convert("RGBA")
        sig_l_img = sig_l_img.resize(
            tuple(sig_l_anchor["size"]), Image.Resampling.LANCZOS
        )
        base_img.paste(
            sig_l_img, (sig_l_anchor["x"], sig_l_anchor["y"]), mask=sig_l_img
        )

    # Composite Right Signature
    sig_r_anchor = template_meta["sig_right_anchor"]
    sig_r_path = assets_dir / "signatures" / template_meta["sig_right_file"]
    if sig_r_path.exists():
        sig_r_img = Image.open(sig_r_path).convert("RGBA")
        sig_r_img = sig_r_img.resize(
            tuple(sig_r_anchor["size"]), Image.Resampling.LANCZOS
        )
        base_img.paste(
            sig_r_img, (sig_r_anchor["x"], sig_r_anchor["y"]), mask=sig_r_img
        )

    # Render Text Fields and compute bounding boxes
    draw = ImageDraw.Draw(base_img)
    field_boxes = {}

    anchors = template_meta["field_anchors"]

    for field_name, val in record.items():
        if field_name not in anchors:
            continue
        cfg = anchors[field_name]
        font = ImageFont.load_default()

        # Compute text dimensions
        bbox = draw.textbbox((0, 0), val, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Determine alignment
        if cfg.get("align") == "center":
            draw_x = cfg["x"] - text_w // 2
        elif cfg.get("align") == "right":
            draw_x = cfg["x"] - text_w
        else:
            draw_x = cfg["x"]

        draw_y = cfg["y"]

        # Text color
        if field_name in ["student_name", "course_degree"]:
            text_color = (20, 20, 20)
        else:
            text_color = (40, 40, 40)

        draw.text((draw_x, draw_y), val, fill=text_color, font=font)

        # Padding for bounding box
        pad = 8
        px_x = max(0, draw_x - pad)
        px_y = max(0, draw_y - pad)
        px_w = text_w + pad * 2
        px_h = text_h + pad * 2

        field_boxes[field_name] = {
            "value": val,
            "bbox_pixel": {
                "x": px_x,
                "y": px_y,
                "width": px_w,
                "height": px_h,
            },
            "bbox_normalized": {
                "x1": round(px_x / width, 4),
                "y1": round(px_y / height, 4),
                "x2": round((px_x + px_w) / width, 4),
                "y2": round((px_y + px_h) / height, 4),
            },
        }

    return base_img.convert("RGB"), field_boxes
