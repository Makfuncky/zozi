"""Admin treasury read service (Treasury domain).

Owns the DB reads (Q1) that were previously inline in ``routers.admin_treasury_governance``.
The router keeps building ``select()`` statements and column-expression filters
(these never reference the session), and this module only *executes* them so the
router no longer calls ``db.query()`` / ``db.execute()`` directly.

Generic helpers:
  * ``run_scalar`` / ``run_scalars`` / ``run_rows`` execute a pre-built
    ``select()`` statement (router builds it) and return the raw result.
  * ``list_model`` / ``count_model`` / ``first_model`` build + run a
    ``db.query(model)`` from column-expression ``filters`` supplied by the
    router (no session reference in the router).
  * ``scalar_sum`` returns ``coalesce(sum(column), 0)`` for simple filtered sums.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import CashFlowForecast
from domains.finance.models.finance import GatewaySettlementSchedule
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TreasuryAccount
from domains.finance.models.finance import VATRemittance
from domains.logistics.models.logistics import Shipment
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.hr.ports import Employee
from domains.logistics.models.logistics import LogisticsPartner
from domains.orders.models.orders import Order as OrderModel
from domains.orders.models.orders import OrderItem
from domains.payments.models.payments import LogisticsPartnerPayout
from domains.payments.models.payments import Payment
from domains.payments.models.payments import Payout
from domains.comms.models.suppliers import SupplierProfile
import structlog
logger = structlog.get_logger(__name__)


# ── select()-statement executors (router builds the statement) ───────────────

def run_scalar(db: Session, stmt):
    """Execute a ``select()`` and return its scalar() result."""
    return db.execute(stmt).scalar()


def run_scalars(db: Session, stmt, unique: bool = False) -> list:
    """Execute a ``select()`` and return ``scalars().all()`` (optionally unique)."""
    result = db.execute(stmt)
    if unique:
        result = result.unique()
    return result.scalars().all()


def run_rows(db: Session, stmt) -> list:
    """Execute a ``select()`` and return ``.all()`` (row/tuple results)."""
    return db.execute(stmt).all()


# ── db.query(model) executors driven by column-expression filters ───────────

def list_model(
    db: Session,
    model,
    filters: Sequence = (),
    order_by=None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> list:
    q = db.query(model)
    for f in filters:
        q = q.filter(f)
    if order_by is not None:
        q = q.order_by(order_by)
    if offset is not None:
        q = q.offset(offset)
    if limit is not None:
        q = q.limit(limit)
    return q.all()


def count_model(db: Session, model, filters: Sequence = ()) -> int:
    q = db.query(model)
    for f in filters:
        q = q.filter(f)
    return q.count()


def first_model(db: Session, model, filters: Sequence = ()) -> Optional[Any]:
    q = db.query(model)
    for f in filters:
        q = q.filter(f)
    return q.first()


def scalar_sum(db: Session, column, filters: Sequence = ()) -> Decimal:
    q = db.query(func.coalesce(func.sum(column), 0))
    for f in filters:
        q = q.filter(f)
    return q.scalar() or Decimal("0")
