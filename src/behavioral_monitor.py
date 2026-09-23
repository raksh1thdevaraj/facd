"""
Admin Behavioral Anomaly Monitor (Khormi et al., IEEE 2026).
Monitors institutional registrar access logs to flag internal certificate fraud
and unauthorized issuance attempts before certificates are recorded on ledger.
Uses: models/behavioral_fraud_model.pkl
"""

import os
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from src.data_loader import is_campus_ip, is_off_hours


class BehavioralMonitor:
    """
    Pre-issuance registrar behavior anomaly detection engine.
    Adheres to Khormi et al. (IEEE 2026).
    """

    def __init__(self, model_path: str = "models/behavioral_fraud_model.pkl"):
        self.model_path = model_path
        self.model_bundle = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.model_bundle = pickle.load(f)
            print(f"[*] BehavioralMonitor loaded model from: {self.model_path}")
        else:
            print(f"[!] Warning: Model file not found at {self.model_path}")

    def evaluate_event(
        self,
        timestamp: str,
        source_ip: str,
        device_type: str,
        location: str,
        action: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate single registrar action event for pre-issuance fraud risks.
        """
        if self.model_bundle is None:
            return {
                "user_id": user_id or "ANONYMOUS",
                "timestamp": timestamp,
                "is_anomalous": False,
                "fraud_probability": 0.0,
                "threat_level": "NORMAL",
                "risk_score": 0.0,
                "flags": ["Model uninitialized"]
            }

        model = self.model_bundle["model"]
        scaler = self.model_bundle["scaler"]
        encoder = self.model_bundle["encoder"]

        off_hr = is_off_hours(timestamp)
        campus_ip = is_campus_ip(source_ip)

        cat_df = pd.DataFrame(
            [[device_type, location, action]],
            columns=["device_type", "location", "action"]
        )
        cat_encoded = encoder.transform(cat_df)

        X_raw = np.hstack([[off_hr, campus_ip], cat_encoded.flatten()]).reshape(1, -1)
        X_scaled = scaler.transform(X_raw)

        prob = float(model.predict_proba(X_scaled)[0, 1])
        is_anomalous = bool(prob >= 0.5)

        # Classify threat level
        flags = []
        if off_hr:
            flags.append("Off-hours issuance activity (11:00 PM - 5:00 AM)")
        if not campus_ip:
            flags.append("External / unverified non-campus IP address")
        if action in ["MODIFY_RECORD", "DELETE_RECORD", "UNAUTHORIZED_ISSUE", "BULK_EXPORT"]:
            flags.append(f"High-risk operational privilege action: {action}")
        if device_type in ["Mobile_Browser", "Unknown_Tablet", "Tor_Browser", "Linux_Curl_Bot"]:
            flags.append(f"Unfamiliar endpoint hardware: {device_type}")

        if prob >= 0.80 or (off_hr and not campus_ip):
            threat_level = "CRITICAL"
        elif prob >= 0.40 or off_hr or not campus_ip:
            threat_level = "ELEVATED"
        else:
            threat_level = "NORMAL"

        return {
            "user_id": user_id or "REGISTRAR_STAFF",
            "timestamp": timestamp,
            "source_ip": source_ip,
            "device_type": device_type,
            "location": location,
            "action": action,
            "is_anomalous": is_anomalous,
            "fraud_probability": round(prob, 4),
            "risk_score": round(prob * 100.0, 1),
            "threat_level": threat_level,
            "flags": flags,
            "recommended_action": "BLOCK_AND_AUDIT" if threat_level == "CRITICAL" else ("FLAG_FOR_REVIEW" if threat_level == "ELEVATED" else "ALLOW")
        }

    def evaluate_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate a sequence or stream of access events."""
        return [
            self.evaluate_event(
                timestamp=e.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                source_ip=e.get("source_ip", "127.0.0.1"),
                device_type=e.get("device_type", "Desktop_Workstation"),
                location=e.get("location", "Registrar_Office"),
                action=e.get("action", "ISSUE_CERTIFICATE"),
                user_id=e.get("user_id") or e.get("masked_user")
            )
            for e in events
        ]


# Singleton instance
_global_monitor: Optional[BehavioralMonitor] = None

def get_behavioral_monitor() -> BehavioralMonitor:
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = BehavioralMonitor()
    return _global_monitor
