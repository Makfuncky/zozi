"""
Image AI Service — background removal and multi-angle product view generation.

Background removal strategy:
    1. rembg BiRefNet-lite — offline, stronger for product cut-outs (primary)
    2. rembg default       — offline compatibility fallback
    3. HF Inference API    — if HF_API_TOKEN is set and model responds (secondary)
    4. Original image      — graceful no-op fallback

Angle view generation strategy:
    1. TRELLIS Space preview video — generate a real rotating 3D preview and
       extract 4 frames as product views
    2. No fake fallback            — return [] rather than warped duplicates

Environment:
    HF_API_TOKEN — optional; used for Hugging Face-authenticated requests
    BG_REMOVAL_MODEL — optional; rembg session name, defaults to birefnet-general-lite
    MULTIVIEW_SPACE_ID — optional; defaults to trellis-community/TRELLIS
"""

import io
import logging
import os
import tempfile
from functools import lru_cache
from typing import Any
from typing import cast
from typing import Optional

import requests
from PIL import Image


class _ImageIOMissing:
    @staticmethod
    def get_reader(*_args: Any, **_kwargs: Any) -> Any:
        raise ImportError("imageio is not installed")

try:
    import imageio.v2 as imageio  # optional – only needed for TRELLIS video frame extraction
    _IMAGEIO_AVAILABLE = True
except ImportError:  # pragma: no cover
    imageio = _ImageIOMissing()  # type: ignore[assignment]
    _IMAGEIO_AVAILABLE = False

logger = logging.getLogger(__name__)

HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
_HF_BASE = "https://api-inference.huggingface.co/models"

RMBG_MODEL = "briaai/RMBG-2.0"
BG_REMOVAL_MODEL = os.getenv("BG_REMOVAL_MODEL", "birefnet-general-lite")
MULTIVIEW_SPACE_ID = os.getenv("MULTIVIEW_SPACE_ID", "trellis-community/TRELLIS")
ZERO123_MODEL = os.getenv("ZERO123_MODEL", "sudo-ai/zero123plus")

_MAX_DIM = 1024  # resize before API calls to save bandwidth


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def remove_background(image_bytes: bytes) -> bytes:
    """
    Remove image background and composite onto a clean white background.

    Strategy (in order):
      1. rembg library        — works offline, uses onnxruntime
      2. HF Inference API     — if HF_API_TOKEN is set and model responds
      3. Original unchanged   — graceful fallback so upload never fails

    Returns JPEG bytes (always; even on failure returns original re-encoded).
    """
    resized = _resize_if_needed(image_bytes)

    # ── 1: rembg preferred model (offline, primary) ───────────────────────
    try:
        png_bytes = _remove_with_rembg(resized, BG_REMOVAL_MODEL)
        result = _composite_white(png_bytes)
        logger.info("Background removed via rembg session %s", BG_REMOVAL_MODEL)
        return result
    except ImportError:
        logger.debug("rembg not installed — skipping")
    except Exception as exc:
        logger.warning("rembg preferred session failed: %s", exc)

    # ── 2: rembg default session fallback ──────────────────────────────────
    try:
        png_bytes = _remove_with_rembg(resized, None)
        result = _composite_white(png_bytes)
        logger.info("Background removed via rembg default session")
        return result
    except ImportError:
        logger.debug("rembg not installed — skipping")
    except Exception as exc:
        logger.warning("rembg default session failed: %s", exc)

    # ── 3: HF Inference API (optional, secondary) ──────────────────────────
    if HF_API_TOKEN:
        png_bytes = _call_hf_image_api(RMBG_MODEL, resized, timeout=60)
        if png_bytes:
            result = _composite_white(png_bytes)
            logger.info("Background removed via HF %s", RMBG_MODEL)
            return result

    # ── 4: Graceful fallback ───────────────────────────────────────────────
    logger.warning(
        "Background removal unavailable (rembg not installed, no HF token, "
        "or API unreachable). Install rembg: pip install rembg"
    )
    return image_bytes


def generate_angles(image_bytes: bytes) -> list[bytes]:
    """
    Generate 4 product angle views.

    Strategy (in order):
      1. TRELLIS Space (HF) — real 3D-based views (best quality)
      2. Zero123Plus Space (HF) — multi-view diffusion model
      3. PIL geometric transforms — instant offline fallback (always works)
    """
    resized = _resize_if_needed(image_bytes)

    # ── 1: TRELLIS ─────────────────────────────────────────────────────────
    try:
        views = _generate_angles_via_trellis_preview(resized)
        if len(views) >= 4:
            logger.info("Generated 4 angle views via TRELLIS")
            return views[:4]
        if views:
            logger.warning("TRELLIS returned %d views (< 4); trying next", len(views))
    except Exception as exc:
        logger.warning("TRELLIS angle generation failed: %s", exc)

    # ── 2: Zero123Plus via HF Gradio Space ─────────────────────────────────
    if HF_API_TOKEN:
        try:
            views = _generate_angles_via_zero123plus(resized)
            if len(views) >= 4:
                logger.info("Generated 4 angle views via Zero123Plus")
                return views[:4]
        except Exception as exc:
            logger.warning("Zero123Plus angle generation failed: %s", exc)

    # ── 3: No fallback by default when online generation services are unavailable
    # only return angles from live model services to avoid inconsistent fake results.
    logger.info("No angle generation backend available; returning empty list")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL – HF API helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hf_headers() -> dict:
    return {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}


