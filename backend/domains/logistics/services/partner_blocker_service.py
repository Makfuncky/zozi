"""Partner delete-precondition checks.

Relocated from ``controllers/logistics/logistics_partner_controller.py`` so the
raw SQL execution stays in the service layer (architectural W1 fix).
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    LogisticsCODRemittanceReceipt,
    LogisticsPartnerBankAccount,
    LogisticsPartnerPayout,
    LogisticsSettlement,
    Order,
    OrderLogisticsAllocation,
    Shipment,
    TransactionLedger,
)
import structlog
logger = structlog.get_logger(__name__)

_PARTNER_DELETE_BLOCKING_MODELS: list[tuple[Any, Any, str]] = [
    (LogisticsSettlement, LogisticsSettlement.partner_id, "logistics settlement record(s)"),
    (LogisticsPartnerPayout, LogisticsPartnerPayout.partner_id, "partner payout record(s)"),
    (LogisticsCODRemittanceReceipt, LogisticsCODRemittanceReceipt.partner_id, "COD remittance receipt(s)"),
    (TransactionLedger, TransactionLedger.logistics_partner_id, "transaction ledger record(s)"),
    (OrderLogisticsAllocation, OrderLogisticsAllocation.partner_id, "order logistics allocation(s)"),
    (Shipment, Shipment.assigned_partner_id, "shipment assignment(s)"),
    (Order, Order.selected_partner_id, "order quote selection(s)"),
    (LogisticsPartnerBankAccount, LogisticsPartnerBankAccount.partner_id, "partner bank account record(s)"),
]


def build_partner_delete_blocker(partner_id: int, db: Session) -> Optional[tuple[int, str]]:
    """Return (status_code, message) if the partner cannot be deleted, else None."""
    count_columns = [
        select(func.count())
        .select_from(model)
        .where(column == partner_id)
        .correlate(None)
        .scalar_subquery()
        for model, column, _label in _PARTNER_DELETE_BLOCKING_MODELS
    ]
    if not count_columns:
        return None
    related_counts = db.execute(select(*count_columns)).one()
    for (_model, _column, label), raw_count in zip(_PARTNER_DELETE_BLOCKING_MODELS, related_counts):
        related_count = raw_count or 0
        if related_count > 0:
            return 409, f"Partner has {related_count} {label}. Suspend the partner instead of deleting."
    return None
