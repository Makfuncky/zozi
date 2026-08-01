"""
Free / open-source image processing tools for supplier product uploads.

All tools use MIT / BSD licensed libraries:
  - Pillow       — rotation, crop, enhance, resize (LANCZOS)
  - rembg        — AI background removal / magic eraser
  - OpenCV       — CLAHE contrast, smart cropping, upscaling, guided filter
  - scikit-image — auto-exposure, histogram matching

Usage:
  processed = auto_process_image(raw_bytes, tools=["magic_erase", "smart_crop", "rotate", "auto_light", "upscale"])
"""

from __future__ import annotations

import gc
import io
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# ── Dependency check ─────────────────────────────────────────────

_HAS_CV2 = False
_HAS_GUIDED_FILTER = False
try:
    import cv2
    _HAS_CV2 = True
    logger.info("OpenCV available for image processing")
    try:
        from cv2 import ximgproc
        _HAS_GUIDED_FILTER = True
        logger.info("Guided Filter available for edge refinement")
    except ImportError:
        pass
except ImportError:
    logger.warning("OpenCV not available, some tools will use Pillow fallbacks")

# ── Constants ────────────────────────────────────────────────────

MAX_DIMENSION = 2048
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}


# ═════════════════════════════════════════════════════════════════
# 1. MAGIC ERASE — AI Background Removal with Clean Edge Refinement
# ═════════════════════════════════════════════════════════════════

class CleanEdgeRefiner:
    """
    Gentle edge refinement for AI-generated alpha masks.

    Philosophy: The AI model does 99% of the work. We only do 1% cleanup.
    - No destructive text/ground slicing
    - No aggressive geometric hardening
    - Pure, high-fidelity edge refinement
    - Respects the original model mask
    """

    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        """
        Apply gentle touch-ups to the raw AI mask.

        Args:
            image_np: RGB image array (H, W, 3)
            alpha: Alpha channel (H, W) float32 in [0, 1]

        Returns:
            Refined alpha channel
        """
        if not _HAS_CV2:
            return alpha

        # 1. Fix light product edge fringing (white halo)
        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0

        # 2. Gentle Edge Smoothing via Guided Filter
        if _HAS_GUIDED_FILTER:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                alpha_f = alpha.astype(np.float32)
                refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
                alpha = np.clip(refined, 0, 1)
            except Exception:
                pass

        # 3. Background ghost cleanup
        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=5)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0

        return alpha


def _load_rembg_session():
    """Lazy-load rembg session (cached after first call)."""
    if not hasattr(_load_rembg_session, "_session"):
        try:
            from rembg import new_session
            _load_rembg_session._session = new_session("isnet-general-use")
        except Exception:
            try:
                from rembg import new_session
                _load_rembg_session._session = new_session("u2net")
            except Exception as exc:
                logger.warning("rembg model load failed: %s", exc)
                _load_rembg_session._session = None
    return _load_rembg_session._session


def _remove_background_rembg(raw: bytes) -> Optional[bytes]:
    session = _load_rembg_session()
    if session is None:
        return None
    try:
        from rembg import remove as rembg_remove
        result = rembg_remove(raw, session=session)
        if result and len(result) > 100:
            return result
        return None
    except Exception as exc:
        logger.warning("rembg inference failed: %s", exc)
        return None


def _remove_background_pillow(raw: bytes) -> Optional[bytes]:
    """Fallback: threshold-based removal for white/light backgrounds."""
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        arr = np.array(img)
        if arr.shape[2] < 4:
            return None
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        mask = (r > 240) & (g > 240) & (b > 240) & (a > 200)
        arr[:, :, 3] = np.where(mask, 0, 255)
        out = Image.fromarray(arr, "RGBA")
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        logger.warning("Pillow fallback bg removal failed: %s", exc)
        return None


