"""
Async Provider Workers
=======================
Async/parallel versions of the heavy AI providers (bg_remover, vision, OCR, text)
designed to handle 1000+ concurrent users on low-VPS hardware.

Uses asyncio.to_thread for CPU-bound operations and a ThreadPoolExecutor for
concurrent model inference. Memory is managed with LRU caches and automatic
model unloading when memory pressure is detected.

Usage:
    from providers.async_workers import (
        remove_background_async,
        analyze_product_image_async,
        embed_text_async,
        parse_bill_async,
        search_products_async,
        batch_analyze_images_async,
        parallel_process_product_async,
    )

    result = await parallel_process_product_async(image_bytes)
    # Returns {bg_result, ai_result} processed in parallel

Test file: backend/tests/_test_provider/test_async_workers.py

Module vs. package (PERF2-018)
------------------------------
ARCHITECTURE_STACK.md §3 draws ``providers/async_workers/`` with a trailing
slash, but this component is canonically the single module
``backend/providers/async_workers.py`` and stays that way. The normative
references all name the module path rather than a package layout: ARCH §3.1
("CPU-bound provider work runs through ``providers.async_workers``"), Law 128
("CPU-bound provider work via providers/async_workers") and
TECHNOLOGY_STACK.md §2 ("| providers/async_workers |"). The §3 slash is a
drawing of the conceptual group ("Thread/process pool executors for CPU-bound
work"), the same way the tree draws ``providers/_base.py`` as a leaf file.

A split was rejected on evidence, not preference:
  * There is no PDF worker here and never was — the module covers
    background removal, vision, OCR, text/embedding and search. Splitting into
    "image / PDF / ML" modules would invent a PDF module that has no code.
  * The audit's proposed ``ProcessPoolExecutor`` is a regression, not a fix.
    ``_run_in_thread`` is called with keyword arguments and with closures
    defined inside function bodies (``_search``, ``ollama_chat``); neither is
    picklable, and forking processes while the ONNX / Ollama / Pillow sessions
    are live is exactly the OOM this module exists to prevent (Law 121, Law
    128, Law 261/269). The heavy native work already releases the GIL, so the
    thread pool is the correct primitive.
  * A directory split is a rename/move and requires proving every import
    updates atomically; the current importer set is tests-only, but the
    restructure would still create files outside the allowed edit set.

Concurrency limits
------------------
Every operator-tunable limit is read from the typed pydantic-settings object
(``config.settings``) — i.e. from the environment variables documented in
TECHNOLOGY_STACK.md §20. No limit is hard-coded, so raising a knob in Coolify
takes effect instead of being silently defeated (Law 66, Law 67).
"""
from __future__ import annotations

import asyncio
import functools

HAS_ASYNC_WORKERS = True
import gc
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global thread pool for CPU-bound provider work
# ---------------------------------------------------------------------------
# A bounded pool prevents 1000+ threads on a VPS. The pool is sized from the
# CPU count (one worker thread per core) under a hard ceiling, so the pool can
# never grow without bound on a large host.

_THREAD_POOL_HARD_CEILING = 32
_THREAD_POOL_CPU_FLOOR = 2

_POOL_SIZE = max(1, min(_THREAD_POOL_HARD_CEILING, os.cpu_count() or _THREAD_POOL_CPU_FLOOR))
_executor = ThreadPoolExecutor(
    max_workers=_POOL_SIZE,
    thread_name_prefix="async_provider",
)

T = TypeVar("T")


