"""
Unified Multi-Modal Certificate Fraud Detection & Verification Engine.
Fuses:
1. Behavioral Issuance Anomaly Analysis (Khormi et al., IEEE 2026)
2. Lightweight Visual & Alignment Tamper Detection (MobileNetV2, IEEE 2026)
3. Structural SSIM & Edge Integrity Analysis (DIAR-AI, Anandamurugan et al., IEEE 2026)
4. Cryptographic QR Decoding & Domain Whitelist Cross-Verification
Target: Fast CPU/edge inference (< 250ms per certificate).
"""

import os
import sys
import glob
import time
import pickle
from typing import Dict, Any, Optional, Union
import numpy as np
import cv2
import torch
import torch.nn as nn
from torchvision.models import mobilenet_v2

# Prevent Windows console UnicodeEncodeError
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from src.deterministic_checks import (
    verify_template_alignment,
    decode_qr_code,
    inspect_domain_legitimacy,
    cross_verify_qr_with_text,
    run_deterministic_verification
)
from src.data_loader import is_campus_ip, is_off_hours


class MobileNetTamperDetector(nn.Module):
    """Head matching train_visual_forensics.py."""
    def __init__(self, freeze_base_layers: int = 14):
        super().__init__()
        base = mobilenet_v2(weights=None)
        self.features = base.features
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(p=0.3),
            nn.Linear(1280, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        out = self.head(feat)
        return out.squeeze(-1)


class UnifiedForensicPipeline:
    """
    End-to-End Multi-Modal Verification Pipeline.
    Evaluates Behavioral, Visual Forensics, Structural Alignment, and QR/URL integrity.
    """

    def __init__(
        self,
        behavioral_model_path: str = "models/behavioral_fraud_model.pkl",
        visual_model_path: str = "models/visual_tamper_mobilenet.pt",
        templates_dir: str = "datasets/templates",
        device: str = "cpu"
    ):
        self.device = torch.device(device)
        self.templates_dir = templates_dir

        # 1. Load Behavioral Model
        self.behavioral_bundle = None
        if os.path.exists(behavioral_model_path):
            with open(behavioral_model_path, "rb") as f:
                self.behavioral_bundle = pickle.load(f)
            print(f"[*] Loaded Behavioral Model from: {behavioral_model_path}")
        else:
            print(f"[!] Warning: Behavioral model not found at {behavioral_model_path}")

        # 2. Load Visual Tamper Detector
        self.visual_threshold = 0.5
        if os.path.exists(visual_model_path):
            self.visual_model = MobileNetTamperDetector()
            checkpoint = torch.load(visual_model_path, map_location=self.device)
            state_dict = checkpoint["state_dict"] if isinstance(checkpoint, dict) and "state_dict" in checkpoint else checkpoint
            self.visual_threshold = float(checkpoint.get("threshold", 0.5)) if isinstance(checkpoint, dict) else 0.5
            self.visual_model.load_state_dict(state_dict)
            self.visual_model.to(self.device)
            self.visual_model.eval()
            print(f"[*] Loaded Visual Tamper Detector from: {visual_model_path} (Decision Threshold: {self.visual_threshold:.2f})")
        else:
            print(f"[!] Warning: Visual model not found at {visual_model_path}")

        # 3. Preload and precompute reference templates for sub-50ms deterministic checks
        self.preloaded_templates = []
        if os.path.exists(self.templates_dir):
            for f in glob.glob(os.path.join(self.templates_dir, "*.*")):
                if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg"]:
                    img = cv2.imread(f)
                    if img is not None:
                        t_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA)
                        t_gray = cv2.cvtColor(t_resized, cv2.COLOR_BGR2GRAY)
                        t_blur = cv2.GaussianBlur(t_gray, (3, 3), 0)
                        e_ref = cv2.Canny(t_gray, 100, 200)
                        self.preloaded_templates.append((os.path.basename(f), t_blur, e_ref))
        print(f"[*] Preloaded & cached {len(self.preloaded_templates)} reference templates into memory")

    def evaluate_behavior(
        self,
        timestamp: str,
        source_ip: str,
        device_type: str,
        location: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Evaluate issuance event behavior according to Khormi et al. (IEEE 2026).
        Features: off_hours, is_campus_ip, device_type, location, action.
        """
        if self.behavioral_bundle is None:
            return {"is_suspicious": False, "fraud_probability": 0.0, "status": "NO_MODEL"}

        model = self.behavioral_bundle["model"]
        scaler = self.behavioral_bundle["scaler"]
        encoder = self.behavioral_bundle["encoder"]

        # Feature engineering
        off_hr = is_off_hours(timestamp)
        campus_ip = is_campus_ip(source_ip)

        # Categorical encoding using named DataFrame
        import pandas as pd
        cat_df = pd.DataFrame(
            [[device_type, location, action]],
            columns=["device_type", "location", "action"]
        )
        cat_encoded = encoder.transform(cat_df)

        # Assemble and scale
        X_raw = np.hstack([[off_hr, campus_ip], cat_encoded.flatten()]).reshape(1, -1)
        X_scaled = scaler.transform(X_raw)

        fraud_prob = float(model.predict_proba(X_scaled)[0, 1])
        is_suspicious = bool(fraud_prob >= 0.5)

        return {
            "is_suspicious": is_suspicious,
            "fraud_probability": round(fraud_prob, 4),
            "off_hours_flag": bool(off_hr == 1),
            "campus_ip_flag": bool(campus_ip == 1),
            "decision": "REVIEW" if is_suspicious else "LEGITIMATE"
        }

    def evaluate_visual_tampering(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate visual tampering using lightweight MobileNetV2 classifier.
        Target: < 100ms CPU latency.
        """
        if self.visual_model is None:
            return {"is_tampered": False, "tamper_probability": 0.0, "status": "NO_MODEL"}

        # Resize to 224x224 and normalize
        resized = cv2.resize(image_bgr, (224, 224), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = torch.tensor(rgb / 255.0, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.visual_model(tensor)
            prob = float(torch.sigmoid(logits).cpu().item())

        is_tampered = bool(prob >= self.visual_threshold)
        return {
            "is_tampered": is_tampered,
            "tamper_probability": round(prob, 4),
            "confidence": round(prob if is_tampered else (1.0 - prob), 4),
            "verdict": "TAMPERED" if is_tampered else "PRISTINE"
        }

    def verify_certificate(
        self,
        image_input: Union[str, np.ndarray],
        issuance_log: Optional[Dict[str, str]] = None,
        extracted_text: str = "",
        reference_template: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Full Multi-Modal Verification:
        1. Behavioral log inspection (Khormi et al.)
        2. Visual tamper detection (MobileNetV2)
        3. Structural SSIM & Edge verification (DIAR-AI)
        4. QR code & domain whitelist inspection
        """
        start_time = time.perf_counter()

        # Load image if file path
        if isinstance(image_input, str):
            image_bgr = cv2.imread(image_input)
            if image_bgr is None:
                raise ValueError(f"Could not read image file at {image_input}")
            img_path = image_input
        else:
            image_bgr = image_input
            img_path = "in_memory_image"

        # 1. Behavioral Check
        behavior_res = None
        if issuance_log:
            behavior_res = self.evaluate_behavior(
                timestamp=issuance_log.get("timestamp", "2026-03-01 12:00:00"),
                source_ip=issuance_log.get("source_ip", "10.10.1.1"),
                device_type=issuance_log.get("device_type", "Desktop_Workstation"),
                location=issuance_log.get("location", "Registrar_Office"),
                action=issuance_log.get("action", "ISSUE_CERTIFICATE")
            )

        # 2. Visual Tamper Detection (MobileNetV2)
        visual_res = self.evaluate_visual_tampering(image_bgr)

        # 3. Deterministic Verification (SSIM + Edge Alignment + QR Whitelist + String Matching)
        deterministic_res = run_deterministic_verification(
            image_bgr=image_bgr,
            certificate_text=extracted_text,
            template_img=reference_template,
            templates_dir=self.templates_dir,
            preloaded_templates=self.preloaded_templates
        )

        # 4. Multi-Modal Fusion Decision
        # Rejection rules:
        # - High visual tampering probability (>= 0.70)
        # - Template SSIM failure (< 0.85) when template is matched
        # - Suspicious behavioral anomaly (if log provided)
        # - Domain fraud in QR
        flags = []
        if visual_res.get("is_tampered", False):
            flags.append(f"Visual tampering detected ({visual_res['tamper_probability']:.1%})")

        align_info = deterministic_res.get("alignment", {})
        if align_info.get("matched_template") and not align_info.get("verified", True):
            if not align_info.get("ssim_passed", True):
                flags.append(f"SSIM failed ({align_info.get('ssim_score')} < {align_info.get('ssim_threshold')})")
            if not align_info.get("edge_passed", True):
                flags.append(f"Edge difference failed ({align_info.get('edge_diff_ratio')} > {align_info.get('edge_diff_threshold')})")

        if behavior_res and behavior_res.get("is_suspicious", False):
            flags.append(f"Behavioral anomaly flagged (Fraud Prob: {behavior_res['fraud_probability']:.1%})")

        qr_info = deterministic_res.get("qr_inspection", {})
        if qr_info.get("has_qr", False) and not qr_info.get("verified", True):
            flags.append("QR domain accreditation failed")

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0

        is_authentic = len(flags) == 0
        overall_status = "AUTHENTIC" if is_authentic else "FRAUDULENT / TAMPERED"

        return {
            "image_source": img_path,
            "overall_status": overall_status,
            "is_authentic": is_authentic,
            "rejection_flags": flags,
            "behavioral_analysis": behavior_res,
            "visual_forensics": visual_res,
            "structural_alignment": align_info,
            "qr_and_domain": qr_info,
            "latency_ms": round(total_latency_ms, 2),
            "target_latency_met": bool(total_latency_ms < 250.0)
        }


if __name__ == "__main__":
    pipeline = UnifiedForensicPipeline()
    # Test on a sample certificate
    sample_imgs = glob.glob("datasets/synthetic_manipulated/genuine/*.png")
    if sample_imgs:
        res = pipeline.verify_certificate(
            image_input=sample_imgs[0],
            issuance_log={
                "timestamp": "2026-03-01 10:15:00",
                "source_ip": "10.10.2.14",
                "device_type": "Desktop_Workstation",
                "location": "Registrar_Office",
                "action": "ISSUE_CERTIFICATE"
            }
        )
        print("Verification Result:", res)
