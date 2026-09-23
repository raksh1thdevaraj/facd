"""
Download and save Hugging Face datasets:
- nielsr/funsd -> datasets/funsd
- naver-clova-ix/cord-v2 -> datasets/cord-v2
"""

import sys
import os
from pathlib import Path

# Remove local directory from sys.path if it conflicts with HF datasets
sys_path_clean = [p for p in sys.path if os.path.basename(os.path.abspath(p)) != "datasets"]
sys.path = sys_path_clean

# Suppress HF symlinks warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from datasets import load_dataset

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = WORKSPACE_ROOT / "datasets"

def download_and_save_funsd():
    target_dir = DATASETS_DIR / "funsd"
    print(f"[*] Processing nielsr/funsd -> {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    ds = load_dataset("nielsr/funsd")
    print(f"[+] Loaded FUNSD: {ds}")
    ds.save_to_disk(str(target_dir))
    print(f"[OK] Successfully saved FUNSD to {target_dir}")
    return ds

def download_and_save_cord_v2():
    target_dir = DATASETS_DIR / "cord-v2"
    print(f"[*] Processing naver-clova-ix/cord-v2 -> {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    ds = load_dataset("naver-clova-ix/cord-v2")
    print(f"[+] Loaded CORD-v2: {ds}")
    ds.save_to_disk(str(target_dir))
    print(f"[OK] Successfully saved CORD-v2 to {target_dir}")
    return ds

if __name__ == "__main__":
    print("=" * 60)
    print("HUGGING FACE DATASET INTAKE PIPELINE")
    print("=" * 60)
    
    funsd_ds = download_and_save_funsd()
    print("-" * 60)
    cord_ds = download_and_save_cord_v2()
    print("=" * 60)
    print("ALL DATASETS SUCCESSFULLY INGESTED INTO datasets/")
    print("=" * 60)
