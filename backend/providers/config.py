from __future__ import annotations

"""
Provider Configuration
======================
Central configuration for all AI providers.
Test file: backend/tests/_test_provider/test_ai_providers.py (config tests)
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderConfig:
    """Configuration for AI provider modules."""

    hf_api_token: str = os.environ.get("HF_API_TOKEN", "")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "moondream:latest")
    ollama_text_model: str = os.environ.get("OLLAMA_TEXT_MODEL", "phi3:mini")

    rembg_default_models: list[str] = field(
        default_factory=lambda: ["isnet-general-use", "u2net"]
    )
    rembg_max_dimension: int = 2048
    rembg_png_compression: int = 6

    bg_preset_models: dict[str, list[str]] = field(default_factory=lambda: {
        "general": ["isnet-general-use", "u2net"],
        "handheld": ["isnet-general-use", "u2net"],
        "wood": ["birefnet-general", "isnet-general-use", "u2net"],
        "texture_gap": ["birefnet-general", "isnet-general-use", "u2net"],
        "marketing": ["birefnet-massive", "birefnet-hrsod", "u2net_cloth_seg", "isnet-general-use"],
        "cloth_lite": ["birefnet-general-lite", "u2net_cloth_seg", "briaai-rmbg-1.4", "isnet-general-use"],
        "ultimate_v11": ["birefnet-general"],
        "ultimate_v12": ["birefnet-hrsod", "birefnet-general-lite"],
        "clean_commercial": ["isnet-general-use"],
        "precision_geometry": ["isnet-general-use", "u2net"],
        "production_birefnet": ["birefnet-general-lite"],
        "variant_testing": ["birefnet-general-lite", "u2net_cloth_seg", "briaai-rmbg-1.4", "isnet-general-use"],
    })

    max_concurrent_bg_removals: int = int(os.environ.get("BG_MAX_CONCURRENT", "2"))
    max_session_cache: int = int(os.environ.get("BG_MAX_SESSION_CACHE", "2"))
    max_image_dim: int = int(os.environ.get("BG_MAX_IMAGE_DIM", "1024"))
    lite_max_dim: int = int(os.environ.get("BG_LITE_MAX_DIM", "1024"))
    memory_warn_mb: int = int(os.environ.get("BG_MEMORY_WARN_MB", "256"))
    skip_heavy_models: bool = field(default_factory=lambda: os.environ.get("BG_SKIP_HEAVY_MODELS", "true").lower() == "true")

    ocr_timeout: int = 30
    ocr_max_file_size_mb: int = 25

    finance_ai_timeout: int = 30

    chatbot_max_history: int = 10
    chatbot_session_ttl_hours: int = 24

    search_default_limit: int = 20
    search_fuzzy_cutoff: float = 0.6

    geo_default_country: str = os.environ.get("DEFAULT_COUNTRY", "US")
    geo_ipapi_timeout: int = 5

    analytics_default_period_days: int = 30


settings = ProviderConfig()