async def _run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous function in the thread pool.

    Uses asyncio.to_thread which automatically acquires a thread from the
    executor. Falls back to loop.run_in_executor if asyncio.to_thread is
    unavailable.
    """
    loop = asyncio.get_running_loop()
    fn = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(_executor, fn)


# ---------------------------------------------------------------------------
# Provider imports (lazy — only loaded when first used)
# ---------------------------------------------------------------------------

def _get_bg_remover():
    from providers.image.bg_remover import remove_background
    return remove_background


def _get_vision():
    from providers.ai.vision import analyze_product_image
    return analyze_product_image


def _get_text():
    from providers.ai.text import embed_text, _ollama_chat
    return embed_text, _ollama_chat


def _get_ocr():
    from providers.image.ocr import parse_bill_text
    return parse_bill_text


def _get_search():
    from providers.ai.search import AdvancedSearchEngine
    return AdvancedSearchEngine


# ---------------------------------------------------------------------------
# 1. ASYNC BACKGROUND REMOVAL
# ---------------------------------------------------------------------------

async def remove_background_async(
    image_bytes: bytes,
    strategy: str = "general",
    model: Optional[str] = None,
) -> bytes:
    """Remove image background asynchronously in a thread pool.

    For high-concurrency scenarios:
    - Images are auto-downscaled before model inference (configurable)
    - Models are cached in _SessionManager (shared across threads)
    - Memory is freed after each call via MemoryManager.cleanup()

    Args:
        image_bytes: Raw image bytes.
        strategy: Processing strategy name.
        model: Optional specific model name.

    Returns:
        Processed PNG bytes.
    """
    remove_fn = _get_bg_remover()
    return await _run_in_thread(remove_fn, image_bytes, model=model, strategy=strategy)


async def batch_remove_background_async(
    image_batches: List[Tuple[bytes, Optional[str], Optional[str]]],
    concurrency: int = 4,
) -> List[bytes]:
    """Remove backgrounds for multiple images concurrently.

    Args:
        image_batches: List of (image_bytes, strategy, model) tuples.
        concurrency: Max concurrent removals.

    Returns:
        List of processed bytes in same order.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _process_one(args: Tuple[bytes, Optional[str], Optional[str]]) -> bytes:
        async with semaphore:
            return await remove_background_async(args[0], args[1] or "general", args[2])

    tasks = [_process_one(batch) for batch in image_batches]
    return await asyncio.gather(*tasks)


# ---------------------------------------------------------------------------
# 2. ASYNC PRODUCT ANALYSIS
# ---------------------------------------------------------------------------

async def analyze_product_image_async(
    image_bytes: bytes,
    filename: str = "",
    generate_copy: bool = False,
    use_vision: bool = True,
    subcategory: str = "",
) -> Dict[str, Any]:
    """Analyze a product image asynchronously.

    Runs the synchronous analyze_product_image in the thread pool.
    When use_vision=True, Ollama HTTP calls are blocking but run in the
    thread pool so they don't block the event loop.

    Args:
        image_bytes: Raw image bytes.
        filename: Optional filename hint.
        generate_copy: Whether to generate marketing copy.
        use_vision: Whether to use vision model.
        subcategory: Optional subcategory hint.

    Returns:
        Analysis result dict.
    """
    analyze_fn = _get_vision()
    async with concurrency.http:
        return await _run_in_thread(
            analyze_fn,
            image_bytes,
            filename=filename,
            generate_copy=generate_copy,
            use_vision=use_vision,
            subcategory=subcategory,
        )


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


async def batch_analyze_images_async(
    image_paths: List[str],
    concurrency: int = 8,
) -> List[Dict[str, Any]]:
    """Analyze multiple product images in parallel.

    Args:
        image_paths: List of image file paths.
        concurrency: Max concurrent analyses.

    Returns:
        List of analysis result dicts.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _analyze_one(path: str) -> Dict[str, Any]:
        async with semaphore:
            try:
                data = await asyncio.to_thread(_read_file_bytes, path)
                return await analyze_product_image_async(
                    data, filename=os.path.basename(path), use_vision=True
                )
            except Exception as exc:
                logger.error("Batch analysis failed for %s: %s", path, exc)
                return {
                    "name": os.path.splitext(os.path.basename(path))[0],
                    "category": "general",
                    "error": str(exc),
                    "image_path": path,
                }

    tasks = [_analyze_one(p) for p in image_paths]
    return await asyncio.gather(*tasks)


# ---------------------------------------------------------------------------
# 3. ASYNC TEXT EMBEDDING
# ---------------------------------------------------------------------------

async def embed_text_async(text: str) -> List[float]:
    """Generate text embedding asynchronously.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector as list of floats.
    """
    embed_fn, _ = _get_text()
    async with concurrency.http:
        return await _run_in_thread(embed_fn, text)


async def batch_embed_text_async(
    texts: List[str],
    concurrency: int = 8,
) -> List[List[float]]:
    """Generate embeddings for multiple texts concurrently.

    Args:
        texts: List of texts to embed.
        concurrency: Max concurrent API calls.

    Returns:
        List of embedding vectors.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _embed_one(text: str) -> List[float]:
        async with semaphore:
            return await embed_text_async(text)

    tasks = [_embed_one(t) for t in texts]
    return await asyncio.gather(*tasks)


