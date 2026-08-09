"""Product moderation controller (LAYER 3).

Wraps :mod:`services.catalog.product_moderation_service` so the router only
declares endpoints. Replaces the ``ProductModerationService`` class that used
to live inside ``routers/product_moderation.py``.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from sqlalchemy.orm import Session

from services.catalog import product_moderation_service
import structlog
logger = structlog.get_logger(__name__)

__all__ = ["get_product_restrictions", "moderate_product_payload"]


def get_product_restrictions(db: Session, country_code: str) -> dict[str, Any]:
    """Return the configured product restrictions for a country."""
    return product_moderation_service.get_restrictions(db, country_code)


def moderate_product_payload(
    db: Session,
    country_code: str,
    product_id: int,
    product_data: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Evaluate a product payload against a country's restrictions."""
    result = product_moderation_service.evaluate_product(
        db, country_code, product_data or {}
    )
    result["product_id"] = product_id
    return result
