"""
Parcel Verification Provider
=============================
Multi-engine image comparison for parcel-photo vs packing-sheet verification.

Three engines, from fastest/lightest to slowest/richest:

1. **SSIM engine** (``scikit-image``)
   - Computes Structural Similarity Index between the parcel photo and a
     blurred version of itself.
   - Low SSIM = high structural content = packages present.
   - Score: 0-1 structural richness.

2. **Feature-match engine** (``opencv-python`` — ORB)
   - Extracts ORB features from the parcel photo.
   - Counts keypoints, contours, and package-like blobs.
   - More features = more visual content = packed items.
   - Score: 0-1 feature richness relative to expected.

3. **Vision AI engine** (Ollama vision)
   - Sends the parcel photo with a structured comparison prompt.
   - Asks the LLM to: count visible packages, list detected items, verify
     packaging quality, flag anomalies.
   - Parses the JSON response into a structured report.
   - Score: 0-1 AI confidence.

The final **combined score** is a weighted average of all three engines
that were able to run.

Test file: ``backend/tests/_test_provider/test_parcel_verification.py``
"""
from __future__ import annotations
from typing import List, Optional

import io
import logging
import time
from typing import Any

import numpy as np

from .text import _ollama_vision_chat, _extract_json

logger = logging.getLogger(__name__)

# ── Engine weights for the combined score ─────────────────────────────────
WEIGHTS = {
    "ssim": 0.10,
    "feature_match": 0.20,
    "homography": 0.35,
    "vision_ai": 0.35,
}

# ── Thresholds ────────────────────────────────────────────────────────────
PASS_THRESHOLD = 0.60
PARTIAL_THRESHOLD = 0.30


# ═══════════════════════════════════════════════════════════════════════════
# Engine 1: SSIM (Structural Similarity Index)
# ═══════════════════════════════════════════════════════════════════════════

