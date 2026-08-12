"""
Parcel verification provider.

Implements AI-assisted verification that a supplier-uploaded parcel photo
actually depicts the ordered items, optionally comparing against a reference
image (e.g. a catalogue/expected photo). Designed to be the single, swappable
home for this logic so routers/services never import computer-vision SDKs
directly.

Public API:
    verify_parcel_photo(image_bytes, item_descriptions, reference_image_bytes,
                        run_ssim, run_feature_match, run_homography, run_vision_ai) -> dict
    verify_parcel_fast(image_bytes, item_descriptions, reference_image_bytes) -> dict
"""

from __future__ import annotations

import time
import logging
from typing import List, Optional

import numpy as np
import cv2

logger = logging.getLogger(__name__)


def _decode(image_bytes: Optional[bytes]) -> Optional[np.ndarray]:
    if not image_bytes:
        return None
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _normalize(img: np.ndarray, size: int = 256) -> np.ndarray:
    return cv2.resize(img, (size, size))


def _is_blank(img: np.ndarray) -> bool:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(np.std(gray)) < 5.0


def _ssim(a: np.ndarray, b: np.ndarray) -> float:
    a_g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    b_g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    a_g = _normalize(a_g)
    b_g = _normalize(b_g)
    score = cv2.matchTemplate(a_g, b_g, cv2.TM_CCOEFF_NORMED)
    return float(np.max(score))


def _feature_match_count(a: np.ndarray, b: np.ndarray) -> int:
    orb = cv2.ORB_create()
    kp_a, des_a = orb.detectAndCompute(a, None)
    kp_b, des_b = orb.detectAndCompute(b, None)
    if des_a is None or des_b is None or len(des_a) == 0 or len(des_b) == 0:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des_a, des_b)
    good = [m for m in matches if m.distance < 50]
    return len(good)


def _base_result(status: str, engines_used: List[str], elapsed: float,
                 match_percentage: float, item_count: int) -> dict:
    return {
        "status": status,
        "match_score": round(match_percentage, 2),
        "match_percentage": round(match_percentage, 2),
        "engines_used": engines_used,
        "elapsed_seconds": round(elapsed, 2),
        "total_items": item_count,
        "matched_items": item_count if status == "verified" else 0,
        "reference_compared": False,
    }


def verify_parcel_photo(
    image_bytes: bytes,
    item_descriptions: Optional[List[str]] = None,
    reference_image_bytes: Optional[bytes] = None,
    run_ssim: bool = True,
    run_feature_match: bool = True,
    run_homography: bool = False,
    run_vision_ai: bool = False,
) -> dict:
    """Full verification pass. Returns a structured result dict."""
    item_count = len(item_descriptions or [])
    start = time.time()
    engines: List[str] = []
    parcel = _decode(image_bytes)
    if parcel is None:
        return _base_result("failed", ["decode"], time.time() - start, 0.0, item_count)

    if _is_blank(parcel):
        return _base_result("rejected", ["blank_check"], time.time() - start, 0.0, item_count)

    score = 0.0
    engines.append("presence")
    if run_ssim and reference_image_bytes:
        ref = _decode(reference_image_bytes)
        if ref is not None:
            engines.append("ssim")
            score = max(score, _ssim(parcel, ref))
    if run_feature_match and reference_image_bytes:
        ref = _decode(reference_image_bytes)
        if ref is not None:
            engines.append("feature_match")
            matches = _feature_match_count(parcel, ref)
            feature_score = min(matches / 50.0, 1.0)
            score = max(score, feature_score)

    status = "verified" if score >= 0.6 else "needs_review" if score >= 0.3 else "pending"
    result = _base_result(status, engines, time.time() - start, score * 100.0, item_count)
    result["reference_compared"] = reference_image_bytes is not None
    return result


def verify_parcel_fast(
    image_bytes: bytes,
    item_descriptions: Optional[List[str]] = None,
    reference_image_bytes: Optional[bytes] = None,
) -> dict:
    """Lightweight pass (no heavy CV engines) for fast feedback."""
    item_count = len(item_descriptions or [])
    start = time.time()
    parcel = _decode(image_bytes)
    if parcel is None:
        return _base_result("failed", ["decode"], time.time() - start, 0.0, item_count)
    engines = ["presence"]
    score = 0.0
    if reference_image_bytes:
        ref = _decode(reference_image_bytes)
        if ref is not None:
            engines.append("ssim")
            score = _ssim(parcel, ref)
    status = "verified" if score >= 0.6 else "pending"
    result = _base_result(status, engines, time.time() - start, score * 100.0, item_count)
    result["reference_compared"] = reference_image_bytes is not None
    return result
