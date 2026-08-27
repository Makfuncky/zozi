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


def validate_coupon_code(db: Session, code: str, order_total: object) -> dict:
    """Sanctioned cross-domain read: validate a coupon code against an order total."""
    from domains.promotions.services.coupons.coupon_service import validate_coupon_code as _svc
    return _svc(db, code, order_total)


def list_coupons_paginated(db: Session, cursor: int | None = None, page_size: int = 20) -> dict:
    """Sanctioned cross-domain read: list coupons with keyset pagination."""
    from domains.promotions.services.coupons.coupon_service import list_coupons_paginated as _svc
    return _svc(db, cursor=cursor, page_size=page_size)


def create_coupon_from_payload(db: Session, payload: dict):
    """Sanctioned cross-domain write: create a coupon from a payload."""
    from domains.promotions.services.coupons.coupon_service import create_coupon_from_payload as _svc
    return _svc(db, payload)


def delete_coupon_by_id(db: Session, coupon_id: str) -> dict:
    """Sanctioned cross-domain write: delete a coupon by ID."""
    from domains.promotions.services.coupons.coupon_service import delete_coupon_by_id as _svc
    return _svc(db, coupon_id)


def get_referral_config(db: Session) -> dict:
    """Referral program configuration read.

    Underlying service lives in the customers domain; the legacy
    ``domains.customers.services.referrals.referrals_service`` controller was
    removed (it was a no-op route marker, not real business logic). Until the
    canonical referral-config service is reintroduced, return a conservative
    default so the rest of the promotions surface can boot.
    """
    return {
        "enabled": False,
        "referrer_points": 0,
        "referee_points": 0,
        "monthly_cap": 0,
        "verification_delay_days": 0,
    }


# ── Low-level coupon CRUD (sanctioned cross-domain delegation) ──────────────
# Thin wrappers so module routers import from promotions.ports instead of
# directly from domains.promotions.services.coupons.coupon_service.

def create_coupon(db: Session, payload: dict):
    """Sanctioned cross-domain write: create a coupon (raw)."""
    from domains.promotions.services.coupons.coupon_service import create_coupon as _svc
    return _svc(db, payload)


def delete_coupon(db: Session, coupon_id: str) -> dict:
    """Sanctioned cross-domain write: delete a coupon by ID (raw)."""
    from domains.promotions.services.coupons.coupon_service import delete_coupon as _svc
    return _svc(db, coupon_id)


def list_coupons(db: Session, cursor: int | None = None, page_size: int = 20) -> dict:
    """Sanctioned cross-domain read: list coupons (raw, keyset paginated)."""
    from domains.promotions.services.coupons.coupon_service import list_coupons as _svc
    return _svc(db, cursor=cursor, page_size=page_size)


def validate_coupon(db: Session, code: str, order_total: object) -> dict:
    """Sanctioned cross-domain read: validate a coupon (raw, returns view)."""
    from domains.promotions.services.coupons.coupon_service import validate_coupon as _svc
    return _svc(db, code, order_total)


__all__ = [
    "get_promotion_engine_config",
    "is_engine_enabled",
    "get_max_combined_discount",
    "validate_coupon_code",
    "list_coupons_paginated",
    "create_coupon_from_payload",
    "delete_coupon_by_id",
    "get_referral_config",
    "create_coupon",
    "delete_coupon",
    "list_coupons",
    "validate_coupon",
]
