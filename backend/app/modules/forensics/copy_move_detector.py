from typing import List, Optional, Tuple

import cv2
import numpy as np
from sklearn.cluster import DBSCAN

from app.schemas.forensics import CloneMatch, ForensicConfig
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class CopyMoveDetector:
    """Detects duplicated or cloned elements (seals, stamps, signatures, text patches)
    using SIFT/ORB keypoints, FLANN matching, DBSCAN clustering, and RANSAC affine verification.
    """

    def __init__(self, config: Optional[ForensicConfig] = None):
        self.config = config or ForensicConfig()

    def analyze(
        self,
        image: np.ndarray,
    ) -> Tuple[float, List[CloneMatch]]:
        """Detect copy-move forgery clusters and return authenticity score and clone matches.

        Returns:
            Tuple of:
            - copy_move_score: float [0.0, 1.0] (1.0 = clean, 0.0 = heavy cloning)
            - clone_matches: List[CloneMatch]
        """
        if image is None or image.size == 0:
            return 1.0, []

        img_h, img_w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Step 1: Feature Extraction
        keypoints, descriptors = self._extract_features(gray)
        if descriptors is None or len(keypoints) < 15:
            return 1.0, []

        # Step 2: Descriptor Self-Matching with Lowe's ratio test & spatial pruning
        matched_pairs = self._match_descriptors(keypoints, descriptors)
        if len(matched_pairs) < self.config.dbscan_min_samples:
            return 1.0, []

        # Step 3: Spatial Displacement Clustering via DBSCAN
        clones = self._cluster_and_verify_clones(matched_pairs, img_w, img_h)

        score = max(0.0, 1.0 - 0.25 * len(clones))
        return round(score, 4), clones

    def _extract_features(
        self, gray_img: np.ndarray
    ) -> Tuple[List[cv2.KeyPoint], Optional[np.ndarray]]:
        """Extract SIFT keypoints and descriptors with automatic fallback to ORB."""
        try:
            sift = cv2.SIFT_create(
                nfeatures=self.config.sift_max_features,
                contrastThreshold=0.03,
                edgeThreshold=10,
            )
            keypoints, descriptors = sift.detectAndCompute(gray_img, None)
            return keypoints, descriptors
        except Exception:
            orb = cv2.ORB_create(nfeatures=self.config.sift_max_features)
            keypoints, descriptors = orb.detectAndCompute(gray_img, None)
            return keypoints, descriptors

    def _match_descriptors(
        self, keypoints: List[cv2.KeyPoint], descriptors: np.ndarray
    ) -> List[Tuple[cv2.KeyPoint, cv2.KeyPoint, float]]:
        """Match descriptors against themselves and filter out self-matches and nearby keypoints."""
        num_kps = len(keypoints)
        if num_kps < 4:
            return []

        # Use FLANN KD-Tree for float descriptors, BFMatcher for binary
        if descriptors.dtype == np.float32:
            index_params = dict(algorithm=1, trees=5)  # KDTREE
            search_params = dict(checks=50)
            matcher = cv2.FlannBasedMatcher(index_params, search_params)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

        try:
            raw_matches = matcher.knnMatch(descriptors, descriptors, k=3)
        except Exception:
            return []

        min_dist_sq = self.config.copy_move_min_distance_px**2
        ratio_thresh = self.config.copy_move_ratio_thresh
        matched_pairs: List[Tuple[cv2.KeyPoint, cv2.KeyPoint, float]] = []

        for m_list in raw_matches:
            if len(m_list) < 3:
                continue

            # m_list[0] is self-match (distance == 0.0)
            # m_list[1] is closest other keypoint
            # m_list[2] is second closest
            m1 = m_list[1]
            m2 = m_list[2]

            # Canonical order prevents duplicate symmetric pairs (kp1, kp2) and (kp2, kp1)
            if m1.queryIdx >= m1.trainIdx:
                continue

            if m1.distance < ratio_thresh * m2.distance:
                kp1 = keypoints[m1.queryIdx]
                kp2 = keypoints[m1.trainIdx]

                # Ensure spatial distance threshold is satisfied
                dx = kp2.pt[0] - kp1.pt[0]
                dy = kp2.pt[1] - kp1.pt[1]
                if (dx * dx + dy * dy) >= min_dist_sq:
                    matched_pairs.append((kp1, kp2, m1.distance))

        return matched_pairs

    def _cluster_and_verify_clones(
        self,
        matched_pairs: List[Tuple[cv2.KeyPoint, cv2.KeyPoint, float]],
        img_w: int,
        img_h: int,
    ) -> List[CloneMatch]:
        """Cluster displacement vectors using DBSCAN and verify transformation via RANSAC."""
        displacements: List[Tuple[float, float]] = []
        ordered_pairs: List[Tuple[cv2.KeyPoint, cv2.KeyPoint]] = []

        for kp1, kp2, _ in matched_pairs:
            dx = kp2.pt[0] - kp1.pt[0]
            dy = kp2.pt[1] - kp1.pt[1]

            # Canonicalize orientation so (kp1, kp2) and (kp2, kp1) match the same vector
            if dx < 0 or (abs(dx) < 1e-4 and dy < 0):
                dx, dy = -dx, -dy
                ordered_pairs.append((kp2, kp1))
            else:
                ordered_pairs.append((kp1, kp2))

            displacements.append((dx, dy))

        disp_arr = np.array(displacements, dtype=np.float32)

        # DBSCAN clustering in displacement space
        db = DBSCAN(
            eps=self.config.dbscan_eps,
            min_samples=self.config.dbscan_min_samples,
        )
        labels = db.fit_predict(disp_arr)

        confirmed_clones: List[CloneMatch] = []
        unique_labels = set(labels) - {-1}

        for label in unique_labels:
            cluster_indices = np.where(labels == label)[0]
            if len(cluster_indices) < self.config.dbscan_min_samples:
                continue

            src_pts = np.float32([ordered_pairs[idx][0].pt for idx in cluster_indices])
            dst_pts = np.float32([ordered_pairs[idx][1].pt for idx in cluster_indices])

            # Ensure spatial contiguity: source keypoints must form a cohesive patch
            spatial_db = DBSCAN(eps=60.0, min_samples=self.config.dbscan_min_samples)
            spatial_labels = spatial_db.fit_predict(src_pts)

            for s_lbl in set(spatial_labels) - {-1}:
                sub_indices = np.where(spatial_labels == s_lbl)[0]
                if len(sub_indices) < self.config.dbscan_min_samples:
                    continue

                sub_src = src_pts[sub_indices]
                sub_dst = dst_pts[sub_indices]

                # RANSAC affine transformation verification
                matrix, inliers = cv2.estimateAffinePartial2D(
                    sub_src,
                    sub_dst,
                    method=cv2.RANSAC,
                    ransacReprojThreshold=self.config.ransac_reproj_thresh,
                )

                if inliers is None:
                    continue

                inlier_count = int(np.sum(inliers))
                if inlier_count >= self.config.dbscan_min_samples:
                    inlier_src = sub_src[inliers.ravel() == 1]
                    inlier_dst = sub_dst[inliers.ravel() == 1]
                    orig_inlier_indices = cluster_indices[sub_indices[inliers.ravel() == 1]]

                    # Bounding boxes for source patch
                    sx_min = float(np.min(inlier_src[:, 0]))
                    sy_min = float(np.min(inlier_src[:, 1]))
                    sx_max = float(np.max(inlier_src[:, 0]))
                    sy_max = float(np.max(inlier_src[:, 1]))

                    # Bounding boxes for target patch
                    tx_min = float(np.min(inlier_dst[:, 0]))
                    ty_min = float(np.min(inlier_dst[:, 1]))
                    tx_max = float(np.max(inlier_dst[:, 0]))
                    ty_max = float(np.max(inlier_dst[:, 1]))

                    sx_w, sy_h = sx_max - sx_min, sy_max - sy_min
                    tx_w, ty_h = tx_max - tx_min, ty_max - ty_min

                    # Exclude small single-line font matches (genuine seals/stamps span 2D patch)
                    if (sx_w < 25.0 or sy_h < 25.0) or (tx_w < 25.0 or ty_h < 25.0):
                        continue
                    if (sx_w * sy_h < 600.0) or (tx_w * ty_h < 600.0):
                        continue

                    # Add modest padding (10px) around keypoint envelopes
                    pad = 10.0
                    src_pix = PixelBoundingBox(
                        x=int(max(0, sx_min - pad)),
                        y=int(max(0, sy_min - pad)),
                        width=int(max(10, sx_max - sx_min + 2 * pad)),
                        height=int(max(10, sy_max - sy_min + 2 * pad)),
                    )
                    tgt_pix = PixelBoundingBox(
                        x=int(max(0, tx_min - pad)),
                        y=int(max(0, ty_min - pad)),
                        width=int(max(10, tx_max - tx_min + 2 * pad)),
                        height=int(max(10, ty_max - ty_min + 2 * pad)),
                    )

                    src_norm = BoundingBox(
                        x1=max(0.0, src_pix.x / img_w),
                        y1=max(0.0, src_pix.y / img_h),
                        x2=min(1.0, (src_pix.x + src_pix.width) / img_w),
                        y2=min(1.0, (src_pix.y + src_pix.height) / img_h),
                    )
                    tgt_norm = BoundingBox(
                        x1=max(0.0, tgt_pix.x / img_w),
                        y1=max(0.0, tgt_pix.y / img_h),
                        x2=min(1.0, (tgt_pix.x + tgt_pix.width) / img_w),
                        y2=min(1.0, (tgt_pix.y + tgt_pix.height) / img_h),
                    )

                    mean_dx = float(np.mean([displacements[idx][0] for idx in orig_inlier_indices]))
                    mean_dy = float(np.mean([displacements[idx][1] for idx in orig_inlier_indices]))
                    conf = min(1.0, 0.50 + 0.05 * inlier_count)

                    confirmed_clones.append(
                        CloneMatch(
                            source_bbox=src_norm,
                            target_bbox=tgt_norm,
                            source_pixel_bbox=src_pix,
                            target_pixel_bbox=tgt_pix,
                            inlier_count=inlier_count,
                            confidence=round(conf, 3),
                            displacement_vector=(round(mean_dx, 1), round(mean_dy, 1)),
                        )
                    )

        return confirmed_clones