# ---------------------------------------------------------------------------
# 4. ASYNC OCR
# ---------------------------------------------------------------------------

async def parse_bill_async(image_bytes: bytes) -> Dict[str, Any]:
    """Parse a bill/receipt image asynchronously.

    Args:
        image_bytes: Raw image bytes.

    Returns:
        Dict with extracted bill fields.
    """
    ocr_fn = _get_ocr()
    return await _run_in_thread(ocr_fn, image_bytes)


# ---------------------------------------------------------------------------
# 5. ASYNC SEARCH
# ---------------------------------------------------------------------------

async def search_products_async(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Execute a product search asynchronously.

    Args:
        query: Natural language search query.
        filters: Optional additional filters.
        limit: Maximum results.

    Returns:
        Search results with parsed query.
    """
    SearchCls = _get_search()
    engine = SearchCls()

    def _search():
        return engine.search(query, filters=filters, limit=limit)

    async with concurrency.http:
        return await _run_in_thread(_search)


# ---------------------------------------------------------------------------
# 6. PARALLEL PROCESSING PIPELINE
# ---------------------------------------------------------------------------

async def parallel_process_product_async(
    image_bytes: bytes,
    filename: str = "",
) -> Dict[str, Any]:
    """Run BG removal and AI analysis in parallel for maximum throughput.

    This is the primary entry point for the supplier upload flow.
    Both operations run simultaneously in the thread pool, cutting
    Step-2 time by ~40%.

    Args:
        image_bytes: Raw image bytes.
        filename: Optional filename hint.

    Returns:
        Combined result with bg_result and ai_result.
    """
    bg_coro = remove_background_async(image_bytes, strategy="general")
    ai_coro = analyze_product_image_async(image_bytes, filename=filename, generate_copy=False)

    bg_result, ai_result = await asyncio.gather(bg_coro, ai_coro)

    return {
        "bg_result": bg_result,
        "ai_result": ai_result,
    }


async def full_supplier_pipeline_async(
    image_bytes: bytes,
    filename: str = "",
) -> Dict[str, Any]:
    """Complete supplier upload pipeline: BG removal → AI analysis → SEO copy.

    Runs steps in parallel where possible:
    - Phase 1 (parallel): BG removal + AI analysis
    - Phase 2 (sequential): Generate marketing copy from AI results

    Total time: ~5-8 seconds for a typical product image.

    Args:
        image_bytes: Raw image bytes.
        filename: Optional filename hint.

    Returns:
        Complete result with bg_removed, analysis, and copy.
    """
    # Phase 1: Parallel BG removal + AI analysis
    bg_coro = remove_background_async(image_bytes, strategy="clean_commercial")
    ai_coro = analyze_product_image_async(
        image_bytes, filename=filename, generate_copy=False, use_vision=True
    )
    bg_result, ai_result = await asyncio.gather(bg_coro, ai_coro)

    # Phase 2: Generate copy from AI results (using lazy-import wrappers)
    _, ollama_chat = _get_text()
    from providers.ai.vision import suggest_price as _suggest_price
    price_result = _suggest_price(image_bytes, product_name=ai_result.get("name", ""), category=ai_result.get("category", ""))

    if ai_result.get("name"):
        copy_prompt = (
            f"Write a short SEO product description for: {ai_result['name']}. "
            f"Category: {ai_result.get('category')}. "
            f"Color: {ai_result.get('color', '')}. "
            f"Return JSON with english_description and bullet_points_en."
        )
        copy_text = await _run_in_thread(ollama_chat, copy_prompt)
    else:
        copy_text = ""

    return {
        "bg_removed": bg_result,
        "analysis": ai_result,
        "price_suggestion": price_result,
        "marketing_copy": copy_text,
    }


# ---------------------------------------------------------------------------
# CONCURRENCY MANAGER
# ---------------------------------------------------------------------------

class ConcurrencyManager:
    """Manages concurrency limits for provider calls.

    Ensures the system never exceeds safe resource limits when handling
    1000+ concurrent users. Uses a semaphore-based token bucket system.

    Every limit resolves from a documented environment knob read through the
    typed settings object (TECHNOLOGY_STACK.md §20, Law 84/203), with named
    constants as the fallback where no knob exists yet:

        bg_removal   -> BG_MAX_CONCURRENT              settings.bg_max_concurrent
        ai_analysis  -> COUNTRY_AI_MAX_CONCURRENT_JOBS settings.country_ai_max_concurrent_jobs
        ocr          -> (no documented knob)           _FALLBACK_MAX_OCR
        embedding    -> (no documented knob)           _FALLBACK_MAX_EMBED
        http         -> (no documented knob)           _FALLBACK_MAX_HTTP

    Two mappings are deliberately NOT made, and the reasons matter:

      * ``BG_MAX_SESSION_CACHE`` has no home here. This module builds
        semaphores; it has no session cache. That knob is correctly consumed
        one layer down by ``providers/bg_removal/bg_removal_service.py``
        (``MAX_SESSION_CACHE = settings.bg_max_session_cache``), which owns the
        rembg LRU. Wiring it here would be a second, competing definition.
      * ``ML_WORKERS`` is likewise consumed one layer down, by
        ``infrastructure/utils/background_jobs.py``, which sizes its own
        dedicated ML thread pool. Reading it here too would make one operator
        knob silently resize two independent pools.

    Explicit keyword overrides are still honoured and still bypass the pool
    clamp, so a caller that deliberately wants more than the pool is not
    second-guessed.

    Usage:
        manager = ConcurrencyManager()          # documented knobs
        manager = ConcurrencyManager(max_bg=4)  # explicit override
        async with manager.bg_removal:
            result = await remove_background_async(image)
    """

    def __init__(
        self,
        max_bg: Optional[int] = None,
        max_ai: Optional[int] = None,
        max_ocr: Optional[int] = None,
        max_embed: Optional[int] = None,
        max_http: Optional[int] = None,
    ):
        limits = resolve_concurrency_limits(
            max_bg=max_bg,
            max_ai=max_ai,
            max_ocr=max_ocr,
            max_embed=max_embed,
            max_http=max_http,
        )
        self.bg_removal = asyncio.Semaphore(limits["max_bg"])
        self.ai_analysis = asyncio.Semaphore(limits["max_ai"])
        self.ocr = asyncio.Semaphore(limits["max_ocr"])
        self.embedding = asyncio.Semaphore(limits["max_embed"])
        self.http = asyncio.Semaphore(limits["max_http"])

    def describe(self) -> Dict[str, Any]:
        """Return the resolved limits and where each came from.

        Useful for startup logging and for operators confirming that a knob
        actually took effect, which is precisely what the two-sources-of-truth
        defect made impossible to see.
        """
        limits = resolve_concurrency_limits()
        return {
            "limits": limits,
            "pool_size": _POOL_SIZE,
            "settings": {
                "bg_max_concurrent": _read_setting("bg_max_concurrent", None),
                "country_ai_max_concurrent_jobs": _read_setting(
                    "country_ai_max_concurrent_jobs", None
                ),
            },
        }


# ---------------------------------------------------------------------------
# CONCURRENCY LIMIT RESOLUTION — single source of truth
# ---------------------------------------------------------------------------
# Historical defaults, kept as named constants so the value lives in exactly
# one place (Law 66, Law 67). They are FALLBACKS: a documented env knob always
# wins. They are deliberately never raised above what the current code used,
# so an operator who sets nothing observes the pre-existing behaviour.

_FALLBACK_MAX_BG = 4
_FALLBACK_MAX_AI = 8
_FALLBACK_MAX_OCR = 4
_FALLBACK_MAX_EMBED = 8
_FALLBACK_MAX_HTTP = 4

# How many of the pool's threads each gate may use when nothing is configured.
# The `// 2` gates are the memory-hungry ones (Law 121 — rembg/ONNX sessions):
# a pool of N threads is assumed able to hold N/2 live native sessions safely.
_BG_POOL_SHARE = 2
_OCR_POOL_SHARE = 2
_AI_POOL_SHARE = 1
_EMBED_POOL_SHARE = 1
_HTTP_POOL_SHARE = 1


def _read_setting(name: str, fallback: Optional[int]) -> Optional[int]:
    """Read one typed integer knob off ``settings``.

    Law 84/203 forbid raw ``os.getenv()`` in production code, so knobs are read
    through pydantic-settings only. A field that does not exist on the settings
    model (or is unset/None) yields ``fallback`` rather than raising — the
    settings object is a growing surface and a missing tuning knob must not take
    the provider layer down (Law 30).

    Existence is tested against ``model_fields`` rather than ``getattr``: a
    pydantic-settings model raises AttributeError (and logs) for an undeclared
    field, which would turn every import of this module into console noise for
    the three gates that have no documented knob.
    """
    if name not in type(settings).model_fields:
        return fallback
    value = getattr(settings, name, None)
    if value is None:
        return fallback
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        logger.warning(
            "async_workers: setting %s=%r is not an integer; using %r",
            name,
            value,
            fallback,
        )
        return fallback
    if parsed < 1:
        logger.warning(
            "async_workers: setting %s=%d is below 1; using %r",
            name,
            parsed,
            fallback,
        )
        return fallback
    return parsed


def _pool_clamp(configured: int, share: int) -> int:
    """Clamp a configured limit to what the thread pool can actually serve.

    The clamp is a memory guard, not a tuning ceiling: raising
    ``BG_MAX_CONCURRENT`` above the pool size must not be able to create more
    simultaneous native sessions than there are threads to drive them. It is
    intentionally as tight as the pre-fix code was, so the fix never weakens the
    OOM guard while making the knob effective.
    """
    return max(1, min(configured, max(1, _POOL_SIZE // share)))


def resolve_concurrency_limits(
    max_bg: Optional[int] = None,
    max_ai: Optional[int] = None,
    max_ocr: Optional[int] = None,
    max_embed: Optional[int] = None,
    max_http: Optional[int] = None,
) -> Dict[str, int]:
    """Resolve the five concurrency limits.

    Precedence, highest first:
      1. an explicit keyword argument (caller intent, unclamped);
      2. the documented typed settings knob;
      3. the named historical constant, clamped to the pool.

    Both the ``ConcurrencyManager`` signature and the module-level ``concurrency``
    singleton route through this one function, so the two can no longer drift
    apart — that drift was the finding.
    """
    bg_setting = _read_setting("bg_max_concurrent", _FALLBACK_MAX_BG)
    ai_setting = _read_setting("country_ai_max_concurrent_jobs", _FALLBACK_MAX_AI)
    ocr_setting = _read_setting("ocr_max_concurrent", _FALLBACK_MAX_OCR)
    embed_setting = _read_setting("embed_max_concurrent", _FALLBACK_MAX_EMBED)
    http_setting = _read_setting("http_max_concurrent", _FALLBACK_MAX_HTTP)

    def _resolve(explicit: Optional[int], setting: int, fallback: int, share: int) -> int:
        if explicit is not None:
            return max(1, int(explicit))
        configured = setting if setting is not None else fallback
        return _pool_clamp(configured, share)

    return {
        "max_bg": _resolve(max_bg, bg_setting, _FALLBACK_MAX_BG, _BG_POOL_SHARE),
        "max_ai": _resolve(max_ai, ai_setting, _FALLBACK_MAX_AI, _AI_POOL_SHARE),
        "max_ocr": _resolve(max_ocr, ocr_setting, _FALLBACK_MAX_OCR, _OCR_POOL_SHARE),
        "max_embed": _resolve(max_embed, embed_setting, _FALLBACK_MAX_EMBED, _EMBED_POOL_SHARE),
        "max_http": _resolve(max_http, http_setting, _FALLBACK_MAX_HTTP, _HTTP_POOL_SHARE),
    }


# Global concurrency manager with conservative defaults for VPS.
# Built through the same resolution path as any hand-made manager, so the
# singleton cannot drift away from the documented knobs.
concurrency = ConcurrencyManager()


# ---------------------------------------------------------------------------
# MEMORY-AWARE BATCH PROCESSOR
# ---------------------------------------------------------------------------

async def process_large_batch_async(
    items: List[Any],
    processor: Callable[..., Any],
    batch_size: int = 10,
    concurrency_limit: int = 4,
) -> List[Any]:
    """Process a large batch of items with memory-aware batching.

    Processes items in batches of `batch_size`, with garbage collection
    between batches to prevent memory buildup.

    Args:
        items: List of items to process.
        processor: Async callable to process each item.
        batch_size: Items per batch before GC.
        concurrency_limit: Max concurrent items within a batch.

    Returns:
        List of results.
    """
    results = []
    semaphore = asyncio.Semaphore(concurrency_limit)

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        async def _process_item(item: Any) -> Any:
            async with semaphore:
                return await processor(item)

        batch_results = await asyncio.gather(*[_process_item(item) for item in batch])
        results.extend(batch_results)

        # Force GC between batches to prevent memory buildup
        gc.collect()

    return results
