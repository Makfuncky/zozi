from typing import Tuple
# ========================== br_08 / br_11 / br_12 / br_13: EXPORTERS ==========================
from .configuration import ProcessingConfig

from PIL import Image

import numpy as np


from typing import Optional, Dict, Any


class Exporter:
    """Export processed images with alpha composition (br_08, br_11, br_12, br_13)."""

    @staticmethod
    def create_canvas(final_img: Image.Image, background: str, config: ProcessingConfig) -> Image.Image:
        bg_colors = {
            "transparent": (0, 0, 0, 0),
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
        }
        bg = bg_colors.get(background.lower(), (0, 0, 0, 0))
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_size, target_size), bg)
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        return canvas

    @staticmethod
    def encode(canvas: Image.Image, output_format: str, config: ProcessingConfig) -> Tuple[bytes, str]:
        if output_format.upper() in ("JPEG", "JPG"):
            canvas = canvas.convert("RGB")
            output_format = "JPEG"
            save_kwargs = {"quality": config.jpeg_quality, "optimize": True}
        else:
            output_format = "PNG"
            save_kwargs = {"optimize": True, "compress_level": config.png_compression}

        buf = io.BytesIO()
        canvas.save(buf, format=output_format, **save_kwargs)
        return buf.getvalue(), output_format

    @staticmethod
    def process_and_save(input_bytes: bytes, output_path: str, config: ProcessingConfig = None):
        """Export pipeline: AI segmentation + post-process + save (br_11/br_12/br_13 style)."""
        config = config or ProcessingConfig()
        img = Image.open(io.BytesIO(input_bytes)).convert("RGB")
        orig_size = img.size
        input_np = np.array(img)

        alpha_map = AISegmenter.generate_alpha(input_bytes, orig_size, config)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)

        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = alpha_uint8

        trans_mask = final_rgba[:, :, 3] == 0
        final_rgba[trans_mask, :3] = 0

        final_img = Image.fromarray(final_rgba, mode="RGBA")
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        canvas.save(output_path, format="PNG", optimize=True)
