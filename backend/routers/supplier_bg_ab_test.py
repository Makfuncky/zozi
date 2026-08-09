"""
BG Strategy A/B Testing Router
================================
Evaluates multiple background-removal strategies on the uploaded image and returns
quality metrics (edge clarity, alpha confidence, coverage) plus the best strategy.

The supplier frontend can then auto-select the winning strategy with one click
instead of manually trying each model.
"""
from __future__ import annotations

import gc
import logging
import time
from typing import Dict, Optional

import base64
import numpy as np
from PIL import Image

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from controllers.admin_controller import require_roles
from services.bg_removal_service import (
    VALID_STRATEGIES,
    remove_background,
    _HAS_CV2,
)
from providers.bg_remover import _bytes_to_image



logger = logging.getLogger(__name__)

router = APIRouter()

# The 6 production strategies mapped to their display names
AB_TEST_STRATEGIES = [
    "clean_commercial",
    "precision_geometry",
    "birefnet_production",
    "ultimate_gaps",
    "marketing_variants",
    "lite_variants",
]


def _compute_quality_score(image_np: np.ndarray, alpha_map: np.ndarray) -> Dict[str, float]:
    """Compute quality metrics for a BG-removed result.

    Returns:
        edge_clarity: 0-1, how sharp the edges are (Laplacian variance on alpha edges)
        alpha_confidence: 0-1, mean alpha value of non-zero pixels
        coverage: 0-1, proportion of image covered by foreground
        overall: 0-1, weighted composite of the above
        edge_pixels_pct: 0-1, proportion of boundary pixels
    """
    h, w = alpha_map.shape
    total_pixels = h * w

    # Alpha confidence: how solid the foreground alpha is
    fg_mask = alpha_map > 0.05
    fg_pixels = np.sum(fg_mask)
    coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0

    if fg_pixels > 0:
        alpha_confidence = float(np.mean(alpha_map[fg_mask]))
    else:
        alpha_confidence = 0.0

    # Edge clarity: use Laplacian variance on the alpha edges
    edge_clarity = 0.0
    edge_pixels_pct = 0.0
    if _HAS_CV2:
        try:
            import cv2
        except ImportError:
            return {
                "edge_clarity": 0.0,
                "alpha_confidence": round(alpha_confidence, 4),
                "coverage": round(coverage, 4),
                "overall": round(alpha_confidence * 0.4 + coverage * 0.2, 4),
                "edge_pixels_pct": 0.0,
            }

        alpha_uint8 = (alpha_map * 255).astype(np.uint8)

        # Find edges in alpha
        edges = cv2.Canny(alpha_uint8, 30, 150)
        edge_pixels = np.sum(edges > 0)
        edge_pixels_pct = float(edge_pixels / total_pixels) if total_pixels > 0 else 0.0

        # For edge region, compute Laplacian variance on the RGB image
        if edge_pixels > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            edge_region = cv2.dilate(edges, kernel, iterations=2)

            if image_np.ndim == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np

            lap = cv2.Laplacian(gray, cv2.CV_64F)
            edge_variance = float(np.var(lap[edge_region > 0])) if np.sum(edge_region > 0) > 0 else 0.0

            # Normalize: typical good edge variance is 50-500
            edge_clarity = min(1.0, edge_variance / 300.0)

    # Overall composite score
    overall = (alpha_confidence * 0.4) + (coverage * 0.2) + (edge_clarity * 0.4)

    return {
        "edge_clarity": round(edge_clarity, 4),
        "alpha_confidence": round(alpha_confidence, 4),
        "coverage": round(coverage, 4),
        "overall": round(overall, 4),
        "edge_pixels_pct": round(edge_pixels_pct, 4),
    }


