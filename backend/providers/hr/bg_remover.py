"""
Background Removal Provider
===========================
Consolidates 6 bg removal models (br_05-br_13) into a unified provider.

Classes preserved from reference files:
  br_05: CleanEdgeRefiner, BackgroundRemover
  br_06: SceneAnalyzer, HandRemover, HoleFiller, ThinPartHandler, HumanPreserver, EdgeRefiner, BackgroundRemover
  br_08: MemoryManager, ColorSpaceUtils, ImageLoader, QualityAnalyzer, SubjectDetector, ModelSelector,
          MultiModelSegmenter, WoodBackgroundRemover, Exporter, ZoziBackgroundRemover
  br_11: AISegmenter, EdgeShaver, GlobalBackgroundBleeder, ArtifactIsolator, Exporter
  br_12: AISegmenter (variants), FloatingArtifactRemover, BottomTextEraser, EdgeShaver, GlobalBackgroundBleeder, Exporter
  br_13: AISegmenter (lite variants), EdgeShaver, GlobalBackgroundBleeder, FloatingArtifactRemover, BottomTextEraser, Exporter

All rembg remove() calls use alpha_matting=False.

Test file: backend/tests/_test_provider/test_bg_remover.py
"""
from __future__ import annotations

import io
import logging
import threading
import time
import base64
import gc
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .config import settings

logger = logging.getLogger(__name__)


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


np = _LazyNumpy()
Image = _LazyPIL()

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False
    cv2 = None

_HEAVY_MODELS = {"birefnet-massive", "birefnet-hrsod", "birefnet-general", "u2net_cloth_seg"}

# ========================== REMBG LAZY LOAD ==========================
_HAS_REMBG = False
remove = None
new_session = None


def _ensure_rembg():
    global remove, new_session, _HAS_REMBG
    if not _HAS_REMBG:
        try:
            from rembg import remove as _remove, new_session as _new_session
            remove = _remove
            new_session = _new_session
            _HAS_REMBG = True
        except ImportError:
            pass


# ========================== CORE I/O ==========================

def _safe_remove(img: Image.Image, session: Any) -> Image.Image:
    """Pass PNG bytes through rembg remove() with alpha_matting=False."""
    _ensure_rembg()
    if remove is None:
        raise RuntimeError("rembg is not available")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    input_bytes = buf.getvalue()
    output_bytes = remove(input_bytes, session=session, alpha_matting=False)
    result = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    if result.size != img.size:
        result = result.resize(img.size, Image.LANCZOS)
    return result


def _bytes_to_image(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, compress_level=settings.rembg_png_compression)
    return buf.getvalue()


# ========================== ENUMS & CONSTANTS ==========================

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


# ========================== CONFIGURATION ==========================

@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 512
    max_output_dimension: int = 768
    min_dimension: int = 128
    max_file_size_mb: int = 50
    default_background: str = "transparent"
    default_format: str = "PNG"
    jpeg_quality: int = 95
    png_compression: int = 6
    enable_model_comparison: bool = False
    memory_limit_mb: int = 2048
    max_models_to_try: int = 1
    models_to_try: List[str] = field(default_factory=lambda: [
        "isnet-general-use",
        "u2net",
        "u2netp",
    ])
    preserve_text: bool = False
    preserve_ground: bool = False
    background: str = "transparent"
    subject_type: str = SubjectCategory.UNKNOWN


# ========================== MEMORY MANAGEMENT (br_08) ==========================

class MemoryManager:
    """Lightweight memory management utilities (br_08)."""

    @staticmethod
    def cleanup() -> None:
        gc.collect()

    @staticmethod
    def get_available_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except ImportError:
            return 4096

    @staticmethod
    def get_total_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().total / 1024 / 1024
        except ImportError:
            return 8192


# ========================== SESSION MANAGEMENT ==========================

