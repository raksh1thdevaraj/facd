"""Deep learning visual tampering classification module."""

from app.modules.visual_model.embedding_extractor import VisualEmbeddingExtractor
from app.modules.visual_model.gradcam import GradCAMExplainer
from app.modules.visual_model.network import CertificateVisualCNN
from app.modules.visual_model.service import VisualCNNService
from app.modules.visual_model.transforms import (
    denormalize_image,
    get_inference_transforms,
    get_train_transforms,
)
from app.schemas.visual_prediction import VisualPredictionResult

__all__ = [
    "CertificateVisualCNN",
    "VisualCNNService",
    "VisualEmbeddingExtractor",
    "GradCAMExplainer",
    "VisualPredictionResult",
    "get_train_transforms",
    "get_inference_transforms",
    "denormalize_image",
]
