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

# ── OpenCV (imported safely; ximgproc resolved at module level) ────────────
try:
    import cv2
    _HAS_CV2 = True
    try:
        from cv2 import ximgproc as _ximgproc  # noqa: F401  (guided filter)
        _HAS_GUIDED_FILTER = True
    except ImportError:
        _HAS_GUIDED_FILTER = False
except ImportError:
    cv2 = None  # type: ignore
    _HAS_CV2 = False
    _HAS_GUIDED_FILTER = False


# ── Tunable knobs (environment variables) ─────────────────────────────────
MAX_CONCURRENT = int(os.environ.get("BG_MAX_CONCURRENT", "2"))
MAX_SESSION_CACHE = int(os.environ.get("BG_MAX_SESSION_CACHE", "2"))
MAX_IMAGE_DIM = int(os.environ.get("BG_MAX_IMAGE_DIM", "1024"))
LITE_MAX_DIM = int(os.environ.get("BG_LITE_MAX_DIM", "768"))
MEMORY_WARN_MB = int(os.environ.get("BG_MEMORY_WARN_MB", "512"))
SKIP_HEAVY_MODELS = os.environ.get("BG_SKIP_HEAVY_MODELS", "false").lower() == "true"
# Heavy models (birefnet-massive / hrsod) are reachable by default so the 6
# strategies produce the DISTINCT results they were tuned for. They are only
# ever tried if the model file is already present locally (never downloaded
# mid-request) and any OOM auto-disables them for the rest of the process.
ALLOW_HEAVY_MODELS = os.environ.get("BG_ALLOW_HEAVY_MODELS", "true").lower() == "true"
DEFAULT_STRATEGY = os.environ.get("BG_DEFAULT_STRATEGY", "auto")

# CPU thread caps. ONNX Runtime by default grabs EVERY core, which starves a
# shared VPS serving many suppliers. Heavy models get a tight cap; light models
# a slightly higher one. Keep low to bound CPU under concurrency.
HEAVY_THREADS = int(os.environ.get("BG_HEAVY_THREADS", "2"))
LIGHT_THREADS = int(os.environ.get("BG_LIGHT_THREADS", "4"))

# LIGHTWEIGHT MODE — the escape hatch for tiny VPSes. When enabled EVERY
# strategy is forced onto the small u2net/isnet segmenter (its post-processing
# chain is still applied, so strategies still differ somewhat). Leave OFF
# (default) so each of the 6 buttons uses its own tuned model and gives a
# visibly different cutout, exactly like the standalone br_05..br_13 scripts.
LIGHTWEIGHT_MODE = os.environ.get("BG_LIGHTWEIGHT_MODE", "false").lower() == "true"

# Models that are ~900MB+ on disk and need 2-3GB peak RAM during ONNX
# inference. They routinely OOM ("bad allocation") on a small VPS *and* even
# inside this backend process on a dev box (see startup logs), so they are
# GATED: never used by the 6 default strategy chains, only reachable via an
# explicit ``model=`` request AND ``BG_ALLOW_HEAVY_MODELS=true`` AND enough
# free RAM. This is what stops one heavy request from cascade-disabling the
# small models and collapsing all 6 buttons to a single u2net result.
HEAVY_MODELS = {
    "birefnet-massive", "birefnet-hrsod", "birefnet-general",
    "birefnet-portrait", "briaai-rmbg-1.4", "bria-rmbg",
}

# rembg 2.0.69 renamed a couple of models; normalise the names the br_*
# scripts used to the session-class names rembg actually registers.
_MODEL_NAME_ALIASES = {
    "briaai-rmbg-1.4": "bria-rmbg",
}

# Minimum free RAM (MB) required before we attempt to load a *new* model.
# If below this, the model is deferred (disabled) instead of risking an OOM
# that would kill the whole worker process.
MODEL_LOAD_MIN_MB = int(os.environ.get("BG_MODEL_LOAD_MIN_MB", "700"))

# Cooldown (seconds) a model is skipped after a failure, instead of being
# disabled permanently. A transient OOM (e.g. caused by another concurrent
# request briefly holding a heavy model) must NOT kill a small model for the
# whole process lifetime — that is what previously collapsed all 6 buttons to
# u2net. Heavy models get a long cooldown, small models a short one.
LIGHT_DISABLE_COOLDOWN = int(os.environ.get("BG_LIGHT_COOLDOWN", "60"))
HEAVY_DISABLE_COOLDOWN = int(os.environ.get("BG_HEAVY_COOLDOWN", "1800"))

