"""Pipeline latency profiling and stage benchmarking script."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
import time
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.certificate import CertificateModel  # noqa: E402
from app.services.pipeline_orchestrator import (  # noqa: E402
    VerificationPipelineOrchestrator,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def profile_pipeline(sample_paths: list[Path], output_json: Path | None = None) -> dict:
    """Benchmark stage execution times across provided certificate images."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    orchestrator = VerificationPipelineOrchestrator()
    reports_dir = Path("ml/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    results = []

    print("\n" + "=" * 75)
    print("      AI CERTIFICATE VERIFICATION PIPELINE LATENCY PROFILER (NFR-03)")
    print("=" * 75)

    for idx, path in enumerate(sample_paths, start=1):
        if not path.exists():
            logger.warning("Sample %s not found, skipping", path)
            continue

        cert_id = str(uuid.uuid4())
        upload_dest = settings.UPLOAD_DIR / f"{cert_id}{path.suffix}"
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, upload_dest)

        with open(upload_dest, "rb") as f:
            file_bytes = f.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        cert_record = CertificateModel(
            id=cert_id,
            file_path=str(upload_dest),
            file_hash=file_hash,
            original_filename=path.name,
            file_size=len(file_bytes),
            mime_type="image/png" if path.suffix.lower() == ".png" else "application/pdf",
            job_status="PENDING",
            job_progress=0,
        )
        db.add(cert_record)
        db.commit()

        start_time = time.perf_counter()
        try:
            report = orchestrator.run_pipeline(certificate_id=cert_id, db=db)
            total_elapsed_s = time.perf_counter() - start_time
            passed_budget = total_elapsed_s <= 15.0

            summary = {
                "sample": path.name,
                "certificate_id": cert_id,
                "verdict": report.verdict.value,
                "authenticity_score": report.authenticity_score,
                "total_time_seconds": round(total_elapsed_s, 2),
                "within_budget_15s": passed_budget,
            }
            results.append(summary)

            verdict_str = report.verdict.value
            pass_str = "PASS <=15s" if passed_budget else "FAIL >15s"
            print(
                f"\n[Sample {idx}/{len(sample_paths)}] {path.name} -> "
                f"Verdict: {verdict_str} (Score: {report.authenticity_score:.2f}) | "
                f"Total: {total_elapsed_s:.2f}s [{pass_str}]"
            )

        except Exception as e:
            logger.error("Profiling failed on %s: %s", path.name, e)

    db.close()

    output_path = output_json or (reports_dir / "pipeline_latency_profile.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 75)
    print(f"Profiling summary exported to: {output_path}")
    print("=" * 75 + "\n")
    return {"results": results, "output_path": str(output_path)}


if __name__ == "__main__":
    test_samples = [
        Path("datasets/synthetic_manipulated/genuine/GEN_00001.png"),
        Path("datasets/synthetic_manipulated/manipulated/MAN_00001.png"),
    ]
    profile_pipeline(test_samples)
