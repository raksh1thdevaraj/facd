"""Final Decision Engine for Course Certificate Authenticity Verification.

Fuses multi-modal verification signals:
- QR code detection and decoding
- Safe URL verification & issuer domain trust
- Cross-modal online record vs OCR field comparison
- Document pixel forensics (ELA, noise, copy-move)
- Signature & seal analysis
- ML fraud risk prediction

Determines the final verification status:
- VERIFIED (Green)
- SUSPICIOUS (Yellow)
- FRAUDULENT (Red)
- UNVERIFIED (Gray)
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

from app.schemas.course_certificate import (
    CourseComparisonResult,
    CourseForensicResult,
    CourseQRResult,
    CourseSealSignatureResult,
    CourseURLVerificationResult,
    CourseVerificationDecision,
    CourseVerificationStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path("ml/models/course_cert_classifier.joblib")


class CourseDecisionEngine:
    """Multi-Signal Decision Fusion Engine for Course Certificates."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.ml_pipeline = None
        self.feature_names: list[str] = []
        self._load_model()

    def _load_model(self) -> None:
        if self.model_path.exists():
            try:
                payload = joblib.load(self.model_path)
                self.ml_pipeline = payload.get("pipeline")
                self.feature_names = payload.get("feature_names", [])
                logger.info("Loaded course certificate ML classifier from %s", self.model_path)
            except Exception as e:
                logger.warning("Could not load ML classifier from %s: %s", self.model_path, e)
        else:
            logger.info("ML model not found at %s. Using rule-based fallback.", self.model_path)

    def extract_feature_vector(
        self,
        ocr_confidence: float,
        qr_result: CourseQRResult,
        url_result: CourseURLVerificationResult,
        comparison_result: CourseComparisonResult,
        forensic_result: CourseForensicResult,
        seal_sig_result: CourseSealSignatureResult,
    ) -> list[float]:
        """Convert multi-signal results into 14-D feature vector for the ML model."""
        qr_detected = 1.0 if qr_result.qr_detected else 0.0
        qr_decoded = 1.0 if qr_result.qr_decoded else 0.0
        url_valid_syntax = 1.0 if url_result.is_valid_url else 0.0
        issuer_trusted = 1.0 if url_result.is_known_issuer else 0.0
        domain_match = 1.0 if url_result.domain_match else 0.0
        online_available = (
            1.0
            if (comparison_result.online_record and comparison_result.online_record.is_available)
            else 0.0
        )

        tampering_prob = forensic_result.tampering_probability

        sig_score = seal_sig_result.signature_score if seal_sig_result else 0.8
        seal_score = seal_sig_result.seal_score if seal_sig_result else 0.8

        return [
            float(np.clip(ocr_confidence, 0.0, 1.0)),
            float(np.clip(tampering_prob, 0.0, 1.0)),
            qr_detected,
            qr_decoded,
            url_valid_syntax,
            issuer_trusted,
            domain_match,
            online_available,
            float(np.clip(comparison_result.name_match_score, 0.0, 1.0)),
            float(np.clip(comparison_result.course_match_score, 0.0, 1.0)),
            float(np.clip(comparison_result.cert_id_match_score, 0.0, 1.0)),
            float(np.clip(comparison_result.date_match_score, 0.0, 1.0)),
            float(np.clip(sig_score, 0.0, 1.0)),
            float(np.clip(seal_score, 0.0, 1.0)),
        ]

    def evaluate(
        self,
        ocr_confidence: float,
        qr_result: CourseQRResult,
        url_result: CourseURLVerificationResult,
        comparison_result: CourseComparisonResult,
        forensic_result: CourseForensicResult,
        seal_sig_result: CourseSealSignatureResult | None = None,
    ) -> CourseVerificationDecision:
        """Fuse all signals into an explainable verification decision."""
        sig_result = seal_sig_result or CourseSealSignatureResult(
            signature_detected=False,
            seal_detected=False,
            signature_score=0.7,
            seal_score=0.7,
            details={"status": "not_performed"},
        )

        risk_factors: list[str] = []
        positive_signals: list[str] = []
        reasons: list[str] = []

        # 1. Critical Hard Rules
        # Copied QR Attack Defense: Valid QR grafted onto someone else's certificate
        if comparison_result.copied_qr_detected:
            risk_factors.append(
                "CRITICAL: Copied/transplanted QR code detected. "
                "Online record belongs to different recipient."
            )
            return CourseVerificationDecision(
                status=CourseVerificationStatus.FRAUDULENT,
                overall_authenticity_score=0.05,
                fraud_risk_score=0.98,
                decision_reasons=[
                    "Transplanted QR code attack intercepted. QR verification URL resolves "
                    "to valid issuer record, but recipient name and certificate ID do not match "
                    "document text."
                ],
                risk_factors=risk_factors,
                signal_scores={
                    "online_verification": 0.0,
                    "field_matching": 0.0,
                    "document_integrity": 1.0 - forensic_result.tampering_probability,
                    "qr_verification": 0.2,
                    "domain_trust": url_result.trust_score,
                    "signature_seal": (sig_result.signature_score + sig_result.seal_score) / 2.0,
                },
            )

        # Malicious / SSRF Blocked URL
        if url_result.risk_level == "MALICIOUS":
            risk_factors.append(
                "CRITICAL: Verification URL points to unsafe or internal IP address (SSRF attempt)."
            )
            return CourseVerificationDecision(
                status=CourseVerificationStatus.FRAUDULENT,
                overall_authenticity_score=0.02,
                fraud_risk_score=0.99,
                decision_reasons=[
                    "Verification URL points to suspicious or malicious host "
                    "prohibited by security policy."
                ],
                risk_factors=risk_factors,
                signal_scores={
                    "online_verification": 0.0,
                    "field_matching": 0.0,
                    "document_integrity": 1.0 - forensic_result.tampering_probability,
                    "qr_verification": 0.0,
                    "domain_trust": 0.0,
                    "signature_seal": 0.5,
                },
            )

        # 2. Compute Multi-Signal Subscores
        # Component Weights:
        # Online Verification: 25%
        # Field Matching: 25%
        # Document Integrity: 20%
        # QR Verification: 15%
        # Domain Trust: 10%
        # Signature/Seal: 5%

        # Online Verification Score (0.0 to 1.0)
        online_score = 0.5  # Neutral default if not available
        has_online = (
            comparison_result.online_record and comparison_result.online_record.is_available
        )
        network_unreachable = False

        if has_online:
            online_score = 1.0
            positive_signals.append(
                "Online certificate registry record successfully retrieved and verified."
            )
        elif qr_result.qr_detected and url_result.is_valid_url:
            # QR was found and points to URL, but online record could not be retrieved
            network_unreachable = True
            online_score = 0.5
            risk_factors.append("Issuer online registry could not be reached or query timed out.")
        else:
            online_score = 0.4
            risk_factors.append("No verification QR code or online verification record available.")

        # Field Matching Score (0.0 to 1.0)
        if has_online:
            field_score = comparison_result.overall_match_score
            if field_score >= 0.85:
                positive_signals.append(
                    f"Certificate text closely matches online issuer records "
                    f"({field_score * 100:.1f}% alignment)."
                )
            elif field_score < 0.50:
                risk_factors.append(
                    f"Significant discrepancy between certificate text and online records "
                    f"({field_score * 100:.1f}% alignment)."
                )
        else:
            field_score = min(1.0, ocr_confidence * 1.1)

        # Document Integrity Score (0.0 to 1.0)
        integrity_score = 1.0 - forensic_result.tampering_probability
        if forensic_result.copy_move_detected:
            risk_factors.append("Copy-move duplication detected in document layout.")
        if forensic_result.tampering_probability > 0.60:
            risk_factors.append(
                f"High pixel-level tampering probability detected "
                f"({forensic_result.tampering_probability * 100:.1f}%)."
            )
        elif forensic_result.tampering_probability < 0.20:
            positive_signals.append(
                "Document image forensics indicate uniform compression and pixel integrity."
            )

        # QR Verification Score (0.0 to 1.0)
        if qr_result.qr_detected and qr_result.qr_decoded:
            qr_score = 1.0
            positive_signals.append("Authentic QR code successfully decoded.")
        elif qr_result.qr_detected and not qr_result.qr_decoded:
            qr_score = 0.3
            risk_factors.append("QR code detected on certificate but could not be decoded.")
        else:
            qr_score = 0.5  # Neutral for certificates without QR

        # Domain Trust Score (0.0 to 1.0)
        domain_score = url_result.trust_score
        if url_result.is_known_issuer:
            positive_signals.append(
                "Issued by recognized authoritative provider "
                f"({url_result.resolved_issuer or 'Authoritative'})."
            )
        elif url_result.is_valid_url and not url_result.is_known_issuer:
            risk_factors.append(
                f"Issuer domain '{url_result.domain}' is not in authoritative issuer registry."
            )

        # Signature & Seal Score (0.0 to 1.0)
        sig_seal_score = (sig_result.signature_score + sig_result.seal_score) / 2.0

        # Weighted Fusion
        overall_authenticity = (
            online_score * 0.25
            + field_score * 0.25
            + integrity_score * 0.20
            + qr_score * 0.15
            + domain_score * 0.10
            + sig_seal_score * 0.05
        )
        overall_authenticity = float(np.clip(overall_authenticity, 0.0, 1.0))

        # 3. ML Risk Prediction
        feature_vec = self.extract_feature_vector(
            ocr_confidence=ocr_confidence,
            qr_result=qr_result,
            url_result=url_result,
            comparison_result=comparison_result,
            forensic_result=forensic_result,
            seal_sig_result=sig_result,
        )

        if self.ml_pipeline is not None:
            try:
                X_in = np.array([feature_vec], dtype=np.float32)
                ml_prob = float(self.ml_pipeline.predict_proba(X_in)[0, 1])
            except Exception as e:
                logger.warning("ML prediction failed, falling back to rule-based risk: %s", e)
                ml_prob = 1.0 - overall_authenticity
        else:
            ml_prob = 1.0 - overall_authenticity

        fraud_risk = float(
            np.clip((ml_prob * 0.60) + ((1.0 - overall_authenticity) * 0.40), 0.0, 1.0)
        )

        # 4. Status Determination
        # CRITICAL SPEC RULE: Web accessibility/network issues must NEVER trigger FRAUDULENT
        if network_unreachable:
            if forensic_result.tampering_probability > 0.65 or forensic_result.copy_move_detected:
                status = CourseVerificationStatus.FRAUDULENT
                reasons.append("Document exhibits strong indicators of physical/pixel tampering.")
            else:
                status = CourseVerificationStatus.UNVERIFIED
                reasons.append(
                    "Online verification registry was unreachable or query timed out. "
                    "Document cannot be validated online, but no active pixel tampering was found."
                )
        elif (
            forensic_result.tampering_probability > 0.65
            or forensic_result.copy_move_detected
            or (has_online and field_score < 0.40)
        ):
            status = CourseVerificationStatus.FRAUDULENT
            reasons.append(
                "Document exhibits strong indicators of digital manipulation or "
                "irreconcilable record mismatch."
            )
        elif fraud_risk >= 0.60:
            status = CourseVerificationStatus.FRAUDULENT
            reasons.append("High fraud risk score computed across multi-signal analysis.")
        elif fraud_risk <= 0.25 and overall_authenticity >= 0.75:
            status = CourseVerificationStatus.VERIFIED
            reasons.append(
                "All verification signals confirm certificate authenticity and "
                "consistency with authoritative standards."
            )
        elif not qr_result.qr_detected and not has_online:
            status = CourseVerificationStatus.UNVERIFIED
            reasons.append(
                "Certificate lacks machine-verifiable online credentials "
                "(no valid QR code or registry link)."
            )
        else:
            status = CourseVerificationStatus.SUSPICIOUS
            reasons.append(
                "Moderate discrepancy or inconclusive indicators observed. "
                "Manual review recommended."
            )

        if positive_signals and not reasons:
            reasons.extend(positive_signals[:2])

        return CourseVerificationDecision(
            status=status,
            overall_authenticity_score=round(overall_authenticity, 4),
            fraud_risk_score=round(fraud_risk, 4),
            decision_reasons=reasons,
            risk_factors=risk_factors,
            signal_scores={
                "online_verification": round(online_score, 4),
                "field_matching": round(field_score, 4),
                "document_integrity": round(integrity_score, 4),
                "qr_verification": round(qr_score, 4),
                "domain_trust": round(domain_score, 4),
                "signature_seal": round(sig_seal_score, 4),
            },
        )
