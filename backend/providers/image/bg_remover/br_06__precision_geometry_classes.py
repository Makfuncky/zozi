from typing import Any
# ========================== br_06: PRECISION GEOMETRY CLASSES ==========================
from PIL import Image

import numpy as np


from typing import Optional, Dict


class SceneAnalyzer:
    """Analyze image scene to determine optimal processing strategy (br_06)."""

    @staticmethod
    def analyze(image_bytes: bytes) -> Dict[str, Any]:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        h, w = img_array.shape[:2]

        has_human = False
        has_product = False
        has_text = False
        complexity = "simple"

        if h > 500 and w > 500:
            complexity = "medium"
        if h > 1500 or w > 1500:
            complexity = "high"

        gray = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY) if _HAS_CV2 else None
        if gray is not None:
            edge_density = float(np.mean(cv2.Canny(gray, 50, 150)))
            if edge_density > 50:
                complexity = "complex"

        return {
            "width": w,
            "height": h,
            "complexity": complexity,
            "has_human": has_human,
            "has_product": has_product,
            "has_text": has_text,
            "recommended_strategy": ProcessingStrategy.CLEAN_COMMERCIAL.value,
        }

    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        """If there is foreground in the top 25% of the image, it's a human (head)."""
        if not _HAS_CV2:
            return False
        h, w = alpha.shape
        top_region = alpha[: int(h * 0.25), :]
        foreground_ratio = float(np.sum(top_region > 0.5)) / top_region.size
        return foreground_ratio > 0.01


class HandRemover:
    """Remove hand artifacts from background removal results (br_06)."""

    @staticmethod
    def remove(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        """Removes hands by shape. If no head, secondary blobs attached to main product are hands."""
        if not _HAS_CV2:
            return alpha_mask
        contours, _ = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours or len(contours) <= 1:
            return alpha_mask

        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        main_product = contours[0]
        main_area = cv2.contourArea(main_product)
        main_mask = np.zeros_like(alpha_mask)
        cv2.drawContours(main_mask, [main_product], -1, 255, -1)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
        danger_zone = cv2.dilate(main_mask, kernel, iterations=1)

        removed = False
        for i in range(1, len(contours)):
            cnt = contours[i]
            area = cv2.contourArea(cnt)
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                overlap = int(np.sum((cnt_mask > 0) & (danger_zone > 0)))
                if overlap > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True

        if removed:
            logger.info("    Removed isolated hand (geometric)")
        return alpha_mask


class HoleFiller:
    """Fill holes inside the foreground object after background removal (br_05/br_06)."""

    @staticmethod
    def fill(image_rgba: np.ndarray) -> np.ndarray:
        """Fill holes in an RGBA image (returns same shape as input).

        Used by production_birefnet strategy.
        """
        alpha = image_rgba[:, :, 3] if image_rgba.ndim > 2 else image_rgba
        binary_mask = (alpha > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1 : h + 1, 1 : w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1 : h + 1, 1 : w + 1] == 0
        filled_count = int(np.sum(internal_holes))
        if filled_count > 50:
            binary_mask[internal_holes] = 255
            logger.debug("Filled internal holes (%dpx)", filled_count)
        return np.dstack([image_rgba[:, :, :3], binary_mask]) if image_rgba.ndim > 2 else binary_mask

    @staticmethod
    def fill_mask(alpha_mask: np.ndarray, min_hole_area: int = 50) -> np.ndarray:
        """Fill holes in an alpha mask (uint8, shape HxW).

        Used by precision_geometry strategy.
        """
        if not _HAS_CV2:
            return alpha_mask
        binary_mask = (alpha_mask > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1 : h + 1, 1 : w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1 : h + 1, 1 : w + 1] == 0
        filled_count = int(np.sum(internal_holes))
        if filled_count > min_hole_area:
            binary_mask[internal_holes] = 255
            logger.debug("Filled internal holes (%dpx)", filled_count)
        return binary_mask


class ThinPartHandler:
    """Reconnect thin parts (e.g., watchbands) that may have been disconnected (br_06)."""

    @staticmethod
    def handle(image_bytes: bytes) -> bytes:
        img = _bytes_to_image(image_bytes)
        img_array = np.array(img)
        alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255

        if _HAS_CV2:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            alpha = cv2.dilate(alpha, kernel, iterations=1)
            alpha = cv2.erode(alpha, kernel, iterations=1)

        result = np.zeros_like(img_array)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = alpha
        return _image_to_bytes(Image.fromarray(result, "RGBA"))

    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        """Reconnects broken thin parts (watchbands) using directional brushes."""
        if not _HAS_CV2:
            return alpha_mask
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        safe_reconnect = original_alpha_f > 0.05
        final = np.where(safe_reconnect & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask)
        reconnected = int(np.sum((final > 0) & (alpha_mask == 0)))
        if reconnected > 20:
            logger.info("    Reconnected thin parts (%dpx)", reconnected)
        return final


class HumanPreserver:
    """Preserve human subjects during background removal (br_06)."""

    @staticmethod
    def preserve(image_bytes: bytes) -> bytes:
        return remove_background(image_bytes, model="birefnet-portrait")

    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        """Fixes human issues (hollow eyes) WITHOUT destroying hair/edges."""
        if not _HAS_CV2:
            return alpha_f
        solid_mask = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        hollows = (alpha_f < 0.1) & (dilated > 0)
        if int(np.sum(hollows)) > 10:
            alpha_f[hollows] = 0.85
            logger.info("    Soft-filled human hollows (eyes/face)")
        return alpha_f


class EdgeRefiner:
    """Micro-smooth staircase jitters, then snap perfectly to RGB edges (br_06)."""

    @staticmethod
    def refine(image_np: np.ndarray, alpha_f: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha_f

        if alpha_f.dtype != np.float32:
            alpha_f = alpha_f.astype(np.float32) / 255.0

        binary_fg = (alpha_f > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha_f > 0.3) & (alpha_f < 0.95) & (safe_zone > 0)
            alpha_f[semi_inside] = 1.0

        alpha_blurred = cv2.GaussianBlur(alpha_f, (3, 3), 0.8)
        try:
            guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
            refined = cv2.ximgproc.guidedFilter(guide, alpha_blurred, radius=6, eps=0.0001)
            alpha_f = np.clip(refined, 0, 1)
        except Exception:
            alpha_f = alpha_blurred

        binary_final = (alpha_f > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        near_edge = cv2.dilate(binary_final, kernel, iterations=1)
        ghost_mask = (near_edge == 0) & (alpha_f < 0.1)
        alpha_f[ghost_mask] = 0.0

        return alpha_f

