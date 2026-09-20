"""Production service for deep learning visual certificate classification."""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Union

import torch
from PIL import Image
from sqlalchemy.orm import Session

from app.models.ml_prediction import MLPredictionModel
from app.modules.visual_model.embedding_extractor import VisualEmbeddingExtractor
from app.modules.visual_model.gradcam import GradCAMExplainer
from app.modules.visual_model.network import CertificateVisualCNN
from app.modules.visual_model.transforms import get_inference_transforms
from app.schemas.pipeline import MLInferenceOutput
from app.schemas.visual_prediction import VisualPredictionResult

logger = logging.getLogger(__name__)


class VisualCNNService:
    """Production service managing model loading, batch inference, embeddings, and Grad-CAM."""

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        threshold: float = 0.5,
        backbone_name: str = "efficientnet_b0",
    ) -> None:
        self.threshold = threshold
        self.backbone_name = backbone_name
        self.model_version = "visual_cnn_v1.0.0"

        # Determine optimal device with CPU fallback
        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        # Instantiate network
        self.model = CertificateVisualCNN(
            backbone_name=backbone_name,
            pretrained=(model_path is None),
        )

        if model_path:
            m_path = Path(model_path)
            if m_path.exists():
                try:
                    checkpoint = torch.load(m_path, map_location=self.device)
                    state_dict = checkpoint.get("state_dict", checkpoint)
                    self.model.load_state_dict(state_dict)
                    logger.info("Loaded visual CNN checkpoint from %s", m_path)
                except Exception as e:
                    logger.warning(
                        "Could not load checkpoint from %s: %s. Using initialized model.", m_path, e
                    )

        self.model.to(self.device)
        self.model.eval()

        self.transforms = get_inference_transforms()
        self.embedding_extractor = VisualEmbeddingExtractor(self.model, self.device)
        self.gradcam = GradCAMExplainer(self.model, self.device)

    def predict(
        self,
        image_path: Union[str, Path],
        certificate_id: Optional[str] = None,
        generate_gradcam: bool = True,
        output_dir: Optional[Union[str, Path]] = None,
        db_session: Optional[Session] = None,
    ) -> VisualPredictionResult:
        """Run visual tampering prediction, extract 512D embedding, and generate Grad-CAM."""
        start_time = time.perf_counter()
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Certificate image not found: {img_path}")

        cert_id = certificate_id or str(uuid.uuid4())

        # 1. Transform image
        with Image.open(img_path) as pil_img:
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            tensor = self.transforms(pil_img)

        # 2. Forward inference & 512D embedding extraction
        tensor_batch = tensor.unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits, _ = self.model(tensor_batch)
            fake_prob = float(torch.sigmoid(logits[0]).item())

        embedding = self.embedding_extractor.extract(tensor)
        predicted_class = "manipulated" if fake_prob >= self.threshold else "genuine"
        confidence = max(fake_prob, 1.0 - fake_prob)

        # 3. Grad-CAM generation
        gradcam_path: Optional[str] = None
        if generate_gradcam:
            out_dir = Path(output_dir) if output_dir else Path("storage/reports")
            out_dir.mkdir(parents=True, exist_ok=True)
            overlay_dest = out_dir / f"{cert_id}_gradcam_overlay.png"
            try:
                self.gradcam.save_overlay(img_path, overlay_dest, tensor=tensor)
                gradcam_path = str(overlay_dest)
            except Exception as e:
                logger.warning("Grad-CAM generation failed for cert %s: %s", cert_id, e)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        result = VisualPredictionResult(
            certificate_id=cert_id,
            model_version=self.model_version,
            model_type="cnn_visual",
            manipulation_probability=round(fake_prob, 4),
            predicted_class=predicted_class,
            confidence=round(confidence, 4),
            visual_embedding=embedding.tolist(),
            gradcam_heatmap_path=gradcam_path,
            latency_ms=round(latency_ms, 2),
        )

        # 4. Optional DB persistence
        if db_session is not None:
            try:
                db_record = MLPredictionModel(
                    id=str(uuid.uuid4()),
                    certificate_id=cert_id,
                    manipulation_probability=result.manipulation_probability,
                    predicted_class=result.predicted_class,
                    confidence=result.confidence,
                    model_version=result.model_version,
                    model_type=result.model_type,
                    execution_time_ms=result.latency_ms,
                    feature_vector_json={"embedding_dim": len(result.visual_embedding)},
                    feature_contributions_json={"gradcam_path": result.gradcam_heatmap_path},
                )
                db_session.add(db_record)
                db_session.commit()
                db_session.refresh(db_record)
            except Exception as e:
                logger.error("Failed saving visual prediction to DB for cert %s: %s", cert_id, e)
                db_session.rollback()

        return result

    def get_pipeline_output(
        self,
        image_path: Union[str, Path],
        certificate_id: Optional[str] = None,
        generate_gradcam: bool = True,
        output_dir: Optional[Union[str, Path]] = None,
        db_session: Optional[Session] = None,
    ) -> MLInferenceOutput:
        """Convenience method returning canonical SPEC-02 pipeline contract schema."""
        res = self.predict(
            image_path=image_path,
            certificate_id=certificate_id,
            generate_gradcam=generate_gradcam,
            output_dir=output_dir,
            db_session=db_session,
        )
        return res.to_pipeline_output()