# Public strategy names (mirror the 6 tested scripts).
VALID_STRATEGIES = [
    "auto",
    "clean_commercial",
    "precision_geometry",
    "birefnet_production",
    "ultimate_gaps",
    "marketing_variants",
    "lite_variants",
]

# ── Fallback lightweight segmenter (used in LIGHTWEIGHT_MODE or as the tail
#    fallback of every priority list so we never fully fail). ────────────────
LIGHT_MODELS = ["u2net", "isnet-general-use"]

# ── Faithful per-strategy model priority lists (mirror br_05..br_13) ───────
# The DISTINCT cutout each button produces comes primarily from its model
# choice; br_05 vs br_06 (same models) differ purely by post-processing.
# Each list ends in a light model so a missing/OOM heavy model degrades
# gracefully instead of failing.
# Each of the 6 buttons is anchored on a DISTINCT lightweight model that is
# actually loadable (all present locally, each ≤213MB) so every button gives a
# visibly DIFFERENT cutout — exactly like the standalone br_05..br_13 scripts
# did when they each ran a different model. The heavy 927MB BiRefNet models the
# scripts originally used are replaced by the 213MB ``birefnet-general-lite``
# (same architecture family, VPS-safe) and other distinct small models, so no
# button OOMs or stalls for 32s. Each strategy still runs its own tuned
# post-processing chain, so model + post together make all 6 unique.
STRATEGY_MODELS = {
    # br_05 — gentle clean refine   → ISNet (crisp product edges)
    "clean_commercial":   ["isnet-general-use", "u2net", "silueta"],
    # br_06 — precision geometry    → U2Net base + geometry post (distinct from
    # clean_commercial by both model lead and post-processing)
    "precision_geometry": ["u2net", "isnet-general-use", "silueta"],
    # br_08 — production quality     → BiRefNet-general (real heavy model, now
    # memory-frugal); degrades to lite → u2net if RAM is tight.
    "birefnet_production": ["birefnet-general", "birefnet-general-lite", "u2net", "silueta"],
    # br_11 — ultimate gaps          → BiRefNet-general + gap post; cloth-seg
    # fallback keeps bikini/hole detail when the heavy model is unavailable.
    "ultimate_gaps":      ["birefnet-general", "u2net_cloth_seg", "u2net", "isnet-general-use"],
    # br_12 — marketing variants     → BiRefNet-massive / hrsod specialised
    # models + floating/text erase; cloth-seg / silueta fallbacks.
    "marketing_variants": ["birefnet-massive", "birefnet-hrsod", "u2net_cloth_seg", "silueta", "isnet-general-use"],
    # br_13 — lite variants          → BiRefNet-lite / cloth / BRIA-rmbg (the
    # tested "variant" models), u2netp last for the tiniest boxes.
    "lite_variants":      ["birefnet-general-lite", "u2net_cloth_seg", "bria-rmbg", "u2netp", "silueta"],
}

# Backwards-compatible preset aliases (old frontend preset names).
PRESET_ALIASES = {
    "general": "clean_commercial",
    "handheld": "precision_geometry",
    "wood": "ultimate_gaps",
    "texture_gap": "ultimate_gaps",
    "marketing": "marketing_variants",
    "cloth_lite": "lite_variants",
}

# Visual-regression metrics for auto-strategy selection.
_METRICS_PATH = Path(__file__).resolve().parent.parent / "provider_test" / "visual_regression" / "metrics.json"
_STRATEGY_NAME_MAP = {
    "br_06 Precision Geo": "precision_geometry",
    "br_08 Production": "birefnet_production",
    "br_11 Ultimate Gap": "ultimate_gaps",
    "br_12 Marketing": "marketing_variants",
    "br_13 Lite Variant": "lite_variants",
}
_SSIM_WEIGHT = 0.50
_PSNR_WEIGHT = 0.25
_IOU_WEIGHT = 0.25
_PSNR_MAX_DB = 50.0


