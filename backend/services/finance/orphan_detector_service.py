"""Orphan Detector Service — detect missing journal entries for finance reconciliation.

This service detects orders that lack corresponding journal entries in the GL.
Moved from treasury_engine to finance domain as it's finance reconciliation functionality.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from data.models import JournalEntry, Order


def run_orphan_detector(db: Session, country_code: Optional[str] = None) -> list[dict]:
    """Daily cron: scan orders for missing journal entries.

    Flags any delivered/paid order that lacks a corresponding
    JournalEntry with matching reference_type/reference_id.
    """
    alerts = []

    query_filter = [Order.status.in_(["delivered", "completed"])]
    if country_code:
        query_filter.append(Order.country_code == country_code)

    delivered_orders = db.execute(
        select(Order).where(
            *query_filter,
            ~Order.id.in_(
                select(JournalEntry.reference_id).where(
                    JournalEntry.reference_type == "order_delivery",
                    JournalEntry.reference_id.isnot(None),
                )
            ),
        )
    ).scalars().all()

    for o in delivered_orders:
        alerts.append({
            "type": "missing_delivery_entry",
            "order_id": o.id,
            "order_number": o.order_number,
            "country_code": o.country_code,
            "severity": "critical",
        })

    payment_filter = [Order.payment_status.in_(["paid", "captured"])]
    if country_code:
        payment_filter.append(Order.country_code == country_code)

    paid_orders = db.execute(
        select(Order).where(
            *payment_filter,
            ~Order.id.in_(
                select(JournalEntry.reference_id).where(
                    JournalEntry.reference_type == "order_payment",
                    JournalEntry.reference_id.isnot(None),
                )
            ),
        )
    ).scalars().all()

    for o in paid_orders:
        alerts.append({
            "type": "missing_payment_entry",
            "order_id": o.id,
            "order_number": o.order_number,
            "country_code": o.country_code,
            "severity": "high",
        })

    return alerts