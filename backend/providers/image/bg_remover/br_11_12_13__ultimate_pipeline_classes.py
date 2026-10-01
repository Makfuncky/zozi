from typing import List, Tuple, Optional, Dict, Any
import threading
# ========================== br_11/12/13: ULTIMATE PIPELINE CLASSES ==========================
from .configuration import ProcessingConfig

from PIL import Image

import numpy as np


class AISegmenter:
    """AI Segmenter with configurable model fallback chain (br_11/br_12/br_13).

    Supports multiple model variants:
    - birefnet-general / isnet-general-use / u2net (general fallback)
    - birefnet-massive / birefnet-hrsod / u2net_cloth_seg (v12 specialized)
    - birefnet-general-lite / briaai-rmbg-1.4 (v13 lite variants)
    """

    _disabled_models = set()
    _sessions: Dict[str, Any] = {}
    _lock = threading.Lock()
    _birefnet_disabled = False

    @classmethod
    def _get_session(cls, model_name: str):
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            if model_name not in cls._sessions:
                try:
                    from rembg import new_session
                    logger.info("  Loading model: %s...", model_name)
                    cls._sessions[model_name] = new_session(model_name)
                except Exception as exc:
                    logger.warning("Failed to load %s: %s", model_name, exc)
                    cls._disabled_models.add(model_name)
                    return None
            return cls._sessions[model_name]

    @classmethod
    def generate_alpha(
        cls,
        image_bytes: bytes,
        orig_size: Tuple[int, int],
        config: ProcessingConfig = None,
        models_to_try: Optional[List[str]] = None,
    ) -> np.ndarray:
        """Run AI segmentation and return float alpha map (0-1 range).

        Args:
            image_bytes: Raw PNG/JPEG bytes.
            orig_size: (width, height) to restore output to.
            config: Optional ProcessingConfig for dimension hints.
            models_to_try: Optional override model list. Falls back to combined list.

        Returns:
            Float32 numpy array (H, W) in range [0, 1].
        """
        _ensure_rembg()
        if remove is None:
            raise RuntimeError("rembg is not available")

        config = config or ProcessingConfig()

        if models_to_try is None:
            models_to_try = [
                "birefnet-general",
                "birefnet-general-lite",
                "isnet-general-use",
                "u2net",
                "u2netp",
                "u2net_cloth_seg",
                "birefnet-massive",
                "birefnet-hrsod",
                "briaai-rmbg-1.4",
            ]

        for model_name in models_to_try:
            session = cls._get_session(model_name)
            if session is None:
                continue

            try:
                logger.info("  Running AI Model: %s...", model_name)
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size

                max_dim = config.max_rembg_dimension
                if "massive" in model_name or "hrsod" in model_name:
                    max_dim = min(max_dim, 768)
                elif "birefnet" in model_name and "lite" not in model_name:
                    max_dim = min(max_dim, 1024)
                if "lite" in model_name:
                    max_dim = min(max_dim, 1280)

                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img_resized = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img_resized.save(buf, format="JPEG", quality=92)
                    input_bytes = buf.getvalue()
                else:
                    input_bytes = image_bytes

                output_bytes = remove(input_bytes, session=session, alpha_matting=False)
                output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

                if max(w, h) > max_dim:
                    output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)

                alpha = np.array(output_img.split()[-1])
                logger.info("  %s succeeded", model_name)
                return alpha.astype(np.float32) / 255.0

            except MemoryError as exc:
                logger.error("  %s OOM: %s", model_name, exc)
                cls._disabled_models.add(model_name)
            except Exception as exc:
                if "bad allocation" in str(exc).lower() or "memory" in str(exc).lower():
                    cls._disabled_models.add(model_name)
                logger.warning("  %s failed: %s", model_name, exc)

        raise Exception("All AI models failed.")


class EdgeShaver:
    """Shave trailing edges to fix jagged fuzzy edges (br_11/br_12/br_13)."""

    @staticmethod
    def shave(image_bytes: bytes, erosion_amount: int = 2) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erosion_amount, erosion_amount))
            alpha = cv2.erode(alpha, kernel, iterations=1)
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        """Shave trailing edges to fix jagged fuzzy edges."""
        if not _HAS_CV2:
            return alpha_map
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 1.0)
        return alpha_smooth.astype(np.float32) / 255.0


