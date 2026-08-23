"""payments domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.payments.models`` or ``domains.payments.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.payments.models.payments import Banner, Coupon, LogisticsPartnerPayout, Payment, PaymentGatewayConnection, PaymentReconciliationRun, Payout


def get_payment_by_id(db: Session, id_: int) -> Optional[Payment]:
    """Return Payment by primary key (or None)."""
    return db.get(Payment, id_)

def list_payments(db: Session, limit: int = 100) -> List[Payment]:
    """Return up to ``limit`` Payment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Payment, db, limit)

def list_payments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Payment rows (scale-ready)."""
    return _keyset_page(Payment, db, cursor, page_size)

def get_payment_reconciliation_run_by_id(db: Session, id_: int) -> Optional[PaymentReconciliationRun]:
    """Return PaymentReconciliationRun by primary key (or None)."""
    return db.get(PaymentReconciliationRun, id_)

def list_payment_reconciliation_runs(db: Session, limit: int = 100) -> List[PaymentReconciliationRun]:
    """Return up to ``limit`` PaymentReconciliationRun rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PaymentReconciliationRun, db, limit)

def list_payment_reconciliation_runs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PaymentReconciliationRun rows (scale-ready)."""
    return _keyset_page(PaymentReconciliationRun, db, cursor, page_size)

def get_coupon_by_id(db: Session, id_: int) -> Optional[Coupon]:
    """Return Coupon by primary key (or None)."""
    return db.get(Coupon, id_)

def list_coupons(db: Session, limit: int = 100) -> List[Coupon]:
    """Return up to ``limit`` Coupon rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Coupon, db, limit)

def list_coupons_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Coupon rows (scale-ready)."""
    return _keyset_page(Coupon, db, cursor, page_size)

def get_banner_by_id(db: Session, id_: int) -> Optional[Banner]:
    """Return Banner by primary key (or None)."""
    return db.get(Banner, id_)

def list_banners(db: Session, limit: int = 100) -> List[Banner]:
    """Return up to ``limit`` Banner rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Banner, db, limit)

def list_banners_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Banner rows (scale-ready)."""
    return _keyset_page(Banner, db, cursor, page_size)

def get_payment_gateway_connection_by_id(db: Session, id_: int) -> Optional[PaymentGatewayConnection]:
    """Return PaymentGatewayConnection by primary key (or None)."""
    return db.get(PaymentGatewayConnection, id_)

def list_payment_gateway_connections(db: Session, limit: int = 100) -> List[PaymentGatewayConnection]:
    """Return up to ``limit`` PaymentGatewayConnection rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PaymentGatewayConnection, db, limit)

def list_payment_gateway_connections_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PaymentGatewayConnection rows (scale-ready)."""
    return _keyset_page(PaymentGatewayConnection, db, cursor, page_size)

def get_payout_by_id(db: Session, id_: int) -> Optional[Payout]:
    """Return Payout by primary key (or None)."""
    return db.get(Payout, id_)

def list_payouts(db: Session, limit: int = 100) -> List[Payout]:
    """Return up to ``limit`` Payout rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Payout, db, limit)

def list_payouts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Payout rows (scale-ready)."""
    return _keyset_page(Payout, db, cursor, page_size)

def get_logistics_partner_payout_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerPayout]:
    """Return LogisticsPartnerPayout by primary key (or None)."""
    return db.get(LogisticsPartnerPayout, id_)

def list_logistics_partner_payouts(db: Session, limit: int = 100) -> List[LogisticsPartnerPayout]:
    """Return up to ``limit`` LogisticsPartnerPayout rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartnerPayout, db, limit)

def list_logistics_partner_payouts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartnerPayout rows (scale-ready)."""
    return _keyset_page(LogisticsPartnerPayout, db, cursor, page_size)


# --- Query delegation (Law 3 sanctioned cross-domain query surface) ---
# Other domains call these instead of importing models directly.

def payout_query(db: Session) -> object:
    """Return a base ``Payout`` query for sanctioned cross-domain delegation."""
    return db.query(Payout)

def payment_query(db: Session) -> object:
    """Return a base ``Payment`` query for sanctioned cross-domain delegation."""
    return db.query(Payment)

def logistics_partner_payout_query(db: Session) -> object:
    """Return a base ``LogisticsPartnerPayout`` query for sanctioned cross-domain delegation."""
    return db.query(LogisticsPartnerPayout)

def payment_gateway_connection_query(db: Session) -> object:
    """Return a base ``PaymentGatewayConnection`` query for sanctioned cross-domain delegation."""
    return db.query(PaymentGatewayConnection)

def payment_reconciliation_run_query(db: Session) -> object:
    """Return a base ``PaymentReconciliationRun`` query for sanctioned cross-domain delegation."""
    return db.query(PaymentReconciliationRun)


# --- Model class references (for column access in cross-domain filters) ---

def payout_model() -> type:
    """Return the ``Payout`` model class (for column reference only)."""
    return Payout


def payment_model() -> type:
    """Return the ``Payment`` model class (for column reference only)."""
    return Payment


def logistics_partner_payout_model() -> type:
    """Return the ``LogisticsPartnerPayout`` model class (for column reference only)."""
    return LogisticsPartnerPayout


def payment_gateway_connection_model() -> type:
    """Return the ``PaymentGatewayConnection`` model class (for column reference only)."""
    return PaymentGatewayConnection


# --- P11 re-exports (Law 3 sanctioned read/behavior surface) ---
from domains.payments.models.payments import Banner, Coupon, LogisticsPartnerPayout, Payment
# --- P11.5 re-exports (orders cross-domain repointing) ---
from domains.payments.services.payments import (
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    is_checkout_payment_method_allowed,
    normalize_checkout_payment_method,
    _order_holds_inventory,
)
from domains.payments.services.payments import _apply_stripe_runtime_key