def magic_erase(data: bytes, max_dim: int = MAX_DIMENSION) -> bytes:
    """
    Remove background using AI (rembg).

    Delegates to the unified, VPS-safe ``bg_removal_service`` so that the
    magic eraser shares the global concurrency semaphore, the LRU rembg
    session cache and the memory monitor with the interactive bg-removal
    endpoint. Falls back to the local rembg path if the service is
    unavailable. Never raises — returns ``data`` unchanged on failure.
    """
    try:
        from services.bg_removal_service import magic_erase as _svc_magic_erase
        return _svc_magic_erase(data)
    except Exception as exc:
        logger.warning("magic_erase: service unavailable (%s), using local path", exc)

    # ── Local fallback (legacy, self-contained) ──
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img_np = np.array(img)
        h, w = img_np.shape[:2]

        ratio = 1.0
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            img_resized = img

        buf = io.BytesIO()
        img_resized.save(buf, format="PNG")
        input_bytes = buf.getvalue()

        output_bytes = _remove_background_rembg(input_bytes)
        if output_bytes is None:
            output_bytes = _remove_background_pillow(input_bytes)
        if output_bytes is None:
            logger.warning("magic_erase: all methods failed, returning original")
            return data

        out_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        if ratio < 1.0:
            out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)

        raw_alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
        final_alpha = CleanEdgeRefiner.refine(img_np, raw_alpha)
        final_alpha[final_alpha < 0.02] = 0.0
        final_alpha[final_alpha > 0.98] = 1.0

        alpha_uint8 = np.clip(final_alpha * 255, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(np.dstack([img_np, alpha_uint8]), mode="RGBA")

        buf = io.BytesIO()
        result_img.save(buf, format="PNG", compress_level=6)
        logger.info("magic_erase: %dx%d -> refined alpha mask", w, h)
        return buf.getvalue()

    except Exception as exc:
        logger.warning("magic_erase failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 2. SMART CROP — Auto-Centering with Content Detection
# ═════════════════════════════════════════════════════════════════

def smart_crop(data: bytes, target_ratio: float = 1.0, padding: float = 0.08) -> bytes:
    """
    Detect content bounding box, auto-center subject, crop to target ratio.

    Uses OpenCV contour detection for precise subject isolation, with
    Pillow getbbox() as fallback.
    """
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        arr = np.array(img)
        has_alpha = arr.shape[2] >= 4
        alpha = arr[:, :, 3] if has_alpha else np.full(arr.shape[:2], 255, dtype=np.uint8)

        # Find content bounds
        x, y, w, h = 0, 0, img.width, img.height
        if _HAS_CV2:
            gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        if (w == img.width and h == img.height) or not _HAS_CV2:
            bbox = img.getbbox()
            if bbox:
                x, y, x2, y2 = bbox
                w, h = x2 - x, y2 - y

        # Add padding
        cx, cy = x + w // 2, y + h // 2
        target_dim = max(w, h) * (1 + padding * 2)
        if padding > 0:
            target_dim = max(target_dim, w * (1 + padding), h * (1 + padding))
        target_dim = max(int(target_dim), 100)

        left = max(0, cx - target_dim // 2)
        top = max(0, cy - target_dim // 2)
        right = min(img.width, left + target_dim)
        bottom = min(img.height, top + target_dim)
        cropped = img.crop((left, top, right, bottom))

        # Pad to target ratio
        if target_ratio != 1.0:
            cw, ch = cropped.size
            target_w = int(max(cw, ch * target_ratio))
            target_h = int(target_w / target_ratio)
            final = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            paste_x = (target_w - cw) // 2
            paste_y = (target_h - ch) // 2
            final.paste(cropped, (paste_x, paste_y), cropped)
            cropped = final

        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        logger.info("smart_crop: %dx%d -> %dx%d", img.width, img.height, cropped.width, cropped.height)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("smart_crop failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 3. AUTO-ROTATE — EXIF Orientation Correction
# ═════════════════════════════════════════════════════════════════

def auto_rotate(data: bytes, angle: float = 0) -> bytes:
    """Auto-rotate to fix orientation (EXIF) or apply a specified angle."""
    try:
        img = Image.open(io.BytesIO(data))

        if angle == 0:
            orient_tag = img.getexif().get(0x0112)
            exif_map = {3: 180, 6: 270, 8: 90}
            angle = float(exif_map.get(orient_tag, 0))

        if angle != 0:
            fill = (255, 255, 255, 0) if img.mode == "RGBA" else (255, 255, 255)
            img = img.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=fill)

        buf = io.BytesIO()
        fmt = "PNG" if img.mode == "RGBA" else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        img.save(buf, format=fmt, **save_kw)
        logger.info("auto_rotate: applied angle=%.0f", angle)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("auto_rotate failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 4. AUTO-LIGHTING — CLAHE + Gamma Correction
# ═════════════════════════════════════════════════════════════════

def auto_lighting(data: bytes, clip_limit: float = 2.0, brightness: float = 1.05, sharpen: bool = True) -> bytes:
    """
    Apply CLAHE adaptive histogram equalization + gamma correction + optional sharpen.

    Preserves alpha channel if present.
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        arr = np.array(img)

        if _HAS_CV2:
            lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            arr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
            arr = np.array(img)

        result = Image.fromarray(arr)

        # Gamma correction
        if brightness != 1.0:
            try:
                from skimage import exposure
                arr = np.array(result)
                arr = exposure.adjust_gamma(arr, gamma=1.0 / brightness)
                result = Image.fromarray(arr)
            except Exception:
                enhancer = ImageEnhance.Brightness(result)
                result = enhancer.enhance(brightness)

        # Subtle sharpen to restore detail after equalization
        if sharpen:
            result = result.filter(ImageFilter.UnsharpMask(radius=1, percent=15, threshold=2))

        if has_alpha:
            result = result.convert("RGBA")
            result.putalpha(alpha_ch)

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        result.save(buf, format=fmt, **save_kw)
        logger.info("auto_lighting: clip_limit=%.1f brightness=%.2f sharpen=%s", clip_limit, brightness, sharpen)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("auto_lighting failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 5. AI IMAGE UPSCALER — High Quality Enlargement
# ═════════════════════════════════════════════════════════════════

def upscale(data: bytes, scale: float = 2.0, method: str = "lanczos") -> bytes:
    """
    Upscale image using high-quality interpolation with post-sharpen.

    Methods:
      - lanczos (default): Pillow LANCZOS
      - cubic: OpenCV INTER_CUBIC
      - edget: OpenCV edgePreservingFilter + resize
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)

        if method == "lanczos" or not _HAS_CV2:
            scaled = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA) if has_alpha else cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            interp = cv2.INTER_CUBIC if method == "cubic" else cv2.INTER_LANCZOS4
            if method == "edget":
                cv_img = cv2.edgePreservingFilter(cv_img, flags=1, sigma_s=60, sigma_r=0.4)
            resized = cv2.resize(cv_img, (new_w, new_h), interpolation=interp)
            scaled = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGRA2RGBA if has_alpha else cv2.COLOR_BGR2RGB))

        # Post-upscale sharpen to recover detail
        scaled = scaled.filter(ImageFilter.UnsharpMask(radius=0.5, percent=20, threshold=1))

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        scaled.save(buf, format=fmt, **save_kw)
        logger.info("upscale: %dx%d -> %dx%d (scale=%.1f, method=%s)", w, h, new_w, new_h, scale, method)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("upscale failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 6. AUTO WHITE BALANCE — Gray World Correction
# ═════════════════════════════════════════════════════════════════

def auto_white_balance(data: bytes, strength: float = 0.5) -> bytes:
    """
    Auto white balance using Gray World assumption.

    strength: 0 (no change) to 1 (full correction). Default 0.5 for subtle fix.
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        arr = np.array(img).astype(np.float32)
        mean_r, mean_g, mean_b = arr[:, :, 0].mean(), arr[:, :, 1].mean(), arr[:, :, 2].mean()
        gray = (mean_r + mean_g + mean_b) / 3.0

        scale_r = 1.0 + (gray / (mean_r + 1e-6) - 1.0) * strength
        scale_g = 1.0 + (gray / (mean_g + 1e-6) - 1.0) * strength
        scale_b = 1.0 + (gray / (mean_b + 1e-6) - 1.0) * strength

        arr[:, :, 0] = np.clip(arr[:, :, 0] * scale_r, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * scale_g, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * scale_b, 0, 255)

        result = Image.fromarray(arr.astype(np.uint8))

        if has_alpha:
            result = result.convert("RGBA")
            result.putalpha(alpha_ch)

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        result.save(buf, format=fmt, **save_kw)
        logger.info("auto_white_balance: strength=%.1f (r=%.3f g=%.3f b=%.3f)", strength, scale_r, scale_g, scale_b)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("auto_white_balance failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 7. DENOISE — Light Noise Reduction
# ═════════════════════════════════════════════════════════════════

def denoise(data: bytes, strength: int = 5) -> bytes:
    """
    Light non-local means denoising for product photos.

    Useful for low-light images or high-ISO phone photos.
    strength: 1 (mild) to 10 (aggressive).
    """
    try:
        if not _HAS_CV2:
            return data

        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        h_param = max(1, strength)
        denoised = cv2.fastNlMeansDenoisingColored(cv_img, None, h_param, h_param, 7, 21)
        result = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))

        if has_alpha:
            result = result.convert("RGBA")
            result.putalpha(alpha_ch)

        buf = io.BytesIO()
        result.save(buf, format="PNG" if has_alpha else "JPEG", quality=92)
        logger.info("denoise: strength=%d", strength)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("denoise failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 8. SHARPEN — Dedicated Image Sharpening
# ═════════════════════════════════════════════════════════════════

def sharpen(data: bytes, strength: float = 1.0) -> bytes:
    """
    Sharpen image using Unsharp Mask with configurable strength.

    A dedicated sharpening tool separate from the subtle sharpen
    built into auto_lighting and upscale. Useful for photos that
    appear slightly soft or out-of-focus.

    strength: 0.0 (none) to 3.0 (very sharp). Default 1.0.
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        radius = max(0.5, min(strength * 0.8, 3.0))
        percent = int(max(5, min(strength * 30, 100)))
        threshold_val = max(0, int(3 - strength))
        img = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold_val))

        if has_alpha:
            img = img.convert("RGBA")
            img.putalpha(alpha_ch)

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        img.save(buf, format=fmt, **save_kw)
        logger.info("sharpen: radius=%.1f percent=%.0f threshold=%d", radius, percent, threshold_val)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("sharpen failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 9. COMPRESS — File Size Optimization
# ═════════════════════════════════════════════════════════════════

def compress(data: bytes, quality: int = 80, optimize: bool = True) -> bytes:
    """
    Reduce image file size via lossy/lossless compression.

    For JPEG: reduces quality level.
    For PNG: applies optimize=True + optional posterization.
    For WebP: reduces quality level.
    Preserves alpha channel.

    quality: 1 (smallest, worst) to 100 (best, largest). Default 80.
    """
    try:
        img = Image.open(io.BytesIO(data))
        src_fmt = img.format or "JPEG"
        has_alpha = img.mode == "RGBA"

        buf = io.BytesIO()
        if src_fmt == "PNG" or has_alpha:
            img.save(buf, format="PNG", optimize=optimize, compress_level=max(1, 9 - quality // 12))
        elif src_fmt in ("WEBP",):
            img.save(buf, format="WEBP", quality=quality)
        else:
            img.save(buf, format="JPEG", quality=quality, optimize=optimize, progressive=True)

        elapsed = len(data) - len(buf.getvalue())
        logger.info("compress: %s quality=%d saved=%d bytes", src_fmt, quality, max(0, elapsed))
        return buf.getvalue()
    except Exception as exc:
        logger.warning("compress failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 10. WEBP CONVERT — Modern Format Conversion
# ═════════════════════════════════════════════════════════════════

def webp_convert(data: bytes, quality: int = 85, lossless: bool = False) -> bytes:
    """
    Convert image to WebP format for smaller file sizes.

    WebP offers 25-35% smaller files than JPEG at equivalent quality.
    Perfect for web-optimized product images.

    quality: 0 (worst) to 100 (best). Default 85.
    lossless: use lossless compression (larger but perfect quality).
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"

        buf = io.BytesIO()
        if lossless:
            img.save(buf, format="WEBP", lossless=True, quality=quality, method=6)
        else:
            img.save(buf, format="WEBP", quality=quality, method=6)

        logger.info("webp_convert: %dx%d quality=%d lossless=%s size=%d bytes",
                     img.width, img.height, quality, lossless, len(buf.getvalue()))
        return buf.getvalue()
    except Exception as exc:
        logger.warning("webp_convert failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 11. COLOR ENHANCE — Saturation & Vibrance Boost
# ═════════════════════════════════════════════════════════════════

def color_enhance(data: bytes, saturation: float = 1.15, vibrance: bool = True) -> bytes:
    """
    Subtle color enhancement — saturation boost with smart vibrance.

    saturation: 1.0 (no change) to 2.0 (very vivid). Default 1.15.
    vibrance: if True, protects skin tones from oversaturation.
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        if vibrance and _HAS_CV2:
            arr = np.array(img).astype(np.float32)
            lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
            l, a_ch, b_ch = cv2.split(lab)
            a_mean = np.mean(np.abs(a_ch - 128))
            b_mean = np.mean(np.abs(b_ch - 128))
            vibrance_factor = 1.0 - min((a_mean + b_mean) / 256.0, 0.6)
            effective_sat = 1.0 + (saturation - 1.0) * (0.4 + vibrance_factor * 0.6)
            a_ch = (a_ch - 128) * effective_sat + 128
            b_ch = (b_ch - 128) * effective_sat + 128
            a_ch = np.clip(a_ch, 0, 255).astype(np.uint8)
            b_ch = np.clip(b_ch, 0, 255).astype(np.uint8)
            l_uint8 = np.clip(l, 0, 255).astype(np.uint8)
            lab = cv2.merge([l_uint8, a_ch, b_ch])
            arr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            img = Image.fromarray(arr)
        else:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)

        if has_alpha:
            img = img.convert("RGBA")
            img.putalpha(alpha_ch)

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        img.save(buf, format=fmt, **save_kw)
        logger.info("color_enhance: saturation=%.2f vibrance=%s", saturation, vibrance)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("color_enhance failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# 12. AUTO LEVELS — Histogram Stretch / Auto Tone
# ═════════════════════════════════════════════════════════════════

def auto_levels(data: bytes, clip_hist: float = 0.5) -> bytes:
    """
    Auto tone — stretch histogram to improve contrast and dynamic range.

    Uses percentile-based clipping to avoid extreme outliers.
    Similar to 'Auto Tone' in photo editors.

    clip_hist: percent of extreme pixels to clip (0-5). Default 0.5.
    """
    try:
        img = Image.open(io.BytesIO(data))
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha_ch = img.split()[-1]
            img = img.convert("RGB")

        arr = np.array(img)
        channels = [arr[:, :, i] for i in range(3)]
        stretched = []

        for ch in channels:
            low = np.percentile(ch, clip_hist)
            high = np.percentile(ch, 100 - clip_hist)
            if high - low < 1:
                stretched.append(ch)
                continue
            stretched.append(np.clip((ch.astype(np.float32) - low) * 255.0 / (high - low), 0, 255).astype(np.uint8))

        arr = np.dstack(stretched)
        if has_alpha:
            result = Image.fromarray(arr).convert("RGBA")
            result.putalpha(alpha_ch)
        else:
            result = Image.fromarray(arr)

        buf = io.BytesIO()
        fmt = "PNG" if has_alpha else "JPEG"
        save_kw = {} if fmt == "PNG" else {"quality": 92}
        result.save(buf, format=fmt, **save_kw)
        logger.info("auto_levels: clip=%.1f%%", clip_hist)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("auto_levels failed: %s", exc)
        return data


# ═════════════════════════════════════════════════════════════════
# BATCH PROCESSING — Efficient Bulk Image Processing
# ═════════════════════════════════════════════════════════════════

@dataclass
class BatchResult:
    filename: str
    success: bool
    input_size: int
    output_size: int
    processing_time: float
    tools_applied: list[str]
    error: Optional[str] = None


def batch_process_folder(
    input_dir: str,
    output_dir: str,
    tools: Optional[list[str]] = None,
    max_workers: int = 4,
    **kwargs,
) -> list[BatchResult]:
    """
    Process all images in a folder through the pipeline in parallel.

    Args:
        input_dir: Source folder path
        output_dir: Output folder path
        tools: List of tools to apply (default: all)
        max_workers: Parallel workers (default: 4)

    Returns:
        List of BatchResult for each processed image
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    files = [f for f in input_path.iterdir() if f.suffix.lower() in extensions]

    if not files:
        logger.warning("No images found in %s", input_dir)
        return []

    logger.info("Batch processing %d images with %d workers", len(files), max_workers)

    results: list[BatchResult] = []
    start = time.time()

    def _process_one(filepath: Path) -> BatchResult:
        t0 = time.time()
        try:
            data = filepath.read_bytes()
            processed = auto_process_image(data, tools=tools, **kwargs)
            out_path = output_path / f"{filepath.stem}_processed.png"
            out_path.write_bytes(processed)
            elapsed = time.time() - t0
            return BatchResult(
                filename=filepath.name,
                success=True,
                input_size=len(data),
                output_size=len(processed),
                processing_time=round(elapsed, 2),
                tools_applied=tools or list(TOOL_REGISTRY.keys()),
            )
        except Exception as exc:
            elapsed = time.time() - t0
            return BatchResult(
                filename=filepath.name,
                success=False,
                input_size=0,
                output_size=0,
                processing_time=round(elapsed, 2),
                tools_applied=tools or [],
                error=str(exc),
            )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_process_one, f): f for f in files}
        for future in as_completed(futures):
            results.append(future.result())

    total_time = time.time() - start
    successes = sum(1 for r in results if r.success)
    logger.info(
        "Batch complete: %d/%d succeeded in %.1fs (avg %.2fs/image)",
        successes, len(results), total_time,
        total_time / len(results) if results else 0,
    )

    return results


def batch_process_bytes(
    items: list[tuple[str, bytes]],
    tools: Optional[list[str]] = None,
    max_workers: int = 4,
    **kwargs,
) -> list[tuple[str, bytes, BatchResult]]:
    """
    Process multiple image byte arrays in parallel.

    Args:
        items: List of (filename, bytes) tuples
        tools: List of tools to apply
        max_workers: Parallel workers

    Returns:
        List of (filename, processed_bytes, result) tuples
    """
    results: list[tuple[str, bytes, BatchResult]] = []

    def _process_one(name: str, data: bytes) -> tuple[str, bytes, BatchResult]:
        t0 = time.time()
        try:
            processed = auto_process_image(data, tools=tools, **kwargs)
            elapsed = time.time() - t0
            return (name, processed, BatchResult(
                filename=name, success=True,
                input_size=len(data), output_size=len(processed),
                processing_time=round(elapsed, 2),
                tools_applied=tools or list(TOOL_REGISTRY.keys()),
            ))
        except Exception as exc:
            elapsed = time.time() - t0
            return (name, data, BatchResult(
                filename=name, success=False,
                input_size=len(data), output_size=len(data),
                processing_time=round(elapsed, 2),
                tools_applied=tools or [],
                error=str(exc),
            ))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_process_one, name, data) for name, data in items]
        for future in as_completed(futures):
            results.append(future.result())

    return results


# ═════════════════════════════════════════════════════════════════
# PIPELINE RUNNER
# ═════════════════════════════════════════════════════════════════

TOOL_REGISTRY: dict[str, Callable] = {
    "magic_erase": magic_erase,
    "smart_crop": smart_crop,
    "rotate": auto_rotate,
    "auto_light": auto_lighting,
    "upscale": upscale,
    "white_balance": auto_white_balance,
    "denoise": denoise,
    "sharpen": sharpen,
    "compress": compress,
    "webp_convert": webp_convert,
    "color_enhance": color_enhance,
    "auto_levels": auto_levels,
}


def auto_process_image(
    data: bytes,
    tools: Optional[list[str]] = None,
    rotate_angle: float = 0,
    crop_ratio: float = 1.0,
    crop_padding: float = 0.08,
    light_clip: float = 2.0,
    light_brightness: float = 1.05,
    light_sharpen: bool = True,
    upscale_scale: float = 2.0,
    upscale_method: str = "lanczos",
    white_balance_strength: float = 0.5,
    denoise_strength: int = 5,
    sharpen_strength: float = 1.0,
    compress_quality: int = 80,
    webp_quality: int = 85,
    webp_lossless: bool = False,
    color_saturation: float = 1.15,
    color_vibrance: bool = True,
    levels_clip: float = 0.5,
) -> bytes:
    """
    Run the image processing pipeline.

    Pipeline order is optimized:
    denoise → white_balance → color_enhance → auto_levels → magic_erase →
    smart_crop → rotate → auto_light → sharpen → upscale → compress → webp_convert
    """
    if tools is None:
        tools = ["magic_erase", "smart_crop", "rotate", "auto_light", "upscale"]

    pipeline_order = [
        "denoise",
        "white_balance",
        "color_enhance",
        "auto_levels",
        "magic_erase",
        "smart_crop",
        "rotate",
        "auto_light",
        "sharpen",
        "upscale",
        "compress",
        "webp_convert",
    ]

    processed = data
    for tool_name in pipeline_order:
        if tool_name not in tools:
            continue
        fn = TOOL_REGISTRY.get(tool_name)
        if fn is None:
            continue

        if tool_name == "rotate":
            processed = fn(processed, angle=rotate_angle)
        elif tool_name == "smart_crop":
            processed = fn(processed, target_ratio=crop_ratio, padding=crop_padding)
        elif tool_name == "auto_light":
            processed = fn(processed, clip_limit=light_clip, brightness=light_brightness, sharpen=light_sharpen)
        elif tool_name == "upscale":
            processed = fn(processed, scale=upscale_scale, method=upscale_method)
        elif tool_name == "white_balance":
            processed = fn(processed, strength=white_balance_strength)
        elif tool_name == "denoise":
            processed = fn(processed, strength=denoise_strength)
        elif tool_name == "sharpen":
            processed = fn(processed, strength=sharpen_strength)
        elif tool_name == "compress":
            processed = fn(processed, quality=compress_quality)
        elif tool_name == "webp_convert":
            processed = fn(processed, quality=webp_quality, lossless=webp_lossless)
        elif tool_name == "color_enhance":
            processed = fn(processed, saturation=color_saturation, vibrance=color_vibrance)
        elif tool_name == "auto_levels":
            processed = fn(processed, clip_hist=levels_clip)
        else:
            processed = fn(processed)

        gc.collect()

    return processed

