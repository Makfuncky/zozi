"""Promotions domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.promotions.models or domains.promotions.services directly.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.promotions.models.promotion_config import PromotionEngineConfig


def get_promotion_engine_config(db: Session, country_code: str) -> Optional[PromotionEngineConfig]:
    """Read the promotion engine configuration for a country."""
    return db.query(PromotionEngineConfig).filter(
        PromotionEngineConfig.country_code == country_code,
    ).first()


def is_engine_enabled(db: Session, country_code: str) -> bool:
    """Check whether the promotion engine is enabled for a country."""
    config = get_promotion_engine_config(db, country_code)
    return bool(config and config.engine_enabled)


def get_max_combined_discount(db: Session, country_code: str) -> Decimal:
    """Get the maximum combined discount percent allowed for a country."""
    config = get_promotion_engine_config(db, country_code)
    return config.max_combined_discount_percent if config else Decimal("50.00")


__all__ = [
    "get_promotion_engine_config",
    "is_engine_enabled",
    "get_max_combined_discount",
]
