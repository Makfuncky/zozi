# ========================== ENUMS & CONSTANTS ==========================
from enum import Enum
from typing import List, Dict, Optional

class ProcessingStrategy(str, Enum):
    CLEAN_COMMERCIAL = "clean_commercial"
    PRECISION_GEOMETRY = "precision_geometry"
    PRODUCTION_BIREFNET = "production_birefnet"
    ULTIMATE_V11 = "ultimate_v11"
    ULTIMATE_V12 = "ultimate_v12"
    VARIANT_TESTING = "variant_testing"
    GENERAL = "general"


class SubjectCategory(str, Enum):
    PRODUCT = "product"
    HUMAN = "human"
    CLOTHING = "clothing"
    FOOD = "food"
    UNKNOWN = "unknown"


AVAILABLE_MODELS: List[str] = [
    "birefnet-general",
    "birefnet-general-lite",
    "birefnet-massive",
    "birefnet-hrsod",
    "birefnet-portrait",
    "birefnet-dis",
    "isnet-general-use",
    "isnet-anime",
    "u2net",
    "u2netp",
    "u2net_cloth_seg",
    "silueta",
    "briaai-rmbg-1.4",
    "sam2",
    "vitmatte",
]

VALID_STRATEGIES: List[str] = [s.value for s in ProcessingStrategy]

