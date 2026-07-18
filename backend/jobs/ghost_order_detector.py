from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from db.database import SessionLocal
from db.models import Order, ProcessedWebhookEvent

logger = logging.getLogger(__name__)


def detect_ghost_orders(lookback_hours: int = 24) -> list[dict]:
    """Find orders marked as 'paid' without a corresponding webhook event.

    This detects:
    - Orders where status was manually set to 'paid' via direct API/SQL
    - Frontend glitches that bypassed proper payment verification
    - Database-level manipulation

    Returns a list of ghost order dicts for investigation.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=lookback_hours)

        ghost_orders = (
            db.query(Order)
            .filter(
                Order.status == "paid",
                Order.paid_at >= cutoff,
            )
            .all()
        )

        findings: list[dict] = []
        for order in ghost_orders:
            payment_intent_id = getattr(order, "payment_intent_id", None) or getattr(order, "stripe_payment_intent_id", None)
            if not payment_intent_id:
                is_ghost = True
            else:
                has_webhook = db.query(ProcessedWebhookEvent).filter(
                    ProcessedWebhookEvent.event_id == payment_intent_id,
                    ProcessedWebhookEvent.processor.in_(["stripe", "tap", "paypal", "thawani", "paytabs"]),
                ).first()
                is_ghost = has_webhook is None

            if is_ghost:
                findings.append({
                    "order_id": getattr(order, "id", None),
                    "order_uuid": getattr(order, "uuid", None),
                    "amount": float(getattr(order, "total_amount", 0) or 0),
                    "paid_at": str(getattr(order, "paid_at", "")),
                    "payment_intent_id": payment_intent_id,
                    "user_id": getattr(order, "user_id", None),
                    "country": getattr(order, "shipping_country", None),
                })

                logger.warning(
                    "GHOST ORDER DETECTED: order_id=%s payment_intent=%s amount=%s",
                    getattr(order, "id", None),
                    payment_intent_id,
                    getattr(order, "total_amount", 0),
                )

                setattr(order, "status", "pending_payment")
                db.commit()
                logger.info("Order %s reverted to pending_payment", getattr(order, "id", None))

        return findings

    except Exception as exc:
        logger.error("Ghost order detector error: %s", exc)
        db.rollback()
        return []
    finally:
        db.close()

