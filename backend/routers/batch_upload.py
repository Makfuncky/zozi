"""
Batch Upload Router — process 10+ products in parallel using async workers
===========================================================================
Accepts up to 20 images + a JSON manifest, processes them concurrently
through the A/B test → BG removal → AI analysis pipeline, and returns
results in under 2 minutes.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from data.controllers_admin_controller import require_roles
from data.db import get_db
from data.providers_async_workers import (
    remove_background_async,
    analyze_product_image_async,
)
from data.providers_bg_remover import (
    VALID_STRATEGIES,
    _bytes_to_image,
    MemoryManager,
)
from data.providers_vision import suggest_price
from services.storage import storage as _storage
from services.media.media_router_service import (
    batch_publish_products as batch_publish_products_service,
)
logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BATCH_SIZE = 20


async def _save_batch_image(
    image_b64: str,
    supplier_id: int,
    product_name: str,
) -> Optional[str]:
    """Save a base64-encoded image through the storage abstraction.

    Returns the public URL or None on failure.
    """
    if not image_b64:
        return None
    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        raw = base64.b64decode(image_b64)

        safe_name = re.sub(r"[^a-z0-9]+", "_", product_name.lower().strip())[:40] or "product"
        filename = f"{supplier_id}_{safe_name}_{uuid.uuid4().hex[:8]}.png"
        key = f"supplier_uploads/{filename}"

        return _storage.save(key, raw, content_type="image/png")
    except Exception as exc:
        logger.error("Failed to save batch image for %s: %s", product_name, exc)
        return None


def _save_batch_image_sync(
    image_b64: str,
    supplier_id: int,
    product_name: str,
) -> Optional[str]:
    """Synchronous wrapper for saving batch images (for service use)."""
    if not image_b64:
        return None
    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        raw = base64.b64decode(image_b64)

        safe_name = re.sub(r"[^a-z0-9]+", "_", product_name.lower().strip())[:40] or "product"
        filename = f"{supplier_id}_{safe_name}_{uuid.uuid4().hex[:8]}.png"
        key = f"supplier_uploads/{filename}"

        return _storage.save(key, raw, content_type="image/png")
    except Exception as exc:
        logger.error("Failed to save batch image for %s: %s", product_name, exc)
        return None


@router.post("/products/batch-publish", status_code=201)
async def batch_publish_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    batch_results_json: str = Form(
        ...,
        description="JSON output from /supplier/products/batch-analyze — the full response body with results array",
    ),
    db: Session = Depends(get_db),
):
    """Publish products from batch-analyze results."""
    from controllers.supplier_controller import _persist_supplier_product

    def _save_image(bg_b64: str, supplier_id: int, name: str) -> Optional[str]:
        loop = asyncio.get_running_loop()
        try:
            return loop.run_until_complete(_save_batch_image(bg_b64, supplier_id, name))
        except RuntimeError:
            return _save_batch_image_sync(bg_b64, supplier_id, name)

    def _persist_product(**kwargs):
        return _persist_supplier_product(**kwargs)

    try:
        return batch_publish_products_service(
            db=db,
            batch_results_json=batch_results_json,
            current_user=current_user,
            save_image_fn=_save_image,
            persist_product_fn=_persist_product,
            max_batch_size=MAX_BATCH_SIZE,
        )
    except Exception as e:
        if "Invalid JSON" in str(e) or "No results" in str(e) or "Maximum" in str(e):
            raise HTTPException(400, str(e))
        raise HTTPException(500, f"Batch publish failed: {e}")


@router.post("/products/batch-analyze")
async def batch_analyze_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    images: List[UploadFile] = File(default=[], description="Up to 20 product images"),
    names_json: str = Form("[]", description="JSON array of product names (optional)"),
):
    """Analyze multiple products in parallel using async workers.

    For each image:
      1. Runs BG A/B test across 6 strategies → selects winner
      2. Applies winning BG strategy
      3. Runs AI analysis (category, variants, tags, price)
      4. Generates SEO copy in background

    All steps run in parallel across all images using asyncio.gather
    with a concurrency manager to prevent VPS overload.

    Args:
        images: Up to 20 product images.
        names_json: Optional JSON array of product name hints.

    Returns:
        List of analysis results with bg_removed (base64), AI fields, timing.
    """
    if len(images) > MAX_BATCH_SIZE:
        raise HTTPException(400, f"Maximum {MAX_BATCH_SIZE} images per batch")

    try:
        name_hints: List[str] = json.loads(names_json) if names_json else []
    except (json.JSONDecodeError, TypeError):
        name_hints = []
    name_hints = (name_hints + [""] * MAX_BATCH_SIZE)[:MAX_BATCH_SIZE]

    async def read_one(file: UploadFile, idx: int) -> tuple[bytes, str]:
        raw = await file.read()
        if not raw:
            raise HTTPException(400, f"Empty file at index {idx}")
        return raw, name_hints[idx] if idx < len(name_hints) else ""

    image_data = await asyncio.gather(*[read_one(f, i) for i, f in enumerate(images)])

    sem = asyncio.Semaphore(min(8, len(images)))

    async def process_one(args: tuple[bytes, str]) -> Dict[str, Any]:
        raw, hint = args
        async with sem:
            result: Dict[str, Any] = {
                "name_hint": hint,
                "status": "processing",
            }
            try:
                best_strategy = "production_birefnet"
                best_score = -1.0

                test_strategies = ["clean_commercial", "production_birefnet", "variant_testing"]
                scored: List[tuple[float, str]] = []

                for strategy in test_strategies:
                    try:
                        t0 = asyncio.get_running_loop().time()
                        processed = await remove_background_async(raw, strategy=strategy)
                        elapsed_ms = (asyncio.get_running_loop().time() - t0) * 1000

                        img = _bytes_to_image(processed)
                        alpha = img.split()[-1] if img.mode == "RGBA" else None
                        if alpha:
                            alpha_arr = alpha.tobytes()
                            fg = sum(1 for b in alpha_arr if b > 12)
                            total = len(alpha_arr)
                            coverage = fg / total if total > 0 else 0
                            score = coverage * 100
                            scored.append((score, strategy))
                    except Exception:
                        continue

                if scored:
                    scored.sort(key=lambda x: x[0], reverse=True)
                    best_score, best_strategy = scored[0]

                bg_result = await remove_background_async(raw, strategy=best_strategy)

                ai_result = await analyze_product_image_async(
                    raw, filename=hint or "", generate_copy=False, use_vision=True
                )

                loop = asyncio.get_running_loop()
                price_result = await loop.run_in_executor(
                    None, suggest_price, raw,
                    ai_result.get("name", hint),
                    ai_result.get("category", ""),
                )

                result.update({
                    "status": "completed",
                    "winner_strategy": best_strategy,
                    "winner_score": round(best_score, 2),
                    "bg_removed_b64": base64.b64encode(bg_result).decode("utf-8"),
                    "bg_size_bytes": len(bg_result),
                    "analysis": ai_result,
                    "price_suggestion": price_result,
                })

            except Exception as exc:
                logger.exception("Batch item failed: %s", exc)
                result["status"] = "failed"
                result["error"] = str(exc)

            return result

    results = await asyncio.gather(*[process_one(args) for args in image_data])

    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    strategy_wins: Dict[str, int] = {}
    for r in results:
        w = r.get("winner_strategy")
        if w:
            strategy_wins[w] = strategy_wins.get(w, 0) + 1

    MemoryManager.cleanup()

    return {
        "total": len(results),
        "completed": completed,
        "failed": failed,
        "strategy_wins": strategy_wins,
        "results": results,
    }


@router.get("/products/batch-limits")
def batch_limits():
    """Return batch upload configuration limits."""
    return {
        "max_batch_size": MAX_BATCH_SIZE,
        "parallel_concurrency": 8,
        "supported_strategies": VALID_STRATEGIES,
        "processing_style": "A/B test → auto-select best → AI analysis → price suggestion",
    }