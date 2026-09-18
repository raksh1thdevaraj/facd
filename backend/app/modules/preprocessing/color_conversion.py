import cv2
import numpy as np


def composite_alpha_on_white(image: np.ndarray) -> np.ndarray:
    """Composite a 4-channel BGRA image over a pure white background to prevent black voids."""
    if image.ndim != 3 or image.shape[2] != 4:
        return image

    b, g, r, a = cv2.split(image)
    alpha = a.astype(float) / 255.0

    white_bg = np.ones_like(b, dtype=float) * 255.0

    b_out = (b.astype(float) * alpha + white_bg * (1.0 - alpha)).astype(np.uint8)
    g_out = (g.astype(float) * alpha + white_bg * (1.0 - alpha)).astype(np.uint8)
    r_out = (r.astype(float) * alpha + white_bg * (1.0 - alpha)).astype(np.uint8)

    return cv2.merge([b_out, g_out, r_out])


def ensure_3channel(image: np.ndarray) -> np.ndarray:
    """Ensure the image is a standard 3-channel BGR image array."""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        return composite_alpha_on_white(image)
    elif image.shape[2] == 3:
        return image
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert an arbitrary image array (RGBA, BGR, or Grayscale) to 2D uint8 Grayscale."""
    if image.ndim == 2:
        return image.copy()

    if image.shape[2] == 4:
        bgr = composite_alpha_on_white(image)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    elif image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError(f"Unsupported image shape for grayscale conversion: {image.shape}")


def to_lab(image: np.ndarray) -> np.ndarray:
    """Convert image to CIE LAB color space."""
    bgr = ensure_3channel(image)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
