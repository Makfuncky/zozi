from __future__ import annotations

"""
Base Provider
=============
Abstract base classes for all AI providers.
Test file: backend/tests/_test_provider/test_ai_providers.py (import tests)
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the provider. Called once on first use."""
        self._initialized = True
        logger.info("Provider %s initialized", self.name)

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider's backend is reachable and ready."""
        return False

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return a health status dict."""
        return {"status": "unknown", "provider": self.name}


class BaseAIProvider(BaseProvider):
    """Abstract base class for AI providers that use model inference."""

    def __init__(self, name: str = "", model: str = ""):
        super().__init__(name)
        self.model = model
        self._model_loaded = False

    @abstractmethod
    def load_model(self) -> None:
        """Load the AI model into memory."""

    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """Run inference on input data."""

    @abstractmethod
    def preprocess(self, input_data: Any) -> Any:
        """Preprocess input data before inference."""
        return input_data

    @abstractmethod
    def postprocess(self, output: Any) -> Any:
        """Postprocess model output."""
        return output

    def is_available(self) -> bool:
        return self._initialized and self._model_loaded

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy" if self.is_available() else "unhealthy",
            "provider": self.name,
            "model": self.model,
            "model_loaded": self._model_loaded,
        }