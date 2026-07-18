"""
Background Removal Presets — consolidated service for supplier product uploads.

Optimised for low-RAM / low-CPU VPS environments:
  - Global semaphore limits concurrent inferences (default 2).
  - LRU session cache with max 2 models loaded at once.
  - Aggressive pre-downscale before rembg inference (max 768 px).
  - Memory-pressure detection skips heavy OpenCV post-processing.
  - Every model failure degrades gracefully; never crashes.
"""

from __future__ import annotations

import gc
import io
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    _HAS_CV2 = False

# ── Config (tune via environment variables) ────────────────────────────

MAX_CONCURRENT = int(os.environ.get("BG_MAX_CONCURRENT", "2"))
"""Max parallel background removal processes (default 2 for low-RAM VPS)."""

MAX_SESSION_CACHE = int(os.environ.get("BG_MAX_SESSION_CACHE", "2"))
"""Max rembg model sessions cached in memory at once (default 2)."""

MAX_IMAGE_DIM = int(os.environ.get("BG_MAX_IMAGE_DIM", "768"))
"""Downscale any image larger than this before rembg inference."""

LITE_MAX_DIM = int(os.environ.get("BG_LITE_MAX_DIM", "512"))
"""Downscale for heavy models (birefnet-massive, birefnet-hrsod)."""

MEMORY_WARN_MB = int(os.environ.get("BG_MEMORY_WARN_MB", "512"))
"""If available RAM drops below this (MB), skip heavy post-processing."""

SKIP_HEAVY_MODELS = os.environ.get("BG_SKIP_HEAVY_MODELS", "false").lower() == "true"
"""Skip RAM-heavy models (birefnet-massive, birefnet-hrsod) entirely."""

HEAVY_MODELS = {"birefnet-massive", "birefnet-hrsod"}


# ── Preset definitions ────────────────────────────────────────────────

_PRESET_MODELS: dict[str, list[str]] = {
    "general":       ["isnet-general-use", "u2net"],
    "handheld":      ["isnet-general-use", "u2net"],
    "wood":          ["birefnet-general", "isnet-general-use", "u2net"],
    "texture_gap":   ["birefnet-general", "isnet-general-use", "u2net"],
    "marketing":     ["birefnet-massive", "birefnet-hrsod", "u2net_cloth_seg", "isnet-general-use"],
    "cloth_lite":    ["birefnet-general-lite", "u2net_cloth_seg", "briaai-rmbg-1.4", "isnet-general-use"],
}

if SKIP_HEAVY_MODELS:
    _PRESET_MODELS["marketing"] = ["u2net_cloth_seg", "isnet-general-use", "u2net"]

DEFAULT_PRESET = "general"
VALID_PRESETS = list(_PRESET_MODELS.keys())

AVAILABLE_MODELS: list[str] = [
    "birefnet-general",
    "isnet-general-use",
    "u2net",
    "u2net_cloth_seg",
    "birefnet-massive",
    "birefnet-hrsod",
    "briaai-rmbg-1.4",
    "birefnet-general-lite",
    "silueta",
]

if SKIP_HEAVY_MODELS:
    for h in HEAVY_MODELS:
        if h in AVAILABLE_MODELS:
            AVAILABLE_MODELS.remove(h)


# ═══════════════════════════════════════════════════════════════════════
# Memory monitor
# ═══════════════════════════════════════════════════════════════════════

def _available_ram_mb() -> float:
    """Return available RAM in MB (approximate)."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except ImportError:
        return 9999.0


def _low_on_ram() -> bool:
    """Check if available RAM is below the warning threshold."""
    return _available_ram_mb() < MEMORY_WARN_MB


# ═══════════════════════════════════════════════════════════════════════
# Concurrency gate — global semaphore
# ═══════════════════════════════════════════════════════════════════════

_BG_SEMAPHORE = threading.Semaphore(MAX_CONCURRENT)


class _ConcurrencyGate:
    """Context manager that acquires the global bg semaphore."""

    @staticmethod
    def acquire(timeout: float = 30.0) -> bool:
        """Acquire with timeout (seconds). Returns False if timeout."""
        return _BG_SEMAPHORE.acquire(blocking=True, timeout=timeout)

    @staticmethod
    def release() -> None:
        _BG_SEMAPHORE.release()


# ═══════════════════════════════════════════════════════════════════════
# Session manager — LRU eviction + memory-aware
# ═══════════════════════════════════════════════════════════════════════

class _SessionManager:
    """Thread-safe rembg session cache with LRU eviction and memory pressure handling."""

    _sessions: OrderedDict[str, object] = OrderedDict()
    _disabled: set[str] = set()
    _lock = threading.Lock()

    @classmethod
    def get(cls, model_name: str):
        if model_name in cls._disabled:
            return None
        with cls._lock:
            if model_name in cls._sessions:
                cls._sessions.move_to_end(model_name)
                return cls._sessions[model_name]

            if len(cls._sessions) >= MAX_SESSION_CACHE:
                cls._evict_one()

            if _low_on_ram() and len(cls._sessions) > 0:
                cls._evict_one()

            try:
                from rembg import new_session
                cls._sessions[model_name] = new_session(model_name)
                logger.info("bg_cache: loaded model '%s' (cache size %d/%d)",
                            model_name, len(cls._sessions), MAX_SESSION_CACHE)
            except Exception as exc:
                logger.warning("bg_cache: model '%s' load failed: %s", model_name, exc)
                cls._disabled.add(model_name)
                return None
            return cls._sessions.get(model_name)

    @classmethod
    def _evict_one(cls) -> None:
        """Evict the least recently used session."""
        if not cls._sessions:
            return
        _evicted_name, _evicted_session = cls._sessions.popitem(last=False)
        del _evicted_session
        gc.collect()
        logger.info("bg_cache: evicted '%s' (LRU)", _evicted_name)

    @classmethod
    def disable(cls, model_name: str) -> None:
        with cls._lock:
            cls._disabled.add(model_name)
            if model_name in cls._sessions:
                del cls._sessions[model_name]
                gc.collect()
                logger.info("bg_cache: removed disabled model '%s'", model_name)

    @classmethod
    def clear_all(cls) -> None:
        with cls._lock:
            cls._sessions.clear()
            cls._disabled.clear()
            gc.collect()
            logger.info("bg_cache: all sessions cleared")


# ═══════════════════════════════════════════════════════════════════════
# Resolution capping
# ═══════════════════════════════════════════════════════════════════════

def _resolution_cap(model_name: str, requested: int) -> int:
    """Cap segmentation resolution per model. More aggressive for low-RAM VPS."""
    if "lite" in model_name:
        return min(requested, MAX_IMAGE_DIM)
    if model_name in HEAVY_MODELS:
        return min(requested, LITE_MAX_DIM)
    if "birefnet" in model_name:
        return min(requested, MAX_IMAGE_DIM)
    return min(requested, MAX_IMAGE_DIM)


def _maybe_downscale(data: bytes, max_dim: int) -> tuple[bytes, tuple[int, int]]:
    """Downscale image so max dimension ≤ max_dim. Returns (data, original_size)."""
    img = Image.open(io.BytesIO(data))
    orig = img.size
    w, h = orig
    if max(w, h) <= max_dim:
        return data, orig
    ratio = max_dim / float(max(w, h))
    img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue(), orig


# ═══════════════════════════════════════════════════════════════════════
# Inference
# ═══════════════════════════════════════════════════════════════════════

def _generate_alpha(data: bytes, model_priority: list[str], orig_size) -> Optional[np.ndarray]:
    """Run through model priority list, return alpha (H, W) float32 in [0,1]."""
    from rembg import remove

    acquired = _ConcurrencyGate.acquire(timeout=30.0)
    if not acquired:
        logger.warning("bg_preset: concurrency timeout (all %d slots busy), returning None", MAX_CONCURRENT)
        return None

    try:
        for model_name in model_priority:
            if model_name in _SessionManager._disabled:
                continue
            session = _SessionManager.get(model_name)
            if session is None:
                continue
            try:
                logger.info("bg_preset: running rembg model '%s'", model_name)
                scaled_data, _ = _maybe_downscale(data, _resolution_cap(model_name, 9999))
                output_bytes = remove(scaled_data, session=session, alpha_matting=False, post_process_mask=True)
                out_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                out_img = out_img.resize(orig_size, Image.Resampling.LANCZOS)
                alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
                logger.info("bg_preset: model '%s' succeeded", model_name)
                return alpha
            except MemoryError as exc:
                logger.error("bg_preset: %s OOM (%s); disabling", model_name, exc)
                _SessionManager.disable(model_name)
            except Exception as exc:
                msg = str(exc).lower()
                if any(k in msg for k in ("bad allocation", "failed to allocate", "runtime_exception")):
                    logger.error("bg_preset: %s allocation failure; disabling", model_name)
                    _SessionManager.disable(model_name)
                else:
                    logger.warning("bg_preset: model '%s' failed: %s", model_name, exc)
        return None
    finally:
        _ConcurrencyGate.release()


# ═══════════════════════════════════════════════════════════════════════
# Post-processing (lightweight versions)
# ═══════════════════════════════════════════════════════════════════════

class MemoryManager:
    @staticmethod
    def cleanup() -> None:
        gc.collect()


class SceneAnalyzer:
    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        h, _w = alpha.shape
        top_region = alpha[: int(h * 0.25), :]
        fg_ratio = np.sum(top_region > 0.5) / max(top_region.size, 1)
        return fg_ratio > 0.01


class HandRemover:
    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
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
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        danger_zone = cv2.dilate(main_mask, kernel, iterations=1)
        removed = False
        for cnt in contours[1:]:
            area = cv2.contourArea(cnt)
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                if np.sum((cnt_mask > 0) & (danger_zone > 0)) > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True
        if removed:
            logger.info("bg_preset: removed isolated hand (geometric)")
        return alpha_mask


class HoleFiller:
    @staticmethod
    def fill(alpha_mask: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        binary_mask = (alpha_mask > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1:h + 1, 1:w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1:h + 1, 1:w + 1] == 0
        if np.sum(internal_holes) > 50:
            binary_mask[internal_holes] = 255
        return binary_mask


class ThinPartHandler:
    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        safe_reconnect = original_alpha_f > 0.05
        final = np.where(safe_reconnect & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask)
        return final


class HumanPreserver:
    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_f
        solid_mask = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        hollows = (alpha_f < 0.1) & (dilated > 0)
        if np.sum(hollows) > 10:
            alpha_f[hollows] = 0.85
        return alpha_f


class EdgeShaver:
    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((2, 2), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 0.8)
        return alpha_smooth.astype(np.float32) / 255.0


class GlobalBackgroundBleeder:
    """Lightweight version — skips k-means when RAM is low."""

    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        if _low_on_ram():
            logger.info("bg_preset: skipping GlobalBackgroundBleeder (low RAM)")
            return alpha_map
        h, w = input_np.shape[:2]
        border = int(min(h, w) * 0.05)
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 1.0)
        try:
            _ret, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
        except cv2.error:
            return alpha_map
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[int(np.argmax(counts))]
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        color_match = dist < 35.0
        ai_confident = alpha_map > 0.90
        bleed_mask = color_match & (~ai_confident)
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        removed = int(np.sum(bleed_mask))
        if removed:
            logger.info("bg_preset: erased %d gap background pixels", removed)
        return alpha_final


class WoodBackgroundRemover:
    @staticmethod
    def remove(image_rgba: np.ndarray, prob_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return image_rgba
        if _low_on_ram():
            logger.info("bg_preset: skipping WoodBackgroundRemover (low RAM)")
            return image_rgba
        gray = cv2.cvtColor(image_rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
        texture_variance = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)))
        if texture_variance < 150:
            return image_rgba
        h, w = image_rgba.shape[:2]
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
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        product_mask = (prob_map > 0.25).astype(np.uint8) * 255
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(product_mask, connectivity=8)
        if num_labels > 1:
            areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
            areas.sort(key=lambda x: x[1], reverse=True)
            if areas and areas[0][1] > (h * w * 0.05):
                largest_label = areas[0][0]
                product_region = (labels == largest_label).astype(np.uint8)
                product_region = cv2.dilate(product_region, kernel, iterations=2)
                bg_mask = cv2.bitwise_and(bg_mask, 255 - product_region)
        image_rgba[bg_mask > 0, 3] = 0
        return image_rgba


class FloatingArtifactRemover:
    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num_labels <= 1:
            return alpha_map
        largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        main_w = stats[largest_label, cv2.CC_STAT_WIDTH]
        main_x = stats[largest_label, cv2.CC_STAT_LEFT]
        main_y = stats[largest_label, cv2.CC_STAT_TOP]
        main_cx = main_x + main_w / 2
        main_cy = main_y + stats[largest_label, cv2.CC_STAT_HEIGHT] / 2
        alpha_clean = alpha_map.copy()
        for i in range(1, num_labels):
            if i == largest_label:
                continue
            area = stats[i, cv2.CC_STAT_AREA]
            if area > (h * w) * 0.01:
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
    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        bottom_region = binary[int(h * 0.8):, :]
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        alpha_clean = alpha_map.copy()
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h * 0.8)
            aspect_ratio = float(cw) / ch if ch > 0 else 0
            if 100 < area < 5000 and aspect_ratio > 2.0 and global_y > h * 0.90:
                alpha_clean[global_y:global_y + ch, x:x + cw] = 0.0
        return alpha_clean


# ═══════════════════════════════════════════════════════════════════════
# CleanEdgeRefiner — lightweight edge refinement (no guided filter)
# ═══════════════════════════════════════════════════════════════════════

class CleanEdgeRefiner:
    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha

        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0

        if not _low_on_ram():
            try:
                import cv2.ximgproc
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                alpha_f = alpha.astype(np.float32)
                refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
                alpha = np.clip(refined, 0, 1)
            except Exception:
                pass

        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        near_edge = cv2.dilate(binary_final, kernel, iterations=3)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0

        return alpha


# ═══════════════════════════════════════════════════════════════════════
# Compose
# ═══════════════════════════════════════════════════════════════════════

def _compose_rgba(input_np: np.ndarray, alpha: np.ndarray) -> bytes:
    h, w = input_np.shape[:2]
    final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    final_rgba[:, :, :3] = input_np
    final_rgba[:, :, 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    trans_mask = final_rgba[:, :, 3] == 0
    final_rgba[trans_mask, :3] = 0
    buf = io.BytesIO()
    Image.fromarray(final_rgba, mode="RGBA").save(buf, format="PNG", compress_level=4)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════
# Pipeline runner
# ═══════════════════════════════════════════════════════════════════════

def _run_preset(data: bytes, preset: str, fast_mode: bool = False) -> bytes:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    input_np = np.array(img)
    h, w = input_np.shape[:2]
    orig_size = (w, h)

    alpha = _generate_alpha(data, _PRESET_MODELS.get(preset, _PRESET_MODELS[DEFAULT_PRESET]), orig_size)
    if alpha is None:
        logger.warning("bg_preset: all rembg models failed, returning original bytes")
        return data

    is_low_ram = _low_on_ram() or fast_mode

    if preset == "general":
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
    elif preset == "handheld":
        if SceneAnalyzer.is_human_photo(alpha):
            alpha = HumanPreserver.fix_hollows(alpha)
        else:
            alpha_mask = (alpha > 0.5).astype(np.uint8) * 255
            alpha_mask = HandRemover.remove_if_isolated(alpha_mask)
            alpha_mask = HoleFiller.fill(alpha_mask)
            alpha_mask = ThinPartHandler.handle(alpha_mask, alpha)
            alpha = alpha_mask.astype(np.float32) / 255.0
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
    elif preset == "wood":
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
        final_rgba = np.dstack([input_np, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
        if not is_low_ram:
            final_rgba = WoodBackgroundRemover.remove(final_rgba, alpha)
        alpha = final_rgba[:, :, 3].astype(np.float32) / 255.0
        alpha = HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
    elif preset == "texture_gap":
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
        alpha = HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
    elif preset == "marketing":
        alpha = FloatingArtifactRemover.remove_floating_objects(alpha)
        alpha = BottomTextEraser.erase_bottom_text(alpha)
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        if not is_low_ram:
            alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
    elif preset == "cloth_lite":
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        alpha = HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
        alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)

    alpha[alpha < 0.02] = 0.0
    alpha[alpha > 0.98] = 1.0

    MemoryManager.cleanup()
    return _compose_rgba(input_np, alpha)


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

def remove_background_preset(data: bytes, preset: str = DEFAULT_PRESET, fast_mode: bool = False) -> bytes:
    """
    Remove the background using a named preset pipeline.

    Args:
        data: raw image bytes.
        preset: one of ``VALID_PRESETS``.
        fast_mode: skip heavy OpenCV post-processing (k-means, connectedComponents, guided filter).

    Returns:
        Transparent PNG bytes. Original bytes on any failure.
    """
    if preset not in _PRESET_MODELS:
        logger.warning("bg_preset: unknown preset '%s', using '%s'", preset, DEFAULT_PRESET)
        preset = DEFAULT_PRESET
    try:
        return _run_preset(data, preset, fast_mode=fast_mode)
    except Exception as exc:
        logger.warning("bg_preset: preset '%s' failed (%s); returning original", preset, exc)
        return data


def remove_background_model(data: bytes, model_name: str = "isnet-general-use", fast_mode: bool = False) -> bytes:
    """
    Remove the background using a single rembg model directly.

    Args:
        data: raw image bytes.
        model_name: one of ``AVAILABLE_MODELS``.
        fast_mode: skip CleanEdgeRefiner guided filter.

    Returns:
        Transparent PNG bytes. Original bytes on any failure.
    """
    if model_name not in AVAILABLE_MODELS:
        logger.warning("bg_model: unknown model '%s', falling back to isnet-general-use", model_name)
        model_name = "isnet-general-use"
    mod_list = [model_name, "isnet-general-use", "u2net"]
    img = Image.open(io.BytesIO(data)).convert("RGB")
    input_np = np.array(img)
    alpha = _generate_alpha(data, mod_list, img.size)

    if alpha is None:
        logger.warning("bg_model: all models failed, returning original")
        return data

    if not fast_mode:
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
    alpha[alpha < 0.02] = 0.0
    alpha[alpha > 0.98] = 1.0
    MemoryManager.cleanup()
    return _compose_rgba(input_np, alpha)

