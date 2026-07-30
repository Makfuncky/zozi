from ._base import BaseProvider, BaseAIProvider
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
from .finance_ai import (
    FinanceAIResult,
    parse_email_to_ledger,
    extract_bill_fields,
    suggest_reconciliation_match,
)
from .text import _ollama_chat, _OLLAMA_TEXT_MODEL, _extract_json
from .vision import suggest_price, normalize_category, VariantConfig, analyze_product_image
from .chatbot import ChatbotProvider
from .search import AdvancedSearchEngine
from .geo import CountryDetectionProvider
from .map import LocationProvider
from .country import CountrySearchProvider
from .analytics import AnalyticsProvider
from .parcel_verification import (
    verify_parcel_photo,
    verify_parcel_fast,
)
from .voice_to_text import (
    transcribe_audio,
    process_product_voice_command,
    process_finance_voice_command,
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