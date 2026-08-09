from ._base import BaseAIProvider, BaseProvider
from .analytics import AnalyticsProvider
from .bg_remover import (
    AVAILABLE_MODELS,
    VALID_STRATEGIES,
    ArtifactIsolator,
    BottomTextEraser,
    CleanEdgeRefiner,
    EdgeRefiner,
    EdgeShaver,
    FloatingArtifactRemover,
    GlobalBackgroundBleeder,
    HandRemover,
    HoleFiller,
    HumanPreserver,
    SceneAnalyzer,
    ThinPartHandler,
    WoodBackgroundRemover,
    magic_erase,
    remove_background,
    remove_background_model,
    remove_background_preset,
    remove_background_strategy,
)
from .chatbot import ChatbotProvider
from .country import CountrySearchProvider
from .finance_ai import (
    FinanceAIResult,
    extract_bill_fields,
    parse_email_to_ledger,
    suggest_reconciliation_match,
)
from .geo import CountryDetectionProvider
from .image import generate_angles
from .image import remove_background as image_remove_background
from .map import LocationProvider
from .ocr import parse_bill_text, parse_statement_csv
from .parcel_verification import (
    verify_parcel_fast,
    verify_parcel_photo,
)
from .search import AdvancedSearchEngine
from .text import _OLLAMA_TEXT_MODEL, _extract_json, _ollama_chat
from .vision import (
    VariantConfig,
    analyze_product_image,
    normalize_category,
    suggest_price,
)
from .voice_to_text import (
    process_finance_voice_command,
    process_product_voice_command,
    transcribe_audio,
)

__all__ = [
    "BaseProvider",
    "BaseAIProvider",
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
    "FinanceAIResult",
    "parse_email_to_ledger",
    "extract_bill_fields",
    "suggest_reconciliation_match",
    "_ollama_chat",
    "_OLLAMA_TEXT_MODEL",
    "_extract_json",
    "suggest_price",
    "normalize_category",
    "VariantConfig",
    "analyze_product_image",
    "ChatbotProvider",
    "AdvancedSearchEngine",
    "CountryDetectionProvider",
    "LocationProvider",
    "CountrySearchProvider",
    "AnalyticsProvider",
    "verify_parcel_photo",
    "verify_parcel_fast",
    "transcribe_audio",
    "process_product_voice_command",
    "process_finance_voice_command",
]