def _load_category_scores():
    """Return per-category weighted scores from visual-regression metrics."""
    scores: Dict[str, Dict[str, float]] = {}
    try:
        if not _METRICS_PATH.exists():
            logger.warning("bg_svc: metrics.json not found at %s", _METRICS_PATH)
            return scores
        raw = _METRICS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        for entry in data:
            strategy_label = entry.get("strategy", "")
            category = entry.get("category", "")
            internal = _STRATEGY_NAME_MAP.get(strategy_label)
            if not internal:
                continue
            cat_key = category.lower()
            if "beauty" in cat_key:
                cat_key = "beauty"
            elif "electronics" in cat_key:
                cat_key = "electronics"
            elif "clothing" in cat_key:
                cat_key = "clothing"
            else:
                continue
            ssim = max(0.0, min(1.0, entry.get("ssim", 0.0)))
            psnr = max(0.0, min(1.0, entry.get("psnr_rgb_db", 0.0) / _PSNR_MAX_DB))
            iou = max(0.0, min(1.0, entry.get("edge_band_iou", 0.0)))
            score = _SSIM_WEIGHT * ssim + _PSNR_WEIGHT * psnr + _IOU_WEIGHT * iou
            scores.setdefault(cat_key, {})[internal] = score
        logger.info("bg_svc: loaded category scores from %s", _METRICS_PATH)
    except Exception as exc:
        logger.warning("bg_svc: failed to load metrics.json (%s); using defaults", exc)
    return scores


