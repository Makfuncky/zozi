"""Image provider package: background removal, OCR, parcel verification,
and a re-export of the Pillow (PIL) SDK so external SDKs stay isolated here."""
from __future__ import annotations

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

HAS_CV2 = False
HAS_GUIDED_FILTER = False
cv2 = None
ximgproc = None

try:
    import cv2 as _cv2
    from cv2 import ximgproc as _ximgproc  # noqa: F401  (guided filter submodule)

    cv2 = _cv2
    ximgproc = _ximgproc
    HAS_CV2 = True
    HAS_GUIDED_FILTER = True
except Exception:  # pragma: no cover - optional heavy SDK
    pass

from .bg_remover import (
    remove_background,
    remove_background_preset,
    remove_background_model,
    remove_background_strategy,
    magic_erase,
    AVAILABLE_MODELS,
    VALID_STRATEGIES,
    CleanEdgeRefiner,
    EdgeRefiner,
    SceneAnalyzer,
    HandRemover,
    HoleFiller,
    ThinPartHandler,
    HumanPreserver,
    EdgeShaver,
    GlobalBackgroundBleeder,
    ArtifactIsolator,
    FloatingArtifactRemover,
    BottomTextEraser,
    WoodBackgroundRemover,
)
from .image import (
    remove_background as image_remove_background,
    generate_angles,
    process_image_search,
)
from .ocr import parse_bill_text, parse_statement_csv
from .parcel_verification import verify_parcel_photo, verify_parcel_fast

__all__ = [
    "remove_background",
    "remove_background_preset",
    "remove_background_model",
    "remove_background_strategy",
    "magic_erase",
    "AVAILABLE_MODELS",
    "VALID_STRATEGIES",
    "CleanEdgeRefiner",
    "EdgeRefiner",
    "SceneAnalyzer",
    "HandRemover",
    "HoleFiller",
    "ThinPartHandler",
    "HumanPreserver",
    "EdgeShaver",
    "GlobalBackgroundBleeder",
    "ArtifactIsolator",
    "FloatingArtifactRemover",
    "BottomTextEraser",
    "WoodBackgroundRemover",
    "image_remove_background",
    "generate_angles",
    "process_image_search",
    "parse_bill_text",
    "parse_statement_csv",
    "verify_parcel_photo",
    "verify_parcel_fast",
    "Image",
    "ImageOps",
    "ImageFilter",
    "ImageEnhance",
    "HAS_CV2",
    "HAS_GUIDED_FILTER",
    "cv2",
    "ximgproc",
]
