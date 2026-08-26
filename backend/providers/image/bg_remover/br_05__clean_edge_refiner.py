# ========================== br_05: CLEAN EDGE REFINER ==========================
import numpy as np


from typing import Optional


class CleanEdgeRefiner:
    """Gentle edge refinement for AI-generated alpha masks.

    Br_05 philosophy: AI does 99% of the work. We only do 1% cleanup.
    Three-step process: fringing fix, guided filter smoothing, ghost cleanup.
    """

    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return alpha

        if alpha.dtype != np.float32:
            alpha = alpha.astype(np.float32)

        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0

        try:
            guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
            alpha_f = alpha.astype(np.float32)
            refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
            alpha = np.clip(refined, 0, 1)
        except Exception:
            pass

        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=5)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0

        return alpha