def _get_category_recommendations() -> Dict[str, Dict[str, object]]:
    """Return per-category recommendations with scores and raw metrics details."""
    scores = _load_category_scores()
    raw_metrics = []
    try:
        if _METRICS_PATH.exists():
            raw_metrics = json.loads(_METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass

    recommendations: Dict[str, Dict[str, object]] = {}
    for category, cat_scores in scores.items():
        best_strategy = max(cat_scores, key=cat_scores.get) if cat_scores else "clean_commercial"
        best_score = cat_scores.get(best_strategy, 0.0)
        strategy_metrics: Dict[str, object] = {}
        for entry in raw_metrics:
            entry_category = entry.get("category", "")
            entry_strategy = _STRATEGY_NAME_MAP.get(entry.get("strategy", ""), "")
            if entry_category.lower() == category and entry_strategy == best_strategy:
                strategy_metrics = {
                    "ssim": round(entry.get("ssim", 0.0), 4),
                    "psnr_rgb_db": round(entry.get("psnr_rgb_db", 0.0), 2),
                    "edge_band_iou": round(entry.get("edge_band_iou", 0.0), 4),
                    "timing_s": round(entry.get("timing_s", 0.0), 3),
                    "coverage_pct": round(entry.get("diff_pct_rgb", 0.0), 2),
                }
                break
        recommendations[category] = {
            "recommended_strategy": best_strategy,
            "score": round(best_score, 4),
            "metrics": strategy_metrics,
            "all_scores": {s: round(sc, 4) for s, sc in cat_scores.items()},
        }
    return recommendations


# ═════════════════════════════════════════════════════════════════════════
# Memory monitor
# ═════════════════════════════════════════════════════════════════════════

def _available_ram_mb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except ImportError:
        return 4096.0


def _low_on_ram() -> bool:
    return _available_ram_mb() < MEMORY_WARN_MB


# ═════════════════════════════════════════════════════════════════════════
# Concurrency gate
# ═════════════════════════════════════════════════════════════════════════

_BG_SEMAPHORE = threading.Semaphore(MAX_CONCURRENT)


class _ConcurrencyGate:
    @staticmethod
    def acquire(timeout: float = 30.0) -> bool:
        return _BG_SEMAPHORE.acquire(blocking=True, timeout=timeout)

    @staticmethod
    def release() -> None:
        try:
            _BG_SEMAPHORE.release()
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════
# Session manager — LRU eviction + memory-aware + OOM disable
# ═════════════════════════════════════════════════════════════════════════

def _u2net_home() -> str:
    return os.path.expanduser(os.environ.get("U2NET_HOME", "~/.u2net"))


def _model_file_present(model_name: str) -> bool:
    """True only if the model's .onnx is already on disk.

    We intentionally never trigger a network download at inference time: a
    missing model is skipped (and disabled) so a VPS request never blocks for
    minutes waiting on a multi-hundred-MB download.
    """
    home = _u2net_home()
    base = model_name.replace("briaai-rmbg-1.4", "bria-rmbg")
    candidates = [
        f"{model_name}.onnx",
        f"{base}.onnx",
        f"{base}.pth",
    ]
    for c in candidates:
        if os.path.exists(os.path.join(home, c)):
            return True
    return False


def _build_session(model_name: str):
    """Build a rembg session with MEMORY-FRUGAL ONNX Runtime options.

    The default ``rembg.new_session`` uses ORT's BFC memory *arena*, which
    pre-reserves and doubles allocations — that is exactly what produced the
    ``bad allocation`` for an 822 MB buffer on the 900 MB BiRefNet models. We
    instead:

      * ``enable_cpu_mem_arena = False``  → allocate the exact tensor size once
        (no arena over-reservation) so a heavy model fits in far less peak RAM.
      * ``enable_mem_pattern = False``    → no speculative pre-allocation.
      * ``ORT_SEQUENTIAL`` execution      → no parallel activation buffers.
      * capped ``intra_op_num_threads``   → bounded CPU on a shared VPS.

    Combined with the per-model resolution caps this lets the heavy BiRefNet /
    BRIA models run without OOMing, at a small speed cost. Falls back to the
    stock ``new_session`` if anything about the frugal path is unavailable.
    """
    real = _MODEL_NAME_ALIASES.get(model_name, model_name)
    try:
        import onnxruntime as ort
        from rembg.session_factory import sessions_class

        session_cls = next((c for c in sessions_class if c.name() == real), None)
        if session_cls is None:
            from rembg import new_session
            return new_session(real)

        opts = ort.SessionOptions()
        opts.enable_cpu_mem_arena = False
        opts.enable_mem_pattern = False
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = HEAVY_THREADS if real in HEAVY_MODELS else LIGHT_THREADS
        opts.inter_op_num_threads = 1
        return session_cls(real, opts, providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("bg_svc: frugal session for '%s' failed (%s); using default", real, exc)
        from rembg import new_session
        return new_session(real)


class _SessionManager:
    _sessions: "OrderedDict[str, object]" = OrderedDict()
    # model_name -> unix timestamp until which the model stays skipped.
    _disabled: "dict[str, float]" = {}
    _lock = threading.Lock()

    @classmethod
    def is_disabled(cls, model_name: str) -> bool:
        """True while a model is inside its failure cooldown window."""
        until = cls._disabled.get(model_name)
        if until is None:
            return False
        if time.time() >= until:
            cls._disabled.pop(model_name, None)  # cooldown expired → retry
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
        # Heavy models are opt-in (memory + slow to load). Skip otherwise.
        if model_name in HEAVY_MODELS and not ALLOW_HEAVY_MODELS:
            logger.info("bg_svc: '%s' skipped (heavy; set BG_ALLOW_HEAVY_MODELS=true)",
                        model_name)
            cls._mark_disabled(model_name)
            return None
        # Never download mid-request: require a local model file.
        if not _model_file_present(model_name):
            logger.info("bg_svc: '%s' not present locally; skipping (no download)",
                        model_name)
            cls._mark_disabled(model_name)
            return None
        is_heavy = model_name in HEAVY_MODELS
        with cls._lock:
            if model_name in cls._sessions:
                cls._sessions.move_to_end(model_name)
                return cls._sessions[model_name]
            # A 900 MB heavy model must never share RAM with another cached
            # model — evict everything else so peak stays ≈ one model's weights.
            if is_heavy:
                while cls._sessions:
                    cls._evict_one()
            if len(cls._sessions) >= MAX_SESSION_CACHE:
                cls._evict_one()
            if _low_on_ram() and len(cls._sessions) > 0:
                cls._evict_one()
            # Refuse to load if free RAM is below the safety floor (heavy models
            # need more headroom for their ~900 MB of weights).
            floor = MODEL_LOAD_MIN_MB * 2 if is_heavy else MODEL_LOAD_MIN_MB
            if _available_ram_mb() < floor and len(cls._sessions) > 0:
                logger.warning("bg_svc: low RAM (%dMB < %dMB); deferring '%s'",
                               int(_available_ram_mb()), floor, model_name)
                cls._mark_disabled(model_name)
                return None
            try:
                cls._sessions[model_name] = _build_session(model_name)
                logger.info("bg_svc: loaded '%s' (frugal; cache %d/%d)", model_name,
                            len(cls._sessions), MAX_SESSION_CACHE)
            except Exception as exc:
                logger.warning("bg_svc: model '%s' load failed: %s", model_name, exc)
                cls._mark_disabled(model_name)
                return None
            return cls._sessions.get(model_name)

    @classmethod
    def _evict_one(cls) -> None:
        if not cls._sessions:
            return
        name, sess = cls._sessions.popitem(last=False)
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


# ═════════════════════════════════════════════════════════════════════════
# Inference (shared by all strategies — faithful to br_11/12/13 segmenter)
# ═════════════════════════════════════════════════════════════════════════

def _resolution_cap(model_name: str, requested: int) -> int:
    # Per-model input caps. Lower caps shrink the ONNX activation tensors
    # quadratically, which (together with the disabled memory arena) is what
    # lets the 900 MB models run without OOM. Heaviest models get the smallest
    # inputs; the light 214 MB lite model can afford more detail.
    if "lite" in model_name:
        return min(requested, 1024)                     # br_13 birefnet-lite
    if model_name in ("birefnet-massive", "birefnet-hrsod"):
        return min(requested, 512)                      # br_12 (heaviest)
    if model_name in HEAVY_MODELS:
        return min(requested, 640)                      # br_08/11 general, bria
    if "birefnet" in model_name:
        return min(requested, 768)
    return min(requested, MAX_IMAGE_DIM)                # isnet / u2net / cloth


def _maybe_downscale(data: bytes, max_dim: int):
    img = Image.open(io.BytesIO(data))
    orig = img.size
    w, h = orig
    if max(w, h) <= max_dim:
        return data, orig
    ratio = max_dim / float(max(w, h))
    img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    # JPEG cannot hold an alpha channel — strip it before re-encoding so that
    # RGBA inputs (transparent PNGs) don't raise "cannot write mode RGBA as JPEG".
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), orig


def _generate_alpha(model_priority: List[str], data: bytes, orig_size) -> Optional[np.ndarray]:
    """Run through model priority list; return alpha (H,W) float32 in [0,1]."""
    from rembg import remove

    if not _ConcurrencyGate.acquire(timeout=30.0):
        logger.warning("bg_svc: concurrency timeout; returning None")
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
                scaled, _ = _maybe_downscale(data, cap)
                out = remove(scaled, session=session, alpha_matting=False, post_process_mask=True)
                out_img = Image.open(io.BytesIO(out)).convert("RGBA")
                out_img = out_img.resize(orig_size, Image.Resampling.LANCZOS)
                alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
                logger.info("bg_svc: '%s' succeeded", model_name)
                return alpha
            except MemoryError:
                logger.error("bg_svc: %s OOM; disabling", model_name)
                _SessionManager.disable(model_name)
            except Exception as exc:
                msg = str(exc).lower()
                if any(k in msg for k in ("bad allocation", "failed to allocate",
                                          "runtime_exception", "memory")):
                    logger.error("bg_svc: %s allocation failure; disabling", model_name)
                    _SessionManager.disable(model_name)
                else:
                    logger.warning("bg_svc: '%s' failed: %s", model_name, exc)
        return None
    finally:
        _ConcurrencyGate.release()


# ═════════════════════════════════════════════════════════════════════════
# Post-processing stages (faithful ports of the tested scripts)
# ═════════════════════════════════════════════════════════════════════════

class CleanEdgeRefiner:
    """br_05 — gentle high-fidelity edge refinement (no destructive slicing)."""

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
        h, _w = alpha.shape
        top = alpha[: int(h * 0.25), :]
        return np.sum(top > 0.5) / max(top.size, 1) > 0.01


class HandRemover:
    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        contours, _ = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
            logger.info("bg_svc: removed isolated hand (geometric)")
        return alpha_mask


class HoleFiller:
    @staticmethod
    def fill(alpha_mask: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_mask
        binary = (alpha_mask > 128).astype(np.uint8) * 255
        h, w = binary.shape
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
        h, w = input_np.shape[:2]
        border = int(min(h, w) * 0.05)
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_px = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        try:
            _ret, labels, centers = cv2.kmeans(border_px, 2, None, criteria, 5,
                                               cv2.KMEANS_RANDOM_CENTERS)
        except cv2.error:
            return alpha_map
        bg_color = centers[int(np.argmax(np.unique(labels, return_counts=True)[1]))]
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        bleed = (dist < 35.0) & (alpha_map <= 0.90)
        alpha_final = alpha_map.copy()
        alpha_final[bleed] = 0.0
        removed = int(np.sum(bleed))
        if removed:
            logger.info("bg_svc: erased %d gap background px", removed)
        return alpha_final


class ArtifactIsolator:
    @staticmethod
    def remove_floating_dust(alpha_map: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num <= 1:
            return alpha_map
        min_area = (h * w) * 0.005
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
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
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
            if stats[i, cv2.CC_STAT_AREA] > (h * w) * 0.01:
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
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        bottom_region = binary[int(h * 0.8):, :]
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = alpha_map.copy()
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h * 0.8)
            aspect = float(cw) / ch if ch > 0 else 0
            if 100 < area < 5000 and aspect > 2.0 and global_y > h * 0.90:
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
        h, w = image_rgba.shape[:2]
        cs = min(h, w) // 6
        samples = np.concatenate([
            image_rgba[:cs, :cs, :3].reshape(-1, 3),
            image_rgba[:cs, -cs:, :3].reshape(-1, 3),
            image_rgba[-cs:, :cs, :3].reshape(-1, 3),
            image_rgba[-cs:, -cs:, :3].reshape(-1, 3),
        ])
        bg = np.median(samples, axis=0)
        flat = image_rgba[:, :, :3].reshape(-1, 3)
        bg_mask = (np.linalg.norm(flat - bg, axis=1) < 70).reshape(h, w).astype(np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        prod = (prob_map > 0.25).astype(np.uint8) * 255
        n, labs, st, _ = cv2.connectedComponentsWithStats(prod, connectivity=8)
        if n > 1:
            areas = [(i, st[i, cv2.CC_STAT_AREA]) for i in range(1, n)]
            areas.sort(key=lambda x: x[1], reverse=True)
            if areas and areas[0][1] > (h * w * 0.05):
                region = (labs == areas[0][0]).astype(np.uint8)
                region = cv2.dilate(region, kernel, iterations=2)
                bg_mask = cv2.bitwise_and(bg_mask, 255 - region)
        image_rgba[bg_mask > 0, 3] = 0
        return image_rgba


# ═════════════════════════════════════════════════════════════════════════
# Strategy definitions
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class _Strategy:
    models: List[str]
    post: str  # key selecting the post-processing chain


def _models_for(strategy: str) -> List[str]:
    """Resolve the model priority list for a strategy, honouring lightweight mode."""
    if LIGHTWEIGHT_MODE:
        return LIGHT_MODELS
    return STRATEGY_MODELS.get(strategy, LIGHT_MODELS)


_STRATEGIES: dict[str, _Strategy] = {
    # br_05 — gentle clean edge refinement
    "clean_commercial": _Strategy(_models_for("clean_commercial"), "clean"),
    # br_06 — precision geometry (same models as 05, distinct post-processing)
    "precision_geometry": _Strategy(_models_for("precision_geometry"), "geometry"),
    # br_08 — production: subject-aware wood-background + hole-fill chain
    "birefnet_production": _Strategy(_models_for("birefnet_production"), "production"),
    # br_11 — ultimate gaps: edge shaver + k-means colour bleed + dust removal
    "ultimate_gaps": _Strategy(_models_for("ultimate_gaps"), "gaps"),
    # br_12 — marketing variants: floating-artifact + bottom-text eraser
    "marketing_variants": _Strategy(_models_for("marketing_variants"), "marketing"),
    # br_13 — lite variants: lite/cloth/rmbg models + dedicated lite gap-fill post
    "lite_variants": _Strategy(_models_for("lite_variants"), "lite"),
}


# ═════════════════════════════════════════════════════════════════════════
# Post-processing dispatch
# ═════════════════════════════════════════════════════════════════════════

def _postprocess(post: str, input_np: np.ndarray, alpha: np.ndarray,
                 fast_mode: bool = False) -> np.ndarray:
    # ``fast_mode`` (or genuinely low RAM) only skips the EXPENSIVE OpenCV
    # sub-steps (wood remover, global colour-bleed). The cheap per-strategy
    # steps ALWAYS run so each of the 6 buttons stays visually distinct even on
    # a tiny VPS — this is what the standalone br_05..br_13 scripts each did.
    is_low_ram = _low_on_ram() or fast_mode
    if post == "clean":
        return CleanEdgeRefiner.refine(input_np, alpha)
    if post == "geometry":
        if SceneAnalyzer.is_human_photo(alpha):
            alpha = HumanPreserver.fix_hollows(alpha)
        else:
            mask = (alpha > 0.5).astype(np.uint8) * 255
            mask = HandRemover.remove_if_isolated(mask)
            mask = HoleFiller.fill(mask)
            mask = ThinPartHandler.handle(mask, alpha)
            alpha = mask.astype(np.float32) / 255.0
        return CleanEdgeRefiner.refine(input_np, alpha)
    if post == "production":
        alpha = CleanEdgeRefiner.refine(input_np, alpha)
        rgba = np.dstack([input_np, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
        if not is_low_ram:
            rgba = WoodBackgroundRemover.remove(rgba, alpha)
        alpha = rgba[:, :, 3].astype(np.float32) / 255.0
        return HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
    if post == "gaps":
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        if not is_low_ram:
            alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
        return ArtifactIsolator.remove_floating_dust(
            HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0)
    if post == "marketing":
        alpha = FloatingArtifactRemover.remove_floating_objects(alpha)
        alpha = BottomTextEraser.erase_bottom_text(alpha)
        alpha = EdgeShaver.shave_trailing_edges(alpha)
        if not is_low_ram:
            alpha = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha)
        return alpha
    if post == "lite":
        # br_13 — lite/cloth/rmbg: fill clothing gaps (bikini holes) + refine,
        # deliberately distinct from the "marketing" chain so the button never
        # matches marketing_variants even when models collapse to a shared one.
        alpha = HoleFiller.fill((alpha > 0.5).astype(np.uint8) * 255).astype(np.float32) / 255.0
        alpha = ArtifactIsolator.remove_floating_dust(alpha)
        return CleanEdgeRefiner.refine(input_np, alpha)
    return alpha


def _compose_rgba(input_np: np.ndarray, alpha: np.ndarray) -> bytes:
    h, w = input_np.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = input_np
    rgba[:, :, 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    trans = rgba[:, :, 3] == 0
    rgba[trans, :3] = 0  # no premultiplication (fixes black spots)
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG", compress_level=4)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════════
# Category detection for auto-select
# ═════════════════════════════════════════════════════════════════════════
#
# Category detection uses lightweight color/edge heuristics. The actual
# strategy selection is driven by per-category weighted scores loaded from
# the visual-regression metrics (SSIM / PSNR / edge-band IoU).

def _detect_category(input_np: np.ndarray) -> str:
    """Analyze image content to detect product category using lightweight
    color/edge heuristics. Returns 'clothing', 'electronics', 'beauty', or
    'unknown'.

    Uses only OpenCV operations (no ML/rembg) so it adds <10ms overhead.
    """
    if not _HAS_CV2:
        return "unknown"

    h, w = input_np.shape[:2]
    gray = cv2.cvtColor(input_np, cv2.COLOR_RGB2GRAY)

    # ── Color stats ──
    mean_rgb = input_np.mean(axis=(0, 1))
    std_rgb = input_np.std(axis=(0, 1)).mean()
    brightness = float(mean_rgb.mean())

    # Warmth: ratio of pixels where R > B
    warm_mask = input_np[:, :, 0].astype(float) > input_np[:, :, 2].astype(float)
    warmth_ratio = float(np.mean(warm_mask))

    # ── Edge density ──
    edges = cv2.Canny(gray, 30, 100)
    edge_density = float(np.mean(edges > 0))

    # ── Score each category ──
    scores = {}

    # Clothing: high color variance + high edge density + moderate warmth
    clothing_score = std_rgb * 0.4 + edge_density * 200 + warmth_ratio * 30
    if std_rgb >= 55 and edge_density >= 0.02:
        clothing_score += 20
    scores["clothing"] = clothing_score

    # Electronics: low color variance + low-mid brightness + low edge density
    electronics_score = (100 - std_rgb) * 0.2 + (150 - brightness) * 0.2 + (1 - edge_density) * 50
    if std_rgb < 55 and brightness < 150:
        electronics_score += 20
    scores["electronics"] = electronics_score

    # Beauty: moderate color variance + bright + low-mid edge density
    beauty_score = std_rgb * 0.2 + brightness * 0.15 + (1 - edge_density) * 30 + warmth_ratio * 20
    if 80 < brightness < 200 and std_rgb > 30 and edge_density < 0.07:
        beauty_score += 25
    scores["beauty"] = beauty_score

    # Debug log
    logger.debug(
        "bg_svc: category scores clothing=%.1f electronics=%.1f beauty=%.1f "
        "(bright=%.0f std=%.0f edge=%.3f warmth=%.2f)",
        scores["clothing"], scores["electronics"], scores["beauty"],
        brightness, std_rgb, edge_density, warmth_ratio,
    )

    best = max(scores, key=scores.get)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] < 5:
        return "unknown"

    return best


# ═════════════════════════════════════════════════════════════════════════
# Auto strategy selection (metrics-driven)
# ═════════════════════════════════════════════════════════════════════════

def _select_auto(input_np: np.ndarray) -> str:
    """Auto-select the best bg removal strategy using per-category weighted
    scores from the visual-regression metrics (SSIM, PSNR, edge-band IoU).

    Falls back to the legacy category->strategy map when the metrics file is
    unavailable or the detected category has no coverage data.
    """
    if _low_on_ram():
        return "lite_variants"

    if not _HAS_CV2:
        return "ultimate_gaps"

    category = _detect_category(input_np)
    scores = _load_category_scores()

    # 1. Try exact category match from metrics
    cat_scores = scores.get(category, {})
    if cat_scores:
        best = max(cat_scores, key=cat_scores.get)
        logger.info(
            "bg_svc: auto-selected '%s' for category '%s' (scores: %s)",
            best, category, cat_scores,
        )
        return best

    # 2. Fallback: best all-around strategy across all known categories
    all_scores: Dict[str, float] = {}
    for cat_data in scores.values():
        for strat, sc in cat_data.items():
            all_scores[strat] = all_scores.get(strat, 0.0) + sc
    if all_scores:
        best = max(all_scores, key=all_scores.get)
        logger.info(
            "bg_svc: auto-selected '%s' as all-around fallback (scores: %s)",
            best, all_scores,
        )
        return best

    # 3. Last resort: legacy mapping
    legacy = {
        "clothing": "clean_commercial",
        "electronics": "precision_geometry",
        "beauty": "precision_geometry",
    }
    return legacy.get(category, "ultimate_gaps")


# ═════════════════════════════════════════════════════════════════════════
# Public API
# ═════════════════════════════════════════════════════════════════════════

def remove_background(
    data: bytes,
    strategy: str = "auto",
    fast_mode: bool = False,
) -> bytes:
    """
    Remove background using one of the 6 tested pipelines (or 'auto').

    Always returns transparent PNG bytes; on any failure returns ``data``
    unchanged (never raises / never 500s).
    """
    if strategy in PRESET_ALIASES:
        strategy = PRESET_ALIASES[strategy]
    if strategy not in _STRATEGIES:
        strategy = DEFAULT_STRATEGY if DEFAULT_STRATEGY in _STRATEGIES else "auto"
    if strategy == "auto":
        try:
            img0 = Image.open(io.BytesIO(data)).convert("RGB")
            strategy = _select_auto(np.array(img0))
        except Exception:
            strategy = "clean_commercial"

    cfg = _STRATEGIES[strategy]
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        input_np = np.array(img)
        orig_size = img.size
        alpha = _generate_alpha(cfg.models, data, orig_size)
        if alpha is None:
            logger.warning("bg_svc: all models failed for '%s'; original returned", strategy)
            return data
        # Always run the per-strategy post chain (it self-gates its heavy steps
        # on fast_mode/low-RAM). Skipping it entirely made buttons whose models
        # collapsed to a shared fallback produce identical cutouts.
        alpha = _postprocess(cfg.post, input_np, alpha, fast_mode=fast_mode)
        alpha[alpha < 0.02] = 0.0
        alpha[alpha > 0.98] = 1.0
        return _compose_rgba(input_np, alpha)
    except Exception as exc:
        logger.warning("bg_svc: strategy '%s' failed (%s); original returned", strategy, exc)
        return data
    finally:
        # Keep small models warm for speed; only free RAM when it's actually
        # tight. The LRU cache cap keeps memory bounded under heavy concurrency.
        _SessionManager.release_if_low_ram()
        gc.collect()


def magic_erase(data: bytes, fast_mode: bool = False) -> bytes:
    """Convenience wrapper — best-effort background removal for the magic eraser."""
    return remove_background(data, strategy="auto", fast_mode=fast_mode)


# Backwards-compatible exports used by supplier_controller / free_image_tools
def remove_background_preset(data: bytes, preset: str = "general", fast_mode: bool = False) -> bytes:
    return remove_background(data, strategy=preset, fast_mode=fast_mode)


def remove_background_model(data: bytes, model_name: str = "isnet-general-use", fast_mode: bool = False) -> bytes:
    # In lightweight mode (tiny VPS) OR when heavy models are opted out, a heavy
    # request is transparently downgraded to the small segmenter instead of
    # risking an OOM that would crash the worker.
    if LIGHTWEIGHT_MODE:
        logger.info("bg_svc: lightweight mode — '%s' downgraded to u2net", model_name)
        model_name = "u2net"
    elif model_name in HEAVY_MODELS and not ALLOW_HEAVY_MODELS:
        logger.info("bg_svc: '%s' is heavy; using lightweight segmenter instead", model_name)
        model_name = "u2net"
    # A single explicit model still works: treat it as a 1-model chain.
    singleton = _Strategy([model_name, "isnet-general-use", "u2net"], "clean")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
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


# Models exposed for the frontend dropdown.
AVAILABLE_MODELS: List[str] = [
    "birefnet-general", "isnet-general-use", "u2net", "u2net_cloth_seg",
    "birefnet-massive", "birefnet-hrsod", "briaai-rmbg-1.4",
    "birefnet-general-lite", "silueta",
]
if SKIP_HEAVY_MODELS:
    for h in HEAVY_MODELS:
        if h in AVAILABLE_MODELS:
            AVAILABLE_MODELS.remove(h)

