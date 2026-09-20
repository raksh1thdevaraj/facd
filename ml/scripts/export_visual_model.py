"""Export and optimize Certificate Visual CNN for production deployment."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import torch
from torch import nn

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.visual_model.network import CertificateVisualCNN

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def export_and_optimize(
    model_path: str = "ml/models/visual_cnn_best.pt",
    config_path: str = "ml/configs/dl_model_config.json",
    output_dir: str = "ml/models",
) -> dict[str, float]:
    """Export TorchScript model, quantized model, and benchmark CPU latency."""
    out_dir = PROJECT_ROOT / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(PROJECT_ROOT / config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    device = torch.device("cpu")
    model = CertificateVisualCNN(
        backbone_name=config.get("backbone", "efficientnet_b0"),
        pretrained=False,
        embedding_dim=config.get("embedding_dim", 512),
    )

    chk = PROJECT_ROOT / model_path
    if chk.exists():
        checkpoint = torch.load(chk, map_location=device)
        state_dict = checkpoint.get("state_dict", checkpoint)
        model.load_state_dict(state_dict)
        logger.info("Loaded base checkpoint from %s", chk)
    else:
        logger.warning(
            "Checkpoint %s not found. Using randomly initialized weights for export.",
            chk,
        )

    model.to(device)
    model.eval()

    image_size = config.get("image_size", 512)
    dummy_input = torch.randn(1, 3, image_size, image_size, device=device)

    # 1. TorchScript Trace Export
    traced_path = out_dir / "visual_cnn_traced.pt"
    try:
        traced_model = torch.jit.trace(model, dummy_input)
        traced_model.save(str(traced_path))
        logger.info("Saved TorchScript traced model to %s", traced_path)
    except (RuntimeError, ValueError) as e:
        logger.error("Failed tracing model: %s", e)

    # 2. Dynamic Quantization (Linear layers quantized to qint8 for CPU)
    quantized_path = out_dir / "visual_cnn_quantized.pt"
    try:
        if "qnnpack" in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = "qnnpack"
        quantized_model = torch.quantization.quantize_dynamic(
            model, {nn.Linear}, dtype=torch.qint8
        )
        torch.save(quantized_model.state_dict(), str(quantized_path))
        logger.info("Saved dynamic quantized model to %s", quantized_path)
    except (RuntimeError, ValueError) as e:
        logger.warning("Dynamic quantization not available on this platform: %s", e)

    # 3. Benchmark CPU Latency (50 runs)
    logger.info("Benchmarking CPU inference latency over 30 runs...")
    with torch.no_grad():
        # Warmup
        for _ in range(5):
            _ = model(dummy_input)

        latencies = []
        for _ in range(30):
            t0 = time.perf_counter()
            _ = model(dummy_input)
            latencies.append((time.perf_counter() - t0) * 1000.0)

    mean_latency = float(sum(latencies) / len(latencies))
    min_latency = float(min(latencies))
    max_latency = float(max(latencies))

    logger.info(
        "CPU Benchmark: Mean = %.2f ms, Min = %.2f ms, Max = %.2f ms",
        mean_latency,
        min_latency,
        max_latency,
    )

    return {
        "mean_latency_ms": round(mean_latency, 2),
        "min_latency_ms": round(min_latency, 2),
        "max_latency_ms": round(max_latency, 2),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export and optimize visual CNN model")
    parser.add_argument("--model", default="ml/models/visual_cnn_best.pt")
    parser.add_argument("--config", default="ml/configs/dl_model_config.json")
    parser.add_argument("--output-dir", default="ml/models")
    args = parser.parse_args()

    export_and_optimize(
        model_path=args.model, config_path=args.config, output_dir=args.output_dir
    )
