from typing import Optional, Tuple

import cv2
import numpy as np


def align_to_template(
    query_img: np.ndarray,
    template_img: np.ndarray,
    max_features: int = 2000,
    inlier_ratio_threshold: float = 0.20,
    precomputed_template_descriptors: Optional[Tuple[np.ndarray, np.ndarray]] = None,
) -> Tuple[np.ndarray, float, bool]:
    """Align query certificate image to reference template using ORB & RANSAC.

    Args:
        query_img: Query certificate BGR or grayscale array.
        template_img: Reference template BGR or grayscale array.
        max_features: Maximum ORB features to detect.
        inlier_ratio_threshold: Minimum RANSAC inlier ratio for success.
        precomputed_template_descriptors: Optional tuple (keypoints_pts, descriptors).

    Returns:
        Tuple of (aligned_image, inlier_ratio, alignment_success).
    """
    if query_img is None or template_img is None:
        raise ValueError("Query image and template image must not be None.")

    h_tpl, w_tpl = template_img.shape[:2]

    # Convert to grayscale for feature detection
    query_gray = (
        cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY) if query_img.ndim == 3 else query_img.copy()
    )
    template_gray = (
        cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        if template_img.ndim == 3
        else template_img.copy()
    )

    orb = cv2.ORB_create(nfeatures=max_features)

    # Detect features in query image
    kp1, des1 = orb.detectAndCompute(query_gray, None)

    # Extract or use precomputed features for template
    if precomputed_template_descriptors is not None:
        tpl_pts, des2 = precomputed_template_descriptors
        kp2 = [cv2.KeyPoint(x=pt[0], y=pt[1], size=1.0) for pt in tpl_pts]
    else:
        kp2, des2 = orb.detectAndCompute(template_gray, None)

    # If insufficient features found, alignment cannot proceed
    if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
        # Return resized query image with 0.0 inlier ratio and False
        resized_query = cv2.resize(query_img, (w_tpl, h_tpl))
        return resized_query, 0.0, False

    # Match descriptors using Hamming distance with cross-checking
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)

    if not matches or len(matches) < 15:
        resized_query = cv2.resize(query_img, (w_tpl, h_tpl))
        return resized_query, 0.0, False

    # Sort matches by distance
    matches = sorted(matches, key=lambda m: m.distance)
    num_to_keep = max(10, int(len(matches) * 0.25))
    top_matches = matches[:num_to_keep]

    if len(top_matches) < 8:
        resized_query = cv2.resize(query_img, (w_tpl, h_tpl))
        return resized_query, 0.0, False

    src_pts = np.float32([kp1[m.queryIdx].pt for m in top_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in top_matches]).reshape(-1, 1, 2)

    # Estimate homography matrix using RANSAC
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if H is None or mask is None:
        resized_query = cv2.resize(query_img, (w_tpl, h_tpl))
        return resized_query, 0.0, False

    inliers = int(np.sum(mask))
    inlier_ratio = float(inliers / len(top_matches))

    # Reject if inlier ratio is below threshold or absolute inliers are insufficient
    if inlier_ratio < inlier_ratio_threshold or inliers < 8:
        resized_query = cv2.resize(query_img, (w_tpl, h_tpl))
        return resized_query, inlier_ratio, False

    # Warp query image into master template coordinate space
    aligned_img = cv2.warpPerspective(
        query_img, H, (w_tpl, h_tpl), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )

    # Attempt sub-pixel ECC refinement (graceful fallback if ECC does not converge)
    try:
        aligned_gray = (
            cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY) if aligned_img.ndim == 3 else aligned_img
        )
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 1e-4)
        _, warp_matrix = cv2.findTransformECC(
            template_gray, aligned_gray, warp_matrix, cv2.MOTION_EUCLIDEAN, criteria
        )
        aligned_img = cv2.warpAffine(
            aligned_img,
            warp_matrix,
            (w_tpl, h_tpl),
            flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
            borderMode=cv2.BORDER_REPLICATE,
        )
    except cv2.error:
        # ECC non-convergence is common on modified documents; proceed with homography
        pass

    return aligned_img, round(inlier_ratio, 4), True
