"""Visual search service.

Owns the database access for visual/product similarity lookups so that the
image *provider* (`providers.image.image.process_image_search`) stays a pure
image-processing adapter with no direct DB access. Per ARCHITECTURE_DIAGRAM.md
the data-access boundary is `services -> DB`; providers only talk to external
models/SDKs.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


def fetch_visually_similar_products(db: Any, limit: int = 10) -> list[dict]:
    """Return a list of candidate products for visual similarity matching.

    This is a placeholder lookup (random active/approved products). A
    production implementation should query vector embeddings (CLIP / ResNet /
    ViT) stored on the product. The caller (a service) passes the result into
    ``providers.image.image.process_image_search``.
    """
    try:
        rows = (
            db.execute(
                text(
                    """
                    SELECT id, name, image_url AS primary_image, COALESCE(price, 0) as price
                     FROM products
                     WHERE is_active = true
                       AND is_approved = true
                     ORDER BY RANDOM()
                     LIMIT :limit
                    """
                ),
                {"limit": min(limit * 2, 20)},
            )
            .mappings()
            .all()
        )
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "image": row["primary_image"],
                "price": float(row["price"]),
            }
            for row in rows
        ]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Visual search DB query failed: %s", exc)
        return []
