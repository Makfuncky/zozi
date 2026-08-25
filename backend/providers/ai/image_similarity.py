from __future__ import annotations

"""
Image Similarity Search Provider
=================================
Compute image embeddings using color histogram + texture features,
then find similar images via cosine similarity.
Pure Python — PIL + numpy only.
"""
import io
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "HAS_PIL",
    "HAS_NUMPY",
    "compute_image_embedding",
    "compute_similarity",
    "find_similar_images",
]

# ---------------------------------------------------------------------------
# PIL availability flag
# ---------------------------------------------------------------------------
try:
    from PIL import Image  # type: ignore

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# numpy availability flag
# ---------------------------------------------------------------------------
try:
    import numpy as np  # type: ignore

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _check_dependencies() -> None:
    """Raise an informative error if required dependencies are missing."""
    if not HAS_PIL:
        raise ImportError(
            "PIL (Pillow) is required for image_similarity. "
            "Install it with: pip install Pillow"
        )
    if not HAS_NUMPY:
        raise ImportError(
            "numpy is required for image_similarity. "
            "Install it with: pip install numpy"
        )


def _load_image(image_bytes: bytes) -> "Image.Image":
    """Load an image from bytes and convert to RGB."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return img.convert("RGB")
    except Exception as exc:
        raise ValueError(f"Failed to decode image: {exc}") from exc


def _color_histogram(image: "Image.Image", bins: int = 16) -> List[float]:
    """Compute a color histogram feature vector.

    Divides each RGB channel into `bins` segments and counts pixel
    frequencies, then normalizes to a unit vector.

    Args:
        image: PIL Image in RGB mode.
        bins: Number of bins per channel.

    Returns:
        Normalized histogram as a flat list of floats.
    """
    if HAS_NUMPY:
        arr = np.array(image)
        # Downsample for speed if image is large
        if arr.shape[0] > 256 or arr.shape[1] > 256:
            image = image.resize((256, 256), Image.BILINEAR)
            arr = np.array(image)

        hist = []
        for channel in range(3):
            h, _ = np.histogram(
                arr[:, :, channel], bins=bins, range=(0, 256)
            )
            hist.extend(h.tolist())
        # Normalize
        total = sum(hist)
        if total > 0:
            return [v / total for v in hist]
        return [0.0] * (bins * 3)
    else:
        # Pure Python fallback
        width, height = image.size
        if width > 256 or height > 256:
            image = image.resize((256, 256), Image.BILINEAR)
        pixels = list(image.getdata())
        hist = [0] * (bins * 3)
        bin_size = 256 // bins
        for r, g, b in pixels:
            ri = min(r // bin_size, bins - 1)
            gi = min(g // bin_size, bins - 1)
            bi = min(b // bin_size, bins - 1)
            hist[ri] += 1
            hist[bins + gi] += 1
            hist[2 * bins + bi] += 1
        total = len(pixels)
        if total > 0:
            return [v / total for v in hist]
        return [0.0] * (bins * 3)


def _texture_features(image: "Image.Image") -> List[float]:
    """Compute texture features using gradient statistics.

    Converts to grayscale, computes horizontal and vertical gradients,
    and returns mean, std, and energy of the gradient magnitude.

    Args:
        image: PIL Image in RGB mode.

    Returns:
        List of texture feature values.
    """
    gray = image.convert("L")
    if HAS_NUMPY:
        arr = np.array(gray, dtype=np.float64)
        # Downsample for speed
        if arr.shape[0] > 128 or arr.shape[1] > 128:
            gray = gray.resize((128, 128), Image.BILINEAR)
            arr = np.array(gray, dtype=np.float64)

        # Gradients
        gx = np.diff(arr, axis=1)
        gy = np.diff(arr, axis=0)
        # Pad to same shape
        min_h = min(gx.shape[0], gy.shape[0])
        min_w = min(gx.shape[1], gy.shape[1])
        gx = gx[:min_h, :min_w]
        gy = gy[:min_h, :min_w]

        magnitude = np.sqrt(gx**2 + gy**2)
        mean_grad = float(np.mean(magnitude))
        std_grad = float(np.std(magnitude))
        energy = float(np.mean(magnitude**2))

        # Edge direction histogram (8 bins)
        direction = np.arctan2(gy, gx)  # range [-pi, pi]
        direction_bins = 8
        dir_hist, _ = np.histogram(
            direction, bins=direction_bins, range=(-math.pi, math.pi)
        )
        dir_hist = dir_hist.astype(np.float64)
        dir_total = dir_hist.sum()
        if dir_total > 0:
            dir_hist /= dir_total

        return [mean_grad, std_grad, energy] + dir_hist.tolist()
    else:
        # Pure Python fallback
        width, height = gray.size
        if width > 128 or height > 128:
            gray = gray.resize((128, 128), Image.BILINEAR)
            width, height = gray.size
        pixels = list(gray.getdata())

        # Build 2D array
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(pixels[y * width + x])
            grid.append(row)

        # Compute gradients
        magnitudes = []
        directions = []
        for y in range(height - 1):
            for x in range(width - 1):
                gx = float(grid[y][x + 1]) - float(grid[y][x])
                gy = float(grid[y + 1][x]) - float(grid[y][x])
                mag = math.sqrt(gx * gx + gy * gy)
                magnitudes.append(mag)
                directions.append(math.atan2(gy, gx))

        n = len(magnitudes)
        if n == 0:
            return [0.0, 0.0, 0.0] + [0.0] * 8

        mean_grad = sum(magnitudes) / n
        variance = sum((m - mean_grad) ** 2 for m in magnitudes) / n
        std_grad = math.sqrt(variance)
        energy = sum(m * m for m in magnitudes) / n

        # Direction histogram
        dir_bins = 8
        dir_hist = [0.0] * dir_bins
        bin_width = (2 * math.pi) / dir_bins
        for d in directions:
            # Shift to [0, 2pi]
            shifted = d + math.pi
            idx = int(shifted / bin_width)
            if idx >= dir_bins:
                idx = dir_bins - 1
            if idx < 0:
                idx = 0
            dir_hist[idx] += 1.0
        for i in range(dir_bins):
            dir_hist[i] /= n

        return [mean_grad, std_grad, energy] + dir_hist


def compute_image_embedding(image_bytes: bytes) -> List[float]:
    """Generate an embedding vector for an image.

    Combines color histogram and texture features into a single vector.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.).

    Returns:
        List of floats representing the image embedding.

    Raises:
        ImportError: If PIL or numpy is not installed.
        ValueError: If the image cannot be decoded.
    """
    _check_dependencies()
    image = _load_image(image_bytes)

    color_feats = _color_histogram(image, bins=16)
    texture_feats = _texture_features(image)

    return color_feats + texture_feats


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Compute cosine similarity between two image embeddings.

    Args:
        embedding1: First embedding vector.
        embedding2: Second embedding vector.

    Returns:
        Cosine similarity score (0 to 1), or 0 if vectors are invalid.
    """
    if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
        return 0.0

    if HAS_NUMPY:
        a = np.array(embedding1, dtype=np.float64)
        b = np.array(embedding2, dtype=np.float64)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    else:
        dot = sum(x * y for x, y in zip(embedding1, embedding2))
        norm_a = math.sqrt(sum(x * x for x in embedding1))
        norm_b = math.sqrt(sum(y * y for y in embedding2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


def find_similar_images(
    query_image_bytes: bytes,
    candidate_images: List[Dict[str, Any]],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Find the most similar images from a candidate set.

    Args:
        query_image_bytes: Raw bytes of the query image.
        candidate_images: List of dicts, each with 'id' and 'image_bytes' keys.
        limit: Maximum number of results.

    Returns:
        List of dicts with 'id', 'score', sorted by score descending.
    """
    _check_dependencies()

    query_embedding = compute_image_embedding(query_image_bytes)
    results: List[Dict[str, Any]] = []

    for candidate in candidate_images:
        cid = candidate.get("id")
        cbytes = candidate.get("image_bytes")
        if cid is None or not cbytes:
            continue
        try:
            cand_embedding = compute_image_embedding(cbytes)
            score = compute_similarity(query_embedding, cand_embedding)
            results.append({"id": cid, "score": round(score, 6)})
        except (ValueError, Exception) as exc:
            logger.warning("Skipping candidate %s: %s", cid, exc)
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
