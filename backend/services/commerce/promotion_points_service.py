"""
Points & Loyalty Service
=========================
Manages user points balance, loyalty tiers (Bronze/Silver/Gold),
points award on orders, point redemption at checkout, and the
audit trail via PointsTransaction.

Loyalty tier thresholds (matching PROMOTION.md):
  - Bronze: 0–500 lifetime points
  - Silver: 501–1000 lifetime points
  - Gold: 1001+ lifetime points

Tier benefits (applied elsewhere, documented here for reference):
  - Bronze: 5% bonus points on purchases
  - Silver: 10% bonus points + free shipping on orders > 50 OMR
  - Gold: 15% bonus points + priority support
"""
from typing import Set

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from data.models import User, UserPoints, PointsTransaction, PromotionEngineConfig
from services.promotion_engine_service import get_or_create_config as _get_promotion_config
from utils.money import to_decimal

logger = logging.getLogger(__name__)

# ── Loyalty tier thresholds ────────────────────────────────────────────

LOYALTY_TIERS = [
    {"name": "bronze", "min_lifetime": 0, "max_lifetime": 500, "bonus_pct": 5},
    {"name": "silver", "min_lifetime": 501, "max_lifetime": 1000, "bonus_pct": 10},
    {"name": "gold", "min_lifetime": 1001, "max_lifetime": None, "bonus_pct": 15},
]


def _get_or_create_points_row(user_id: int, db: Session) -> UserPoints:
    """Get or create a UserPoints row for the given user."""
    row = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if row:
        return row
    row = UserPoints(
        user_id=user_id,
        balance=0,
        lifetime_earned=0,
        lifetime_redeemed=0,
        loyalty_tier="bronze",
    )
    db.add(row)
    db.flush()
    return row


def _compute_loyalty_tier(lifetime_earned: int) -> str:
    """Return the tier name based on lifetime points earned."""
    for tier in LOYALTY_TIERS:
        if tier["max_lifetime"] is None and lifetime_earned >= tier["min_lifetime"]:
            return tier["name"]
        if tier["min_lifetime"] <= lifetime_earned <= tier["max_lifetime"]:
            return tier["name"]
    return "bronze"


def _get_tier_bonus_pct(tier_name: str) -> int:
    """Return the bonus percentage for the given tier."""
    for tier in LOYALTY_TIERS:
        if tier["name"] == tier_name:
            return tier["bonus_pct"]
    return 5


def _get_promotion_config(db: Session) -> PromotionEngineConfig:
    """Get the promotion engine config row (creates defaults if missing)."""
    return _get_promotion_config(db)


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


def get_points_balance(user_id: int, db: Session) -> dict:
    """Return the user's current points balance and loyalty info."""
    row = _get_or_create_points_row(user_id, db)
    return {
        "balance": row.balance,
        "lifetime_earned": row.lifetime_earned,
        "lifetime_redeemed": row.lifetime_redeemed,
        "loyalty_tier": row.loyalty_tier,
        "points_expire_at": row.points_expire_at.isoformat() if row.points_expire_at else None,
    }


def award_points_for_order(
    *,
    user_id: int,
    order_id: int,
    order_total: Decimal,
    db: Session,
) -> Optional[dict]:
    """Award points to a user based on their order total.

    Points formula: 1 point per 1 OMR spent, then multiplied by the
    loyalty tier bonus.  Only awarded once per order (caller should
    check that points were not already awarded).

    Returns the transaction dict or None if no points awarded.
    """
    config = _get_promotion_config(db)
    points_per_omr = getattr(config, "points_per_omr", 1) or 1

    if points_per_omr <= 0 or order_total <= 0:
        return None

    # Base points: floor(order_total) * points_per_omr
    base_points = int(float(order_total)) * points_per_omr
    if base_points <= 0:
        return None

    # Apply loyalty tier bonus
    row = _get_or_create_points_row(user_id, db)
    bonus_pct = _get_tier_bonus_pct(row.loyalty_tier)
    bonus_points = base_points * bonus_pct // 100
    total_points = base_points + bonus_points

    # Update balance
    row.balance += total_points
    row.lifetime_earned += total_points
    row.loyalty_tier = _compute_loyalty_tier(row.lifetime_earned)

    # Set expiry
    expiry_months = getattr(config, "points_expiry_months", 12) or 12
    if expiry_months > 0:
        row.points_expire_at = datetime.now(timezone.utc) + timedelta(days=expiry_months * 30)

    # Record transaction
    tx = PointsTransaction(
        user_id=user_id,
        points=total_points,
        transaction_type="earn_order",
        order_id=order_id,
        source_description=f"{base_points} base + {bonus_points} {row.loyalty_tier} bonus points",
        balance_after=row.balance,
    )
    db.add(tx)
    db.flush()

    logger.info(
        "Awarded %d points (base=%d bonus=%d tier=%s) for order %d user %d",
        total_points, base_points, bonus_points, row.loyalty_tier, order_id, user_id,
    )

    return {
        "points_awarded": total_points,
        "base_points": base_points,
        "bonus_points": bonus_points,
        "bonus_pct": bonus_pct,
        "loyalty_tier": row.loyalty_tier,
        "balance_after": row.balance,
    }


