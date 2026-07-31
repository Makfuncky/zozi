"""Commission write service — DB write operations for commission-related entities."""

from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    ProductCommissionOverride,
)


def create_commission_category_rate(db: Session, **rate_data) -> CommissionCategoryRate:
    rate = CommissionCategoryRate(**rate_data)
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def create_commission_badge_tier(db: Session, **tier_data) -> CommissionBadgeTier:
    tier = CommissionBadgeTier(**tier_data)
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def create_commission_agreement(
    db: Session,
    supplier_id: int,
    rate: Decimal,
    effective_from: datetime,
    effective_to: datetime | None,
    is_active: bool,
    set_by_admin_id: int,
    note: str | None,
) -> CommissionAgreement:
    agreement = CommissionAgreement(
        supplier_id=supplier_id,
        rate=rate,
        effective_from=effective_from,
        effective_to=effective_to,
        is_active=is_active,
        set_by_admin_id=set_by_admin_id,
        note=note,
    )
    db.add(agreement)
    db.commit()
    db.refresh(agreement)
    return agreement


def delete_commission_agreement(db: Session, agreement: CommissionAgreement) -> None:
    db.delete(agreement)
    db.commit()


def create_product_commission_override(
    db: Session,
    product_id: int,
    supplier_id: int,
    rate_percent: Decimal,
    is_active: bool,
    set_by_admin_id: int,
) -> ProductCommissionOverride:
    override = ProductCommissionOverride(
        product_id=product_id,
        supplier_id=supplier_id,
        rate_percent=rate_percent,
        is_active=is_active,
        set_by_admin_id=set_by_admin_id,
    )
    db.add(override)
    db.flush()
    override_id = override.id
    db.commit()
    return override


def update_product_commission_override(
    db: Session,
    override: ProductCommissionOverride,
    updates: dict,
) -> ProductCommissionOverride:
    for key, value in updates.items():
        setattr(override, key, value)
    db.commit()
    db.refresh(override)
    return override


def delete_product_commission_override(db: Session, override: ProductCommissionOverride) -> None:
    db.delete(override)
    db.commit()


def update_commission_global_config(
    db: Session,
    config: CommissionGlobalConfig,
    updates: dict,
) -> CommissionGlobalConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def update_commission_category_rate(
    db: Session,
    row: CommissionCategoryRate,
    updates: dict,
) -> CommissionCategoryRate:
    for key, value in updates.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def update_commission_badge_tier(
    db: Session,
    row: CommissionBadgeTier,
    updates: dict,
) -> CommissionBadgeTier:
    for key, value in updates.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def update_commission_ledger_entry(
    db: Session,
    entry: CommissionLedgerEntry,
    updates: dict,
) -> CommissionLedgerEntry:
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry