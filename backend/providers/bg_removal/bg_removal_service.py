"""
Unified, VPS-safe background-removal service.

This module consolidates the SIX battle-tested pipelines from the
``Working_API/zozi_ai_image_service`` scripts so they can be selected at
runtime by name while sharing a single, resource-aware execution layer:

    strategy          | source script | intent
    ------------------|--------------|------------------------------------------
    clean_commercial  | br_05.py      | gentle edge refine (isnet / u2net)
    precision_geometry| br_06.py      | hand remover, hole filler, thin-part fix
    birefnet_production | br_08.py    | subject-aware model selection + safety
    ultimate_gaps     | br_11.py      | edge shaver + k-means colour bleed
    marketing_variants| br_12.py      | floating-artifact + bottom-text eraser
    lite_variants     | br_13.py      | lite / cloth / rmbg models (low RAM)

VPS-safety layer (safe for 100s of concurrent suppliers):
  * Global concurrency semaphore (BG_MAX_CONCURRENT, default 2).
  * LRU rembg session cache (BG_MAX_SESSION_CACHE, default 2 models live).
  * Aggressive pre-downscale before inference (BG_MAX_IMAGE_DIM 768px).
  * Per-model resolution caps + OOM auto-disable.
  * Memory-pressure monitor skips heavy OpenCV post-processing.
  * Never raises: always returns the original bytes on any failure.

Everything is designed to degrade gracefully instead of crashing.
"""
from __future__ import annotations
import gc
import io
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from providers.image import Image
from providers.image.bg_remover import _bytes_to_image, create_frugal_rembg_session, rembg_remove_bytes
logger = logging.getLogger(__name__)
from providers.image import HAS_CV2 as _HAS_CV2, HAS_GUIDED_FILTER as _HAS_GUIDED_FILTER, cv2, ximgproc as _ximgproc
MAX_CONCURRENT = int(os.environ.get('BG_MAX_CONCURRENT', '2'))
MAX_SESSION_CACHE = int(os.environ.get('BG_MAX_SESSION_CACHE', '2'))
MAX_IMAGE_DIM = int(os.environ.get('BG_MAX_IMAGE_DIM', '1024'))
LITE_MAX_DIM = int(os.environ.get('BG_LITE_MAX_DIM', '768'))
MEMORY_WARN_MB = int(os.environ.get('BG_MEMORY_WARN_MB', '512'))
SKIP_HEAVY_MODELS = os.environ.get('BG_SKIP_HEAVY_MODELS', 'false').lower() == 'true'
ALLOW_HEAVY_MODELS = os.environ.get('BG_ALLOW_HEAVY_MODELS', 'true').lower() == 'true'
DEFAULT_STRATEGY = os.environ.get('BG_DEFAULT_STRATEGY', 'auto')
HEAVY_THREADS = int(os.environ.get('BG_HEAVY_THREADS', '2'))
LIGHT_THREADS = int(os.environ.get('BG_LIGHT_THREADS', '4'))
LIGHTWEIGHT_MODE = os.environ.get('BG_LIGHTWEIGHT_MODE', 'false').lower() == 'true'
HEAVY_MODELS = {'birefnet-massive', 'birefnet-hrsod', 'birefnet-general', 'birefnet-portrait', 'briaai-rmbg-1.4', 'bria-rmbg'}
_MODEL_NAME_ALIASES = {'briaai-rmbg-1.4': 'bria-rmbg'}
MODEL_LOAD_MIN_MB = int(os.environ.get('BG_MODEL_LOAD_MIN_MB', '700'))
LIGHT_DISABLE_COOLDOWN = int(os.environ.get('BG_LIGHT_COOLDOWN', '60'))
HEAVY_DISABLE_COOLDOWN = int(os.environ.get('BG_HEAVY_COOLDOWN', '1800'))
VALID_STRATEGIES = ['auto', 'clean_commercial', 'precision_geometry', 'birefnet_production', 'ultimate_gaps', 'marketing_variants', 'lite_variants']
LIGHT_MODELS = ['u2net', 'isnet-general-use']
STRATEGY_MODELS = {'clean_commercial': ['isnet-general-use', 'u2net', 'silueta'], 'precision_geometry': ['u2net', 'isnet-general-use', 'silueta'], 'birefnet_production': ['birefnet-general', 'birefnet-general-lite', 'u2net', 'silueta'], 'ultimate_gaps': ['birefnet-general', 'u2net_cloth_seg', 'u2net', 'isnet-general-use'], 'marketing_variants': ['birefnet-massive', 'birefnet-hrsod', 'u2net_cloth_seg', 'silueta', 'isnet-general-use'], 'lite_variants': ['birefnet-general-lite', 'u2net_cloth_seg', 'bria-rmbg', 'u2netp', 'silueta']}
PRESET_ALIASES = {'general': 'clean_commercial', 'handheld': 'precision_geometry', 'wood': 'ultimate_gaps', 'texture_gap': 'ultimate_gaps', 'marketing': 'marketing_variants', 'cloth_lite': 'lite_variants'}
_METRICS_PATH = Path(__file__).resolve().parent.parent / 'provider_test' / 'visual_regression' / 'metrics.json'
_STRATEGY_NAME_MAP = {'br_06 Precision Geo': 'precision_geometry', 'br_08 Production': 'birefnet_production', 'br_11 Ultimate Gap': 'ultimate_gaps', 'br_12 Marketing': 'marketing_variants', 'br_13 Lite Variant': 'lite_variants'}
_SSIM_WEIGHT = 0.5
_PSNR_WEIGHT = 0.25
_IOU_WEIGHT = 0.25
_PSNR_MAX_DB = 50.0

def _load_category_scores():
    """Return per-category weighted scores from visual-regression metrics."""
    scores: Dict[str, Dict[str, float]] = {}
    try:
        if not _METRICS_PATH.exists():
            logger.warning('bg_svc: metrics.json not found at %s', _METRICS_PATH)
            return scores
        raw = _METRICS_PATH.read_text(encoding='utf-8')
        data = json.loads(raw)
        for entry in data:
            strategy_label = entry.get('strategy', '')
            category = entry.get('category', '')
            internal = _STRATEGY_NAME_MAP.get(strategy_label)
            if not internal:
                continue
            cat_key = category.lower()
            if 'beauty' in cat_key:
                cat_key = 'beauty'
            elif 'electronics' in cat_key:
                cat_key = 'electronics'
            elif 'clothing' in cat_key:
                cat_key = 'clothing'
            else:
                continue
            ssim = max(0.0, min(1.0, entry.get('ssim', 0.0)))
            psnr = max(0.0, min(1.0, entry.get('psnr_rgb_db', 0.0) / _PSNR_MAX_DB))
            iou = max(0.0, min(1.0, entry.get('edge_band_iou', 0.0)))
            score = _SSIM_WEIGHT * ssim + _PSNR_WEIGHT * psnr + _IOU_WEIGHT * iou
            scores.setdefault(cat_key, {})[internal] = score
        logger.info('bg_svc: loaded category scores from %s', _METRICS_PATH)
    except Exception as exc:
        logger.warning('bg_svc: failed to load metrics.json (%s); using defaults', exc)
    return scores

def _get_category_recommendations() -> Dict[str, Dict[str, object]]:
    """Return per-category recommendations with scores and raw metrics details."""
    scores = _load_category_scores()
    raw_metrics = []
    try:
        if _METRICS_PATH.exists():
            raw_metrics = json.loads(_METRICS_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    recommendations: Dict[str, Dict[str, object]] = {}
    for (category, cat_scores) in scores.items():
        best_strategy = max(cat_scores, key=cat_scores.get) if cat_scores else 'clean_commercial'
        best_score = cat_scores.get(best_strategy, 0.0)
        strategy_metrics: Dict[str, object] = {}
        for entry in raw_metrics:
            entry_category = entry.get('category', '')
            entry_strategy = _STRATEGY_NAME_MAP.get(entry.get('strategy', ''), '')
            if entry_category.lower() == category and entry_strategy == best_strategy:
                strategy_metrics = {'ssim': round(entry.get('ssim', 0.0), 4), 'psnr_rgb_db': round(entry.get('psnr_rgb_db', 0.0), 2), 'edge_band_iou': round(entry.get('edge_band_iou', 0.0), 4), 'timing_s': round(entry.get('timing_s', 0.0), 3), 'coverage_pct': round(entry.get('diff_pct_rgb', 0.0), 2)}
                break
        recommendations[category] = {'recommended_strategy': best_strategy, 'score': round(best_score, 4), 'metrics': strategy_metrics, 'all_scores': {s: round(sc, 4) for (s, sc) in cat_scores.items()}}
    return recommendations

def _available_ram_mb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except ImportError:
        return 4096.0

def _low_on_ram() -> bool:
    return _available_ram_mb() < MEMORY_WARN_MB
_BG_SEMAPHORE = threading.Semaphore(MAX_CONCURRENT)

class _ConcurrencyGate:

    @staticmethod
    def acquire(timeout: float=30.0) -> bool:
        return _BG_SEMAPHORE.acquire(blocking=True, timeout=timeout)

    @staticmethod
    def release() -> None:
        try:
            _BG_SEMAPHORE.release()
        except Exception:
            pass

def _u2net_home() -> str:
    return os.path.expanduser(os.environ.get('U2NET_HOME', '~/.u2net'))

def _model_file_present(model_name: str) -> bool:
    """True only if the model's .onnx is already on disk.

    We intentionally never trigger a network download at inference time: a
    missing model is skipped (and disabled) so a VPS request never blocks for
    minutes waiting on a multi-hundred-MB download.
    """
    home = _u2net_home()
    base = model_name.replace('briaai-rmbg-1.4', 'bria-rmbg')
    candidates = [f'{model_name}.onnx', f'{base}.onnx', f'{base}.pth']
    for c in candidates:
        if os.path.exists(os.path.join(home, c)):
            return True
    return False

def _build_session(model_name: str):
    """Build a memory-frugal rembg session (delegates to the bg-remover provider).

    The frugal ONNX Runtime options live in
    :func:`providers.bg_remover.create_frugal_rembg_session` so this service no
    longer imports ``rembg`` / ``onnxruntime`` directly.
    """
    return create_frugal_rembg_session(model_name, aliases=_MODEL_NAME_ALIASES, heavy_models=HEAVY_MODELS, heavy_threads=HEAVY_THREADS, light_threads=LIGHT_THREADS)

class _SessionManager:
    _sessions: 'OrderedDict[str, object]' = OrderedDict()
    _disabled: 'dict[str, float]' = {}
    _lock = threading.Lock()

    @classmethod
    def is_disabled(cls, model_name: str) -> bool:
        """True while a model is inside its failure cooldown window."""
        until = cls._disabled.get(model_name)
        if until is None:
            return False
        if time.time() >= until:
            cls._disabled.pop(model_name, None)
            return False
        return True

    @classmethod
    def _mark_disabled(cls, model_name: str) -> None:
        """Skip a model for a cooldown window (NOT permanently). Heavy models
        get a long cooldown; small models a short one so a transient failure
        never collapses every strategy to a single fallback model."""
        cooldown = HEAVY_DISABLE_COOLDOWN if model_name in HEAVY_MODELS else LIGHT_DISABLE_COOLDOWN
        cls._disabled[model_name] = time.time() + cooldown

    @classmethod
    def get(cls, model_name: str):
        if cls.is_disabled(model_name):
            return None
        if model_name in HEAVY_MODELS and (not ALLOW_HEAVY_MODELS):
            logger.info("bg_svc: '%s' skipped (heavy; set BG_ALLOW_HEAVY_MODELS=true)", model_name)
            cls._mark_disabled(model_name)
            return None
        if not _model_file_present(model_name):
            logger.info("bg_svc: '%s' not present locally; skipping (no download)", model_name)
            cls._mark_disabled(model_name)
            return None
        is_heavy = model_name in HEAVY_MODELS
        with cls._lock:
            if model_name in cls._sessions:
                cls._sessions.move_to_end(model_name)
                return cls._sessions[model_name]
            if is_heavy:
                while cls._sessions:
                    cls._evict_one()
            if len(cls._sessions) >= MAX_SESSION_CACHE:
                cls._evict_one()
            if _low_on_ram() and len(cls._sessions) > 0:
                cls._evict_one()
            floor = MODEL_LOAD_MIN_MB * 2 if is_heavy else MODEL_LOAD_MIN_MB
            if _available_ram_mb() < floor and len(cls._sessions) > 0:
                logger.warning("bg_svc: low RAM (%dMB < %dMB); deferring '%s'", int(_available_ram_mb()), floor, model_name)
                cls._mark_disabled(model_name)
                return None
            try:
                cls._sessions[model_name] = _build_session(model_name)
                logger.info("bg_svc: loaded '%s' (frugal; cache %d/%d)", model_name, len(cls._sessions), MAX_SESSION_CACHE)
            except Exception as exc:
                logger.warning("bg_svc: model '%s' load failed: %s", model_name, exc)
                cls._mark_disabled(model_name)
                return None
            return cls._sessions.get(model_name)

    @classmethod
    def _evict_one(cls) -> None:
        if not cls._sessions:
            return
        (name, sess) = cls._sessions.popitem(last=False)
        del sess
        gc.collect()
        logger.info("bg_svc: evicted '%s' (LRU)", name)

    @classmethod
    def disable(cls, model_name: str) -> None:
        with cls._lock:
            cls._mark_disabled(model_name)
            cls._sessions.pop(model_name, None)
            gc.collect()

    @classmethod
    def clear_all(cls) -> None:
        with cls._lock:
            cls._sessions.clear()
            cls._disabled.clear()
            gc.collect()

    @classmethod
    def release_sessions(cls) -> None:
        """Drop loaded model sessions to free RAM, but keep the ``_disabled``
        set so models that previously OOM'd / are missing are not retried."""
        with cls._lock:
            cls._sessions.clear()
            gc.collect()

    @classmethod
    def release_if_low_ram(cls) -> None:
        """Free model sessions ONLY when RAM is tight. Keeping the small models
        warm between requests removes the multi-second reload that made every
        request feel like it hung (and made the frontend 'Failed to fetch').
        The LRU cache is capped by ``MAX_SESSION_CACHE`` so RAM stays bounded
        even under 100s of concurrent supplier uploads on a small VPS."""
        if _low_on_ram():
            with cls._lock:
                cls._sessions.clear()
                gc.collect()

def _resolution_cap(model_name: str, requested: int) -> int:
    if 'lite' in model_name:
        return min(requested, 1024)
    if model_name in ('birefnet-massive', 'birefnet-hrsod'):
        return min(requested, 512)
    if model_name in HEAVY_MODELS:
        return min(requested, 640)
    if 'birefnet' in model_name:
        return min(requested, 768)
    return min(requested, MAX_IMAGE_DIM)

def _maybe_downscale(data: bytes, max_dim: int):
    img = Image.open(io.BytesIO(data))
    orig = img.size
    (w, h) = orig
    if max(w, h) <= max_dim:
        return (data, orig)
    ratio = max_dim / float(max(w, h))
    img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=92)
    return (buf.getvalue(), orig)

def _generate_alpha(model_priority: List[str], data: bytes, orig_size) -> Optional[np.ndarray]:
    """Run through model priority list; return alpha (H,W) float32 in [0,1]."""
    if not _ConcurrencyGate.acquire(timeout=30.0):
        logger.warning('bg_svc: concurrency timeout; returning None')
        return None
    try:
        for model_name in model_priority:
            if _SessionManager.is_disabled(model_name):
                continue
            session = _SessionManager.get(model_name)
            if session is None:
                continue
            try:
                logger.info("bg_svc: running model '%s'", model_name)
                cap = _resolution_cap(model_name, 9999)
                (scaled, _) = _maybe_downscale(data, cap)
                out = rembg_remove_bytes(scaled, session, alpha_matting=False, post_process_mask=True)
                out_img = Image.open(io.BytesIO(out)).convert('RGBA')
                out_img = out_img.resize(orig_size, Image.Resampling.LANCZOS)
                alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
                logger.info("bg_svc: '%s' succeeded", model_name)
                return alpha
            except MemoryError:
                logger.error('bg_svc: %s OOM; disabling', model_name)
                _SessionManager.disable(model_name)
            except Exception as exc:
                msg = str(exc).lower()
                if any((k in msg for k in ('bad allocation', 'failed to allocate', 'runtime_exception', 'memory'))):
                    logger.error('bg_svc: %s allocation failure; disabling', model_name)
                    _SessionManager.disable(model_name)
                else:
                    logger.warning("bg_svc: '%s' failed: %s", model_name, exc)
        return None
    finally:
        _ConcurrencyGate.release()

class CleanEdgeRefiner:
    """br_05 â€” gentle high-fidelity edge refinement (no destructive slicing)."""

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
        if _HAS_GUIDED_FILTER:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                alpha_f = alpha.astype(np.float32)
                refined = _ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
                alpha = np.clip(refined, 0, 1)
            except Exception:
                pass
        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        near_edge = cv2.dilate(binary_final, kernel, iterations=3)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0
        return alpha

class SceneAnalyzer:

    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        (h, _w) = alpha.shape
        top = alpha[:int(h * 0.25), :]
        return np.sum(top > 0.5) / max(top.size, 1) > 0.01

class HandRemover:

    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        (contours, _) = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours or len(contours) <= 1:
            return alpha_mask
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        main = contours[0]
        main_area = cv2.contourArea(main)
        main_mask = np.zeros_like(alpha_mask)
        cv2.drawContours(main_mask, [main], -1, 255, -1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        danger = cv2.dilate(main_mask, kernel, iterations=1)
        removed = False
        for cnt in contours[1:]:
            area = cv2.contourArea(cnt)
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                if np.sum((cnt_mask > 0) & (danger > 0)) > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True
        if removed:
            logger.info('bg_svc: removed isolated hand (geometric)')
        return alpha_mask

class HoleFiller:

    @staticmethod
    def fill(alpha_mask: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        binary = (alpha_mask > 128).astype(np.uint8) * 255
        (h, w) = binary.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1:h + 1, 1:w + 1] = binary
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal = padded[1:h + 1, 1:w + 1] == 0
        if np.sum(internal) > 50:
            binary[internal] = 255
        return binary

class ThinPartHandler:

    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        safe = original_alpha_f > 0.05
        return np.where(safe & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask).astype(np.uint8)

class HumanPreserver:

    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_f
        solid = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(solid, kernel, iterations=1)
        hollows = (alpha_f < 0.1) & (dilated > 0)
        if np.sum(hollows) > 10:
            alpha_f[hollows] = 0.85
        return alpha_f

class EdgeShaver:

    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        alpha_u8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(alpha_u8, kernel, iterations=1)
        smoothed = cv2.GaussianBlur(eroded, (3, 3), 1.0)
        return smoothed.astype(np.float32) / 255.0

class GlobalBackgroundBleeder:
    """Lightweight k-means colour-bleed (br_11/12/13). Skips when RAM is low."""

    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2 or _low_on_ram():
            return alpha_map
        (h, w) = input_np.shape[:2]
        border = int(min(h, w) * 0.05)
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_px = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        try:
            (_ret, labels, centers) = cv2.kmeans(border_px, 2, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        except cv2.error:
            return alpha_map
        bg_color = centers[int(np.argmax(np.unique(labels, return_counts=True)[1]))]
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        bleed = (dist < 35.0) & (alpha_map <= 0.9)
        alpha_final = alpha_map.copy()
        alpha_final[bleed] = 0.0
        removed = int(np.sum(bleed))
        if removed:
            logger.info('bg_svc: erased %d gap background px', removed)
        return alpha_final

class ArtifactIsolator:

    @staticmethod
    def remove_floating_dust(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        (h, w) = alpha_map.shape
        (_, binary) = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        (num, labels, stats, _) = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num <= 1:
            return alpha_map
        min_area = h * w * 0.005
        out = alpha_map.copy()
        for i in range(1, num):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                out[labels == i] = 0.0
        return out

class FloatingArtifactRemover:

    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        (h, w) = alpha_map.shape
        (_, binary) = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        (num, labels, stats, _) = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num <= 1:
            return alpha_map
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        main_w = stats[largest, cv2.CC_STAT_WIDTH]
        main_cx = stats[largest, cv2.CC_STAT_LEFT] + main_w / 2
        main_cy = stats[largest, cv2.CC_STAT_TOP] + stats[largest, cv2.CC_STAT_HEIGHT] / 2
        out = alpha_map.copy()
        for i in range(1, num):
            if i == largest:
                continue
            if stats[i, cv2.CC_STAT_AREA] > h * w * 0.01:
                cx = stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] / 2
                cy = stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] / 2
                if np.sqrt((cx - main_cx) ** 2 + (cy - main_cy) ** 2) > main_w * 1.5:
                    out[labels == i] = 0.0
        return out

class BottomTextEraser:

    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        (h, w) = alpha_map.shape
        (_, binary) = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        bottom_region = binary[int(h * 0.8):, :]
        (contours, _) = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = alpha_map.copy()
        for contour in contours:
            (x, y, cw, ch) = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h * 0.8)
            aspect = float(cw) / ch if ch > 0 else 0
            if 100 < area < 5000 and aspect > 2.0 and (global_y > h * 0.9):
                out[global_y:global_y + ch, x:x + cw] = 0.0
        return out

class WoodBackgroundRemover:

    @staticmethod
    def remove(image_rgba: np.ndarray, prob_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2 or _low_on_ram():
            return image_rgba
        gray = cv2.cvtColor(image_rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
        if np.var(cv2.Laplacian(gray, cv2.CV_64F)) < 150:
            return image_rgba
        (h, w) = image_rgba.shape[:2]
        cs = min(h, w) // 6
        samples = np.concatenate([image_rgba[:cs, :cs, :3].reshape(-1, 3), image_rgba[:cs, -cs:, :3].reshape(-1, 3), image_rgba[-cs:, :cs, :3].reshape(-1, 3), image_rgba[-cs:, -cs:, :3].reshape(-1, 3)])
        bg = np.median(samples, axis=0)
        flat = image_rgba[:, :, :3].reshape(-1, 3)
        bg_mask = (np.linalg.norm(flat - bg, axis=1) < 70).reshape(h, w).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        prod = (prob_map > 0.25).astype(np.uint8) * 255
        (n, labs, st, _) = cv2.connectedComponentsWithStats(prod, connectivity=8)
        if n > 1:
            areas = [(i, st[i, cv2.CC_STAT_AREA]) for i in range(1, n)]
            areas.sort(key=lambda x: x[1], reverse=True)
            if areas and areas[0][1] > h * w * 0.05:
                region = (labs == areas[0][0]).astype(np.uint8)
                region = cv2.dilate(region, kernel, iterations=2)
                bg_mask = cv2.bitwise_and(bg_mask, 255 - region)
        image_rgba[bg_mask > 0, 3] = 0
        return image_rgba

@dataclass
class _Strategy:
    models: List[str]
    post: str

def _models_for(strategy: str) -> List[str]:
    """Resolve the model priority list for a strategy, honouring lightweight mode."""
    if LIGHTWEIGHT_MODE:
        return LIGHT_MODELS
    return STRATEGY_MODELS.get(strategy, LIGHT_MODELS)
_STRATEGIES: dict[str, _Strategy] = {'clean_commercial': _Strategy(_models_for('clean_commercial'), 'clean'), 'precision_geometry': _Strategy(_models_for('precision_geometry'), 'geometry'), 'birefnet_production': _Strategy(_models_for('birefnet_production'), 'production'), 'ultimate_gaps': _Strategy(_models_for('ultimate_gaps'), 'gaps'), 'marketing_variants': _Strategy(_models_for('marketing_variants'), 'marketing'), 'lite_variants': _Strategy(_models_for('lite_variants'), 'lite')}

def _postprocess(post: str, input_np: np.ndarray, alpha: np.ndarray, fast_mode: bool=False) -> np.ndarray:
    is_low_ram = _low_on_ram() or fast_mode
    if post == 'clean':
        return CleanEdgeRefiner.refine(input_np, alpha)
    if post == 'geometry':
        if SceneAnalyzer.is_human_photo(alpha):
            alpha = HumanPreserver.fix_hollows(alpha)
        else:
            mask = (alpha > 0.5).astype(np.uint8) * 255
            mask = HandRemover.remove_if_isolated(mask)
            mask = HoleFiller.fill(mask)
            mask = ThinPartHandler.handle(mask, alpha)
            alpha = mask.astype(np.float32) / 255.0
        return CleanEdgeRefiner.refine(input_np, alpha)
    if post == 'production':
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
        rgba = np.dstack([input_np, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
        if not is_low_ram:
            rgba = WoodBackgroundRemover.remove(rgba, alpha)
        alpha = rgba[:, :, 3].astype(np.float32) / 255.0
        return HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
    if post == 'gaps':
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        if not is_low_ram:
            alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
        return ArtifactIsolator.remove_floating_dust(HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0)
    if post == 'marketing':
        alpha = FloatingArtifactRemover.remove_floating_objects(alpha)
        alpha = BottomTextEraser.erase_bottom_text(alpha)
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        if not is_low_ram:
            alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
        return alpha
    if post == 'lite':
        alpha = HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
        alpha = ArtifactIsolator.remove_floating_dust(alpha)
        return CleanEdgeRefiner.refine(input_np, alpha)
    return alpha

def _compose_rgba(input_np: np.ndarray, alpha: np.ndarray) -> bytes:
    (h, w) = input_np.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = input_np
    rgba[:, :, 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    trans = rgba[:, :, 3] == 0
    rgba[trans, :3] = 0
    buf = io.BytesIO()
    Image.fromarray(rgba, mode='RGBA').save(buf, format='PNG', compress_level=4)
    return buf.getvalue()

def _compute_quality_score(img_rgb: np.ndarray, alpha: np.ndarray) -> Dict[str, float]:
    """Score a background-removed result.

    ``img_rgb`` is the original RGB array (H, W, 3) and ``alpha`` is the
    foreground mask as a float array (H, W) in ``[0, 1]``.

    Returns a dict with the metrics consumed by the A/B-test router:
        edge_clarity     - sharpness of the cutout boundary (0..1)
        alpha_confidence - how bimodal the mask is, i.e. how decisive the cut (0..1)
        coverage         - fraction of pixels kept as foreground (0..1)
        edge_pixels_pct  - share of pixels in the soft-transition band (0..100)
        overall         - weighted quality score (0..1)
    """
    try:
        a = alpha.astype(np.float32)
        (h, w) = a.shape[:2]
        total = float(h * w) if h * w else 1.0
        coverage = float(np.mean(a))
        edge_band = (a > 0.05) & (a < 0.95)
        edge_pixels_pct = float(np.count_nonzero(edge_band)) / total * 100.0
        fg = float(np.count_nonzero(a > 0.9)) / total
        bg = float(np.count_nonzero(a < 0.1)) / total
        alpha_confidence = float(np.clip(fg + bg, 0.0, 1.0))
        if h > 2 and w > 2:
            (gy, gx) = np.gradient(a)
            grad = np.sqrt(gx ** 2 + gy ** 2)
            edge_clarity = float(np.mean(grad[edge_band])) if np.any(edge_band) else 0.0
            edge_clarity = float(np.clip(edge_clarity / 2.0, 0.0, 1.0))
        else:
            edge_clarity = 0.0
        coverage_conf = 1.0 - abs(coverage - 0.5) * 1.3
        coverage_conf = float(np.clip(coverage_conf, 0.0, 1.0))
        overall = float(np.clip(0.35 * edge_clarity + 0.4 * alpha_confidence + 0.25 * coverage_conf, 0.0, 1.0))
        return {'edge_clarity': round(edge_clarity, 4), 'alpha_confidence': round(alpha_confidence, 4), 'coverage': round(coverage, 4), 'overall': round(overall, 4), 'edge_pixels_pct': round(edge_pixels_pct, 4)}
    except Exception as exc:
        logger.warning('bg_svc: quality score failed: %s', exc)
        return {'edge_clarity': 0.0, 'alpha_confidence': 0.0, 'coverage': 0.0, 'overall': 0.0, 'edge_pixels_pct': 0.0}

def _detect_category(input_np: np.ndarray) -> str:
    """Analyze image content to detect product category using lightweight
    color/edge heuristics. Returns 'clothing', 'electronics', 'beauty', or
    'unknown'.

    Uses only OpenCV operations (no ML/rembg) so it adds <10ms overhead.
    """
    if not _HAS_CV2:
        return 'unknown'
    (h, w) = input_np.shape[:2]
    gray = cv2.cvtColor(input_np, cv2.COLOR_RGB2GRAY)
    mean_rgb = input_np.mean(axis=(0, 1))
    std_rgb = input_np.std(axis=(0, 1)).mean()
    brightness = float(mean_rgb.mean())
    warm_mask = input_np[:, :, 0].astype(float) > input_np[:, :, 2].astype(float)
    warmth_ratio = float(np.mean(warm_mask))
    edges = cv2.Canny(gray, 30, 100)
    edge_density = float(np.mean(edges > 0))
    scores = {}
    clothing_score = std_rgb * 0.4 + edge_density * 200 + warmth_ratio * 30
    if std_rgb >= 55 and edge_density >= 0.02:
        clothing_score += 20
    scores['clothing'] = clothing_score
    electronics_score = (100 - std_rgb) * 0.2 + (150 - brightness) * 0.2 + (1 - edge_density) * 50
    if std_rgb < 55 and brightness < 150:
        electronics_score += 20
    scores['electronics'] = electronics_score
    beauty_score = std_rgb * 0.2 + brightness * 0.15 + (1 - edge_density) * 30 + warmth_ratio * 20
    if 80 < brightness < 200 and std_rgb > 30 and (edge_density < 0.07):
        beauty_score += 25
    scores['beauty'] = beauty_score
    logger.debug('bg_svc: category scores clothing=%.1f electronics=%.1f beauty=%.1f (bright=%.0f std=%.0f edge=%.3f warmth=%.2f)', scores['clothing'], scores['electronics'], scores['beauty'], brightness, std_rgb, edge_density, warmth_ratio)
    best = max(scores, key=scores.get)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] < 5:
        return 'unknown'
    return best

def _select_auto(input_np: np.ndarray) -> str:
    """Auto-select the best bg removal strategy using per-category weighted
    scores from the visual-regression metrics (SSIM, PSNR, edge-band IoU).

    Falls back to the legacy category->strategy map when the metrics file is
    unavailable or the detected category has no coverage data.
    """
    if _low_on_ram():
        return 'lite_variants'
    if not _HAS_CV2:
        return 'ultimate_gaps'
    category = _detect_category(input_np)
    scores = _load_category_scores()
    cat_scores = scores.get(category, {})
    if cat_scores:
        best = max(cat_scores, key=cat_scores.get)
        logger.info("bg_svc: auto-selected '%s' for category '%s' (scores: %s)", best, category, cat_scores)
        return best
    all_scores: Dict[str, float] = {}
    for cat_data in scores.values():
        for (strat, sc) in cat_data.items():
            all_scores[strat] = all_scores.get(strat, 0.0) + sc
    if all_scores:
        best = max(all_scores, key=all_scores.get)
        logger.info("bg_svc: auto-selected '%s' as all-around fallback (scores: %s)", best, all_scores)
        return best
    legacy = {'clothing': 'clean_commercial', 'electronics': 'precision_geometry', 'beauty': 'precision_geometry'}
    return legacy.get(category, 'ultimate_gaps')

def remove_background(data: bytes, strategy: str='auto', fast_mode: bool=False) -> bytes:
    """
    Remove background using one of the 6 tested pipelines (or 'auto').

    Always returns transparent PNG bytes; on any failure returns ``data``
    unchanged (never raises / never 500s).
    """
    if strategy in PRESET_ALIASES:
        strategy = PRESET_ALIASES[strategy]
    if strategy not in _STRATEGIES:
        strategy = DEFAULT_STRATEGY if DEFAULT_STRATEGY in _STRATEGIES else 'auto'
    if strategy == 'auto':
        try:
            img0 = Image.open(io.BytesIO(data)).convert('RGB')
            strategy = _select_auto(np.array(img0))
        except Exception:
            strategy = 'clean_commercial'
    cfg = _STRATEGIES[strategy]
    try:
        img = Image.open(io.BytesIO(data)).convert('RGB')
        input_np = np.array(img)
        orig_size = img.size
        alpha = _generate_alpha(cfg.models, data, orig_size)
        if alpha is None:
            logger.warning("bg_svc: all models failed for '%s'; original returned", strategy)
            return data
        alpha = _postprocess(cfg.post, input_np, alpha, fast_mode=fast_mode)
        alpha[alpha < 0.02] = 0.0
        alpha[alpha > 0.98] = 1.0
        return _compose_rgba(input_np, alpha)
    except Exception as exc:
        logger.warning("bg_svc: strategy '%s' failed (%s); original returned", strategy, exc)
        return data
    finally:
        _SessionManager.release_if_low_ram()
        gc.collect()

def magic_erase(data: bytes, fast_mode: bool=False) -> bytes:
    """Convenience wrapper â€” best-effort background removal for the magic eraser."""
    return remove_background(data, strategy='auto', fast_mode=fast_mode)

def remove_background_preset(data: bytes, preset: str='general', fast_mode: bool=False) -> bytes:
    return remove_background(data, strategy=preset, fast_mode=fast_mode)

def remove_background_model(data: bytes, model_name: str='isnet-general-use', fast_mode: bool=False) -> bytes:
    if LIGHTWEIGHT_MODE:
        logger.info("bg_svc: lightweight mode â€” '%s' downgraded to u2net", model_name)
        model_name = 'u2net'
    elif model_name in HEAVY_MODELS and (not ALLOW_HEAVY_MODELS):
        logger.info("bg_svc: '%s' is heavy; using lightweight segmenter instead", model_name)
        model_name = 'u2net'
    singleton = _Strategy([model_name, 'isnet-general-use', 'u2net'], 'clean')
    try:
        img = Image.open(io.BytesIO(data)).convert('RGB')
        input_np = np.array(img)
        orig_size = img.size
        alpha = _generate_alpha(singleton.models, data, orig_size)
        if alpha is None:
            return data
        if not fast_mode:
            alpha = CleanEdgeRefiner.refine(input_np, alpha)
        alpha[alpha < 0.02] = 0.0
        alpha[alpha > 0.98] = 1.0
        return _compose_rgba(input_np, alpha)
    except Exception as exc:
        logger.warning("bg_svc: model '%s' failed (%s); original returned", model_name, exc)
        return data
    finally:
        _SessionManager.release_if_low_ram()
        gc.collect()
AVAILABLE_MODELS: List[str] = ['birefnet-general', 'isnet-general-use', 'u2net', 'u2net_cloth_seg', 'birefnet-massive', 'birefnet-hrsod', 'briaai-rmbg-1.4', 'birefnet-general-lite', 'silueta']
if SKIP_HEAVY_MODELS:
    for h in HEAVY_MODELS:
        if h in AVAILABLE_MODELS:
            AVAILABLE_MODELS.remove(h)

def __getattr__(name):
    _LAZY = {'AVAILABLE_MODELS': 'services.ai.bg_removal_service'}
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