def _call_hf_image_api(model: str, image_bytes: bytes, timeout: int = 60) -> Optional[bytes]:
    """POST raw image bytes to an HF Inference API endpoint; return image bytes on success."""
    try:
        resp = requests.post(
            f"{_HF_BASE}/{model}",
            headers={**_hf_headers(), "Content-Type": "application/octet-stream"},
            data=image_bytes,
            timeout=timeout,
        )
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "image" in ct:
            return resp.content
        if resp.status_code == 410:
            logger.debug("HF model %s: HTTP 410 (removed from free tier)", model)
        elif resp.status_code == 503:
            logger.warning("HF model %s: 503 (loading); try again shortly", model)
        else:
            logger.warning("HF model %s: HTTP %d — %.200s", model, resp.status_code, resp.text)
    except requests.Timeout:
        logger.warning("HF model %s: request timed out after %ds", model, timeout)
    except Exception as exc:
        logger.warning("HF model %s: %s", model, exc)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL – rembg helpers
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=4)
def _get_rembg_session(session_name: Optional[str]):
    from rembg import new_session  # type: ignore

    if not session_name:
        return None
    return new_session(session_name)


def _remove_with_rembg(image_bytes: bytes, session_name: Optional[str]) -> bytes:
    from rembg import remove as rembg_remove  # type: ignore

    session = _get_rembg_session(session_name)
    if session is None:
        return cast(bytes, rembg_remove(image_bytes))
    return cast(bytes, rembg_remove(image_bytes, session=session))


def _get_trellis_client():
    from gradio_client import Client  # type: ignore

    token = HF_API_TOKEN or None
    return Client(MULTIVIEW_SPACE_ID, token=token, verbose=False)


def _generate_angles_via_trellis_preview(image_bytes: bytes) -> list[bytes]:
    from gradio_client import handle_file  # type: ignore

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_input:
        temp_input.write(image_bytes)
        input_path = temp_input.name

    try:
        last_error: Optional[Exception] = None
        for attempt in range(2):
            client = _get_trellis_client()
            try:
                client.predict(api_name="/start_session")
            except Exception:
                logger.debug("TRELLIS start_session failed or is unnecessary", exc_info=True)

            image_inputs = []
            try:
                preprocessed = client.predict(image=handle_file(input_path), api_name="/preprocess_image")
                image_inputs.append(preprocessed)
            except Exception:
                logger.debug("TRELLIS preprocess_image failed; falling back to direct input", exc_info=True)
            image_inputs.append(handle_file(input_path))

            for image_input in image_inputs:
                try:
                    result = client.predict(
                        image=image_input,
                        multiimages=[],
                        seed=0,
                        ss_guidance_strength=7.5,
                        ss_sampling_steps=12,
                        slat_guidance_strength=3.0,
                        slat_sampling_steps=12,
                        multiimage_algo="stochastic",
                        mesh_simplify=0.95,
                        texture_size=1024,
                        api_name="/generate_and_extract_glb",
                    )
                    preview_video = result[0]["video"] if isinstance(result, tuple) and result and isinstance(result[0], dict) else None
                    if preview_video:
                        return _extract_views_from_preview_video(preview_video, count=4)
                except Exception as exc:
                    last_error = exc
                    logger.debug("TRELLIS generate attempt %d failed", attempt + 1, exc_info=True)

        if last_error:
            raise last_error
        return []
    finally:
        try:
            os.unlink(input_path)
        except OSError:
            pass


