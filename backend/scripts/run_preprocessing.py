import argparse
import sys
import uuid
from pathlib import Path

import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.preprocessing.artifact_manager import PreprocessingArtifactManager
from app.modules.preprocessing.service import PreprocessingService


def create_comparison_image(
    original: np.ndarray, enhanced: np.ndarray, binarized: np.ndarray
) -> np.ndarray:
    """Create a side-by-side composite [Original | Enhanced | Binarized]."""
    h, w = enhanced.shape[:2]

    # Resize original to match enhanced dimensions
    orig_resized = cv2.resize(original, (w, h), interpolation=cv2.INTER_AREA)
    if orig_resized.ndim == 2:
        orig_resized = cv2.cvtColor(orig_resized, cv2.COLOR_GRAY2BGR)

    if enhanced.ndim == 2:
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    else:
        enhanced_bgr = enhanced

    # Convert binarized (2D uint8) to 3-channel BGR
    bin_bgr = cv2.cvtColor(binarized, cv2.COLOR_GRAY2BGR)

    # Label headers
    for img, label in [
        (orig_resized, "ORIGINAL"),
        (enhanced_bgr, "ENHANCED"),
        (bin_bgr, "BINARIZED (OCR)"),
    ]:
        cv2.putText(
            img,
            label,
            (30, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )

    return np.hstack([orig_resized, enhanced_bgr, bin_bgr])


def main():
    parser = argparse.ArgumentParser(
        description="Run certificate image preprocessing pipeline CLI."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=str,
        help="Path to certificate image or directory of images.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="./storage/preprocessed",
        help="Destination directory for processed artifacts.",
    )
    parser.add_argument(
        "--save-comparison",
        action="store_true",
        help="Generate side-by-side [Original | Enhanced | Binarized] image.",
    )
    parser.add_argument(
        "--show-timings",
        action="store_true",
        help="Print execution durations for each pipeline step.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        image_files = [input_path]
    elif input_path.is_dir():
        image_files = sorted(
            [
                f
                for f in input_path.iterdir()
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
            ]
        )
    else:
        print(f"Error: Input path '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(image_files)} image(s) to process.")

    artifact_manager = PreprocessingArtifactManager(target_dir=output_dir)
    service = PreprocessingService(artifact_manager=artifact_manager)

    for idx, img_file in enumerate(image_files, 1):
        cert_id = uuid.uuid4()
        print(f"[{idx}/{len(image_files)}] Processing {img_file.name} (UUID: {cert_id})...")

        raw = cv2.imread(str(img_file))
        if raw is None:
            print(f"  Warning: Failed to load {img_file.name}, skipping.")
            continue

        result = service.preprocess(cert_id, img_file)

        print(f"  -> Skew corrected: {result.applied_skew_angle:.2f}°")
        print(f"  -> Perspective corrected: {result.perspective_corrected}")
        orig_res = f"{result.original_width}x{result.original_height}"
        proc_res = f"{result.processed_width}x{result.processed_height}"
        print(f"  -> Resolution: {orig_res} -> {proc_res}")

        if args.show_timings:
            print("  -> Step timings:")
            for step, ms in result.step_metrics.items():
                print(f"     * {step}: {ms:.2f} ms")

        if args.save_comparison:
            comp_img = create_comparison_image(raw, result.enhanced_image, result.binarized_image)
            comp_path = output_dir / f"{cert_id}_comparison.png"
            cv2.imwrite(str(comp_path), comp_img)
            print(f"  -> Saved comparison image: {comp_path.name}")

    print("\nPreprocessing complete.")


if __name__ == "__main__":
    main()