class GlobalBackgroundBleeder:
    """Fix color bleeding (e.g., wood inside product gaps) using K-Means border sampling (br_11/br_12/br_13)."""

    @staticmethod
    def fix(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2 and alpha.shape[0] > 0 and alpha.shape[1] > 0:
            border_mask = np.zeros_like(alpha, dtype=np.uint8)
            border_mask[0, :] = 255
            border_mask[-1, :] = 255
            border_mask[:, 0] = 255
            border_mask[:, -1] = 255
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (12, 12))
            border_mask = cv2.dilate(border_mask, kernel, iterations=3)

            rgb = img_array[:, :, :3].astype(np.float32)
            border_pixels = rgb[border_mask > 0]
            if len(border_pixels) > 100:
                mean_border_color = np.mean(border_pixels, axis=0)
                color_dist = np.linalg.norm(rgb - mean_border_color, axis=2)
                alpha_blend_arr = np.clip(1.0 - color_dist / 255.0, 0, 1)
                alpha = np.clip(alpha.astype(np.float32) * (1 - alpha_blend_arr * 0.3), 0, 255).astype(np.uint8)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        """Fix color bleeding using K-Means border sampling."""
        if not _HAS_CV2:
            return alpha_map
        h, w = input_np.shape[:2]
        if h * w > 500000:
            return alpha_map
        border = int(min(h, w) * 0.05)
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 3, 1.0)
        _, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 2, cv2.KMEANS_RANDOM_CENTERS)
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[np.argmax(counts)]
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        color_match = dist < 35.0
        ai_confident = alpha_map > 0.90
        bleed_mask = color_match & (~ai_confident)
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        return alpha_final


class ArtifactIsolator:
    """Isolate and remove floating dust/artifacts from background removal (br_11)."""

    @staticmethod
    def isolate(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(alpha, connectivity=8)
            if num_labels > 1:
                min_area = 50
                for i in range(1, num_labels):
                    area = stats[i, cv2.CC_STAT_AREA]
                    if area < min_area:
                        alpha[labels == i] = 0

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_floating_dust(alpha_map: np.ndarray) -> np.ndarray:
        """Removes small isolated floating artifacts."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        if h * w > 300000:
            return alpha_map
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        min_area = int((h * w) * 0.005)
        alpha_clean = alpha_map.copy()
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                alpha_clean[labels == i] = 0.0
        return alpha_clean


class FloatingArtifactRemover:
    """Remove floating artifacts (e.g., gold piece behind perfume) (br_12/br_13)."""

    @staticmethod
    def remove(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            blurred = cv2.GaussianBlur(alpha, (9, 9), 0)
            diff = cv2.absdiff(alpha, blurred)
            _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            alpha = cv2.bitwise_and(alpha, mask)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        """Remove floating background props using connected component analysis."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        if h * w > 300000:
            return alpha_map
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num_labels <= 1:
            return alpha_map

        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        main_x = stats[largest_label, cv2.CC_STAT_LEFT]
        main_y = stats[largest_label, cv2.CC_STAT_TOP]
        main_w = stats[largest_label, cv2.CC_STAT_WIDTH]
        main_h = stats[largest_label, cv2.CC_STAT_HEIGHT]
        main_cx = main_x + main_w / 2
        main_cy = main_y + main_h / 2

        alpha_clean = alpha_map.copy()
        for i in range(1, num_labels):
            if i == largest_label:
                continue
            area = stats[i, cv2.CC_STAT_AREA]
            if area > (h * w) * 0.02:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                comp_cx = x + comp_w / 2
                comp_cy = y + comp_h / 2
                dist = np.sqrt((comp_cx - main_cx) ** 2 + (comp_cy - main_cy) ** 2)
                if dist > main_w * 1.5:
                    alpha_clean[labels == i] = 0.0
        return alpha_clean


class BottomTextEraser:
    """Remove bottom text/watermark from images (br_12/br_13)."""

    @staticmethod
    def erase(image_bytes: bytes, bottom_ratio: float = 0.15) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        h, w = img_array.shape[:2]

        if _HAS_CV2:
            bottom_start = int(h * (1 - bottom_ratio))
            alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255
            alpha[bottom_start:, :] = 0

            result = np.zeros_like(img_array)
            result[:, :, :3] = img_array[:, :, :3]
            result[:, :, 3] = alpha
            return _image_to_bytes(Image.fromarray(result, "RGBA"))

        return image_bytes

    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray, input_np: np.ndarray) -> np.ndarray:
        """Remove bottom text/watermark from alpha map."""
        if not _HAS_CV2:
            return alpha_map
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        bottom_region = binary[int(h * 0.8) :, :]
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        alpha_clean = alpha_map.copy()
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h * 0.8)
            aspect_ratio = float(cw) / ch if ch > 0 else 0
            if 100 < area < 5000 and aspect_ratio > 2.0:
                if global_y > h * 0.90:
                    alpha_clean[global_y : global_y + ch, x : x + cw] = 0.0
        return alpha_clean