class _SessionManager:
    """Thread-safe rembg session cache with memory-aware limits."""
    _sessions: Dict[str, Any] = {}
    _disabled_models: set = set()
    _availability_cache: Dict[str, bool] = {}
    _lock = threading.Lock()
    _birefnet_globally_disabled = False
    _max_cached_sessions: int = 1
    _access_order: List[str] = []

    @classmethod
    def _adaptive_max_sessions(cls) -> int:
        try:
            available_mb = MemoryManager.get_available_memory_mb()
            if available_mb < 2048:
                return 0
            if available_mb < 4096:
                return 1
            return 1
        except Exception:
            return 1

    @classmethod
    def get_session(cls, model_name: str) -> Optional[Any]:
        cls._update_birefnet_availability()
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            cls._max_cached_sessions = cls._adaptive_max_sessions()
            if model_name in cls._availability_cache and not cls._availability_cache[model_name]:
                return None
            if model_name not in cls._sessions:
                try:
                    _ensure_rembg()
                    if new_session is None:
                        return None
                    logger.info("Loading rembg model: %s", model_name)
                    cls._sessions[model_name] = new_session(model_name)
                    cls._availability_cache[model_name] = True
                    cls._access_order.append(model_name)
                    cls._enforce_session_limit()
                except Exception as exc:
                    logger.warning("Failed to load model %s: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    cls._availability_cache[model_name] = False
                    return None
            else:
                if model_name in cls._access_order:
                    cls._access_order.remove(model_name)
                cls._access_order.append(model_name)
            return cls._sessions[model_name]

    @classmethod
    def _enforce_session_limit(cls) -> None:
        while len(cls._sessions) > cls._max_cached_sessions:
            oldest = cls._access_order.pop(0)
            if oldest in cls._sessions:
                del cls._sessions[oldest]

    @classmethod
    def release_session(cls, model_name: str) -> None:
        with cls._lock:
            if model_name in cls._sessions:
                del cls._sessions[model_name]
            if model_name in cls._access_order:
                cls._access_order.remove(model_name)

    @classmethod
    def has_session(cls, model_name: str) -> bool:
        cls._update_birefnet_availability()
        if model_name in cls._disabled_models:
            return False
        with cls._lock:
            cls._max_cached_sessions = cls._adaptive_max_sessions()
            if model_name in cls._availability_cache and not cls._availability_cache[model_name]:
                return False
            if model_name not in cls._sessions:
                try:
                    _ensure_rembg()
                    if new_session is None:
                        cls._availability_cache[model_name] = False
                        return False
                    cls._sessions[model_name] = new_session(model_name)
                    cls._availability_cache[model_name] = True
                    cls._access_order.append(model_name)
                    cls._enforce_session_limit()
                except Exception as exc:
                    logger.debug("Model %s unavailable: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    cls._availability_cache[model_name] = False
                    return False
            else:
                if model_name in cls._access_order:
                    cls._access_order.remove(model_name)
                cls._access_order.append(model_name)
            return True

    @classmethod
    def _update_birefnet_availability(cls) -> None:
        if cls._birefnet_globally_disabled:
            return
        try:
            available_mb = MemoryManager.get_available_memory_mb()
            if available_mb < 2048:
                logger.warning("Low available memory, disabling BiRefNet globally")
                cls._birefnet_globally_disabled = True
        except Exception:
            pass

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._sessions.clear()
            cls._disabled_models.clear()
            cls._availability_cache.clear()
            cls._birefnet_globally_disabled = False
            cls._access_order.clear()


# ========================== IMAGE HELPERS ==========================

def _resize_image(img: Image.Image, max_dim: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    ratio = max_dim / max(w, h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    return img.resize((new_w, new_h), Image.BILINEAR)


def _adaptive_max_rembg_dimension(preferred: int) -> int:
    available_mb = MemoryManager.get_available_memory_mb()
    if available_mb < 2048:
        return min(preferred, 384)
    if available_mb < 3072:
        return min(preferred, 448)
    return preferred


def _get_model_max_dimension(model_name: str, preferred: int) -> int:
    if "massive" in model_name:
        return min(preferred, 768)
    if "hrsod" in model_name:
        return min(preferred, 768)
    if "birefnet" in model_name:
        return min(preferred, 1024)
    if "lite" in model_name:
        return min(preferred, 1280)
    return preferred


def _run_model_with_dimension(
    img: Image.Image, session: Any, model_name: str, preferred_dim: int
) -> np.ndarray:
    model_max = _get_model_max_dimension(model_name, preferred_dim)
    current_img = img
    if max(img.size) > model_max:
        ratio = model_max / max(img.size)
        current_img = img.resize(
            (int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS
        )
    raw_output = np.array(_safe_remove(current_img, session).convert("RGBA"))
    if max(img.size) > model_max:
        raw_output = np.array(
            Image.fromarray(raw_output).resize(img.size, Image.LANCZOS)
        )
    return raw_output


def _apply_alpha_composite(rgb_array: np.ndarray, alpha_array: np.ndarray) -> np.ndarray:
    h, w = alpha_array.shape
    alpha_3ch = np.stack([alpha_array] * 3, axis=-1)
    result = np.zeros((h, w, 4), dtype=np.uint8)
    result[:, :, :3] = rgb_array
    result[:, :, 3] = (alpha_3ch * 255).astype(np.uint8)
    return result


def _compose_pure_alpha(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
    """Compose RGBA using pure alpha (no premultiplication).

    Matches br_11/br_12/br_13 convention: RGB untouched,
    transparent pixels forced to RGB=0 (prevents viewer fringing).
    """
    h, w = input_np.shape[:2]
    final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    final_rgba[:, :, :3] = input_np
    final_rgba[:, :, 3] = np.clip(alpha_map * 255, 0, 255).astype(np.uint8)
    final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
    return final_rgba


def _create_canvas(final_img: Image.Image, background: str, max_output_dimension: int) -> Image.Image:
    bg_colors = {
        "transparent": (0, 0, 0, 0),
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
    }
    bg = bg_colors.get(background.lower(), (0, 0, 0, 0))
    target_size = min(max(final_img.width, final_img.height), max_output_dimension)
    ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
    new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
    resized = final_img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), bg)
    canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
    return canvas


# ========================== STRATEGY CONFIG ==========================

def _filter_heavy_models(models: List[str]) -> List[str]:
    if settings.skip_heavy_models:
        return [m for m in models if m not in _HEAVY_MODELS]
    return models


def _get_strategy_config(strategy: str) -> ProcessingConfig:
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


# ========================== REMOVAL STRATEGY RUNNERS ==========================

def _run_general(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for general")
        return image_bytes

    try:
        alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_rgba = _compose_pure_alpha(input_np, alpha_float)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("general failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_clean_commercial(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_05: Gentle edge refinement, pure high-fidelity extraction."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for clean_commercial")
        return image_bytes

    try:
        raw_alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_alpha = CleanEdgeRefiner.refine(input_np, raw_alpha_float)
        final_alpha[final_alpha < 0.02] = 0.0
        final_alpha[final_alpha > 0.98] = 1.0
        final_rgba = _compose_pure_alpha(input_np, final_alpha)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("clean_commercial failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_precision_geometry(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_06: Scene-aware geometry (human bypass, hand removal, hole fill, thin reconnect)."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for precision_geometry")
        return image_bytes

    try:
        raw_alpha_f = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_mask = (raw_alpha_f > 0.5).astype(np.uint8) * 255

        is_human = SceneAnalyzer.is_human_photo(raw_alpha_f)

        if is_human:
            alpha_f = HumanPreserver.fix_hollows(raw_alpha_f)
        else:
            alpha_mask = HandRemover.remove_if_isolated(alpha_mask)
            alpha_mask = HoleFiller.fill_mask(alpha_mask, min_hole_area=50)
            alpha_mask = ThinPartHandler.handle(alpha_mask, raw_alpha_f)
            alpha_f = alpha_mask.astype(np.float32) / 255.0

        alpha_f = EdgeRefiner.refine(input_np, alpha_f)
        alpha_f[alpha_f < 0.02] = 0.0
        alpha_f[alpha_f > 0.98] = 1.0
        final_rgba = _compose_pure_alpha(input_np, alpha_f)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("precision_geometry failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_production_birefnet(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_08: Multi-model comparison + wood removal + hole filling."""
    _ensure_rembg()
    best_score = -1.0
    best_result = None
    best_model = None

    for model_name in config.models_to_try[: config.max_models_to_try]:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            raw_output = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )

            prob_map = raw_output[:, :, 3].astype(np.float32) / 255.0
            coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
            confidence = (
                float(np.mean(prob_map[prob_map > 0.3]))
                if np.any(prob_map > 0.3)
                else 0.0
            )
            score = (coverage * 0.4) + (confidence * 0.6)

            if score > best_score:
                best_score = score
                best_result = raw_output
                best_model = model_name

            if score > 0.85:
                break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if best_result is None:
        logger.error("All models failed for production_birefnet")
        return image_bytes

    try:
        alpha_float = best_result[:, :, 3].astype(np.float32) / 255.0
        image_rgba = _compose_pure_alpha(input_np, alpha_float)
        image_rgba = WoodBackgroundRemover.remove(image_rgba, alpha_float)
        image_rgba = HoleFiller.fill(image_rgba.astype(np.uint8))
        return _image_to_bytes(Image.fromarray(image_rgba.astype(np.uint8), mode="RGBA"))
    except Exception as exc:
        logger.error("production_birefnet failed: %s", exc)
        return image_bytes
    finally:
        del best_result
        MemoryManager.cleanup()


def _run_ultimate_v11(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_11: Edge shave + color bleed + artifact isolation."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for ultimate_v11")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        alpha_map = ArtifactIsolator.remove_floating_dust(alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("ultimate_v11 failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_ultimate_v12(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_12: Floating artifact removal + bottom text + edge shave + color bleed."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for ultimate_v12")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("ultimate_v12 failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_variant_testing(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_13: Lite variant pipeline (same post-processing as v12)."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for variant_testing")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("variant_testing failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_strategy(
    image_bytes: bytes,
    strategy: str,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    strategy_lower = strategy.lower()
    if strategy_lower == ProcessingStrategy.CLEAN_COMMERCIAL.value:
        return _run_clean_commercial(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.PRECISION_GEOMETRY.value:
        return _run_precision_geometry(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.PRODUCTION_BIREFNET.value:
        return _run_production_birefnet(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V11.value:
        return _run_ultimate_v11(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V12.value:
        return _run_ultimate_v12(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.VARIANT_TESTING.value:
        return _run_variant_testing(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.GENERAL.value:
        return _run_general(image_bytes, config, img, input_np)
    return image_bytes


# ========================== PUBLIC API ==========================

def remove_background(
    image_bytes: bytes,
    model: Optional[str] = None,
    strategy: Optional[str] = None,
) -> bytes:
    """Core background-removal entry point.

    Args:
        image_bytes: Raw image bytes.
        model: Optional specific rembg model name.
        strategy: Optional processing strategy (ProcessingStrategy values).

    Returns:
        PNG bytes with transparent background.
    """
    _ensure_rembg()
    if not _HAS_REMBG or remove is None:
        logger.error("rembg is not installed")
        return image_bytes

    config = ProcessingConfig()
    if strategy:
        config = _get_strategy_config(strategy)

    config.max_rembg_dimension = _adaptive_max_rembg_dimension(config.max_rembg_dimension)

    img = _bytes_to_image(image_bytes)
    img = _resize_image(img, config.max_rembg_dimension)
    input_np = np.array(img.convert("RGB"))

    if strategy:
        try:
            return _run_strategy(image_bytes, strategy, config, img, input_np)
        except Exception as exc:
            logger.error("Strategy %s failed: %s", strategy, exc)

    def _try_model(model_name: str) -> Optional[np.ndarray]:
        session = _SessionManager.get_session(model_name)
        if session is None:
            return None
        try:
            return _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
            return None
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    selected_models = [model] if model else config.models_to_try
    result_image = None
    used_model = None

    if config.enable_model_comparison:
        best_score = -1.0
        best_result = None

        for model_name in selected_models[: config.max_models_to_try]:
            session = _SessionManager.get_session(model_name)
            if session is None:
                continue

            try:
                raw_output = _try_model(model_name)
                if raw_output is None:
                    continue

                prob_map = raw_output[:, :, 3].astype(np.float32) / 255.0
                coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
                confidence = float(np.mean(prob_map[prob_map > 0.3])) if np.any(prob_map > 0.3) else 0.0
                score = (coverage * 0.4) + (confidence * 0.6)

                if score > best_score:
                    best_score = score
                    best_result = raw_output
                    used_model = model_name

                if score > 0.85:
                    break
            except Exception as exc:
                logger.warning("Model comparison failed for %s: %s", model_name, exc)
            finally:
                _SessionManager.release_session(model_name)
                MemoryManager.cleanup()

        if best_result is not None:
            result_image = best_result

    if result_image is None:
        for model_name in selected_models:
            result_image = _try_model(model_name)
            used_model = model_name if result_image is not None else None
            if result_image is not None:
                break

    if result_image is None:
        logger.error("No rembg model session available")
        return image_bytes

    try:
        alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_rgba = _compose_pure_alpha(input_np, alpha_float)
        final_img = Image.fromarray(final_rgba, mode="RGBA")

        if config.background.lower() != "transparent":
            final_img = _create_canvas(final_img, config.background, config.max_output_dimension)

        return _image_to_bytes(final_img)
    except Exception as exc:
        logger.error("Background removal failed with model %s: %s", used_model, exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def remove_background_preset(image_bytes: bytes, preset_name: str) -> bytes:
    """Remove background using a named preset model list.

    Args:
        image_bytes: Raw image bytes.
        preset_name: Key from settings.bg_preset_models.

    Returns:
        PNG bytes with transparent background.
    """
    preset_models = settings.bg_preset_models.get(preset_name)
    if not preset_models:
        logger.warning("Unknown preset %s, falling back to general", preset_name)
        preset_models = settings.bg_preset_models["general"]

    config = ProcessingConfig(
        max_rembg_dimension=settings.max_image_dim,
        models_to_try=preset_models,
        background="transparent",
    )

    img = _bytes_to_image(image_bytes)
    img = _resize_image(img, config.max_rembg_dimension)
    input_np = np.array(img.convert("RGB"))

    for model_name in preset_models:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = np.array(_safe_remove(img, session).convert("RGBA"))
            alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
            final_rgba = _compose_pure_alpha(input_np, alpha_float)
            final_img = Image.fromarray(final_rgba, mode="RGBA")
            return _image_to_bytes(final_img)
        except Exception as exc:
            logger.warning("Model %s failed: %s, trying next", model_name, exc)
            continue
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    logger.error("All preset models failed for preset %s", preset_name)
    return image_bytes


def remove_background_model(image_bytes: bytes, model_name: str) -> bytes:
    """Remove background using a specific model by name.

    Args:
        image_bytes: Raw image bytes.
        model_name: Exact rembg model name (e.g. 'isnet-general-use').

    Returns:
        Processed image bytes with transparent background.
    """
    if model_name not in AVAILABLE_MODELS:
        logger.warning("Model %s not in AVAILABLE_MODELS, using anyway", model_name)
    return remove_background(image_bytes, model=model_name)


def remove_background_strategy(image_bytes: bytes, strategy: str) -> bytes:
    """Remove background using a specific processing strategy.

    Args:
        image_bytes: Raw image bytes.
        strategy: Strategy name (e.g. 'clean_commercial', 'precision_geometry').

    Returns:
        Processed image bytes with transparent background.
    """
    return remove_background(image_bytes, strategy=strategy)


def magic_erase(image_bytes: bytes, mask: np.ndarray) -> bytes:
    """Erase specific regions from an image using a mask.

    Args:
        image_bytes: Raw image bytes.
        mask: NumPy array (H, W) with 255 for regions to erase, 0 for keep.

    Returns:
        Processed image bytes with erased regions made transparent.
    """
    img = _bytes_to_image(image_bytes)
    img_array = np.array(img)

    if mask.shape[:2] != img_array.shape[:2]:
        mask = np.array(Image.fromarray(mask).resize(
            (img_array.shape[1], img_array.shape[0]),
            Image.NEAREST,
        ))

    alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255
    mask_bool = mask > 128
    alpha[mask_bool] = 0

    result = np.zeros_like(img_array)
    result[:, :, :3] = img_array[:, :, :3]
    result[:, :, 3] = alpha

    return _image_to_bytes(Image.fromarray(result, "RGBA"))


def process_folder(
    input_folder: str,
    output_folder: str,
    strategy: Optional[str] = None,
    model: Optional[str] = None,
    background: str = "transparent",
) -> List[Dict[str, Any]]:
    """Batch-process a folder of images with aggressive memory cleanup.

    This is the batch-safe entry point for processing thousands of images.
    It loads one model at a time, processes each image, then releases the
    session and runs ``gc.collect()`` before the next image.
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    supported_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    image_files = sorted(
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in supported_ext
    )

    if not image_files:
        logger.warning("No images found in %s", input_folder)
        return []

    logger.info("Batch processing %d images -> %s", len(image_files), output_folder)
    results: List[Dict[str, Any]] = []

    for idx, img_file in enumerate(image_files, 1):
        logger.info("[%d/%d] %s", idx, len(image_files), img_file.name)
        result: Dict[str, Any] = {
            "input": str(img_file),
            "success": False,
            "time_seconds": 0.0,
        }

        try:
            image_bytes = img_file.read_bytes()
            start = time.perf_counter()

            if strategy:
                output_bytes = remove_background(image_bytes, strategy=strategy)
            elif model:
                output_bytes = remove_background(image_bytes, model=model)
            else:
                output_bytes = remove_background(image_bytes)

            elapsed = time.perf_counter() - start
            result["time_seconds"] = round(elapsed, 2)
            result["output_size_bytes"] = len(output_bytes)

            if isinstance(output_bytes, bytes) and len(output_bytes) > 0:
                out_file = output_path / f"{img_file.stem}.png"
                out_file.write_bytes(output_bytes)
                result["success"] = True
                result["output"] = str(out_file)
            else:
                result["error"] = "empty output"

        except Exception as exc:
            result["error"] = str(exc)
        finally:
            _SessionManager.reset()
            gc.collect()
            results.append(result)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    avg_time = (
        sum(r["time_seconds"] for r in successful) / len(successful)
        if successful
        else 0.0
    )
    logger.info(
        "Batch complete: %d success, %d failed | avg %.2fs",
        len(successful),
        len(failed),
        avg_time,
    )
    return results


def process_product_image(
    image_bytes: bytes,
    background: str = "transparent",
    output_format: str = "PNG",
) -> Dict[str, Any]:
    """Process a product image using the ultimate pipeline.

    Args:
        image_bytes: Raw image bytes.
        background: Background color for output.
        output_format: Output image format.

    Returns:
        Dict with processing results including base64 encoded image.
    """
    config = ProcessingConfig()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_size = img.size
    input_np = np.array(img)

    alpha_map = AISegmenter.generate_alpha(image_bytes, orig_size, config)
    alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
    alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
    alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)

    alpha_uint8 = (alpha_map * 255).astype(np.uint8)
    final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
    final_rgba[:, :, :3] = input_np
    final_rgba[:, :, 3] = alpha_uint8

    final_img = Image.fromarray(final_rgba, mode="RGBA")
    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    output_bytes = buf.getvalue()

    return {
        "base64": base64.b64encode(output_bytes).decode("utf-8"),
        "format": "PNG",
        "width": final_img.width,
        "height": final_img.height,
        "background": background,
    }


def generate_angles(image_bytes: bytes, product_name: str = "", category: str = "") -> List[Dict[str, str]]:
    """Generate AI-suggested descriptions for multiple product photo angles."""
    _ANGLE_PROMPTS = [
        ("Front View", "front view of the product, showing the main face"),
        ("Back View", "rear view of the product, showing the reverse side"),
        ("Side View", "side profile of the product, showing dimensions"),
        ("Detail Shot", "close-up detail showing material texture and quality"),
        ("In Use", "product in use, demonstrating its practical application"),
    ]

    results = []
    for angle_name, angle_context in _ANGLE_PROMPTS:
        description = (
            f"Photograph the {angle_name.lower()} of '{product_name}' to highlight {angle_context}. "
            f"Ensure good lighting and a clean background."
        )
        results.append({
            "angle": angle_name,
            "description": description,
        })

    return results


# ========================== br_05: CLEAN EDGE REFINER ==========================

class CleanEdgeRefiner:
    """Gentle edge refinement for AI-generated alpha masks.

    Br_05 philosophy: AI does 99% of the work. We only do 1% cleanup.
    Three-step process: fringing fix, guided filter smoothing, ghost cleanup.
    """

    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha

        if alpha.dtype != np.float32:
            alpha = alpha.astype(np.float32)

        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0

        try:
            guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
            alpha_f = alpha.astype(np.float32)
            refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
            alpha = np.clip(refined, 0, 1)
        except Exception:
            pass

        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=5)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0

        return alpha


# ========================== br_05 / br_06: BACKGROUND REMOVER LEGACY ==========================

class BackgroundRemover:
    """Legacy clean-commercial and precision-geometry background remover (br_05/br_06)."""

    def __init__(self, config=None):
        self.config = config
        self.session = None
        self.model_name = None
        self.stats = {"total_processed": 0, "total_time": 0, "errors": 0}

    def _load_best_model(self):
        if self.config is None:
            models = ["isnet-general-use", "u2net"]
        else:
            models = self.config.models
        for model_name in models:
            try:
                self.session = _SessionManager.get_session(model_name)
                self.model_name = model_name
                return True
            except Exception:
                pass
        return False

    def process_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        start_time = time.time()
        result = {"input": input_path, "output": output_path, "success": False, "time_seconds": 0}

        try:
            img = Image.open(input_path).convert("RGB")
            img_np = np.array(img)
            h, w = img_np.shape[:2]

            ratio = 1.0
            img_resized = img
            if max(w, h) > 2048:
                ratio = 2048 / max(w, h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            input_bytes = buf.getvalue()

            session = self.session
            if session is None:
                return result

            output_bytes = _safe_remove(img_resized, session)
            out_img = Image.open(io.BytesIO(output_bytes.tobytes() if hasattr(output_bytes, 'tobytes') else output_bytes)).convert("RGBA") if isinstance(output_bytes, Image.Image) else Image.open(io.BytesIO(output_bytes)).convert("RGBA")

            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)

            raw_alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            final_alpha = CleanEdgeRefiner.refine(img_np, raw_alpha)
            final_alpha[final_alpha < 0.02] = 0.0
            final_alpha[final_alpha > 0.98] = 1.0

            alpha_uint8 = np.clip(final_alpha * 255, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(np.dstack([img_np, alpha_uint8]), mode="RGBA")

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result_img.save(output_path, "PNG", compress_level=6)

            elapsed = time.time() - start_time
            result.update({"success": True, "time_seconds": round(elapsed, 2)})
            self.stats["total_processed"] += 1
            self.stats["total_time"] += elapsed
        except Exception as exc:
            logger.error("BackgroundRemover failed: %s", exc)
            result["error"] = str(exc)
            self.stats["errors"] += 1

        return result

    def process_folder(self, input_folder: str, output_folder: str) -> List[Dict[str, Any]]:
        input_path = Path(input_folder)
        output_path = Path(output_folder)

        if not input_path.exists():
            logger.error("Input folder not found: %s", input_folder)
            return []

        supported_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
        image_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in supported_ext]

        if not image_files:
            logger.warning("No images found in %s", input_folder)
            return []

        if not self._load_best_model():
            logger.error("No models could be loaded!")
            return []

        output_path.mkdir(parents=True, exist_ok=True)
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f"{img_file.stem}.png"
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()

        successful = [r for r in results if r["success"]]
        logger.info("BR05 legacy: %d/%d processed", len(successful), len(results))
        return results


# ========================== br_06: PRECISION GEOMETRY CLASSES ==========================

class SceneAnalyzer:
    """Analyze image scene to determine optimal processing strategy (br_06)."""

    @staticmethod
    def analyze(image_bytes: bytes) -> Dict[str, Any]:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        h, w = img_array.shape[:2]

        has_human = False
        has_product = False
        has_text = False
        complexity = "simple"

        if h > 500 and w > 500:
            complexity = "medium"
        if h > 1500 or w > 1500:
            complexity = "high"

        gray = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY) if _HAS_CV2 else None
        if gray is not None:
            edge_density = float(np.mean(cv2.Canny(gray, 50, 150)))
            if edge_density > 50:
                complexity = "complex"

        return {
            "width": w,
            "height": h,
            "complexity": complexity,
            "has_human": has_human,
            "has_product": has_product,
            "has_text": has_text,
            "recommended_strategy": ProcessingStrategy.CLEAN_COMMERCIAL.value,
        }

    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        """If there is foreground in the top 25% of the image, it's a human (head)."""
        if not _HAS_CV2:
            return False
        h, w = alpha.shape
        top_region = alpha[: int(h * 0.25), :]
        foreground_ratio = float(np.sum(top_region > 0.5)) / top_region.size
        return foreground_ratio > 0.01


class HandRemover:
    """Remove hand artifacts from background removal results (br_06)."""

    @staticmethod
    def remove(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        """Removes hands by shape. If no head, secondary blobs attached to main product are hands."""
        if not _HAS_CV2:
            return alpha_mask
        contours, _ = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours or len(contours) <= 1:
            return alpha_mask

        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        main_product = contours[0]
        main_area = cv2.contourArea(main_product)
        main_mask = np.zeros_like(alpha_mask)
        cv2.drawContours(main_mask, [main_product], -1, 255, -1)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
        danger_zone = cv2.dilate(main_mask, kernel, iterations=1)

        removed = False
        for i in range(1, len(contours)):
            cnt = contours[i]
            area = cv2.contourArea(cnt)
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                overlap = int(np.sum((cnt_mask > 0) & (danger_zone > 0)))
                if overlap > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True

        if removed:
            logger.info("    Removed isolated hand (geometric)")
        return alpha_mask


class HoleFiller:
    """Fill holes inside the foreground object after background removal (br_05/br_06)."""

    @staticmethod
    def fill(image_rgba: np.ndarray) -> np.ndarray:
        """Fill holes in an RGBA image (returns same shape as input).

        Used by production_birefnet strategy.
        """
        alpha = image_rgba[:, :, 3] if image_rgba.ndim > 2 else image_rgba
        binary_mask = (alpha > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1 : h + 1, 1 : w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1 : h + 1, 1 : w + 1] == 0
        filled_count = int(np.sum(internal_holes))
        if filled_count > 50:
            binary_mask[internal_holes] = 255
            logger.debug("Filled internal holes (%dpx)", filled_count)
        return np.dstack([image_rgba[:, :, :3], binary_mask]) if image_rgba.ndim > 2 else binary_mask

    @staticmethod
    def fill_mask(alpha_mask: np.ndarray, min_hole_area: int = 50) -> np.ndarray:
        """Fill holes in an alpha mask (uint8, shape HxW).

        Used by precision_geometry strategy.
        """
        if not _HAS_CV2:
            return alpha_mask
        binary_mask = (alpha_mask > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1 : h + 1, 1 : w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1 : h + 1, 1 : w + 1] == 0
        filled_count = int(np.sum(internal_holes))
        if filled_count > min_hole_area:
            binary_mask[internal_holes] = 255
            logger.debug("Filled internal holes (%dpx)", filled_count)
        return binary_mask


class ThinPartHandler:
    """Reconnect thin parts (e.g., watchbands) that may have been disconnected (br_06)."""

    @staticmethod
    def handle(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            alpha = cv2.dilate(alpha, kernel, iterations=1)
            alpha = cv2.erode(alpha, kernel, iterations=1)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        """Reconnects broken thin parts (watchbands) using directional brushes."""
        if not _HAS_CV2:
            return alpha_mask
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        safe_reconnect = original_alpha_f > 0.05
        final = np.where(safe_reconnect & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask)
        reconnected = int(np.sum((final > 0) & (alpha_mask == 0)))
        if reconnected > 20:
            logger.info("    Reconnected thin parts (%dpx)", reconnected)
        return final


class HumanPreserver:
    """Preserve human subjects during background removal (br_06)."""

    @staticmethod
    def preserve(image_bytes: bytes) -> bytes:
        return remove_background(image_bytes, model="birefnet-portrait")

    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        """Fixes human issues (hollow eyes) WITHOUT destroying hair/edges."""
        if not _HAS_CV2:
            return alpha_f
        solid_mask = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        hollows = (alpha_f < 0.1) & (dilated > 0)
        if int(np.sum(hollows)) > 10:
            alpha_f[hollows] = 0.85
            logger.info("    Soft-filled human hollows (eyes/face)")
        return alpha_f


class EdgeRefiner:
    """Micro-smooth staircase jitters, then snap perfectly to RGB edges (br_06)."""

    @staticmethod
    def refine(image_np: np.ndarray, alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_f

        if alpha_f.dtype != np.float32:
            alpha_f = alpha_f.astype(np.float32) / 255.0

        binary_fg = (alpha_f > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha_f > 0.3) & (alpha_f < 0.95) & (safe_zone > 0)
            alpha_f[semi_inside] = 1.0

        alpha_blurred = cv2.GaussianBlur(alpha_f, (3, 3), 0.8)
        try:
            guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
            refined = cv2.ximgproc.guidedFilter(guide, alpha_blurred, radius=6, eps=0.0001)
            alpha_f = np.clip(refined, 0, 1)
        except Exception:
            alpha_f = alpha_blurred

        binary_final = (alpha_f > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        near_edge = cv2.dilate(binary_final, kernel, iterations=1)
        ghost_mask = (near_edge == 0) & (alpha_f < 0.1)
        alpha_f[ghost_mask] = 0.0

        return alpha_f


# ========================== br_08: PRODUCTION PIPELINE CLASSES ==========================

class ColorSpaceUtils:
    """Utility class for color space conversions (br_08)."""

    @staticmethod
    def rgb_to_gray(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return np.mean(image[:, :, :3], axis=2)
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    @staticmethod
    def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    @staticmethod
    def rgb_to_lab(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    @staticmethod
    def detect_skin_regions(image: np.ndarray) -> np.ndarray:
        hsv = ColorSpaceUtils.rgb_to_hsv(image)
        lower1 = np.array([0, 20, 70], dtype=np.uint8)
        upper1 = np.array([20, 255, 255], dtype=np.uint8)
        lower2 = np.array([160, 20, 70], dtype=np.uint8)
        upper2 = np.array([180, 255, 255], dtype=np.uint8)
        mask1 = cv2.inRange(hsv, lower1, upper1) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        mask2 = cv2.inRange(hsv, lower2, upper2) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        skin_mask = cv2.bitwise_or(mask1, mask2) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)) if _HAS_CV2 else np.ones((5, 5), np.uint8)
        return cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2) if _HAS_CV2 else skin_mask


class ImageLoader:
    """Load and preprocess images for background removal (br_08)."""

    @staticmethod
    def load_from_bytes(image_bytes: bytes) -> Tuple[Image.Image, np.ndarray]:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.load()
        return img, np.array(img)

    @staticmethod
    def preprocess_for_segmentation(image_np: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)


class QualityAnalyzer:
    """Analyze image quality for optimal processing (br_08)."""

    @staticmethod
    def analyze(image_np: np.ndarray) -> Dict[str, float]:
        gray = ColorSpaceUtils.rgb_to_gray(image_np)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return {
            "texture_complexity": float(np.var(laplacian)),
            "brightness": float(np.mean(gray)),
        }


class SubjectDetector:
    """Detect subject type (product, human, clothing, food) from initial mask (br_08)."""

    @staticmethod
    def detect(image_np: np.ndarray, initial_mask: np.ndarray) -> Tuple[str, Dict[str, float]]:
        metrics = {}

        try:
            skin_mask = ColorSpaceUtils.detect_skin_regions(image_np)
            metrics["skin_ratio"] = float(np.sum(skin_mask > 0)) / skin_mask.size

            mask_binary = (initial_mask > 127).astype(np.uint8)
            metrics["coverage"] = float(np.sum(mask_binary > 0)) / mask_binary.size

            gray_full = ColorSpaceUtils.rgb_to_gray(image_np)
            full_edges = cv2.Canny(gray_full, 50, 150)
            metrics["edge_density"] = float(np.sum(full_edges > 0)) / full_edges.size

            if metrics.get("skin_ratio", 0) < 0.05:
                subject_type = SubjectCategory.CLOTHING.value if metrics.get("edge_density", 0) > 0.1 else SubjectCategory.PRODUCT.value
            elif metrics.get("skin_ratio", 0) > 0.15:
                if metrics.get("edge_density", 0) < 0.15:
                    subject_type = SubjectCategory.HUMAN.value
                else:
                    subject_type = SubjectCategory.CLOTHING.value
            else:
                subject_type = SubjectCategory.PRODUCT.value

        except Exception as exc:
            logger.warning("Subject detection failed: %s, using default", exc)
            subject_type = SubjectCategory.PRODUCT.value

        return subject_type, metrics


class ModelSelector:
    """Select optimal model list per subject type (br_08)."""

    def __init__(self):
        self.model_configs = {
            SubjectCategory.PRODUCT: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["u2net", "silueta"],
            },
            SubjectCategory.HUMAN: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["silueta"],
            },
            SubjectCategory.CLOTHING: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["silueta"],
            },
            SubjectCategory.UNKNOWN: {
                "primary": ["isnet-general-use", "birefnet-general"],
                "fallback": ["u2net", "silueta"],
            },
        }

    def select(self, subject_type: str) -> Dict[str, Any]:
        return self.model_configs.get(subject_type, self.model_configs[SubjectCategory.UNKNOWN])


class MultiModelSegmenter:
    """Multi-model segmentation with memory-safe fallbacks (br_08)."""

    _global_birefnet_disabled = False

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.available_models: List[str] = []
        self._availability_cache: Dict[str, bool] = {}

        if not MultiModelSegmenter._global_birefnet_disabled:
            total_mem = MemoryManager.get_total_memory_mb()
            if total_mem < 8192:
                logger.warning("Low total RAM (%.0fMB). Disabling BiRefNet globally.", total_mem)
                MultiModelSegmenter._global_birefnet_disabled = True

    def _check_model_availability(self, model_name: str) -> bool:
        if model_name in self._availability_cache:
            return self._availability_cache[model_name]

        if "birefnet" in model_name:
            if MultiModelSegmenter._global_birefnet_disabled:
                self._availability_cache[model_name] = False
                return False
            available_mem = MemoryManager.get_available_memory_mb()
            if available_mem < 2048:
                logger.warning("Low memory (%.0fMB). Disabling %s", available_mem, model_name)
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
                return False

        try:
            session = new_session(model_name)
            self._availability_cache[model_name] = session is not None
            return self._availability_cache[model_name]
        except Exception as exc:
            logger.debug("Model %s not available: %s", model_name, exc)
            self._availability_cache[model_name] = False
            return False

    def _get_session(self, model_name: str):
        with self._lock:
            if model_name not in self.sessions:
                if not self._check_model_availability(model_name):
                    return None
                try:
                    self.sessions[model_name] = new_session(model_name)
                    if model_name not in self.available_models:
                        self.available_models.append(model_name)
                except Exception as exc:
                    logger.warning("Model %s failed: %s", model_name, exc)
                    if "birefnet" in model_name:
                        MultiModelSegmenter._global_birefnet_disabled = True
                    return None
            return self.sessions[model_name]

    def _generate_probability_map(
        self,
        image_bytes: bytes,
        model_name: str,
        orig_size: Tuple[int, int],
        config: ProcessingConfig,
    ) -> Optional[np.ndarray]:
        _ensure_rembg()
        session = self._get_session(model_name)
        if session is None:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            max_dim = config.max_rembg_dimension
            if "birefnet" in model_name:
                max_dim = min(max_dim, 768)
                logger.debug("Using reduced resolution (%dpx) for %s", max_dim, model_name)

            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                input_bytes = buf.getvalue()
            else:
                input_bytes = image_bytes

            output_bytes = remove(input_bytes, session=session, alpha_matting=False)
            output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

            if max(w, h) > max_dim:
                output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)

            alpha = np.array(output_img.split()[-1], dtype=np.uint8)
            prob_map = alpha.astype(np.float32) / 255.0

            del output_img, alpha, output_bytes
            return prob_map

        except MemoryError as exc:
            logger.error("Model %s OOM: %s", model_name, exc)
            if "birefnet" in model_name:
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
            return None

        except Exception as exc:
            error_msg = str(exc)
            if "bad allocation" in error_msg or "Failed to allocate" in error_msg or "RUNTIME_EXCEPTION" in error_msg:
                logger.error("Model %s memory allocation failed", model_name)
                if "birefnet" in model_name:
                    MultiModelSegmenter._global_birefnet_disabled = True
                    self._availability_cache[model_name] = False
            else:
                logger.error("Model %s failed: %s", model_name, exc)
            return None

    def segment_with_comparison(
        self,
        image_bytes: bytes,
        model_config: Dict[str, Any],
        orig_size: Tuple[int, int],
        config: ProcessingConfig,
    ) -> Tuple[np.ndarray, str]:
        models_to_try = model_config["primary"] + model_config["fallback"]
        available_models = [m for m in models_to_try if self._check_model_availability(m)]

        if not available_models:
            logger.error("No models available!")
            return None, ""

        best_prob_map = None
        best_model = ""
        best_score = -1
        models_tried = 0

        for model_name in available_models[: config.max_models_to_try]:
            logger.info("Testing %s...", model_name)

            mem_usage = MemoryManager.get_available_memory_mb()
            if mem_usage < 1024:
                logger.warning("Low memory (%.0fMB), stopping model tests", mem_usage)
                break

            prob_map = self._generate_probability_map(image_bytes, model_name, orig_size, config)

            if prob_map is not None:
                models_tried += 1
                coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
                confidence = float(np.mean(prob_map[prob_map > 0.3])) if np.any(prob_map > 0.3) else 0.0
                score = (coverage * 0.4) + (confidence * 0.6)

                logger.info(
                    "  %s - Coverage: %.1f%%, Confidence: %.1f%%, Score: %.3f",
                    model_name, coverage * 100, confidence * 100, score,
                )

                if score > best_score:
                    best_score = score
                    best_prob_map = prob_map
                    best_model = model_name

                    if score > 0.85:
                        logger.info("  Excellent score (%.3f), stopping model tests", score)
                        break
            else:
                logger.warning("  %s failed, trying next model...", model_name)

            gc.collect()

        if best_prob_map is not None:
            logger.info("Selected best model: %s (score: %.3f, tested %d models)", best_model, best_score, models_tried)
            return best_prob_map, best_model

        return None, ""


class WoodBackgroundRemover:
    """Specialized remover for wood texture backgrounds inside product gaps (br_08)."""

    @staticmethod
    def remove(image_rgba: np.ndarray, fused_prob_map: np.ndarray = None) -> np.ndarray:
        """Remove wood texture background from inside product gaps."""
        if not _HAS_CV2:
            return image_rgba
        gray = cv2.cvtColor(image_rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
        texture_variance = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)))
        if texture_variance < 150:
            return image_rgba

        h, w = image_rgba.shape[:2]
        if h * w > 300000:
            corner_size = min(h, w) // 8
        else:
            corner_size = min(h, w) // 6

        corner_samples = np.concatenate([
            image_rgba[:corner_size, :corner_size, :3].reshape(-1, 3),
            image_rgba[:corner_size, -corner_size:, :3].reshape(-1, 3),
            image_rgba[-corner_size:, :corner_size, :3].reshape(-1, 3),
            image_rgba[-corner_size:, -corner_size:, :3].reshape(-1, 3),
        ])
        bg_color = np.median(corner_samples, axis=0)
        all_pixels = image_rgba[:, :, :3].reshape(-1, 3)
        distances = np.linalg.norm(all_pixels - bg_color, axis=1)
        bg_mask_flat = distances < 70
        bg_mask = bg_mask_flat.reshape(h, w).astype(np.uint8)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        if fused_prob_map is not None and h * w <= 300000:
            product_mask = (fused_prob_map > 0.25).astype(np.uint8) * 255
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(product_mask, connectivity=8)
            if num_labels > 1:
                areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
                areas.sort(key=lambda x: x[1], reverse=True)
                if areas:
                    largest_label = areas[0][0]
                    if areas[0][1] > (h * w * 0.05):
                        product_region = (labels == largest_label).astype(np.uint8)
                        product_region = cv2.dilate(product_region, kernel, iterations=1)
                        bg_mask = cv2.bitwise_and(bg_mask, 255 - product_region)

        image_rgba[bg_mask > 0, 3] = 0
        logger.info("    Removed %d wood background pixels", int(np.sum(bg_mask > 0)))
        return image_rgba


class ZoziBackgroundRemover:
    """Full production pipeline orchestrator (br_08 Zozi v20 style)."""

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.segmenter = MultiModelSegmenter()
        self.model_selector = ModelSelector()
        logger.info("Zozi AI - Pipeline Initialized (Resolution: %dpx)", self.config.max_rembg_dimension)

    def process(self, image_bytes: bytes, background: str = "transparent", output_format: str = "PNG") -> Dict[str, Any]:
        try:
            start_time = time.time()

            input_img, input_np = ImageLoader.load_from_bytes(image_bytes)
            orig_size = input_img.size
            logger.info("Image: %dx%d", orig_size[0], orig_size[1])

            input_np_enhanced = ImageLoader.preprocess_for_segmentation(input_np)
            quality_metrics = QualityAnalyzer.analyze(input_np)

            initial_prob_map = self.segmenter._generate_probability_map(
                image_bytes, "isnet-general-use", orig_size, self.config
            )
            if initial_prob_map is None:
                return {"error": "Initial segmentation failed"}

            initial_mask = (initial_prob_map > 0.3).astype(np.uint8) * 255
            subject_type, subject_metrics = SubjectDetector.detect(input_np_enhanced, initial_mask)
            logger.info("Detected: %s", subject_type)

            model_config = self.model_selector.select(subject_type)
            fused_prob_map, best_model = self.segmenter.segment_with_comparison(
                image_bytes, model_config, orig_size, self.config
            )
            if fused_prob_map is None:
                return {"error": "Segmentation failed - all models failed"}
            logger.info("Best model: %s", best_model)

            h, w = input_np.shape[:2]
            final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            for i in range(3):
                final_rgba[:, :, i] = (input_np[:, :, i].astype(np.float32) * fused_prob_map).astype(np.uint8)
            final_rgba[:, :, 3] = (fused_prob_map * 255).astype(np.uint8)

            logger.info("Wood background removal...")
            final_rgba = WoodBackgroundRemover.remove(final_rgba, fused_prob_map)

            logger.info("Hole filling...")
            final_rgba = HoleFiller.fill(final_rgba)

            final_img = Image.fromarray(final_rgba, mode="RGBA")
            canvas = Exporter.create_canvas(final_img, background, self.config)
            if background.lower() == "transparent":
                output_format = "PNG"
            encoded, final_format = Exporter.encode(canvas, output_format, self.config)
            elapsed = round(time.time() - start_time, 2)

            logger.info("Completed in %ds | Subject: %s | Model: %s", elapsed, subject_type, best_model)

            return {
                "base64": base64.b64encode(encoded).decode("utf-8"),
                "format": final_format,
                "width": canvas.width,
                "height": canvas.height,
                "processing_time_seconds": elapsed,
                "subject_type": subject_type,
                "best_model": best_model,
                "file_size_kb": round(len(encoded) / 1024, 1),
            }
        finally:
            MemoryManager.cleanup()


# ========================== br_11/12/13: ULTIMATE PIPELINE CLASSES ==========================

class AISegmenter:
    """AI Segmenter with configurable model fallback chain (br_11/br_12/br_13).

    Supports multiple model variants:
    - birefnet-general / isnet-general-use / u2net (general fallback)
    - birefnet-massive / birefnet-hrsod / u2net_cloth_seg (v12 specialized)
    - birefnet-general-lite / briaai-rmbg-1.4 (v13 lite variants)
    """

    _disabled_models = set()
    _sessions: Dict[str, Any] = {}
    _lock = threading.Lock()
    _birefnet_disabled = False

    @classmethod
    def _get_session(cls, model_name: str):
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            if model_name not in cls._sessions:
                try:
                    from rembg import new_session
                    logger.info("  Loading model: %s...", model_name)
                    cls._sessions[model_name] = new_session(model_name)
                except Exception as exc:
                    logger.warning("Failed to load %s: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    return None
            return cls._sessions[model_name]

    @classmethod
    def generate_alpha(
        cls,
        image_bytes: bytes,
        orig_size: Tuple[int, int],
        config: ProcessingConfig = None,
        models_to_try: Optional[List[str]] = None,
    ) -> np.ndarray:
        """Run AI segmentation and return float alpha map (0-1 range).

        Args:
            image_bytes: Raw PNG/JPEG bytes.
            orig_size: (width, height) to restore output to.
            config: Optional ProcessingConfig for dimension hints.
            models_to_try: Optional override model list. Falls back to combined list.

        Returns:
            Float32 numpy array (H, W) in range [0, 1].
        """
        _ensure_rembg()
        if remove is None:
            raise RuntimeError("rembg is not available")

        config = config or ProcessingConfig()

        if models_to_try is None:
            models_to_try = [
                "birefnet-general",
                "birefnet-general-lite",
                "isnet-general-use",
                "u2net",
                "u2netp",
                "u2net_cloth_seg",
                "birefnet-massive",
                "birefnet-hrsod",
                "briaai-rmbg-1.4",
            ]

        for model_name in models_to_try:
            session = cls._get_session(model_name)
            if session is None:
                continue

            try:
                logger.info("  Running AI Model: %s...", model_name)
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size

                max_dim = config.max_rembg_dimension
                if "massive" in model_name or "hrsod" in model_name:
                    max_dim = min(max_dim, 768)
                elif "birefnet" in model_name and "lite" not in model_name:
                    max_dim = min(max_dim, 1024)
                if "lite" in model_name:
                    max_dim = min(max_dim, 1280)

                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img_resized = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img_resized.save(buf, format="JPEG", quality=92)
                    input_bytes = buf.getvalue()
                else:
                    input_bytes = image_bytes

                output_bytes = remove(input_bytes, session=session, alpha_matting=False)
                output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

                if max(w, h) > max_dim:
                    output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)

                alpha = np.array(output_img.split()[-1])
                logger.info("  %s succeeded", model_name)
                return alpha.astype(np.float32) / 255.0

            except MemoryError as exc:
                logger.error("  %s OOM: %s", model_name, exc)
                cls._disabled_models.add(model_name)
            except Exception as exc:
                if "bad allocation" in str(exc).lower() or "memory" in str(exc).lower():
                    cls._disabled_models.add(model_name)
                logger.warning("  %s failed: %s", model_name, exc)

        raise Exception("All AI models failed.")


class EdgeShaver:
    """Shave trailing edges to fix jagged fuzzy edges (br_11/br_12/br_13)."""

    @staticmethod
    def shave(image_bytes: bytes, erosion_amount: int = 2) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erosion_amount, erosion_amount))
            alpha = cv2.erode(alpha, kernel, iterations=1)
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        """Shave trailing edges to fix jagged fuzzy edges."""
        if not _HAS_CV2:
            return alpha_map
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 1.0)
        return alpha_smooth.astype(np.float32) / 255.0


class GlobalBackgroundBleeder:
    """Fix color bleeding (e.g., wood inside product gaps) using K-Means border sampling (br_11/br_12/br_13)."""

    @staticmethod
    def fix(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2 and alpha.shape[0] > 0 and alpha.shape[1] > 0:
            border_mask = np.zeros_like(alpha, dtype=np.uint8)
            border_mask[0, :] = 255
            border_mask[-1, :] = 255
            border_mask[:, 0] = 255
            border_mask[:, -1] = 255
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (12, 12))
            border_mask = cv2.dilate(border_mask, kernel, iterations=3)

            rgb = img_array[:, :, :3].astype(np.float32)
            border_pixels = rgb[border_mask > 0]
            if len(border_pixels) > 100:
                mean_border_color = np.mean(border_pixels, axis=0)
                color_dist = np.linalg.norm(rgb - mean_border_color, axis=2)
                alpha_blend_arr = np.clip(1.0 - color_dist / 255.0, 0, 1)
                alpha = np.clip(alpha.astype(np.float32) * (1 - alpha_blend_arr * 0.3), 0, 255).astype(np.uint8)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        """Fix color bleeding using K-Means border sampling."""
        if not _HAS_CV2:
            return alpha_map
        h, w = input_np.shape[:2]
        if h * w > 500000:
            return alpha_map
        border = int(min(h, w) * 0.05)
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 3, 1.0)
        _, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 2, cv2.KMEANS_RANDOM_CENTERS)
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[np.argmax(counts)]
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        color_match = dist < 35.0
        ai_confident = alpha_map > 0.90
        bleed_mask = color_match & (~ai_confident)
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        return alpha_final


class ArtifactIsolator:
    """Isolate and remove floating dust/artifacts from background removal (br_11)."""

    @staticmethod
    def isolate(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(alpha, connectivity=8)
            if num_labels > 1:
                min_area = 50
                for i in range(1, num_labels):
                    area = stats[i, cv2.CC_STAT_AREA]
                    if area < min_area:
                        alpha[labels == i] = 0

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_floating_dust(alpha_map: np.ndarray) -> np.ndarray:
        """Removes small isolated floating artifacts."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        if h * w > 300000:
            return alpha_map
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        min_area = int((h * w) * 0.005)
        alpha_clean = alpha_map.copy()
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                alpha_clean[labels == i] = 0.0
        return alpha_clean


class FloatingArtifactRemover:
    """Remove floating artifacts (e.g., gold piece behind perfume) (br_12/br_13)."""

    @staticmethod
    def remove(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            blurred = cv2.GaussianBlur(alpha, (9, 9), 0)
            diff = cv2.absdiff(alpha, blurred)
            _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            alpha = cv2.bitwise_and(alpha, mask)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        """Remove floating background props using connected component analysis."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        if h * w > 300000:
            return alpha_map
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num_labels <= 1:
            return alpha_map

        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        main_x = stats[largest_label, cv2.CC_STAT_LEFT]
        main_y = stats[largest_label, cv2.CC_STAT_TOP]
        main_w = stats[largest_label, cv2.CC_STAT_WIDTH]
        main_h = stats[largest_label, cv2.CC_STAT_HEIGHT]
        main_cx = main_x + main_w / 2
        main_cy = main_y + main_h / 2

        alpha_clean = alpha_map.copy()
        for i in range(1, num_labels):
            if i == largest_label:
                continue
            area = stats[i, cv2.CC_STAT_AREA]
            if area > (h * w) * 0.02:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                comp_cx = x + comp_w / 2
                comp_cy = y + comp_h / 2
                dist = np.sqrt((comp_cx - main_cx) ** 2 + (comp_cy - main_cy) ** 2)
                if dist > main_w * 1.5:
                    alpha_clean[labels == i] = 0.0
        return alpha_clean


class BottomTextEraser:
    """Remove bottom text/watermark from images (br_12/br_13)."""

    @staticmethod
    def erase(image_bytes: bytes, bottom_ratio: float = 0.15) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        h, w = img_array.shape[:2]

        if _HAS_CV2:
            bottom_start = int(h * (1 - bottom_ratio))
            alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255
            alpha[bottom_start:, :] = 0

            result = np.zeros_like(img_array)
            result[:, :, :3] = img_array[:, :, :3]
            result[:, :, 3] = alpha
            return _image_to_bytes(Image.fromarray(result, "RGBA"))

        return image_bytes

    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray, input_np: np.ndarray) -> np.ndarray:
        """Remove bottom text/watermark from alpha map."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        bottom_region = binary[int(h * 0.8) :, :]
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        alpha_clean = alpha_map.copy()
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h * 0.8)
            aspect_ratio = float(cw) / ch if ch > 0 else 0
            if 100 < area < 5000 and aspect_ratio > 2.0:
                if global_y > h * 0.90:
                    alpha_clean[global_y : global_y + ch, x : x + cw] = 0.0
        return alpha_clean


# ========================== br_08 / br_11 / br_12 / br_13: EXPORTERS ==========================

class Exporter:
    """Export processed images with alpha composition (br_08, br_11, br_12, br_13)."""

    @staticmethod
    def create_canvas(final_img: Image.Image, background: str, config: ProcessingConfig) -> Image.Image:
        bg_colors = {
            "transparent": (0, 0, 0, 0),
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
        }
        bg = bg_colors.get(background.lower(), (0, 0, 0, 0))
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_size, target_size), bg)
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        return canvas

    @staticmethod
    def encode(canvas: Image.Image, output_format: str, config: ProcessingConfig) -> Tuple[bytes, str]:
        if output_format.upper() in ("JPEG", "JPG"):
            canvas = canvas.convert("RGB")
            output_format = "JPEG"
            save_kwargs = {"quality": config.jpeg_quality, "optimize": True}
        else:
            output_format = "PNG"
            save_kwargs = {"optimize": True, "compress_level": config.png_compression}

        buf = io.BytesIO()
        canvas.save(buf, format=output_format, **save_kwargs)
        return buf.getvalue(), output_format

    @staticmethod
    def process_and_save(input_bytes: bytes, output_path: str, config: ProcessingConfig = None):
        """Export pipeline: AI segmentation + post-process + save (br_11/br_12/br_13 style)."""
        config = config or ProcessingConfig()
        img = Image.open(io.BytesIO(input_bytes)).convert("RGB")
        orig_size = img.size
        input_np = np.array(img)

        alpha_map = AISegmenter.generate_alpha(input_bytes, orig_size, config)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)

        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = alpha_uint8

        trans_mask = final_rgba[:, :, 3] == 0
        final_rgba[trans_mask, :3] = 0

        final_img = Image.fromarray(final_rgba, mode="RGBA")
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        canvas.save(output_path, format="PNG", optimize=True)