def _engine_ssim(
    image_bytes: bytes,
    max_dim: int = 512,
) -> dict[str, Any]:
    """Compute SSIM-based structural richness of the parcel photo.

    The idea: an empty background has high structural similarity to itself
    after slight perturbation (blur), while a packed parcel has clear edges,
    contours, and texture that change significantly when blurred.

    Returns a dict with ``score`` (0-1), ``has_content``, and raw metrics.
    """
    try:
        from PIL import Image
        from skimage.metrics import structural_similarity as ssim
        from skimage.filters import sobel
        from scipy.ndimage import gaussian_filter

        img = Image.open(io.BytesIO(image_bytes)).convert("L")  # greyscale
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
        arr = np.array(img, dtype=np.uint8)

        h, w = arr.shape
        if h < 16 or w < 16:
            return {"score": 0.0, "has_content": False, "error": "Image too small"}

        # Create three analysis windows to compute average SSIM
        windows = []
        mid_h, mid_w = h // 2, w // 2
        for (y1, y2, x1, x2) in [
            (0, h, 0, w),
            (mid_h - h // 4, mid_h + h // 4, mid_w - w // 4, mid_w + w // 4),
            (0, h // 2, 0, w // 2),
        ]:
            if y2 - y1 < 16 or x2 - x1 < 16:
                continue
            window = arr[y1:y2, x1:x2]
            # SSIM of the window against a blurred version of itself.
            # High SSIM = low structure = probably empty.
            blurred = gaussian_filter(window.astype(np.float32), sigma=3.0)
            score, _ = ssim(window, blurred.astype(np.uint8), data_range=255, full=True)
            windows.append(score)

        if not windows:
            return {"score": 0.0, "has_content": False, "error": "No valid windows"}

        # Invert: high SSIM with blur = low structure = empty.
        # We want LOW SSIM with blur = high structure = has content.
        avg_ssim = sum(windows) / len(windows)
        structure_score = max(0.0, min(1.0, 1.0 - avg_ssim))

        # Edge detection: count strong edges as a secondary signal.
        edges = sobel(arr)
        edge_ratio = float(np.mean(edges > 0.08))

        # Edge ratio > 0.05 usually means there's something in the image.
        has_content = edge_ratio > 0.05 or structure_score > 0.3

        # Blend SSIM inverted score with edge ratio.
        blended = 0.6 * structure_score + 0.4 * min(1.0, edge_ratio * 5.0)

        return {
            "score": round(blended, 4),
            "has_content": has_content,
            "ssim_raw": round(avg_ssim, 4),
            "edge_ratio": round(edge_ratio, 4),
            "structure_score": round(structure_score, 4),
            "dimensions": f"{w}x{h}",
        }
    except ImportError as exc:
        logger.warning("SSIM engine unavailable: %s", exc)
        return {"score": 0.0, "has_content": False, "error": f"ImportError: {exc}"}
    except Exception as exc:
        logger.warning("SSIM engine failed: %s", exc)
        return {"score": 0.0, "has_content": False, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# Engine 2: Feature Matching (OpenCV ORB)
# ═══════════════════════════════════════════════════════════════════════════

def _engine_feature_match(
    image_bytes: bytes,
    expected_item_count: int = 1,
    max_dim: int = 800,
) -> dict[str, Any]:
    """Extract ORB features from the parcel photo to assess packaging richness.

    A packed parcel with multiple items will have many distinct visual
    features, corners, edges, and textures. An empty or near-empty photo
    will have very few ORB keypoints.

    Returns a dict with ``score`` (0-1), ``keypoint_count``, and
    ``estimated_packages``.
    """
    try:
        import cv2

        img_arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"score": 0.0, "error": "Could not decode image"}

        h, w = img.shape
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w = img.shape

        # ── ORB feature detection ────────────────────────────────────────
        orb = cv2.ORB_create(nfeatures=500, scaleFactor=1.2, nlevels=8)
        keypoints, descriptors = orb.detectAndCompute(img, None)

        kp_count = len(keypoints) if keypoints else 0

        # ── Edge / contour analysis ───────────────────────────────────────
        edges = cv2.Canny(img, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_contour_area = (h * w) * 0.005  # 0.5 % of image area
        significant_contours = [
            c for c in contours if cv2.contourArea(c) > min_contour_area
        ]
        object_count = len(significant_contours)

        # ── Blob / package detection via adaptive thresholding ───────────
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 2,
        )
        kernel = np.ones((5, 5), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        blob_contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        package_like_blobs = [
            c for c in blob_contours
            if cv2.contourArea(c) > min_contour_area * 0.5
        ]
        estimated_packages = max(1, len(package_like_blobs))

        # ── Compute feature score ────────────────────────────────────────
        expected_kp = max(30, int(h * w * 0.0003))
        kp_ratio = min(1.0, kp_count / expected_kp)
        obj_ratio = min(1.0, object_count / max(1, expected_item_count * 2))
        feature_score = 0.6 * kp_ratio + 0.4 * obj_ratio

        return {
            "score": round(min(1.0, feature_score), 4),
            "keypoint_count": kp_count,
            "expected_keypoints": expected_kp,
            "keypoint_ratio": round(kp_ratio, 4),
            "contour_count": object_count,
            "estimated_packages": estimated_packages,
            "package_like_blobs": len(package_like_blobs),
            "has_content": kp_count > 15,
        }
    except ImportError as exc:
        logger.warning("Feature-match engine unavailable: %s", exc)
        return {"score": 0.0, "error": f"ImportError: {exc}"}
    except Exception as exc:
        logger.warning("Feature-match engine failed: %s", exc)
        return {"score": 0.0, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# Engine 3: ORB Homography — Feature Matching Against a Reference Photo
# ═══════════════════════════════════════════════════════════════════════════

def _engine_feature_match_homography(
    parcel_bytes: bytes,
    reference_bytes: bytes,
    max_dim: int = 800,
) -> dict[str, Any]:
    """Compute ORB feature matches + homography between the parcel photo and
    a **reference packaging photo** (e.g. a photo of the product before wrapping).

    This answers the question: *"Is the same item/box visible in the parcel
    photo that was provided as the reference?"*

    Algorithm:
    1. Extract ORB features from both images.
    2. Match features with a Brute-Force Hamming matcher.
    3. Apply Lowe's ratio test to filter good matches.
    4. Compute a homography matrix with ``cv2.findHomography`` (RANSAC).
    5. A high inlier count + low reprojection error = same object present.

    Returns a dict with:
    - ``score`` (0-1): confidence that the reference item appears in the parcel
    - ``keypoints_reference`` / ``keypoints_parcel``: feature counts per image
    - ``good_matches``: number of Lowe-filtered matches
    - ``inliers``: number of RANSAC-validated inlier matches
    - ``homography_found``: bool — whether a reasonable homography was computed
    - ``inlier_ratio``: fraction of matches that are inliers (0-1)
    - ``coverage_area_pct``: estimated percentage of the parcel photo covered
      by the warped reference (0-1)
    - ``has_content``: derived boolean
    """
    try:
        import cv2
        import numpy as np

        # ── Decode both images ───────────────────────────────────────────
        parcel_arr = np.frombuffer(parcel_bytes, dtype=np.uint8)
        parcel_img = cv2.imdecode(parcel_arr, cv2.IMREAD_GRAYSCALE)
        if parcel_img is None:
            return {"score": 0.0, "error": "Could not decode parcel image"}

        ref_arr = np.frombuffer(reference_bytes, dtype=np.uint8)
        ref_img = cv2.imdecode(ref_arr, cv2.IMREAD_GRAYSCALE)
        if ref_img is None:
            return {"score": 0.0, "error": "Could not decode reference image"}

        # ── Resize to max_dim ────────────────────────────────────────────
        h, w = parcel_img.shape
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            parcel_img = cv2.resize(
                parcel_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )
        h, w = ref_img.shape
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            ref_img = cv2.resize(
                ref_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )

        # ── ORB feature extraction ───────────────────────────────────────
        nfeatures = max(200, int(max_dim * max_dim * 0.0006))  # scale with image size
        orb = cv2.ORB_create(nfeatures=nfeatures, scaleFactor=1.2, nlevels=8)

        kp_ref, des_ref = orb.detectAndCompute(ref_img, None)
        kp_parcel, des_parcel = orb.detectAndCompute(parcel_img, None)

        if des_ref is None or des_parcel is None or len(des_ref) < 4 or len(des_parcel) < 4:
            return {
                "score": 0.0,
                "keypoints_reference": len(kp_ref) if kp_ref is not None else 0,
                "keypoints_parcel": len(kp_parcel) if kp_parcel is not None else 0,
                "good_matches": 0,
                "inliers": 0,
                "homography_found": False,
                "inlier_ratio": 0.0,
                "has_content": False,
                "error": "Not enough features in one or both images",
            }

        # ── Feature matching ─────────────────────────────────────────────
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        knn_matches = matcher.knnMatch(des_ref, des_parcel, k=2)

        # ── Lowe's ratio test ────────────────────────────────────────────
        good_matches = []
        for m_pair in knn_matches:
            if len(m_pair) >= 2:
                m, n = m_pair[0], m_pair[1]
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        num_good = len(good_matches)

        # ── Need at least 4 points for homography ────────────────────────
        if num_good < 4:
            return {
                "score": 0.0,
                "keypoints_reference": len(des_ref),
                "keypoints_parcel": len(des_parcel),
                "good_matches": num_good,
                "inliers": 0,
                "homography_found": False,
                "inlier_ratio": 0.0,
                "coverage_area_pct": 0.0,
                "has_content": num_good > 1,
                "error": None,
            }

        # ── Compute homography with RANSAC ───────────────────────────────
        src_pts = np.float32([kp_ref[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_parcel[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # RANSAC reprojection threshold: 3.0 pixels (strict)
        homography_matrix, inlier_mask = cv2.findHomography(
            src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=3.0
        )

        if homography_matrix is None or inlier_mask is None:
            return {
                "score": 0.0,
                "keypoints_reference": len(des_ref),
                "keypoints_parcel": len(des_parcel),
                "good_matches": num_good,
                "inliers": 0,
                "homography_found": False,
                "inlier_ratio": 0.0,
                "coverage_area_pct": 0.0,
                "has_content": False,
                "error": "Homography computation failed to converge",
            }

        inlier_count = int(np.sum(inlier_mask))
        inlier_ratio = inlier_count / max(1, num_good)

        # ── Compute coverage area ────────────────────────────────────────
        # Warp the reference image bounding box into the parcel image space
        h_ref, w_ref = ref_img.shape
        h_par, w_par = parcel_img.shape

        ref_corners = np.float32([
            [0, 0],
            [w_ref, 0],
            [w_ref, h_ref],
            [0, h_ref],
        ]).reshape(-1, 1, 2)

        warped_corners = cv2.perspectiveTransform(ref_corners, homography_matrix)

        if warped_corners is not None:
            # Compute the area of the warped quadrilateral
            warped_pts = warped_corners.reshape(-1, 2)
            warped_area = cv2.contourArea(warped_pts.astype(np.float32))
            parcel_area = h_par * w_par
            coverage_area_pct = min(1.0, warped_area / max(1.0, parcel_area))
        else:
            coverage_area_pct = 0.0

        # ── Compute score ────────────────────────────────────────────────
        # High score requires:
        # - Many inlier matches (absolute count)           weight: 0.30
        # - High inlier ratio (precision)                  weight: 0.35
        # - Good coverage of parcel area                   weight: 0.15
        # - Higher is better than random distribution       weight: 0.20

        # Expected inliers scales with image complexity
        expected_inliers = max(10, int(max_dim * 0.015))
        inlier_score = min(1.0, inlier_count / expected_inliers)

        # Inlier ratio directly — >0.5 is excellent
        ratio_score = min(1.0, inlier_ratio * 1.5)  # boost to reward >0.66

        # Coverage — warped reference should cover a meaningful part
        coverage_score = min(1.0, coverage_area_pct * 2.0)

        # Uniformity bonus: if matches are spread across the image
        # (not clustered), it's more likely the actual object is present.
        if inlier_count >= 4:
            inlier_pts = dst_pts[inlier_mask.ravel() == 1]
            if len(inlier_pts) >= 4:
                mean_pt = np.mean(inlier_pts.reshape(-1, 2), axis=0)
                variances = np.var(inlier_pts.reshape(-1, 2), axis=0)
                spread = np.sqrt(variances[0] + variances[1]) / max(w_par, h_par)
                uniformity_bonus = min(1.0, spread * 3.0)
            else:
                uniformity_bonus = 0.0
        else:
            uniformity_bonus = 0.0

        score = (
            0.30 * inlier_score +
            0.35 * ratio_score +
            0.15 * coverage_score +
            0.20 * uniformity_bonus
        )

        score = round(min(1.0, max(0.0, score)), 4)

        has_content = score > 0.15 and inlier_count >= 4

        return {
            "score": score,
            "keypoints_reference": len(des_ref),
            "keypoints_parcel": len(des_parcel),
            "good_matches": num_good,
            "inliers": inlier_count,
            "inlier_ratio": round(inlier_ratio, 4),
            "homography_found": True,
            "reprojection_threshold_px": 3.0,
            "coverage_area_pct": round(coverage_area_pct, 4),
            "uniformity_spread": round(uniformity_bonus, 4),
            "has_content": has_content,
            "error": None,
        }
    except ImportError as exc:
        logger.warning("Homography engine unavailable: %s", exc)
        return {"score": 0.0, "error": f"ImportError: {exc}"}
    except Exception as exc:
        logger.warning("Homography engine failed: %s", exc)
        return {"score": 0.0, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# Engine 4: Vision AI (Ollama)
# ═══════════════════════════════════════════════════════════════════════════

def _engine_vision_ai(
    image_bytes: bytes,
    item_descriptions: list[str],
) -> dict[str, Any]:
    """Use Ollama vision to analyze the parcel photo and compare against
    the packing sheet items.

    Sends a structured prompt asking the LLM to:
    - Count visible packages
    - List detected items and match them to the packing sheet
    - Assess packaging quality
    - Flag any anomalies

    Returns a dict with ``score`` (0-1), ``match_details`` (per-item), and
    the raw LLM response.
    """
    packing_context = "; ".join(item_descriptions)

    prompt = (
        "You are a parcel verification AI. Analyze this parcel photo carefully.\n\n"
        f"Expected items from the packing sheet:\n{packing_context}\n\n"
        "Please respond with STRICT JSON only (no markdown, no extra text):\n"
        "{\n"
        '  "package_count": <number of visible packages/boxes>,\n'
        '  "detected_items": ["item1", "item2", ...],\n'
        '  "item_match_results": [\n'
        '    {"expected": "Item name xQty", "detected": true/false, "confidence": 0.0-1.0}\n'
        "  ],\n"
        '  "packaging_quality": "good" | "fair" | "poor",\n'
        '  "seal_integrity": "sealed" | "open" | "unclear",\n'
        '  "anomalies_found": ["anomaly description"] or [],\n'
        '  "overall_match_percent": <0-100>,\n'
        '  "notes": "brief analysis"\n'
        "}"
    )

    response = _ollama_vision_chat(prompt, image_bytes)
    if not response:
        return {"score": 0.0, "error": "Vision AI returned empty response"}

    data = _extract_json(response)
    if not data:
        logger.warning("Could not parse vision AI response: %.200s", response)
        return {"score": 0.0, "error": "Could not parse AI response", "raw": response[:500]}

    # Parse the structured response
    overall_pct = data.get("overall_match_percent", 0)
    if isinstance(overall_pct, str):
        try:
            overall_pct = float(overall_pct.rstrip("%"))
        except (ValueError, TypeError):
            overall_pct = 0

    ai_score = max(0.0, min(1.0, overall_pct / 100.0))

    # Build per-item match details
    match_details = []
    item_results = data.get("item_match_results", [])
    if not item_results:
        detected = [d.lower() for d in data.get("detected_items", [])]
        for desc in item_descriptions:
            product_name = desc.split(" x")[0].lower()
            is_detected = any(
                kw in detected_item
                for detected_item in detected
                for kw in product_name.split()
                if len(kw) > 3
            )
            match_details.append({
                "expected": desc,
                "detected": is_detected,
                "confidence": 0.5 if is_detected else 0.0,
            })
    else:
        for r in item_results:
            match_details.append({
                "expected": r.get("expected", ""),
                "detected": bool(r.get("detected", False)),
                "confidence": float(r.get("confidence", 0.5)),
            })

    anomalies = data.get("anomalies_found", [])

    return {
        "score": round(ai_score, 4),
        "package_count": data.get("package_count", 0),
        "packaging_quality": data.get("packaging_quality", "unclear"),
        "seal_integrity": data.get("seal_integrity", "unclear"),
        "anomalies_found": anomalies if isinstance(anomalies, list) else [str(anomalies)],
        "match_details": match_details,
        "overall_match_percent": overall_pct,
        "detected_items": data.get("detected_items", []),
        "raw_response": response[:1000],
    }


# ═══════════════════════════════════════════════════════════════════════════
# Main verification function
# ═══════════════════════════════════════════════════════════════════════════

def verify_parcel_photo(
    image_bytes: bytes,
    item_descriptions: list[str],
    *,
    reference_image_bytes: bytes | None = None,
    run_ssim: bool = True,
    run_feature_match: bool = True,
    run_homography: bool = True,
    run_vision_ai: bool = True,
    fast_mode: bool = False,
) -> dict[str, Any]:
    """Run all available verification engines and produce a combined report.

    Each engine returns a 0-1 ``score``. The final ``match_score`` is a
    weighted average weighted by ``WEIGHTS``.

    Args:
        image_bytes: Raw bytes of the parcel photo.
        item_descriptions: List of strings like ``["Blue T-Shirt x2",
            "USB Cable x1"]``.
        reference_image_bytes: **Optional** raw bytes of a reference
            packaging photo. When provided, the ORB homography engine runs
            to detect whether the **same object** appears in the parcel
            photo (feature matching + perspective alignment).
        run_ssim: Whether to run the SSIM engine (fast).
        run_feature_match: Whether to run the OpenCV feature-match engine.
        run_homography: Whether to run the ORB homography engine
            (requires ``reference_image_bytes``).
        run_vision_ai: Whether to run the Ollama vision AI engine.
        fast_mode: When True, skip vision AI (slowest) and use only
            SSIM + feature match at lower resolution.

    Returns:
        A dict with the combined verification report.
    """
    start = time.time()
    results: dict[str, dict[str, Any]] = {}
    total_weight = 0.0
    weighted_score = 0.0

    expected_item_count = len(item_descriptions) or 1

    # ── Engine 1: SSIM ───────────────────────────────────────────────────
    if run_ssim:
        ssim_result = _engine_ssim(image_bytes, max_dim=512 if fast_mode else 1024)
        results["ssim"] = ssim_result
        if ssim_result.get("has_content", False) or ssim_result["score"] > 0.1:
            total_weight += WEIGHTS["ssim"]
            weighted_score += WEIGHTS["ssim"] * ssim_result["score"]

    # ── Engine 2: Feature Match (parcel-only content richness) ───────────
    if run_feature_match:
        fm_result = _engine_feature_match(
            image_bytes,
            expected_item_count=expected_item_count,
            max_dim=512 if fast_mode else 800,
        )
        results["feature_match"] = fm_result
        if fm_result.get("has_content", False) or fm_result.get("score", 0) > 0:
            total_weight += WEIGHTS["feature_match"]
            weighted_score += WEIGHTS["feature_match"] * fm_result["score"]

    # ── Engine 3: ORB Homography (reference-image comparison) ────────────
    if run_homography and reference_image_bytes is not None and len(reference_image_bytes) > 0:
        hg_result = _engine_feature_match_homography(
            image_bytes,
            reference_image_bytes,
            max_dim=512 if fast_mode else 800,
        )
        results["homography"] = hg_result
        if "error" not in hg_result:
            # Even a low score provides signal
            total_weight += WEIGHTS["homography"]
            weighted_score += WEIGHTS["homography"] * hg_result["score"]
    elif run_homography and reference_image_bytes is None:
        logger.info("Homography engine skipped: no reference image provided")

    # ── Engine 4: Vision AI ──────────────────────────────────────────────
    if run_vision_ai and not fast_mode:
        va_result = _engine_vision_ai(image_bytes, item_descriptions)
        results["vision_ai"] = va_result
        if "error" not in va_result:
            total_weight += WEIGHTS["vision_ai"]
            weighted_score += WEIGHTS["vision_ai"] * va_result["score"]

    # ── Compute combined score ───────────────────────────────────────────
    if total_weight > 0:
        match_score = weighted_score / total_weight
    else:
        match_score = 0.0

    match_score = round(min(1.0, max(0.0, match_score)), 4)

    # ── Determine result status ──────────────────────────────────────────
    if match_score >= PASS_THRESHOLD:
        status = "verified"
        message = "Packing matches parcel photo - items verified."
    elif match_score >= PARTIAL_THRESHOLD:
        status = "partial"
        message = "Partial match - review the discrepancies above."
    else:
        status = "unverified"
        message = "Low match score - the parcel photo may not match the packing sheet."

    # Count how many engines actually ran successfully
    engines_used = 0
    if run_ssim and "ssim" in results and "error" not in results["ssim"]:
        engines_used += 1
    if run_feature_match and "feature_match" in results and "error" not in results["feature_match"]:
        engines_used += 1
    if run_homography and "homography" in results and "error" not in results["homography"]:
        engines_used += 1
    if run_vision_ai and "vision_ai" in results and "error" not in results["vision_ai"]:
        engines_used += 1

    # Count matched items from the best available source
    matched_items = 0
    if "vision_ai" in results and "error" not in results["vision_ai"]:
        for detail in results["vision_ai"].get("match_details", []):
            if detail.get("detected", False):
                matched_items += 1

    elapsed = round(time.time() - start, 3)

    return {
        "status": status,
        "match_score": match_score,
        "match_percentage": round(match_score * 100, 1),
        "message": message,
        "total_items": len(item_descriptions),
        "matched_items": matched_items if matched_items > 0 else int(match_score * len(item_descriptions)),
        "engines_used": engines_used,
        "engine_details": results,
        "engine_weights": dict(WEIGHTS),
        "reference_used": reference_image_bytes is not None,
        "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": elapsed,
    }


def verify_parcel_fast(
    image_bytes: bytes,
    item_descriptions: list[str],
    reference_image_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Fast verification - SSIM + feature match + homography (if reference given),
    no vision AI. Use this when speed matters and Ollama is unavailable.
    """
    return verify_parcel_photo(
        image_bytes,
        item_descriptions,
        reference_image_bytes=reference_image_bytes,
        run_vision_ai=False,
        fast_mode=True,
    )
