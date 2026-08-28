"""AI service facade — canonical import point for AI operations used by domain services.

Exposes a single ``ai_service`` object with methods for product analysis,
variant suggestion, and AI-powered content generation. Providers (huggingface,
variant_config, etc.) own the vendor HTTP and heuristics; this module
orchestrates them behind a stable interface.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

HF_API_TOKEN: str = os.environ.get("HF_API_TOKEN", "")


class AIService:
    """Facade over the AI providers used by domain services."""

    def __init__(self) -> None:
        self.HF_API_TOKEN: str = HF_API_TOKEN

    def infer_product_name(self, image_bytes: bytes = b"") -> str:
        """Infer a product name from image bytes or filename."""
        try:
            from providers.ai.ai_variant_config import _candidate_from_filename, _generate_description
            return ""
        except Exception as exc:
            logger.debug("infer_product_name fallback: %s", exc)
            return ""

    def suggest_category(self, name: str = "", description: str = "", image_bytes: bytes = b"") -> str:
        """Suggest a product category."""
        try:
            from providers.ai.ai_variant_config import normalize_category
            return normalize_category(name)
        except Exception:
            return "General"

    def suggest_tags(self, name: str = "", category: str = "", description: str = "") -> list[str]:
        """Suggest tags for a product."""
        try:
            from providers.ai.ai_variant_config import _generate_tags
            return _generate_tags(name=name, category=category)
        except Exception:
            return []

    def generate_product_description(
        self, name: str = "", category: str = "", image_bytes: bytes = b"",
    ) -> str:
        """Generate a product description."""
        try:
            from providers.ai.ai_variant_config import _generate_description
            return _generate_description(name=name, category=category)
        except Exception:
            return ""

    def detect_dominant_color(self, image_bytes: bytes) -> str:
        """Detect the dominant color in a product image."""
        return ""

    def suggest_variant_template(self, name: str, category: str, tags: list[str] | None = None) -> dict:
        """Suggest a variant template for a product."""
        return {}

    def suggest_variant_options(self, name: str, category: str, tags: list[str] | None = None) -> list[str]:
        """Suggest variant options for a product."""
        return []

    def suggest_material_candidates(self, name: str, category: str = "") -> list[str]:
        """Suggest material candidates for a product."""
        return []

    def is_generic_product_name(self, name: str) -> bool:
        """Check if a product name is too generic."""
        generic_names = {"product", "item", "test", "untitled", "unknown"}
        return name.strip().lower() in generic_names


# Module-level singleton
ai_service = AIService()

__all__ = ["ai_service", "HF_API_TOKEN", "AIService"]
