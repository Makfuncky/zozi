"""Background remover service stub."""
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class CleanEdgeRefiner:
    def __init__(self, **kwargs): pass
    def refine(self, image_bytes: bytes) -> bytes: return image_bytes

class EdgeRefiner:
    def __init__(self, **kwargs): pass
    def refine(self, image_bytes: bytes) -> bytes: return image_bytes

class SceneAnalyzer:
    def __init__(self, **kwargs): pass
    def analyze(self, image_bytes: bytes) -> dict: return {}

class HandRemover:
    def __init__(self, **kwargs): pass
    def remove(self, image_bytes: bytes) -> bytes: return image_bytes

class HoleFiller:
    def __init__(self, **kwargs): pass
    def fill(self, image_bytes: bytes) -> bytes: return image_bytes

class ThinPartHandler:
    def __init__(self, **kwargs): pass
    def handle(self, image_bytes: bytes) -> bytes: return image_bytes

class HumanPreserver:
    def __init__(self, **kwargs): pass
    def preserve(self, image_bytes: bytes) -> bytes: return image_bytes

class EdgeShaver:
    def __init__(self, **kwargs): pass
    def shave(self, image_bytes: bytes) -> bytes: return image_bytes

class GlobalBackgroundBleeder:
    def __init__(self, **kwargs): pass
    def bleed(self, image_bytes: bytes) -> bytes: return image_bytes

class ArtifactIsolator:
    def __init__(self, **kwargs): pass
    def isolate(self, image_bytes: bytes) -> bytes: return image_bytes

class FloatingArtifactRemover:
    def __init__(self, **kwargs): pass
    def remove(self, image_bytes: bytes) -> bytes: return image_bytes

class BottomTextEraser:
    def __init__(self, **kwargs): pass
    def erase(self, image_bytes: bytes) -> bytes: return image_bytes

class WoodBackgroundRemover:
    def __init__(self, **kwargs): pass
    def remove(self, image_bytes: bytes) -> bytes: return image_bytes


AVAILABLE_MODELS = ["isnet-general-use", "u2net", "bge-reranker", "bge-m3"]
VALID_STRATEGIES = ["auto", "clean_commercial", "precision_geometry", "portrait"]

def remove_background(image_data: bytes, **kwargs) -> bytes:
    """Remove background from image - stub implementation."""
    return image_data

def remove_background_preset(image_data: bytes, preset: str = "auto", **kwargs) -> bytes:
    """Remove background with preset - stub implementation."""
    return image_data

def remove_background_model(image_bytes: bytes, model_name: str = "isnet-general-use", fast_mode: bool = False) -> bytes:
    """Remove background using a specific model - stub implementation."""
    return image_bytes

def remove_background_strategy(image_bytes: bytes, strategy: str) -> bytes:
    """Remove background using a specific strategy - stub implementation."""
    return image_bytes

def magic_erase(image_bytes: bytes, mask: Any = None) -> bytes:
    """Erase specific regions - stub implementation."""
    return image_bytes

def process_image_search(query: str, **kwargs) -> list:
    """Process image search - stub implementation."""
    return []

def _bytes_to_image(image_bytes: bytes):
    """Convert bytes to image - stub."""
    return None

def _image_to_bytes(img):
    """Convert image to bytes - stub."""
    return b''

class ProcessingConfig:
    """Stub processing config."""
    DEFAULT_SIZE = 1024
    MAX_SIZE = 4096
    SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "webp"]