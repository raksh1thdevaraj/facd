from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

import numpy as np


class BasePreprocessingStep(ABC):
    """Abstract Base Class for an atomic preprocessing pipeline transformation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier of the preprocessing step."""
        pass

    @abstractmethod
    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply transformation to the input image array.

        Args:
            image: NumPy array representing image (BGR or Grayscale).
            context: Shared pipeline dictionary storing intermediate metrics and states.

        Returns:
            Tuple of (transformed_image, updated_context).
        """
        pass
