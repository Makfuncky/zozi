# ========================== IMAGE HELPERS ==========================

import numpy as np
from typing import Any, Optional, Dict, Tuple
from PIL import Image
import io

from .memory_management__br_08_ import MemoryManager



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

