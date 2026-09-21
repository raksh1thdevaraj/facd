"""Certificate Template & Asset Generator.

Generates high-resolution base certificate templates, Guilloché background patterns,
decorative borders, institutional seals, and signature graphic assets.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


def create_guilloche_pattern(
    width: int, height: int, color: tuple[int, int, int, int] = (220, 215, 205, 40)
) -> Image.Image:
    """Create a subtle geometric Guilloché rosette/wave security background pattern."""
    pattern = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pattern)

    cx, cy = width // 2, height // 2
    R, r, p = 280, 70, 95

    # Draw mathematical hypotrochoid rosette curves
    points = []
    for t in np.linspace(0, 16 * math.pi, 2500):
        x = (R - r) * math.cos(t) + p * math.cos((R - r) * t / r) + cx
        y = (R - r) * math.sin(t) - p * math.sin((R - r) * t / r) + cy
        points.append((x, y))

    if len(points) > 1:
        draw.line(points, fill=color, width=1)

    # Secondary wavy border grid
    for y_line in range(60, height - 60, 40):
        wave_pts = []
        for x_val in range(60, width - 60, 10):
            y_val = y_line + 4 * math.sin(x_val / 25.0)
            wave_pts.append((x_val, y_val))
        if len(wave_pts) > 1:
            draw.line(wave_pts, fill=(color[0], color[1], color[2], 25), width=1)

    return pattern


def draw_decorative_border(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    primary_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
) -> None:
    """Draw an ornate double border with decorative corner brackets."""
    # Outer border
    draw.rectangle([30, 30, width - 30, height - 30], outline=primary_color, width=6)
    # Inner thin border
    draw.rectangle([44, 44, width - 44, height - 44], outline=accent_color, width=2)
    # Inset fine line
    draw.rectangle([54, 54, width - 54, height - 54], outline=primary_color, width=1)

    # Corner decorative flourishes
    corner_size = 40
    corners = [
        (44, 44, 44 + corner_size, 44 + corner_size),
        (width - 44 - corner_size, 44, width - 44, 44 + corner_size),
        (44, height - 44 - corner_size, 44 + corner_size, height - 44),
        (width - 44 - corner_size, height - 44 - corner_size, width - 44, height - 44),
    ]
    for c in corners:
        draw.rectangle(c, outline=accent_color, width=2)


def generate_seal_image(
    institution_name: str,
    color: tuple[int, int, int],
    size: int = 240,
    motto: str = "OFFICIAL SEAL • EXCELLENCE & INTEGRITY",
) -> Image.Image:
    """Generate a circular institutional seal with concentric rings, star icons, and circular text."""
    seal = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(seal)

    center = size // 2
    r_outer = center - 10
    r_inner = r_outer - 18
    r_core = r_inner - 24

    # Outer serrated / toothed ring
    num_teeth = 48
    for i in range(num_teeth):
        angle = 2 * math.pi * i / num_teeth
        r_tooth = r_outer + (4 if i % 2 == 0 else -2)
        x = center + r_tooth * math.cos(angle)
        y = center + r_tooth * math.sin(angle)
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)

    # Concentric rings
    draw.ellipse(
        [center - r_outer, center - r_outer, center + r_outer, center + r_outer],
        outline=color,
        width=3,
    )
    draw.ellipse(
        [center - r_inner, center - r_inner, center + r_inner, center + r_inner],
        outline=color,
        width=2,
    )
    draw.ellipse(
        [center - r_core, center - r_core, center + r_core, center + r_core],
        outline=color,
        width=1,
    )

    # Core insignia (Shield / Star)
    draw.regular_polygon(
        (center, center, r_core - 15), n_sides=6, rotation=0, outline=color
    )
    draw.text((center - 16, center - 12), "★", fill=color)

    # Circular text around perimeter
    chars = list(motto)
    angle_step = (2 * math.pi) / max(len(chars), 1)
    for i, ch in enumerate(chars):
        a = i * angle_step - math.pi / 2
        r_text = (r_outer + r_inner) / 2 - 2
        tx = center + r_text * math.cos(a) - 4
        ty = center + r_text * math.sin(a) - 6
        draw.text((tx, ty), ch, fill=color)

    return seal


def generate_signature_image(
    signer_name: str,
    color: tuple[int, int, int] = (20, 30, 80),
    size: tuple[int, int] = (280, 80),
) -> Image.Image:
    """Generate a realistic curved cursive signature graphic."""
    sig = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(sig)

    w, h = size
    # Generate smooth Bezier-like curve strokes
    pts = []
    num_pts = 35
    for i in range(num_pts):
        x = 20 + (w - 50) * (i / num_pts)
        y = h / 2 + 18 * math.sin(i * 0.8) + 8 * math.cos(i * 1.7)
        pts.append((x, y))

    if len(pts) > 1:
        draw.line(pts, fill=color, width=3)

    # Underline flourish
    under_pts = [(25, h - 18), (w / 2, h - 12), (w - 20, h - 22)]
    draw.line(under_pts, fill=color, width=2)

    return sig


def generate_all_templates(output_dir: Path) -> list[dict[str, Any]]:
    """Generate all 4 institutional templates and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    seals_dir = output_dir / "assets" / "seals"
    sigs_dir = output_dir / "assets" / "signatures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    seals_dir.mkdir(parents=True, exist_ok=True)
    sigs_dir.mkdir(parents=True, exist_ok=True)

    templates_spec = [
        {
            "template_id": "template_tech_univ",
            "institution_name": "INSTITUTE OF TECHNOLOGY & SCIENCE",
            "motto": "INNOVATION • INTEGRITY • EXCELLENCE",
            "primary_color": (15, 45, 95),  # Deep Navy
            "accent_color": (195, 145, 40),  # Gold
            "bg_color": (250, 248, 243),
            "seal_file": "seal_tech.png",
            "sig_left_file": "sig_dean.png",
            "sig_right_file": "sig_registrar.png",
            "sig_left_title": "Dean of Academic Affairs",
            "sig_right_title": "Registrar",
        },
        {
            "template_id": "template_heritage_univ",
            "institution_name": "HERITAGE GLOBAL UNIVERSITY",
            "motto": "TRUTH • WISDOM • LEADERSHIP",
            "primary_color": (80, 20, 25),  # Crimson / Burgundy
            "accent_color": (175, 130, 50),  # Antique Gold
            "bg_color": (248, 245, 238),
            "seal_file": "seal_heritage.png",
            "sig_left_file": "sig_provost.png",
            "sig_right_file": "sig_chancellor.png",
            "sig_left_title": "University Provost",
            "sig_right_title": "Vice-Chancellor",
        },
        {
            "template_id": "template_metro_univ",
            "institution_name": "METROPOLITAN STATE UNIVERSITY",
            "motto": "KNOWLEDGE • DIVERSITY • PROGRESS",
            "primary_color": (20, 70, 50),  # Emerald Forest
            "accent_color": (180, 140, 60),  # Bronze
            "bg_color": (252, 250, 245),
            "seal_file": "seal_metro.png",
            "sig_left_file": "sig_head.png",
            "sig_right_file": "sig_controller.png",
            "sig_left_title": "Head of Examinations",
            "sig_right_title": "Controller of Examinations",
        },
        {
            "template_id": "template_national_academy",
            "institution_name": "NATIONAL ACADEMY OF HIGHER EDUCATION",
            "motto": "DISCOVERY • EMPOWERMENT • SERVICE",
            "primary_color": (35, 35, 40),  # Charcoal Slate
            "accent_color": (160, 120, 30),  # Dark Gold
            "bg_color": (246, 244, 240),
            "seal_file": "seal_national.png",
            "sig_left_file": "sig_director.png",
            "sig_right_file": "sig_president.png",
            "sig_left_title": "Director of Academics",
            "sig_right_title": "President",
        },
    ]

    width, height = 1920, 1350
    templates_meta = []

    for spec in templates_spec:
        # Create base canvas
        img = Image.new("RGB", (width, height), spec["bg_color"])
        draw = ImageDraw.Draw(img)

        # 1. Overlay Guilloché pattern
        guilloche = create_guilloche_pattern(width, height)
        img.paste(guilloche, (0, 0), mask=guilloche)

        # 2. Draw border
        draw_decorative_border(
            draw, width, height, spec["primary_color"], spec["accent_color"]
        )

        # 3. Create and save seal asset
        seal_img = generate_seal_image(
            spec["institution_name"], spec["accent_color"], size=220
        )
        seal_path = seals_dir / spec["seal_file"]
        seal_img.save(seal_path, "PNG")

        # 4. Create and save signatures
        sig_l_img = generate_signature_image(spec["sig_left_title"], color=(10, 20, 70))
        sig_r_img = generate_signature_image(
            spec["sig_right_title"], color=(20, 10, 60)
        )
        sig_l_path = sigs_dir / spec["sig_left_file"]
        sig_r_path = sigs_dir / spec["sig_right_file"]
        sig_l_img.save(sig_l_path, "PNG")
        sig_r_img.save(sig_r_path, "PNG")

        # 5. Render Header texts on Template
        draw.text(
            (width // 2 - 320, 90), spec["institution_name"], fill=spec["primary_color"]
        )
        draw.text((width // 2 - 180, 130), spec["motto"], fill=spec["accent_color"])
        draw.line(
            [width // 2 - 400, 160, width // 2 + 400, 160],
            fill=spec["accent_color"],
            width=2,
        )
        draw.text(
            (width // 2 - 220, 190),
            "OFFICIAL DEGREE CERTIFICATE",
            fill=spec["primary_color"],
        )

        # 6. Static Boilerplate Labels
        draw.text((width // 2 - 140, 290), "This is to certify that", fill=(60, 60, 60))
        draw.text(
            (width // 2 - 260, 480),
            "has successfully fulfilled the prescribed requirements for the award of",
            fill=(60, 60, 60),
        )
        draw.text(
            (width // 2 - 80, 680), "with academic standing of", fill=(60, 60, 60)
        )

        # 7. Signature Labels
        draw.line([220, height - 200, 520, height - 200], fill=(80, 80, 80), width=1)
        draw.text((260, height - 190), spec["sig_left_title"], fill=(80, 80, 80))

        draw.line(
            [width - 520, height - 200, width - 220, height - 200],
            fill=(80, 80, 80),
            width=1,
        )
        draw.text(
            (width - 480, height - 190), spec["sig_right_title"], fill=(80, 80, 80)
        )

        # 8. Save base template image
        template_filename = f"{spec['template_id']}.png"
        template_img_path = raw_dir / template_filename
        img.save(template_img_path, "PNG")

        meta = {
            "template_id": spec["template_id"],
            "filename": template_filename,
            "institution_name": spec["institution_name"],
            "dimensions": [width, height],
            "field_anchors": {
                "student_name": {
                    "x": width // 2,
                    "y": 380,
                    "align": "center",
                    "font_size": 48,
                },
                "register_number": {
                    "x": 260,
                    "y": 240,
                    "align": "left",
                    "font_size": 24,
                },
                "certificate_number": {
                    "x": width - 420,
                    "y": 240,
                    "align": "left",
                    "font_size": 24,
                },
                "course_degree": {
                    "x": width // 2,
                    "y": 570,
                    "align": "center",
                    "font_size": 40,
                },
                "grade_or_marks": {
                    "x": width // 2,
                    "y": 750,
                    "align": "center",
                    "font_size": 36,
                },
                "issue_date": {
                    "x": width // 2,
                    "y": 860,
                    "align": "center",
                    "font_size": 24,
                },
            },
            "seal_anchor": {"x": width // 2 - 110, "y": height - 340, "size": 220},
            "sig_left_anchor": {"x": 230, "y": height - 280, "size": [280, 80]},
            "sig_right_anchor": {
                "x": width - 510,
                "y": height - 280,
                "size": [280, 80],
            },
            "seal_file": spec["seal_file"],
            "sig_left_file": spec["sig_left_file"],
            "sig_right_file": spec["sig_right_file"],
        }
        templates_meta.append(meta)

    # Save master templates metadata JSON
    with open(raw_dir / "templates_meta.json", "w", encoding="utf-8") as f:
        json.dump({"templates": templates_meta}, f, indent=2)

    return templates_meta


if __name__ == "__main__":
    generate_all_templates(Path("./datasets"))
    print("Successfully generated 4 base certificate templates and assets.")
