#!/usr/bin/env python3
"""CLI utility to test OCR engine and academic field extraction on certificate images."""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.modules.ocr.engine_factory import EngineFactory  # noqa: E402
from app.modules.ocr.service import OCRService  # noqa: E402
from app.schemas.ocr import OCRConfig  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run OCR and academic field extraction on certificate image(s)."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to an image file or directory of certificate images.",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="auto",
        choices=["auto", "easyocr", "pytesseract", "mock"],
        help="OCR engine to use (default: auto)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./storage/reports"),
        help="Directory to save visual overlays (default: ./storage/reports)",
    )
    parser.add_argument(
        "--show-tokens",
        action="store_true",
        help="Print all extracted OCR tokens with confidences",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = args.input_path.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("AI Certificate Verification - OCR & Information Extraction")
    print("=" * 70)

    engines = EngineFactory.get_available_engines()
    print("Available OCR engines:")
    for eng, avail in engines.items():
        status = "AVAILABLE" if avail else "UNAVAILABLE"
        print(f"  * {eng:<12}: {status}")

    config = OCRConfig(engine=args.engine, generate_overlay=True)
    service = OCRService(config=config, report_dir=output_dir)
    print(f"\nInitialized OCR Engine: {service.engine.engine_name}")

    if input_path.is_file():
        image_files = [input_path]
    elif input_path.is_dir():
        image_files = sorted(
            [p for p in input_path.glob("*.*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
        )
    else:
        print(f"Error: Invalid input path: {input_path}")
        sys.exit(1)

    print(f"Processing {len(image_files)} image(s)...\n")

    for img_file in image_files:
        doc_id = img_file.stem
        print(f"--- Document: {img_file.name} ---")

        result = service.process_document(doc_id, img_file)

        print(f"  Execution Time: {result.execution_time_ms:.2f} ms")
        print(f"  Tokens Detected: {result.token_count}")
        print(f"  Avg OCR Confidence: {result.average_ocr_confidence:.4f}")
        print(f"  Low Confidence Flag: {result.low_confidence_flag}")
        print("\n  Extracted Academic Fields:")
        for name, field in result.field_details.items():
            flag_str = "[FLAGGED < 0.70]" if field.is_flagged else "[OK]"
            print(f"    * {name:<20}: {field.value} (conf: {field.confidence:.2f}) {flag_str}")

        if result.overlay_path:
            print(f"\n  Visual Overlay Saved: {result.overlay_path}")

        if args.show_tokens:
            print("\n  Tokens:")
            tokens = service.engine.extract_tokens(img_file)
            for tok in tokens:
                print(f"    - '{tok.text}' (conf: {tok.confidence:.2f})")
        print()


if __name__ == "__main__":
    main()
