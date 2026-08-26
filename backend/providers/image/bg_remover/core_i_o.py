# ========================== CORE I/O ==========================
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional

from PIL import Image

from . import rembg_lazy_load
import providers.image.bg_remover as _pkg


logger = logging.getLogger(__name__)


def _get_remove():
    """Get the current remove function (allows mocking in tests)."""
    return _pkg.remove


def _get_new_session():
    """Get the current new_session function (allows mocking in tests)."""
    return _pkg.new_session


def _ensure_rembg():
    """Ensure rembg is loaded (delegates to rembg_lazy_load).
    
    If remove is already set at the package level (e.g., by tests), don't override it.
    """
    if _pkg.remove is not None:
        return
    rembg_lazy_load._ensure_rembg()
    # Sync package-level remove/new_session with rembg_lazy_load
    if _pkg.remove is None:
        _pkg.remove = rembg_lazy_load.remove
    if _pkg.new_session is None:
        _pkg.new_session = rembg_lazy_load.new_session


def _safe_remove(img: Image.Image, session: Any) -> Image.Image:
    """Pass PNG bytes through rembg remove() with alpha_matting=False."""
    _ensure_rembg()
    remove = _get_remove()
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


def rembg_remove_bytes(
    data: bytes,
    session: Any,
    alpha_matting: bool = False,
    post_process_mask: bool = True,
) -> bytes:
    """Run rembg remove() on raw image bytes; return the resulting PNG bytes.

    Centralises the live rembg SDK call so services no longer import rembg
    directly. ``session`` must be a rembg session built by the caller.
    """
    _ensure_rembg()
    remove = _get_remove()
    if remove is None:
        raise RuntimeError("rembg is not available")
    return remove(
        data,
        session=session,
        alpha_matting=alpha_matting,
        post_process_mask=post_process_mask,
    )


def create_rembg_session(model_name: str):
    """Create a rembg session for ``model_name`` (no caching).

    Centralises the ``rembg.new_session`` SDK call so services no longer
    import rembg directly. Returns the session, or ``None`` if rembg is
    unavailable.
    """
    _ensure_rembg()
    new_session = _get_new_session()
    if new_session is None:
        return None
    return new_session(model_name)


def create_frugal_rembg_session(
    model_name: str,
    *,
    aliases: Optional[Dict[str, str]] = None,
    heavy_models: Optional[set] = None,
    heavy_threads: int = 2,
    light_threads: int = 4,
) -> Any:
    """Build a rembg session with MEMORY-FRUGAL ONNX Runtime options.

    The default ``rembg.new_session`` uses ORT's BFC memory *arena*, which
    pre-reserves and doubles allocations — that is what produced the
    ``bad allocation`` for heavy BiRefNet models. This path instead:

      * ``enable_cpu_mem_arena = False``  → allocate the exact tensor size once.
      * ``enable_mem_pattern = False``    → no speculative pre-allocation.
      * ``ORT_SEQUENTIAL`` execution      → no parallel activation buffers.
      * capped ``intra_op_num_threads``   → bounded CPU on a shared VPS.

    Centralises the live ``rembg`` / ``onnxruntime`` SDK calls so services no
    longer import them directly. Falls back to ``create_rembg_session`` if the
    frugal path is unavailable.
    """
    real = (aliases or {}).get(model_name, model_name)
    try:
        import onnxruntime as ort
        from rembg.session_factory import sessions_class

        session_cls = next((c for c in sessions_class if c.name() == real), None)
        if session_cls is None:
            return create_rembg_session(real)

        opts = ort.SessionOptions()
        opts.enable_cpu_mem_arena = False
        opts.enable_mem_pattern = False
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = heavy_threads if real in (heavy_models or set()) else light_threads
        opts.inter_op_num_threads = 1
        return session_cls(real, opts, providers=["CPUExecutionProvider"])
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("bg_remover: frugal session for '%s' failed (%s); using default", real, exc)
        return create_rembg_session(real)


def _bytes_to_image(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    compress_level = 4  # default PNG compression
    try:
        from infrastructure.utils.config import settings
        compress_level = getattr(settings, "rembg_png_compression", 4)
    except Exception:
        pass
    img.save(buf, format=fmt, compress_level=compress_level)
    return buf.getvalue()


def bytes_to_image(data: bytes) -> Image.Image:
    """Inverse of :func:`_image_to_bytes` — load raw image bytes into a PIL image."""
    return Image.open(io.BytesIO(data)).convert("RGBA")

