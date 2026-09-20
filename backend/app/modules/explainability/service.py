"""Production service for explainability, feature attributions, and spatial overlays."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
from PIL import Image

from app.modules.explainability.coordinate_mapper import CoordinateMapper
from app.modules.explainability.nlg_generator import NLGExplanationGenerator
from app.modules.explainability.shap_explainer import SHAPTabularExplainer
from app.modules.explainability.unified_overlay import UnifiedOverlayRenderer
from app.schemas.decision import FinalVerificationDecision
from app.schemas.explainability import (
    ExplainabilityReport,
    FindingSeverity,
    InteractiveOverlayPayload,
    UnifiedAnomalyBox,
)

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """Orchestrates coordinate mapping, SHAP attribution, NLG synthesis, and visual overlays."""

    def __init__(
        self,
        baseline_model_path: Optional[Union[str, Path]] = "ml/models/baseline_model_v1.joblib",
    ) -> None:
        self.shap_explainer = SHAPTabularExplainer(model_path=baseline_model_path)
        self.overlay_renderer = UnifiedOverlayRenderer()

    def explain_certificate(
        self,
        certificate_id: str,
        raw_image_path: Union[str, Path],
        decision: FinalVerificationDecision,
        tabular_features: np.ndarray,
        text_result: Optional[Any] = None,
        forensic_result: Optional[Any] = None,
        tier_result: Optional[Any] = None,
        record_result: Optional[Any] = None,
        gradcam_path: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> ExplainabilityReport:
        """Generate comprehensive explainability report, visual overlay, and interactive JSON."""
        start_time = time.perf_counter()
        raw_p = Path(raw_image_path)
        if not raw_p.exists():
            raise FileNotFoundError(f"Original certificate image not found at {raw_p}")

        # Get raw dimensions
        with Image.open(raw_p) as img:
            orig_w, orig_h = img.size

        coord_mapper = CoordinateMapper(orig_width=orig_w, orig_height=orig_h)

        # 1. Collect and Map Spatial Anomalies
        spatial_anomalies: List[UnifiedAnomalyBox] = []
        box_idx = 1

        # From Text Consistency (baseline drift, font size mismatch)
        if text_result is not None:
            anomalies = getattr(text_result, "anomalies", [])
            for anom in anomalies:
                bbox = getattr(anom, "bbox", getattr(anom, "bounding_box", None))
                if bbox is not None:
                    # If bbox is normalized [0, 1]
                    if hasattr(bbox, "x1") and hasattr(bbox, "y1"):
                        pbox, nbox = coord_mapper.map_normalized(
                            bbox.x1, bbox.y1, bbox.x2 - bbox.x1, bbox.y2 - bbox.y1
                        )
                    else:
                        pbox = coord_mapper.map_box(
                            getattr(bbox, "x", 50),
                            getattr(bbox, "y", 50),
                            getattr(bbox, "width", 150),
                            getattr(bbox, "height", 30),
                        )
                        nbox = coord_mapper.to_normalized_box(pbox)

                    anom_type = getattr(anom, "type", "Typography")
                    desc = getattr(anom, "description", "Typographical inconsistency")
                    spatial_anomalies.append(
                        UnifiedAnomalyBox(
                            id=f"box_{box_idx}",
                            category="TEXT",
                            severity=FindingSeverity.MAJOR,
                            box=pbox,
                            normalized_box=nbox,
                            label=f"Text: {anom_type}",
                            description=str(desc),
                            color="#D50000",
                        )
                    )
                    box_idx += 1

        # From Forensics (Copy-Move cloned regions)
        if forensic_result is not None:
            copy_move = getattr(forensic_result, "copy_move", None)
            if copy_move and getattr(copy_move, "cloned_regions_count", 0) > 0:
                regions = getattr(copy_move, "regions", [])
                for reg in regions:
                    bbox = getattr(reg, "bbox", None)
                    if bbox:
                        pbox = coord_mapper.map_box(
                            getattr(bbox, "x", 100),
                            getattr(bbox, "y", 100),
                            getattr(bbox, "width", 80),
                            getattr(bbox, "height", 80),
                        )
                        nbox = coord_mapper.to_normalized_box(pbox)
                        spatial_anomalies.append(
                            UnifiedAnomalyBox(
                                id=f"box_{box_idx}",
                                category="CLONE",
                                severity=FindingSeverity.CRITICAL,
                                box=pbox,
                                normalized_box=nbox,
                                label="Cloned Patch",
                                description="Replicated pixel patch matching another region",
                                color="#00E5FF",
                            )
                        )
                        box_idx += 1

        # 2. Compute Local SHAP Attributions
        top_features = self.shap_explainer.explain(tabular_features, top_k=6)

        # 3. Natural Language Generation (NLG)
        primary_rationale = NLGExplanationGenerator.generate_summary_paragraph(decision)
        finding_bullets = NLGExplanationGenerator.generate_finding_bullets(
            decision=decision,
            text_result=text_result,
            forensic_result=forensic_result,
            tier_result=tier_result,
            record_result=record_result,
        )

        # 4. Interactive Overlay JSON Payload
        interactive_payload = InteractiveOverlayPayload(
            certificate_id=certificate_id,
            image_width=orig_w,
            image_height=orig_h,
            anomalies=spatial_anomalies,
        )

        # 5. Render Unified Visual Overlay Image
        out_dir = Path(output_dir) if output_dir else Path("storage/reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        overlay_path = out_dir / f"{certificate_id}_unified_evidence.png"

        try:
            self.overlay_renderer.render(
                raw_image_path=raw_p,
                output_path=overlay_path,
                anomalies=spatial_anomalies,
                heatmap_overlay_path=gradcam_path,
            )
            overlay_file_str: Optional[str] = str(overlay_path)
        except Exception as e:
            logger.warning("Unified visual overlay rendering failed: %s", e)
            overlay_file_str = None

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ExplainabilityReport(
            certificate_id=certificate_id,
            primary_verdict_rationale=primary_rationale,
            key_findings=finding_bullets,
            top_contributing_features=top_features,
            spatial_anomalies=spatial_anomalies,
            unified_overlay_path=overlay_file_str,
            interactive_overlay=interactive_payload,
            execution_time_ms=round(latency_ms, 2),
        )
