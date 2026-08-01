"""
Promotion Engine Service — DB write operations for promotion engine configuration.

Moved out of controllers/promotion_controller.py to break the
services -> controllers forbidden dependency edge.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from db.base import Base
from models import PromotionEngineConfig, PromotionOrderTier


def _is_safe_to_create_tables() -> bool:
    """Check if it's safe to create tables (dev/SQLite only)."""
    if os.getenv("APP_ENV", "development").lower() == "production":
        return False
    from db.database import _IS_POSTGRES
    if _IS_POSTGRES:
        return False
    return True


def ensure_promotion_tables(db: Session) -> None:
    """Create promotion tables if they don't exist (idempotent)."""
    if not _is_safe_to_create_tables():
        return
    bind = db.get_bind()
    Base.metadata.create_all(
        bind=bind,
        tables=[
            PromotionEngineConfig.__table__,
            PromotionOrderTier.__table__,
        ],
        checkfirst=True,
    )


def seed_default_tiers(db: Session, updated_by: Optional[int]) -> None:
    if db.query(PromotionOrderTier).count() > 0:
        return

    defaults = [
        {
            "tier_name": "Tier A",
            "min_order": Decimal("10.00"),
            "max_order": Decimal("24.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("0.50"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 1,
        },
        {
            "tier_name": "Tier B",
            "min_order": Decimal("25.00"),
            "max_order": Decimal("49.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("1.50"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 2,
        },
        {
            "tier_name": "Tier C",
            "min_order": Decimal("50.00"),
            "max_order": Decimal("99.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("4.00"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 3,
        },
        {
            "tier_name": "Tier D",
            "min_order": Decimal("100.00"),
            "max_order": None,
            "discount_type": "percent",
            "discount_value": Decimal("5.00"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 4,
        },
    ]

    for payload in defaults:
        db.add(
            PromotionOrderTier(
                tier_name=payload["tier_name"],
                min_order_amount=payload["min_order"],
                max_order_amount=payload["max_order"],
                discount_type=payload["discount_type"],
                discount_amount=payload["discount_value"],
                discount_value=payload["discount_value"],
                stacking_allowed=payload["stacking_allowed"],
                is_active=payload["is_active"],
                sort_order=payload["sort_order"],
                updated_by=updated_by,
            )
        )


def get_or_create_config(db: Session) -> PromotionEngineConfig:
    """Return the singleton promotion engine config, creating defaults if missing."""
    ensure_promotion_tables(db)
    row = db.query(PromotionEngineConfig).order_by(PromotionEngineConfig.id.asc()).first()
    if row:
        return row

    row = PromotionEngineConfig(
        engine_enabled=False,
        allow_product_coupons=True,
        allow_category_coupons=True,
        allow_order_tier_discounts=True,
        allow_referral_rewards=True,
        allow_supplier_promotions=True,
        allow_global_coupons=True,
        stacking_mode="best_only",
        max_combined_discount_percent=Decimal("50.00"),
        max_combined_discount_amount=Decimal("0.000"),
        show_savings_line_item=True,
        tier_discount_visible=True,
        points_per_omr=1000,
        referral_referrer_points=100,
        referral_referee_points=100,
        points_expiry_months=12,
        referral_monthly_cap=20,
        referral_verification_delay_days=7,
        min_points_redeem=1000,
        allow_partial_points_redemption=True,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    seed_default_tiers(db, updated_by=None)
    db.commit()
    db.refresh(row)
    return row
