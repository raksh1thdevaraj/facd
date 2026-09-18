import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """Sequential executor for registered preprocessing transformation steps."""

    def __init__(self, steps: Optional[List[BasePreprocessingStep]] = None):
        self.steps: List[BasePreprocessingStep] = steps or []

    def add_step(self, step: BasePreprocessingStep) -> "PreprocessingPipeline":
        """Register an additional transformation step."""
        self.steps.append(step)
        return self

    def run(
        self, image: np.ndarray, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Sequentially execute registered steps, tracking elapsed time and context."""
        ctx = context or {}
        step_metrics: Dict[str, float] = ctx.setdefault("step_metrics", {})

        current_img = image

        for step in self.steps:
            t0 = time.perf_counter()
            try:
                current_img, ctx = step.process(current_img, ctx)
            except Exception as exc:
                logger.warning(
                    "Error in preprocessing step '%s': %s. Continuing with current buffer.",
                    step.name,
                    exc,
                )
                ctx[f"{step.name}_error"] = str(exc)

            dt_ms = (time.perf_counter() - t0) * 1000.0
            step_metrics[step.name] = round(dt_ms, 2)

            if dt_ms > 1000.0:
                logger.warning("Preprocessing step '%s' exceeded 1000ms: %.2f ms", step.name, dt_ms)

        return current_img, ctx
