"""Commission write operations (canonical module).

Implements the commission domain write surface. Previously stubbed with
``_missing_symbol`` placeholders after a refactor; now contains the real
DB-write logic, consistent with the platform contract (``data.models``,
soft-delete via ``utils.soft_delete``).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    ProductCommissionOverride,
)
from utils.soft_delete import soft_delete
import structlog
logger = structlog.get_logger(__name__)


def apply_changes(record, changes: dict) -> None:
    for key, value in changes.items():
        if value is not None:
            setattr(record, key, value)


def _resolve_and_update(db: Session, model, record_or_id, changes, label: str):
    """Update ``record_or_id`` (an ORM instance or its integer id) with ``changes``.

    Accepts both the keyword form (``rate_id=..., **changes``) used by some
    callers and the positional form (``row, updates``) used by the controllers.
    """
    merged = dict(changes or {})
    if isinstance(record_or_id, int):
        obj = db.get(model, record_or_id)
    else:
        obj = record_or_id
    if obj is None:
        raise ValueError(f"{label} {record_or_id} not found")
    apply_changes(obj, merged)
    db.commit()
    db.refresh(obj)
    return obj


def create_commission_agreement(
    db: Session,
    *,
    supplier_id: int,
    tier: str,
    rate: float,
    country_code: str | None = None,
    set_by_admin_id: int | None = None,
    is_active: bool = True,
    effective_from=None,
    effective_to=None,
    note: str | None = None,
) -> CommissionAgreement:
    obj = CommissionAgreement(
        supplier_id=supplier_id,
        tier=tier,
        rate=rate,
        country_code=country_code,
        set_by_admin_id=set_by_admin_id,
        is_active=is_active,
        effective_from=effective_from,
        effective_to=effective_to,
        note=note,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_product_commission_override(
    db: Session,
    *,
    product_id: int,
    supplier_id: int,
    rate_percent: float,
    set_by_admin_id: int | None = None,
    is_active: bool = True,
    country_code: str | None = None,
) -> ProductCommissionOverride:
    obj = ProductCommissionOverride(
        product_id=product_id,
        supplier_id=supplier_id,
        rate_percent=rate_percent,
        set_by_admin_id=set_by_admin_id,
        is_active=is_active,
        country_code=country_code,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_commission_badge_tier(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionBadgeTier:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionBadgeTier, record_or_id, merged, "CommissionBadgeTier")


def update_commission_category_rate(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionCategoryRate:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionCategoryRate, record_or_id, merged, "CommissionCategoryRate")


def update_commission_global_config(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionGlobalConfig:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionGlobalConfig, record_or_id, merged, "CommissionGlobalConfig")


def update_commission_ledger_entry(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionLedgerEntry:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionLedgerEntry, record_or_id, merged, "CommissionLedgerEntry")


def update_product_commission_override(db: Session, record_or_id, changes: dict | None = None, **kw) -> ProductCommissionOverride:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, ProductCommissionOverride, record_or_id, merged, "ProductCommissionOverride")


def delete_product_commission_override(db: Session, override: ProductCommissionOverride) -> None:
    """Hard-delete a product-level commission override (revert to supplier agreement)."""
    db.delete(override)
    db.commit()


def delete_commission_agreement(db: Session, agreement_id: int, acting_user: int | None = None, reason: str | None = None) -> None:
    soft_delete(db, CommissionAgreement, agreement_id, acting_user, reason=reason)
