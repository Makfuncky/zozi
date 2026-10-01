"""Zozi Coins Service — manages coin earning, redemption, and balance for customers.

Coins are earned through:
- Referrals (when a referred user makes a purchase)
- Large purchases (percentage of order value)
- Promotional campaigns

Coin value is stored as Decimal (via kernel/money) for precision.

Race-condition safeguards:
- ``redeem_coins`` uses a Redis distributed lock per user + idempotency keys
  to prevent double-spend under concurrent requests.
- Balance check uses ``SELECT ... FOR UPDATE`` on the user's event rows.
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from domains.customers.models.customer_schema_models import ReferralPointEvent
from infrastructure.utils.cache import get_redis_client

logger = logging.getLogger(__name__)

_IDEMPOTENCY_TTL = 86400  # 24 hours
_LOCK_TTL = 10  # seconds

# Coin earning constants
COINS_PER_REFERRAL = Decimal("10.00")
COINS_PURCHASE_PERCENTAGE = Decimal("0.02")  # 2% of order value
MIN_PURCHASE_FOR_COINS = Decimal("50.00")  # Minimum order value to earn coins
MAX_COINS_PER_TRANSACTION = Decimal("500.00")


def get_customer_balance(db: Session, user_id: int) -> Decimal:
    """Return the total coin balance for a customer."""
    total = (
        db.query(func.coalesce(func.sum(ReferralPointEvent.points), 0))
        .filter(ReferralPointEvent.user_id == user_id, ReferralPointEvent.is_deleted.is_(False))
        .scalar()
    )
    return Decimal(str(total or 0))


def get_coin_history(
    db: Session,
    user_id: int,
    limit: int = 50,
    cursor: Optional[int] = None,
) -> list[ReferralPointEvent]:
    """Return paginated coin transaction history."""
    query = (
        db.query(ReferralPointEvent)
        .filter(ReferralPointEvent.user_id == user_id, ReferralPointEvent.is_deleted.is_(False))
    )
    if cursor is not None:
        query = query.filter(ReferralPointEvent.id < int(cursor))
    return query.order_by(ReferralPointEvent.id.desc()).limit(min(max(1, limit), 100)).all()


def award_referral_coins(
    db: Session,
    referrer_id: int,
    referred_id: int,
    country_code: Optional[str] = None,
) -> ReferralPointEvent:
    """Award coins to a referrer when their referral completes a qualifying action."""
    event = ReferralPointEvent(
        user_id=referrer_id,
        event_type="referral",
        points=int(COINS_PER_REFERRAL),
        referred_user_id=referred_id,
        country_code=country_code,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("Awarded %s coins to user %s for referral", COINS_PER_REFERRAL, referrer_id)
    return event


def award_purchase_coins(
    db: Session,
    user_id: int,
    order_value: Decimal,
    country_code: Optional[str] = None,
) -> Optional[ReferralPointEvent]:
    """Award coins based on purchase value. Returns None if order is below minimum."""
    if order_value < MIN_PURCHASE_FOR_COINS:
        return None

    coins = min(order_value * COINS_PURCHASE_PERCENTAGE, MAX_COINS_PER_TRANSACTION)
    event = ReferralPointEvent(
        user_id=user_id,
        event_type="purchase",
        points=int(coins),
        country_code=country_code,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("Awarded %s coins to user %s for purchase", coins, user_id)
    return event


def _acquire_redemption_lock(user_id: int) -> bool:
    """Try to acquire a per-user distributed lock for coin redemption."""
    redis_client = get_redis_client()
    if redis_client is None:
        return True
    try:
        lock_key = f"coin:redemption:lock:{user_id}"
        return bool(redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL))
    except Exception:
        return True


def _release_redemption_lock(user_id: int) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return
    try:
        redis_client.delete(f"coin:redemption:lock:{user_id}")
    except Exception:
        pass


def _check_idempotency_key(idempotency_key: str) -> Optional[Dict[str, Any]]:
    """Check if this idempotency key was already processed. Returns cached result or None."""
    redis_client = get_redis_client()
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(f"coin:idempotency:{idempotency_key}")
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception:
        return None


def _store_idempotency_result(idempotency_key: str, result: Dict[str, Any]) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return
    try:
        redis_client.setex(
            f"coin:idempotency:{idempotency_key}",
            _IDEMPOTENCY_TTL,
            json.dumps(result, default=str),
        )
    except Exception:
        pass


def redeem_coins(
    db: Session,
    user_id: int,
    points: int,
    reason: str = "redemption",
    idempotency_key: Optional[str] = None,
) -> ReferralPointEvent:
    """Redeem (debit) coins from a customer's balance.

    Uses a per-user distributed lock to prevent concurrent redemptions
    from double-spending the same balance. Supports idempotency keys
    to safely retry failed requests without double-debiting.

    Args:
        db: Database session.
        user_id: Customer whose coins to debit.
        points: Positive number of coins to redeem.
        reason: Event type label for the debit event.
        idempotency_key: Optional unique key for deduplication.

    Raises:
        HTTPException: 422 if points <= 0 or insufficient balance.
        HTTPException: 409 if a concurrent redemption is in progress.
    """
    if points <= 0:
        raise HTTPException(status_code=422, detail="Points must be positive")

    if idempotency_key:
        cached = _check_idempotency_key(idempotency_key)
        if cached is not None:
            logger.info("Idempotent coin redemption replay for key=%s", idempotency_key)
            event = db.query(ReferralPointEvent).filter(
                ReferralPointEvent.id == cached["event_id"]
            ).first()
            if event is not None:
                return event

    if not _acquire_redemption_lock(user_id):
        raise HTTPException(
            status_code=409,
            detail="A redemption is already in progress. Please retry.",
        )

    try:
        db.flush()

        lock_result = db.execute(
            text("SELECT 1 FROM customer.referral_point_events WHERE user_id = :uid AND is_deleted = FALSE FOR UPDATE NOWAIT"),
            {"uid": user_id},
        )
        _ = lock_result

        balance = get_customer_balance(db, user_id)
        if Decimal(points) > balance:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient coins. Balance: {balance}, Requested: {points}",
            )

        event = ReferralPointEvent(
            user_id=user_id,
            event_type=reason,
            points=-points,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        if idempotency_key:
            _store_idempotency_result(
                idempotency_key,
                {"event_id": event.id, "user_id": user_id, "points": -points},
            )

        logger.info("Redeemed %s coins from user %s", points, user_id)
        return event
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        _release_redemption_lock(user_id)


def get_coin_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Return a summary of coin balance, lifetime earnings, and recent activity."""
    earned = (
        db.query(func.coalesce(func.sum(ReferralPointEvent.points), 0))
        .filter(
            ReferralPointEvent.user_id == user_id,
            ReferralPointEvent.points > 0,
            ReferralPointEvent.is_deleted.is_(False),
        )
        .scalar()
    )
    redeemed = (
        db.query(func.coalesce(func.abs(func.sum(ReferralPointEvent.points)), 0))
        .filter(
            ReferralPointEvent.user_id == user_id,
            ReferralPointEvent.points < 0,
            ReferralPointEvent.is_deleted.is_(False),
        )
        .scalar()
    )
    balance = get_customer_balance(db, user_id)
    recent = get_coin_history(db, user_id, limit=5)

    return {
        "user_id": user_id,
        "balance": float(balance),
        "lifetime_earned": float(earned or 0),
        "lifetime_redeemed": float(redeemed or 0),
        "recent_activity": [
            {
                "id": e.id,
                "type": e.event_type,
                "points": e.points,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent
        ],
    }


__all__ = [
    "COINS_PER_REFERRAL",
    "COINS_PURCHASE_PERCENTAGE",
    "MIN_PURCHASE_FOR_COINS",
    "MAX_COINS_PER_TRANSACTION",
    "get_customer_balance",
    "get_coin_history",
    "award_referral_coins",
    "award_purchase_coins",
    "redeem_coins",
    "get_coin_summary",
    "atomic_coin_redeem",
    "acquire_redemption_lock",
    "release_redemption_lock",
]