def award_referral_points(
    *,
    referrer_id: int,
    referee_id: int,
    db: Session,
    event_type: str = "earn_referral",
) -> Optional[dict]:
    """Award referral points to both referrer and referee.

    Points amounts come from the promotion engine config.
    Returns a dict with referrer and referee award details.
    """
    config = _get_promotion_config(db)
    referrer_points = getattr(config, "referral_referrer_points", 100) or 100
    referee_points = getattr(config, "referral_referee_points", 100) or 100

    if referrer_points <= 0 and referee_points <= 0:
        return None

    result = {}

    if referrer_points > 0:
        row = _get_or_create_points_row(referrer_id, db)
        row.balance += referrer_points
        row.lifetime_earned += referrer_points
        row.loyalty_tier = _compute_loyalty_tier(row.lifetime_earned)
        tx = PointsTransaction(
            user_id=referrer_id,
            points=referrer_points,
            transaction_type=event_type,
            source_description=f"Referral reward for referring user {referee_id}",
            balance_after=row.balance,
        )
        db.add(tx)
        result["referrer"] = {
            "user_id": referrer_id,
            "points": referrer_points,
            "balance_after": row.balance,
        }

    if referee_points > 0:
        row = _get_or_create_points_row(referee_id, db)
        row.balance += referee_points
        row.lifetime_earned += referee_points
        row.loyalty_tier = _compute_loyalty_tier(row.lifetime_earned)
        tx = PointsTransaction(
            user_id=referee_id,
            points=referee_points,
            transaction_type=event_type,
            source_description=f"Welcome bonus for being referred by user {referrer_id}",
            balance_after=row.balance,
        )
        db.add(tx)
        result["referee"] = {
            "user_id": referee_id,
            "points": referee_points,
            "balance_after": row.balance,
        }

    db.flush()
    logger.info("Awarded referral points: referrer=%s referee=%s", referrer_points, referee_points)
    return result if result else None


def redeem_points(
    *,
    user_id: int,
    points_to_redeem: int,
    order_id: Optional[int] = None,
    db: Session,
) -> dict:
    """Redeem points for a discount on an order.

    Returns the redemption result with the OMR value of the points.
    Conversion: configurable points_per_omr (default 1000 points = 1 OMR).
    """
    config = _get_promotion_config(db)
    min_redeem = getattr(config, "min_points_redeem", 1000) or 1000
    allow_partial = getattr(config, "allow_partial_points_redemption", True) or True
    per_omr = getattr(config, "points_per_omr", 1000) or 1000

    if not allow_partial and points_to_redeem < min_redeem:
        raise ValueError(f"Minimum redemption is {min_redeem} points")

    row = _get_or_create_points_row(user_id, db)
    if row.balance < points_to_redeem:
        raise ValueError(f"Insufficient points: have {row.balance}, need {points_to_redeem}")

    if points_to_redeem < min_redeem:
        raise ValueError(f"Minimum redemption is {min_redeem} points")

    omr_value = float(points_to_redeem) / float(per_omr)

    row.balance -= points_to_redeem
    row.lifetime_redeemed += points_to_redeem

    tx = PointsTransaction(
        user_id=user_id,
        points=-points_to_redeem,
        transaction_type="redeem",
        order_id=order_id,
        source_description=f"Redeemed {points_to_redeem} points for {omr_value:.3f} OMR",
        balance_after=row.balance,
    )
    db.add(tx)
    db.flush()

    return {
        "points_redeemed": points_to_redeem,
        "omr_value": round(omr_value, 3),
        "balance_after": row.balance,
    }


def get_points_transactions(
    user_id: int,
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Return the user's points transaction history."""
    rows = (
        db.query(PointsTransaction)
        .filter(PointsTransaction.user_id == user_id)
        .order_by(PointsTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": tx.id,
            "points": tx.points,
            "transaction_type": tx.transaction_type,
            "order_id": tx.order_id,
            "source_description": tx.source_description,
            "balance_after": tx.balance_after,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
        for tx in rows
    ]
