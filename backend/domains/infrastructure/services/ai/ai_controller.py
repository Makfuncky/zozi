"""AI Controller — stub module providing AI suggestion endpoints.

This module was reconstructed because the original `controllers.core.ai_controller`
was removed during the controllers→domains migration but its callers were never
updated. The functions here provide a minimal implementation that matches the
expected signature; replace with real AI integration when available.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def get_ai_suggestions(
    name: str = "",
    description: str = "",
    image: Any = None,
    images: Optional[List[Any]] = None,
    image_url: str = "",
    image_urls: Optional[List[str]] = None,
) -> dict:
    """Generate AI suggestions for category, tags, and description."""
    logger.info("AI suggestions requested for product: %s", name)
    return {
        "name": name,
        "description": description,
        "suggestions": {
            "category": "general",
            "tags": [],
            "enhanced_description": description,
        },
    }


def queue_ai_suggestions_job(
    name: str = "",
    description: str = "",
    image: Any = None,
    images: Optional[List[Any]] = None,
    image_url: str = "",
    image_urls: Optional[List[str]] = None,
    current_user: Optional[dict] = None,
) -> dict:
    """Queue an async AI suggestions job."""
    job_id = str(uuid.uuid4())
    logger.info("AI suggestions job queued: %s for product: %s", job_id, name)
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "AI suggestions job has been queued for processing.",
    }


def queue_ai_text_suggestions_job(
    name: str = "",
    description: str = "",
    current_user: Optional[dict] = None,
) -> dict:
    """Queue an async AI text-only suggestions job."""
    job_id = str(uuid.uuid4())
    logger.info("AI text suggestions job queued: %s for product: %s", job_id, name)
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "AI text suggestions job has been queued for processing.",
    }


def get_product_angles(
    name: str = "",
    category: str = "",
    image: Any = None,
) -> dict:
    """Generate AI-guided photo angle descriptions for a product."""
    logger.info("Product angles requested for: %s", name)
    return {
        "product_name": name,
        "category": category,
        "angles": [
            {"name": "Front", "description": "Standard front-facing product shot."},
            {"name": "Back", "description": "Rear view showing product details."},
            {"name": "Side", "description": "Side profile view."},
            {"name": "Detail Shot", "description": "Close-up of key features."},
            {"name": "In-Use", "description": "Product in context/usage scenario."},
        ],
    }


def queue_product_angles_job(
    name: str = "",
    category: str = "",
    image: Any = None,
    current_user: Optional[dict] = None,
) -> dict:
    """Queue an async product angles job."""
    job_id = str(uuid.uuid4())
    logger.info("Product angles job queued: %s for product: %s", job_id, name)
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Product angles job has been queued for processing.",
    }
