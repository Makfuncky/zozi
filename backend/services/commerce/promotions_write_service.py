"""Promotions write service — DB write operations for promotions and discounts."""

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    Promotion,
    PromotionEngineConfig,
    PromotionLedgerEntry,
    PromotionOrderTier,
    PromotionRedemption,
    PromotionRule,
)


def create_promotion(db: Session, **promotion_data) -> Promotion:
    promotion = Promotion(**promotion_data)
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion


def update_promotion(db: Session, promotion: Promotion, updates: dict) -> Promotion:
    for key, value in updates.items():
        setattr(promotion, key, value)
    db.commit()
    db.refresh(promotion)
    return promotion


def delete_promotion(db: Session, promotion: Promotion) -> None:
    db.delete(promotion)
    db.commit()


def create_promotion_rule(db: Session, promotion_id: int, **rule_data) -> PromotionRule:
    rule = PromotionRule(promotion_id=promotion_id, **rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_promotion_rule(db: Session, rule: PromotionRule, updates: dict) -> PromotionRule:
    for key, value in updates.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete_promotion_rule(db: Session, rule: PromotionRule) -> None:
    db.delete(rule)
    db.commit()


def create_promotion_redemption(
    db: Session, promotion_id: int, user_id: int, **redemption_data
) -> PromotionRedemption:
    redemption = PromotionRedemption(
        promotion_id=promotion_id, user_id=user_id, **redemption_data
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption


def update_promotion_engine_config(
    db: Session, config: PromotionEngineConfig, updates: dict
) -> PromotionEngineConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def create_promotion_order_tier(db: Session, **tier_data) -> PromotionOrderTier:
    tier = PromotionOrderTier(**tier_data)
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def update_promotion_order_tier(
    db: Session, tier: PromotionOrderTier, updates: dict
) -> PromotionOrderTier:
    for key, value in updates.items():
        setattr(tier, key, value)
    db.commit()
    db.refresh(tier)
    return tier


def delete_promotion_order_tier(db: Session, tier: PromotionOrderTier) -> None:
    db.delete(tier)
    db.commit()


def create_promotion_ledger_entry(
    db: Session,
    order_id: int,
    user_id: int | None,
    tier: PromotionOrderTier,
    discount_amount: Decimal,
) -> PromotionLedgerEntry:
    entry = PromotionLedgerEntry(
        order_id=order_id,
        user_id=user_id,
        promotion_type="order_tier",
        promotion_code=getattr(tier, "tier_name", None),
        tier_id=getattr(tier, "id", None),
        discount_amount=discount_amount,
        points_awarded=0,
        points_redeemed=0,
        stacking_flag=bool(getattr(tier, "stacking_allowed", False)),
        source="checkout",
        metadata_json=None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry