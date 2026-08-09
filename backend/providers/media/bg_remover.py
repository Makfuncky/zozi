"""Background remover service provider.

Re-exports from :mod:`providers.hr.bg_remover` (the canonical, full
implementation) so that legacy call-site imports (``from providers.bg_remover
import …``) resolve to the real code rather than a no-op stub.
"""
from __future__ import annotations

from providers.hr.bg_remover import *  # noqa: F401,F403
from providers.hr.bg_remover import (  # noqa: F401
    AVAILABLE_MODELS,
    VALID_STRATEGIES,
    ProcessingConfig,
    ProcessingStrategy,
    SubjectCategory,
    MemoryManager,
    CleanEdgeRefiner,
    BackgroundRemover,
    SceneAnalyzer,
    HandRemover,
    HoleFiller,
    ThinPartHandler,
    HumanPreserver,
    EdgeRefiner,
    ColorSpaceUtils,
    ImageLoader,
    QualityAnalyzer,
    SubjectDetector,
    ModelSelector,
    MultiModelSegmenter,
    WoodBackgroundRemover,
    ZoziBackgroundRemover,
    AISegmenter,
    EdgeShaver,
    GlobalBackgroundBleeder,
    ArtifactIsolator,
    FloatingArtifactRemover,
    BottomTextEraser,
    Exporter,
    remove_background,
    remove_background_preset,
    remove_background_model,
    remove_background_strategy,
    magic_erase,
    process_product_image,
    generate_angles,
    bytes_to_image,
    _image_to_bytes,
)

# `process_image_search` lives in the canonical media provider, not `providers.hr.bg_remover`.
from providers.media.image import process_image_search  # noqa: F401
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "AVAILABLE_MODELS",
    "VALID_STRATEGIES",
    "ProcessingConfig",
    "ProcessingStrategy",
    "SubjectCategory",
    "MemoryManager",
    "CleanEdgeRefiner",
    "BackgroundRemover",
    "SceneAnalyzer",
    "HandRemover",
    "HoleFiller",
    "ThinPartHandler",
    "HumanPreserver",
    "EdgeRefiner",
    "ColorSpaceUtils",
    "ImageLoader",
    "QualityAnalyzer",
    "SubjectDetector",
    "ModelSelector",
    "MultiModelSegmenter",
    "WoodBackgroundRemover",
    "ZoziBackgroundRemover",
    "AISegmenter",
    "EdgeShaver",
    "GlobalBackgroundBleeder",
    "ArtifactIsolator",
    "FloatingArtifactRemover",
    "BottomTextEraser",
    "Exporter",
    "remove_background",
    "remove_background_preset",
    "remove_background_model",
    "remove_background_strategy",
    "magic_erase",
    "process_image_search",
    "process_product_image",
    "generate_angles",
    "bytes_to_image",
    "_image_to_bytes",
]
