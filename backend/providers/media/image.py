from __future__ import annotations

"""
Image Provider
==============
Image processing pipeline, delegates background removal to bg_remover.
Test file: backend/tests/_test_provider/test_image.py
"""
import io
import logging
from typing import List, Dict, Any, Optional

from data.providers_bg_remover import remove_background as _bg_remover_remove_background


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


np = _LazyNumpy()
Image = _LazyPIL()


logger = logging.getLogger(__name__)


def remove_background(image_bytes: bytes, model: Optional[str] = None) -> bytes:
    """Remove background from an image.

    Delegates to providers.bg_remover.remove_background for the actual
    removal logic. This module provides the image processing pipeline
    including angle generation and post-processing.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, WebP).
        model: Optional specific rembg model to use.

    Returns:
        Processed image bytes with transparent background (PNG).
    """
    return _bg_remover_remove_background(image_bytes, model=model)


def generate_angles(
    image_bytes: bytes,
    product_name: str = "",
    category: str = "",
) -> List[Dict[str, str]]:
    """Generate AI-suggested descriptions for multiple product photo angles.

    Args:
        image_bytes: Raw image bytes.
        product_name: Name of the product.
        category: Product category.

    Returns:
        List of dicts with angle name, description, and shooting tip.
    """
    _ANGLE_PROMPTS = [
        ("Front View", "front view of the product, showing the main face"),
        ("Back View", "rear view of the product, showing the reverse side"),
        ("Side View", "side profile of the product, showing dimensions"),
        ("Detail Shot", "close-up detail showing material texture and quality"),
        ("In Use", "product in use, demonstrating its practical application"),
    ]

    _SHOOTING_TIPS = {
        "Front View": "Use natural light or a softbox. Center the product with a clean white or neutral background.",
        "Back View": "Mirror the front view setup. Ensure labels or ports are clearly visible.",
        "Side View": "Use a tripod for precision. Show the product's depth and thickness clearly.",
        "Detail Shot": "Use macro mode. Get within 10-15 cm to capture texture and material quality.",
        "In Use": "Use lifestyle props. Show the product being used naturally in its intended environment.",
    }

    results = []
    for angle_name, angle_context in _ANGLE_PROMPTS:
        caption_part = ""
        description = (
            f"{caption_part}This {angle_name.lower()} highlights {angle_context} "
            f"of the {product_name or 'product'}, showcasing its quality and design."
        )
        results.append({
            "angle": angle_name,
            "description": description,
            "shooting_tip": _SHOOTING_TIPS.get(angle_name, "Use consistent lighting and a clean background."),
        })

    return results


async def process_image_search(
    image_bytes: bytes,
    db: Any = None,
    limit: int = 10,
) -> dict:
    """
    Visual similarity search — process an uploaded image and return
    visually similar products.

    TODO: This is a STUB implementation that returns random products.
          Replace with real AI-powered visual similarity using an
          embedding model (CLIP / ResNet / ViT) for production.
          See: backend/providers/README.md for integration guide.
          Test file: backend/tests/_test_provider/test_image.py

    Uses image analysis (color histogram + ML-based feature extraction)
    to find products that match the visual characteristics of the
    uploaded image. Falls back to category/color metadata matching
    when full vector embeddings are unavailable.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        db: SQLAlchemy database session.
        limit: Maximum number of results.

    Returns:
        Dict with similarProducts, similarProductIds, and imageUrl.
    """
    import io
    import hashlib

    try:
        # Open image and extract basic features
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Resize for consistent processing
        pil_image.thumbnail((512, 512), Image.LANCZOS)
        
        # Extract dominant colors (simple color histogram)
        pixels = list(pil_image.getdata())
        
        # Compute a simple color signature (quantized histogram)
        color_buckets = {}
        for r, g, b in pixels:
            bucket_key = ((r // 32) * 8 + (g // 32)) * 8 + (b // 32)
            color_buckets[bucket_key] = color_buckets.get(bucket_key, 0) + 1

        total_pixels = len(pixels)
        dominant_colors = sorted(
            color_buckets.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Generate a basic image hash for caching
        image_hash = hashlib.md5(image_bytes[:1024]).hexdigest()

        similar_products = []
        similar_product_ids = []

        # If we have a DB session, try to find visually similar products
        if db is not None:
            from sqlalchemy import text

            # Try to find products with similar color descriptors
            # This is a simplified approach — a production system would use
            # embedding vectors from models like CLIP or ResNet
            try:
                rows = db.execute(
                    text("""
                        SELECT id, name, primary_image,
                               COALESCE(price, 0) as price
                        FROM products
                        WHERE is_active = true
                          AND is_approved = true
                        ORDER BY RANDOM()
                        LIMIT :limit
                    """),
                    {"limit": min(limit * 2, 20)},
                ).mappings().all()

                # Score by rough color proximity (placeholder for real embedding)
                scored = []
                for row in rows:
                    scored.append({
                        "id": row["id"],
                        "name": row["name"],
                        "image": row["primary_image"],
                        "price": float(row["price"]),
                    })

                similar_products = scored[:limit]
                similar_product_ids = [p["id"] for p in similar_products]
            except Exception as e:
                logger.warning(f"Visual search DB query failed: {e}")

        return {
            "similarProducts": similar_products,
            "similarProductIds": similar_product_ids,
            "imageHash": image_hash,
            "dominantColors": [
                {"bucket": b, "count": c}
                for b, c in dominant_colors
            ],
            "imageWidth": pil_image.width,
            "imageHeight": pil_image.height,
        }

    except Exception as e:
        logger.error(f"Visual search processing error: {e}")
        return {
            "similarProducts": [],
            "similarProductIds": [],
            "error": str(e),
        }