@router.post("/upload/ab-test-bg")
async def ab_test_bg_strategies(
    image: UploadFile = File(...),
    strategies: Optional[str] = Form(None),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Enqueue A/B test across multiple BG removal strategies and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job tests
    up to 6 strategies and returns quality scores plus the winning image.
    """
    import uuid
    from utils.background_jobs import enqueue_ml_job
    from services.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_ab_test() -> dict:
        from services.bg_removal_service import remove_background, VALID_STRATEGIES
        from providers.bg_remover import _bytes_to_image, _compute_quality_score
        from PIL import Image
        import base64, time, gc

        raw_local = raw
        test_strategies = AB_TEST_STRATEGIES
        if strategies:
            parsed = [s.strip() for s in strategies.split(",") if s.strip() in VALID_STRATEGIES]
            if parsed:
                test_strategies = parsed

        img = _bytes_to_image(raw_local)
        img_rgb = np.array(img.convert("RGB"))
        max_test_dim = 384
        if max(img.size) > max_test_dim:
            ratio = max_test_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            img_rgb = np.array(img.convert("RGB"))

        results = {}
        scores = {}
        timing = {}
        winner = test_strategies[0]
        best_score = -1.0

        for strategy in test_strategies:
            try:
                t0 = time.perf_counter()
                processed = remove_background(raw_local, strategy=strategy)
                elapsed = (time.perf_counter() - t0) * 1000
                processed_img = _bytes_to_image(processed)
                processed_np = np.array(processed_img)
                if processed_np.shape[2] == 4:
                    alpha = processed_np[:, :, 3].astype(np.float32) / 255.0
                else:
                    alpha = np.ones(processed_np.shape[:2], dtype=np.float32)
                score = _compute_quality_score(img_rgb, alpha)
                scores[strategy] = score
                timing[strategy] = round(elapsed, 1)
                img_b64 = base64.b64encode(processed).decode("utf-8")
                results[strategy] = f"data:image/png;base64,{img_b64}"
                if score["overall"] > best_score:
                    best_score = score["overall"]
                    winner = strategy
            except Exception as exc:
                logger.warning("A/B test strategy %s failed: %s", strategy, exc)
                scores[strategy] = {
                    "edge_clarity": 0.0,
                    "alpha_confidence": 0.0,
                    "coverage": 0.0,
                    "overall": 0.0,
                    "edge_pixels_pct": 0.0,
                }
                timing[strategy] = 0.0
                results[strategy] = ""

        gc.collect()
        return {"winner": winner, "scores": scores, "results": results, "timing_ms": timing,
                "strategies_tested": test_strategies,
                "image_dimensions": {"width": img.width, "height": img.height}}

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_ab_test,
        metadata={"strategies": strategies},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}

@router.get("/upload/ab-test-strategies")
async def list_ab_test_strategies(
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return the list of available BG strategies for A/B testing."""
    return {
        "strategies": [
            {
                "key": "clean_commercial",
                "label": "Clean Commercial",
                "description": "br05 — Best for simple product shots, clean edges",
                "icon": "Wand2",
            },
            {
                "key": "precision_geometry",
                "label": "Precision Geometry",
                "description": "br06 — Best for geometric shapes, electronics, accessories",
                "icon": "Layers",
            },
            {
                "key": "birefnet_production",
                "label": "Production BiRefNet",
                "description": "br08 — Best for general products, good quality-speed tradeoff",
                "icon": "Zap",
            },
            {
                "key": "ultimate_gaps",
                "label": "Ultimate v11",
                "description": "br11 — Best for complex shapes with gaps and fine details",
                "icon": "Sparkles",
            },
            {
                "key": "marketing_variants",
                "label": "Ultimate v12",
                "description": "br12 — Best for marketing photos, floating artifacts removal",
                "icon": "Tag",
            },
            {
                "key": "lite_variants",
                "label": "Variant Testing",
                "description": "br13 — Best for clothing / fabric, lightweight model chain",
                "icon": "Camera",
            },
        ]
    }


# ── In-memory cache for category recommendations ─────────────────────────
_CATEGORY_RECO_CACHE: Dict[str, tuple] = {}
_CATEGORY_RECO_TTL_S = 3600  # 1 hour


@router.get("/upload/bg-recommendations")
async def get_bg_recommendations(
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return per-category BG strategy recommendations with metrics.

    Results are cached for 1 hour because the underlying visual-regression
    metrics only change when a new comparison run is executed.
    """
    import time
    from services.bg_removal_service import _get_category_recommendations

    now = time.time()
    cache_key = "bg_category_recommendations"
    cached = _CATEGORY_RECO_CACHE.get(cache_key)
    if cached and (now - cached[1] < _CATEGORY_RECO_TTL_S):
        return cached[0]

    recommendations = _get_category_recommendations()
    payload = {
        "recommendations": recommendations,
        "strategies": [
            {"key": "clean_commercial", "label": "Clean Commercial", "icon": "Wand2"},
            {"key": "precision_geometry", "label": "Precision Geometry", "icon": "Layers"},
            {"key": "birefnet_production", "label": "Production BiRefNet", "icon": "Zap"},
            {"key": "ultimate_gaps", "label": "Ultimate v11", "icon": "Sparkles"},
            {"key": "marketing_variants", "label": "Ultimate v12", "icon": "Tag"},
            {"key": "lite_variants", "label": "Variant Testing", "icon": "Camera"},
        ],
    }
    _CATEGORY_RECO_CACHE[cache_key] = (payload, now)
    return payload