def _extract_views_from_preview_video(video_path: str, count: int = 4) -> list[bytes]:
    try:
        reader = imageio.get_reader(video_path)
    except Exception:
        logger.warning("imageio not installed – skipping TRELLIS video frame extraction")
        return []
    try:
        frame_count_fn = cast(Any, getattr(reader, "count_frames", None))
        frame_count_raw = frame_count_fn() if callable(frame_count_fn) else 0
        frame_count = int(cast(Any, frame_count_raw))
        if frame_count <= 0:
            return []

        indices = [int(round(i * (frame_count - 1) / max(count, 1))) for i in range(count)]
        results: list[bytes] = []
        for frame_index in indices:
            frame = reader.get_data(frame_index)
            frame_img = Image.fromarray(frame).convert("RGB")
            buf = io.BytesIO()
            frame_img.save(buf, format="JPEG", quality=92)
            # Normalize each view back onto white background for product display consistency.
            results.append(remove_background(buf.getvalue()))
        return results
    finally:
        reader.close()


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL – shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resize_if_needed(image_bytes: bytes) -> bytes:
    """Resize so the longest side ≤ _MAX_DIM; return original if already small enough."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if max(w, h) <= _MAX_DIM:
            return image_bytes
        ratio = _MAX_DIM / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        fmt = "JPEG" if (img.format or "JPEG") in ("JPEG", "WEBP") else (img.format or "JPEG")
        img.save(buf, format=fmt, quality=92)
        return buf.getvalue()
    except Exception:
        return image_bytes


def _composite_white(png_bytes: bytes) -> bytes:
    """Composite a (possibly transparent) PNG onto white and return JPEG bytes."""
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    out = io.BytesIO()
    bg.convert("RGB").save(out, format="JPEG", quality=95)
    return out.getvalue()


def _split_grid(grid_bytes: bytes, count: int = 4) -> list[bytes]:
    """
    Split a zero123-plus output grid into individual angle images.

    zero123-plus outputs a 2-col × 3-row grid (6 views).
    Landscape grids (w > h) are treated as 3-col × 2-row.
    """
    img = Image.open(io.BytesIO(grid_bytes))
    w, h = img.size
    cols, rows = (3, 2) if w > h else (2, 3)
    cell_w, cell_h = w // cols, h // rows

    results: list[bytes] = []
    for r in range(rows):
        for c in range(cols):
            if len(results) >= count:
                break
            cell = img.crop((c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)).convert("RGB")
            buf = io.BytesIO()
            cell.save(buf, format="JPEG", quality=92)
            results.append(buf.getvalue())
    return results


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL – Zero123Plus multi-view via HF Gradio Space
# ─────────────────────────────────────────────────────────────────────────────

def _generate_angles_via_zero123plus(image_bytes: bytes) -> list[bytes]:
    """Try the sudo-ai/zero123plus Gradio Space to generate 6 novel-angle views."""
    from gradio_client import Client, handle_file  # type: ignore

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        input_path = tmp.name

    try:
        client = Client(ZERO123_MODEL, hf_token=HF_API_TOKEN or None, verbose=False)
        result = client.predict(
            image=handle_file(input_path),
            scale=4,
            api_name="/predict",
        )
        # result[0] is the output grid image path
        grid_path = result[0] if isinstance(result, (list, tuple)) and result else result
        if not grid_path or not os.path.exists(str(grid_path)):
            return []
        with open(str(grid_path), "rb") as f:
            grid_bytes = f.read()
        return _split_grid(grid_bytes, count=4)
    finally:
        try:
            os.unlink(input_path)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL – PIL geometric angle simulation (always-available fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_pil_angle_views(image_bytes: bytes) -> list[bytes]:
    """
    Generate 4 product angle simulation views using PIL transforms.
    Works entirely offline — no external dependencies.

    Views produced:
      1. Front (original cleaned image)
      2. Right side (horizontal flip)
      3. Three-quarter angle (slight shear / perspective)
      4. Detail zoom (10% crop, resampled to full size)
    """
    from PIL import Image, ImageOps, ImageFilter  # type: ignore

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        # Composite onto white
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        white.paste(img, mask=img.split()[3])
        base = white.convert("RGB")
        w, h = base.size

        views: list[bytes] = []

        # View 1 — Front (as-is)
        buf = io.BytesIO()
        base.save(buf, format="JPEG", quality=90)
        views.append(buf.getvalue())

        # View 2 — Right side (horizontal flip)
        flipped = ImageOps.mirror(base)
        buf = io.BytesIO()
        flipped.save(buf, format="JPEG", quality=90)
        views.append(buf.getvalue())

        # View 3 — Three-quarter angle (affine shear transform)
        shear_factor = 0.08
        shear_x = int(w * shear_factor)
        coeffs = (1, shear_factor, -shear_x, 0, 1, 0)
        sheared = base.transform(
            (w, h), Image.Transform.AFFINE, coeffs, resample=Image.Resampling.BILINEAR,
            fillcolor=(255, 255, 255)
        )
        buf = io.BytesIO()
        sheared.save(buf, format="JPEG", quality=90)
        views.append(buf.getvalue())

        # View 4 — Detail crop (centre 80%, enlarged back)
        margin_x, margin_y = int(w * 0.10), int(h * 0.10)
        cropped = base.crop((margin_x, margin_y, w - margin_x, h - margin_y))
        cropped = cropped.resize((w, h), Image.Resampling.LANCZOS)
        # Subtle sharpening for detail view
        cropped = cropped.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        buf = io.BytesIO()
        cropped.save(buf, format="JPEG", quality=90)
        views.append(buf.getvalue())

        return views

    except Exception as exc:
        logger.warning("PIL angle simulation failed: %s", exc)
        return []

