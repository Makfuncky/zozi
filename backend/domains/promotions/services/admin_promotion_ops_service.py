from __future__ import annotations

"""Admin promotion management service layer.

Handles PromotionOrderTier CRUD, promotion config updates,
flash sale archive/restore, and coupon patch/archive/restore.
"""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.promotions.models.promotions import PromotionOrderTier
# LAZY: from domains.governance.ports import PromotionOrderTier
from domains.promotions.models.promotion_config import PromotionEngineConfig
# LAZY: from domains.governance.ports import PromotionEngineConfig
from domains.promotions.models.promotions import Coupon, FlashSale


# ── Promotion Engine Config ───────────────────────────────────────────────────


def update_promotion_config_full(
    db: Session,
    config_id: int,
    updates: dict,
    admin_id: int,
) -> PromotionEngineConfig:
    """Update promotion engine config with a dict of updatable fields."""
    config = db.get(PromotionEngineConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="No promotion config found")

    for key, value in updates.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)

    config.updated_by = admin_id
    db.commit()
    db.refresh(config)
    return config


# ── Promotion Order Tiers ─────────────────────────────────────────────────────


def list_all_promotion_tiers(db: Session) -> list[PromotionOrderTier]:
    """Get all non-deleted promotion order tiers."""
    return db.query(PromotionOrderTier).filter(
        PromotionOrderTier.is_deleted == False  # noqa: E712
    ).order_by(PromotionOrderTier.sort_order).all()


def create_promotion_tier(
    db: Session,
    *,
    tier_name: Optional[str] = None,
    min_order: Optional[float] = None,
    max_order: Optional[float] = None,
    discount_type: str = "fixed",
    discount_value: Optional[float] = None,
    stacking_allowed: bool = False,
    is_active: bool = True,
    sort_order: int = 0,
    updated_by_id: Optional[int] = None,
) -> PromotionOrderTier:
    """Create a new promotion order tier."""
    tier = PromotionOrderTier(
        tier_name=tier_name,
        min_order_amount=min_order,
        max_order_amount=max_order,
        discount_type=discount_type,
        discount_value=discount_value,
        stacking_allowed=stacking_allowed,
        is_active=is_active,
        sort_order=sort_order,
        updated_by_id=updated_by_id,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def update_promotion_tier(
    db: Session,
    tier_id: int,
    updates: dict,
    updated_by_id: Optional[int] = None,
) -> Optional[PromotionOrderTier]:
    """Update a promotion order tier."""
    tier = db.query(PromotionOrderTier).filter(PromotionOrderTier.id == tier_id).first()
    if not tier:
        return None

    field_map = {
        "tier_name": "tier_name",
        "min_order": "min_order_amount",
        "max_order": "max_order_amount",
        "discount_type": "discount_type",
        "discount_value": "discount_value",
        "stacking_allowed": "stacking_allowed",
        "is_active": "is_active",
        "sort_order": "sort_order",
    }

    for payload_key, model_attr in field_map.items():
        if payload_key in updates:
            setattr(tier, model_attr, updates[payload_key])

    if updated_by_id is not None:
        tier.updated_by_id = updated_by_id

    db.commit()
    db.refresh(tier)
    return tier


def delete_promotion_tier(db: Session, tier_id: int) -> bool:
    """Soft-delete a promotion order tier."""
    tier = db.query(PromotionOrderTier).filter(PromotionOrderTier.id == tier_id).first()
    if not tier:
        return False

    tier.is_deleted = True
    db.commit()
    return True


# ── Flash Sales ───────────────────────────────────────────────────────────────


def archive_flash_sale(db: Session, sale_id: int) -> bool:
    """Archive (soft-delete) a flash sale."""
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        return False

    sale.is_deleted = True
    sale.is_active = False
    db.commit()
    return True


def restore_flash_sale(db: Session, sale_id: int) -> bool:
    """Restore an archived flash sale."""
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        return False

    sale.is_deleted = False
    db.commit()
    return True


# ── Coupons ───────────────────────────────────────────────────────────────────


def update_coupon(
    db: Session,
    coupon_id: int,
    updates: dict,
) -> Optional[Coupon]:
    """Update a coupon with a dict of fields."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        return None

    for key, value in updates.items():
        if key == "discount_value":
            value = float(value or 0)
        if hasattr(coupon, key):
            setattr(coupon, key, value)

    db.commit()
    db.refresh(coupon)
    return coupon


def archive_coupon(db: Session, coupon_id: int) -> bool:
    """Archive (soft-delete) a coupon."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        return False

    coupon.is_deleted = True
    coupon.is_active = False
    db.commit()
    return True


def restore_coupon(db: Session, coupon_id: int) -> bool:
    """Restore an archived coupon."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        return False

    coupon.is_deleted = False
    db.commit()
    return True


# ── Preview ───────────────────────────────────────────────────────────────────


def preview_promotion_discount(
    db: Session,
    order_subtotal: float,
    coupon_discount: float,
) -> dict:
    """Calculate promotion preview including tier discount."""
    tiers = db.query(PromotionOrderTier).filter(
        PromotionOrderTier.is_deleted == False,  # noqa: E712
        PromotionOrderTier.is_active == True,  # noqa: E712
    ).order_by(PromotionOrderTier.sort_order).all()

    matched = None
    tier_discount = 0.0
    for t in tiers:
        min_o = float(t.min_order_amount or 0)
        max_o = float(t.max_order_amount) if t.max_order_amount is not None else None
        if order_subtotal >= min_o and (max_o is None or order_subtotal <= max_o):
            matched = t
            if t.discount_type == "percent":
                tier_discount = order_subtotal * (float(t.discount_value or t.discount_amount or 0) / 100)
            else:
                tier_discount = float(t.discount_value or t.discount_amount or 0)
            break

    final_discount = coupon_discount + tier_discount
    return {
        "after_coupon": order_subtotal - coupon_discount,
        "tier_discount": tier_discount,
        "final_discount": final_discount,
        "matched_tier": {
            "tier_name": matched.tier_name,
            "discount_type": matched.discount_type,
            "discount_value": float(matched.discount_value or matched.discount_amount or 0),
        } if matched else None,
    }
