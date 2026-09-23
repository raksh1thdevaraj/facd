"""
Data Loader & Preprocessing Pipeline for Academic Certificate Fraud Detection.
Implements data ingestion, feature engineering, SMOTE balancing, and dual-stream
visual forensics preprocessing adhering to:
- Khormi et al. (IEEE 2026): Behavioral Fraud Detection from Access Logs
- Anandamurugan et al. (IEEE 2026): DIAR-AI Visual and Structural Verification
"""

import os
import io
import re
import glob
import ipaddress
import numpy as np
import pandas as pd
from PIL import Image
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from imblearn.over_sampling import SMOTE


# ==============================================================================
# 1. TABULAR ACCESS / ISSUANCE LOG DATA LOADER
# ==============================================================================

CAMPUS_SUBNETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

def is_campus_ip(ip_str: str) -> int:
    """Determine if IP address belongs to campus or trusted internal subnet."""
    try:
        ip = ipaddress.ip_address(str(ip_str).strip())
        for subnet in CAMPUS_SUBNETS:
            if ip in subnet:
                return 1
        return 0
    except ValueError:
        # If masked or invalid, check for known campus prefix patterns
        s = str(ip_str).lower()
        if "campus" in s or "internal" in s or s.startswith("10.") or s.startswith("192.168."):
            return 1
        return 0

def is_off_hours(timestamp_val) -> int:
    """Flag activity between 11:00 PM (23:00) and 5:00 AM (05:00)."""
    try:
        dt = pd.to_datetime(timestamp_val)
        hour = dt.hour
        # Off hours: 23, 0, 1, 2, 3, 4
        if hour >= 23 or hour < 5:
            return 1
        return 0
    except Exception:
        return 0

def generate_synthetic_access_logs(
    num_samples: int = 5000,
    fraud_ratio: float = 0.088,
    random_state: int = 42,
    output_path: str = "datasets/tabular/issuance_access_logs.csv"
) -> pd.DataFrame:
    """
    Synthesize 5,000 access log entries following Khormi et al. (IEEE 2026 Table II, III).
    Attributes: timestamp, masked_user, source_ip, action, location, device_type, target.
    Target: 0 for Legitimate, 1 for Fraudulent (<10% fraud instances).
    """
    np.random.seed(random_state)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    num_fraud = int(num_samples * fraud_ratio)
    num_legit = num_samples - num_fraud

    # Legitimate distributions
    legit_users = [f"STAFF_{i:04d}" for i in range(1, 45)]
    legit_ips = [f"10.10.{np.random.randint(1, 20)}.{np.random.randint(1, 250)}" for _ in range(100)] + \
                [f"192.168.1.{np.random.randint(2, 200)}" for _ in range(50)]
    legit_locations = ["Registrar_Office", "Examination_Branch", "Academic_Affairs_Hall", "Campus_Admin_Building"]
    legit_devices = ["Desktop_Workstation", "University_Terminal"]
    legit_actions = ["LOGIN", "VIEW_RECORD", "ISSUE_CERTIFICATE", "GENERATE_HASH", "VERIFY_RECORD"]

    # Fraudulent distributions
    fraud_users = [f"COMPROMISED_{i:03d}" for i in range(1, 15)] + [f"STAFF_{i:04d}" for i in [7, 14, 22]]
    fraud_ips = [f"198.51.100.{np.random.randint(1, 254)}" for _ in range(30)] + \
                [f"203.0.113.{np.random.randint(1, 254)}" for _ in range(30)] + \
                [f"185.220.101.{np.random.randint(1, 254)}" for _ in range(20)]  # Tor exit nodes / proxies
    fraud_locations = ["Off_Campus_Unknown", "Foreign_Proxy", "Unregistered_VPN", "Residential_ISP"]
    fraud_devices = ["Mobile_Browser", "Unknown_Tablet", "Tor_Browser", "Linux_Curl_Bot"]
    fraud_actions = ["MODIFY_RECORD", "DELETE_RECORD", "BULK_EXPORT", "UNAUTHORIZED_ISSUE", "LOGIN"]

    records = []

    # Generate Legitimate Records (Target = 0)
    # Working hours: 08:00 to 18:00
    base_date = pd.Timestamp("2026-03-01 08:30:00")
    for i in range(num_legit):
        day_offset = np.random.randint(0, 120)
        hour = np.random.randint(8, 19)
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        ts = base_date + pd.Timedelta(days=day_offset, hours=hour - 8, minutes=minute, seconds=second)

        # Rare legitimate after-hours check (e.g. 1% accidental overtime)
        if np.random.rand() < 0.015:
            ts = ts.replace(hour=np.random.choice([23, 0, 4]))

        user = np.random.choice(legit_users)
        ip = np.random.choice(legit_ips)
        loc = np.random.choice(legit_locations, p=[0.45, 0.35, 0.15, 0.05])
        dev = np.random.choice(legit_devices, p=[0.85, 0.15])
        act = np.choice(legit_actions, p=[0.20, 0.40, 0.25, 0.10, 0.05]) if hasattr(np, 'choice') else np.random.choice(legit_actions, p=[0.20, 0.40, 0.25, 0.10, 0.05])

        records.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "masked_user": user,
            "source_ip": ip,
            "action": act,
            "location": loc,
            "device_type": dev,
            "target": 0
        })

    # Generate Fraudulent Records (Target = 1)
    # Highlighted Paper Scenario: Issued at 02:15 AM, off-campus, unfamiliar device
    for i in range(num_fraud):
        day_offset = np.random.randint(0, 120)
        # ~85% of fraud happens in off-hours (23:00 to 05:00)
        if np.random.rand() < 0.88:
            hour = np.random.choice([23, 0, 1, 2, 3, 4])
            # Specifically inject 02:15 AM instances matching the paper's case study
            if np.random.rand() < 0.25:
                hour = 2
                minute = 15
            else:
                minute = np.random.randint(0, 60)
        else:
            hour = np.random.randint(8, 18)
            minute = np.random.randint(0, 60)

        ts = base_date + pd.Timedelta(days=day_offset, hours=hour - 8, minutes=minute, seconds=np.random.randint(0, 60))
        user = np.random.choice(fraud_users)
        ip = np.random.choice(fraud_ips)
        loc = np.random.choice(fraud_locations, p=[0.50, 0.25, 0.15, 0.10])
        dev = np.random.choice(fraud_devices, p=[0.45, 0.30, 0.15, 0.10])
        act = np.random.choice(fraud_actions, p=[0.35, 0.20, 0.15, 0.25, 0.05])

        records.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "masked_user": user,
            "source_ip": ip,
            "action": act,
            "location": loc,
            "device_type": dev,
            "target": 1
        })

    df = pd.DataFrame(records).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Generated {len(df)} synthetic access logs -> {output_path} (Fraud ratio: {df['target'].mean():.2%})")
    return df


