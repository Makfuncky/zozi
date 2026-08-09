"""Admin Treasury write orchestration controller.

Thin delegation layer between ``routers.admin_treasury_governance`` and
``services.treasury.admin_treasury_write_service``. It owns the request-scoped
concerns (country existence check + RLS context window) and contains **no** DB
write verbs itself — every mutation lives in the service (W1 contract).

``HTTPException`` raised by the service propagates untouched so the HTTP
status codes the frontend relies on are preserved.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from services.treasury.admin_treasury_write_service import (
    approve_payout_batch as _approve_payout_batch,
)
from services.treasury.admin_treasury_write_service import (
    approve_settlement as _approve_settlement,
)
from services.treasury.admin_treasury_write_service import (
    dispatch_payout_batch as _dispatch_payout_batch,
)
from services.treasury.admin_treasury_write_service import (
    generate_payout_batch as _generate_payout_batch,
)
from services.treasury.admin_treasury_write_service import (
    record_cod_remittance as _record_cod_remittance,
)
from services.treasury.admin_treasury_write_service import (
    settle_supplier as _settle_supplier,
)
from services.treasury.admin_treasury_write_service import (
    snapshot_cash_position as _snapshot_cash_position,
)
from utils.country_access import get_country_or_404
from utils.rls_interceptor import clear_rls_context, set_rls_context
import structlog
logger = structlog.get_logger(__name__)


# ── Payout Batches (global scope) ──────────────────────────────────────


def generate_payout_batch(country_code: str, cutoff_date: date, current_user: dict, db) -> dict:
    return _generate_payout_batch(
        db,
        country_code=country_code,
        cutoff_date=cutoff_date,
        created_by=current_user.get("id"),
    )


def approve_payout_batch(batch_id: int, current_user: dict, db) -> dict:
    return _approve_payout_batch(db, batch_id=batch_id, actor_id=current_user.get("id"))


def dispatch_payout_batch(batch_id: int, current_user: dict, db) -> dict:
    return _dispatch_payout_batch(db, batch_id=batch_id, actor_id=current_user.get("id"))


# ── Cash Position Snapshot ─────────────────────────────────────────────


def snapshot_cash_position(current_user: dict, db) -> dict:
    return _snapshot_cash_position(db)


# ── Reconciliation (country scoped) ────────────────────────────────────


def record_cod_remittance(
    country_code: str,
    order_id: int,
    partner_id: int,
    amount: float,
    bank_reference: str,
    current_user: dict,
    db,
) -> dict:
    cc = country_code.upper()
    get_country_or_404(cc, db)
    set_rls_context({cc}, is_restricted=True)
    try:
        return _record_cod_remittance(
            db,
            country_code=cc,
            order_id=order_id,
            partner_id=partner_id,
            amount=amount,
            bank_reference=bank_reference,
        )
    finally:
        clear_rls_context()


def settle_supplier(
    country_code: str,
    order_id: int,
    supplier_id: int,
    net_amount: float,
    current_user: dict,
    db,
    gross_amount: Optional[float] = None,
    commission_amount: Optional[float] = None,
    currency: Optional[str] = None,
    payout_id: Optional[int] = None,
) -> dict:
    cc = country_code.upper()
    get_country_or_404(cc, db)
    set_rls_context({cc}, is_restricted=True)
    try:
        return _settle_supplier(
            db,
            country_code=cc,
            order_id=order_id,
            supplier_id=supplier_id,
            net_amount=net_amount,
            gross_amount=gross_amount,
            commission_amount=commission_amount,
            currency=currency,
            payout_id=payout_id,
        )
    finally:
        clear_rls_context()


def approve_settlement(country_code: str, settlement_id: int, current_user: dict, db) -> dict:
    cc = country_code.upper()
    get_country_or_404(cc, db)
    set_rls_context({cc}, is_restricted=True)
    try:
        return _approve_settlement(db, country_code=cc, settlement_id=settlement_id)
    finally:
        clear_rls_context()


__all__: list[str] = [
    "approve_payout_batch",
    "approve_settlement",
    "dispatch_payout_batch",
    "generate_payout_batch",
    "record_cod_remittance",
    "settle_supplier",
    "snapshot_cash_position",
]
