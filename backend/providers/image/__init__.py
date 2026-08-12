"""Image provider package: background removal, OCR, parcel verification,
and a re-export of the Pillow (PIL) SDK so external SDKs stay isolated here."""

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

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
from .image import remove_background as image_remove_background, generate_angles
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
    "parse_bill_text",
    "parse_statement_csv",
    "verify_parcel_photo",
    "verify_parcel_fast",
    "Image",
    "ImageOps",
    "ImageFilter",
    "ImageEnhance",
]
