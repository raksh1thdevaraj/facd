import time
from typing import Any, Dict

import cv2
import numpy as np

from app.modules.preprocessing.service import PreprocessingService


def run_preprocessing_diagnostics() -> Dict[str, Any]:
    """Execute diagnostic self-tests and performance benchmarks for the preprocessing subsystem."""
    cv_optimized = cv2.useOptimized()
    num_threads = cv2.getNumThreads()

    # Create synthetic 1800x1200 certificate canvas for benchmarking
    test_canvas = np.ones((1200, 1800, 3), dtype=np.uint8) * 250
    # Add synthetic text lines
    for y in range(200, 1000, 100):
        cv2.putText(
            test_canvas,
            "University Certificate Verification Benchmark",
            (200, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        )

    service = PreprocessingService()
    context: Dict[str, Any] = {}

    t0 = time.perf_counter()
    enhanced, context = service.pipeline.run(test_canvas, context)
    benchmark_ms = (time.perf_counter() - t0) * 1000.0

    is_healthy = benchmark_ms < 3000.0 and enhanced is not None

    return {
        "status": "ok" if is_healthy else "degraded",
        "opencv_simd_optimized": cv_optimized,
        "opencv_threads": num_threads,
        "benchmark_canvas_size": "1800x1200",
        "benchmark_duration_ms": round(benchmark_ms, 2),
        "target_max_ms": 3000.0,
    }
