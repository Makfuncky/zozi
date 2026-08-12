from ._base import BaseProvider, BaseAIProvider
from .image.bg_remover import (
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
from .image.image import remove_background as image_remove_background, generate_angles
from .image.ocr import parse_bill_text, parse_statement_csv
from .ai.finance_ai import (
    FinanceAIResult,
    parse_email_to_ledger,
    extract_bill_fields,
    suggest_reconciliation_match,
)
from .ai.text import _ollama_chat, _OLLAMA_TEXT_MODEL, _extract_json
from .ai.vision import suggest_price, normalize_category, VariantConfig, analyze_product_image
from .ai.chatbot import ChatbotProvider
from .ai.search import AdvancedSearchEngine
from .geography.geo import CountryDetectionProvider
from .geography.map import LocationProvider
from .geography.country import CountrySearchProvider
from .analytics.analytics import AnalyticsProvider
from .image.parcel_verification import (
    verify_parcel_photo,
    verify_parcel_fast,
)
from .voice.voice_to_text import (
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