class TabularDataLoader:
    """Discovers, parses, extracts features, and balances issuance access logs."""

    def __init__(self, search_dir: str = "datasets"):
        self.search_dir = search_dir
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False

    def find_tabular_file(self) -> str:
        """Locate existing access log or tabular issuance file."""
        candidates = glob.glob(os.path.join(self.search_dir, "**", "*.csv"), recursive=True) + \
                     glob.glob(os.path.join(self.search_dir, "**", "*.parquet"), recursive=True) + \
                     glob.glob(os.path.join(self.search_dir, "**", "*.json"), recursive=True)

        target_keywords = ["access", "log", "issuance", "audit", "behavior"]
        for c in candidates:
            basename = os.path.basename(c).lower()
            if any(k in basename for k in target_keywords):
                return c

        default_target = os.path.join("datasets", "tabular", "issuance_access_logs.csv")
        if not os.path.exists(default_target):
            generate_synthetic_access_logs(num_samples=5000, output_path=default_target)
        return default_target

    def load_raw_data(self, file_path: str = None) -> pd.DataFrame:
        if file_path is None or not os.path.exists(file_path):
            file_path = self.find_tabular_file()

        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_json(file_path)

        # Standardize column naming
        col_map = {c: c.strip().lower() for c in df.columns}
        df = df.rename(columns=col_map)
        return df

    def extract_features(self, df: pd.DataFrame, fit_preprocessors: bool = True) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """
        Extract behavioral features per Khormi et al. (Table IV):
        - IP Address -> is_campus_ip
        - Off_hours -> derived from timestamp
        - Location -> one-hot encoded
        - Device -> one-hot encoded
        - Action -> one-hot encoded
        """
        data = df.copy()

        # 1. Feature: off_hours
        if "timestamp" in data.columns:
            data["off_hours"] = data["timestamp"].apply(is_off_hours)
        elif "off_hours" not in data.columns:
            data["off_hours"] = 0

        # 2. Feature: is_campus_ip
        ip_col = "source_ip" if "source_ip" in data.columns else [c for c in data.columns if "ip" in c][0] if any("ip" in c for c in data.columns) else None
        if ip_col:
            data["is_campus_ip"] = data[ip_col].apply(is_campus_ip)
        elif "is_campus_ip" not in data.columns:
            data["is_campus_ip"] = 1

        # 3. Categorical columns
        cat_cols = []
        for candidate in ["device_type", "device", "location", "action"]:
            if candidate in data.columns:
                cat_cols.append(candidate)

        numeric_feats = data[["off_hours", "is_campus_ip"]].values.astype(np.float32)

        if fit_preprocessors:
            cat_feats = self.encoder.fit_transform(data[cat_cols])
            cat_feat_names = list(self.encoder.get_feature_names_out(cat_cols))
            self.feature_names = ["off_hours", "is_campus_ip"] + cat_feat_names
            X_all = np.hstack([numeric_feats, cat_feats])
            X_scaled = self.scaler.fit_transform(X_all)
            self.is_fitted = True
        else:
            if not self.is_fitted:
                raise RuntimeError("Preprocessor must be fitted first!")
            cat_feats = self.encoder.transform(data[cat_cols])
            X_all = np.hstack([numeric_feats, cat_feats])
            X_scaled = self.scaler.transform(X_all)

        # Target label
        target_col = None
        for cand in ["target", "label", "fraud", "is_fraud"]:
            if cand in data.columns:
                target_col = cand
                break

        if target_col is not None:
            y = data[target_col].values.astype(np.int64)
        else:
            y = np.zeros(len(data), dtype=np.int64)

        return X_scaled, y, self.feature_names

    def get_train_test_data(
        self,
        test_size: float = 0.2,
        apply_smote: bool = True,
        random_state: int = 42
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Load data, extract features, split, and apply SMOTE to train set."""
        df = self.load_raw_data()
        X, y, feature_names = self.extract_features(df, fit_preprocessors=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=random_state
        )

        if apply_smote:
            sm = SMOTE(random_state=random_state)
            X_train, y_train = sm.fit_resample(X_train, y_train)
            print(f"[OK] Applied SMOTE: Train shape {X_train.shape} (Positives: {(y_train==1).sum()}, Negatives: {(y_train==0).sum()})")

        return X_train, X_test, y_train, y_test, feature_names


# ==============================================================================
# 2. CERTIFICATE IMAGE FORENSICS & DUAL-STREAM DATASET
# ==============================================================================

def compute_ela_and_canny(
    image_bgr: np.ndarray,
    jpeg_quality: int = 90,
    canny_low: int = 100,
    canny_high: int = 200
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Error Level Analysis (ELA) and Canny Edge Map for forensic stream.
    Stream B represents forensic cues (compression artifacts & structural edges).
    """
    # 1. Error Level Analysis
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
    _, enc_img = cv2.imencode(".jpg", image_bgr, encode_param)
    resaved_bgr = cv2.imdecode(enc_img, cv2.IMREAD_COLOR)

    # Absolute difference scaled
    diff = cv2.absdiff(image_bgr, resaved_bgr).astype(np.float32)
    # Scale multiplier (10x) for visibility and normalized to [0, 1]
    ela_rgb = np.clip(diff * 10.0 / 255.0, 0.0, 1.0)
    ela_gray = cv2.cvtColor((ela_rgb * 255.0).astype(np.uint8), cv2.COLOR_BGR2GRAY) / 255.0

    # 2. Canny Edge Map
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    canny_map = cv2.Canny(gray, canny_low, canny_high) / 255.0

    # 3. Composite 3-channel Forensic Representation
    # Channel 0: ELA Gray, Channel 1: Canny Edge, Channel 2: Average Fusion
    forensic_3ch = np.stack([ela_gray, canny_map, (ela_gray + canny_map) / 2.0], axis=-1).astype(np.float32)

    return ela_rgb, canny_map, forensic_3ch


class CertificateImageDataset(Dataset):
    """
    Multi-modal PyTorch Dataset scanning local datasets for certificate forensic analysis.
    Assigns:
    - 0: Authentic / Pristine
    - 1: Forged / Tampered / Spliced
    """

    def __init__(
        self,
        samples: list[tuple[str, int]],
        target_size: tuple[int, int] = (224, 224),
        augment: bool = False,
        return_forensic: bool = False
    ):
        self.samples = samples
        self.target_size = target_size
        self.augment = augment
        self.return_forensic = return_forensic

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        # Load image
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            # Fallback to black canvas
            img_bgr = np.zeros((self.target_size[1], self.target_size[0], 3), dtype=np.uint8)

        # Resize
        img_bgr = cv2.resize(img_bgr, self.target_size, interpolation=cv2.INTER_AREA)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Stream A: Standard RGB normalized to [0, 1], CHW
        rgb_norm = (img_rgb / 255.0).astype(np.float32).transpose(2, 0, 1)

        # Optional simple data augmentation (horizontal flip)
        if self.augment and np.random.rand() > 0.5:
            rgb_norm = np.flip(rgb_norm, axis=2).copy()

        # Stream B: Forensic ELA + Canny Edge Map, CHW
        if self.return_forensic:
            _, _, forensic_3ch = compute_ela_and_canny(img_bgr)
            forensic_norm = forensic_3ch.transpose(2, 0, 1)
            if self.augment and np.random.rand() > 0.5:
                forensic_norm = np.flip(forensic_norm, axis=2).copy()
            forensic_tensor = torch.tensor(forensic_norm, dtype=torch.float32)
        else:
            forensic_tensor = torch.zeros((3, self.target_size[1], self.target_size[0]), dtype=torch.float32)

        return (
            torch.tensor(rgb_norm, dtype=torch.float32),
            forensic_tensor,
            torch.tensor(label, dtype=torch.float32)
        )


def discover_all_certificate_images(datasets_dir: str = "datasets") -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """
    Scans all local datasets in `./datasets/` and categorizes into train/val samples.
    Discovers:
    1. CG-1050 (datasets/TRAINING_CG-1050, datasets/VALIDATION_CG-1050)
       - Pristine: without _cm, _col, _r -> 0
       - Tampered: with _cm, _col, _r -> 1
    2. Synthetic Manipulated (datasets/synthetic_manipulated/)
       - genuine -> 0, manipulated -> 1
    3. d1Certificate forgery detection (datasets/d1Certificate forgery detection/)
       - roboflow images
    """
    train_samples = []
    val_samples = []

    # 1. CG-1050 Training Set
    cg_train_files = glob.glob(os.path.join(datasets_dir, "TRAINING_CG-1050", "**", "*.*"), recursive=True)
    for f in cg_train_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".tiff"]:
            basename = os.path.basename(f)
            is_tampered = 1 if any(t in basename for t in ["_cm", "_col", "_r"]) else 0
            train_samples.append((f, is_tampered))

    # CG-1050 Validation Set
    cg_val_files = glob.glob(os.path.join(datasets_dir, "VALIDATION_CG-1050", "**", "*.*"), recursive=True)
    for f in cg_val_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".tiff"]:
            basename = os.path.basename(f)
            is_tampered = 1 if any(t in basename for t in ["_cm", "_col", "_r"]) else 0
            val_samples.append((f, is_tampered))

    # 2. Synthetic Manipulated
    synth_gen = glob.glob(os.path.join(datasets_dir, "synthetic_manipulated", "genuine", "*.*"))
    for f in synth_gen:
        if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg"]:
            train_samples.append((f, 0))

    synth_man = glob.glob(os.path.join(datasets_dir, "synthetic_manipulated", "manipulated", "*.*"))
    for f in synth_man:
        if os.path.splitext(f)[1].lower() in [".png", ".jpg", ".jpeg"]:
            train_samples.append((f, 1))

    # 3. d1Certificate forgery detection
    d1_images = glob.glob(os.path.join(datasets_dir, "d1Certificate forgery detection", "**", "images", "*.*"), recursive=True)
    for f in d1_images:
        ext = os.path.splitext(f)[1].lower()
        if ext in [".jpg", ".jpeg", ".png"]:
            label_file = f.replace("images", "labels").replace(ext, ".txt")
            is_fake = 1
            if os.path.exists(label_file):
                with open(label_file, "r") as lf:
                    content = lf.read().strip()
                    if not content:
                        is_fake = 0
            val_samples.append((f, is_fake))

    # Deduplicate and verify
    train_samples = list(set(train_samples))
    val_samples = list(set(val_samples))

    # If validation set is empty, do stratified split
    if len(val_samples) == 0:
        all_samples = train_samples
        labels = [s[1] for s in all_samples]
        train_samples, val_samples = train_test_split(all_samples, test_size=0.2, stratify=labels, random_state=42)

    print(f"[OK] Discovered Image Datasets: {len(train_samples)} Train Samples, {len(val_samples)} Validation Samples")
    return train_samples, val_samples


def get_image_data_loaders(
    datasets_dir: str = "datasets",
    batch_size: int = 32,
    target_size: tuple[int, int] = (224, 224),
    num_workers: int = 0
) -> tuple[DataLoader, DataLoader]:
    """Build and return PyTorch DataLoaders for visual forensics."""
    train_samples, val_samples = discover_all_certificate_images(datasets_dir)

    train_ds = CertificateImageDataset(train_samples, target_size=target_size, augment=True)
    val_ds = CertificateImageDataset(val_samples, target_size=target_size, augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader
