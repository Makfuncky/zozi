# ========================== STRATEGY CONFIG ==========================

from typing import Dict, Optional, List


def _filter_heavy_models(models: List[str]) -> List[str]:
    if settings.skip_heavy_models:
        return [m for m in models if m not in _HEAVY_MODELS]
    return models


def _get_strategy_config(strategy: str):
    from .configuration import ProcessingConfig
    strategy_lower = strategy.lower()
    if strategy_lower == ProcessingStrategy.CLEAN_COMMERCIAL.value:
        return ProcessingConfig(max_rembg_dimension=1024, models_to_try=["isnet-general-use", "u2net"])
    elif strategy_lower == ProcessingStrategy.PRECISION_GEOMETRY.value:
        return ProcessingConfig(
            max_rembg_dimension=1024, models_to_try=["isnet-general-use", "u2net"]
        )
    elif strategy_lower == ProcessingStrategy.PRODUCTION_BIREFNET.value:
        return ProcessingConfig(
            max_rembg_dimension=1024,
            models_to_try=_filter_heavy_models([
                "birefnet-general",
                "isnet-general-use",
                "u2net",
                "silueta",
            ]),
        )
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V11.value:
        return ProcessingConfig(
            max_rembg_dimension=1024,
            models_to_try=_filter_heavy_models([
                "birefnet-general",
                "isnet-general-use",
                "u2net",
            ]),
        )
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V12.value:
        return ProcessingConfig(
            max_rembg_dimension=1024,
            models_to_try=_filter_heavy_models([
                "birefnet-massive",
                "birefnet-hrsod",
                "u2net_cloth_seg",
                "isnet-general-use",
            ]),
        )
    elif strategy_lower == ProcessingStrategy.VARIANT_TESTING.value:
        return ProcessingConfig(
            max_rembg_dimension=1024,
            models_to_try=_filter_heavy_models([
                "birefnet-general-lite",
                "u2net_cloth_seg",
                "briaai-rmbg-1.4",
                "isnet-general-use",
            ]),
        )
    elif strategy_lower == ProcessingStrategy.GENERAL.value:
        return ProcessingConfig(
            max_rembg_dimension=1024,
            models_to_try=["isnet-general-use", "u2net", "u2netp"],
        )
    return ProcessingConfig()

