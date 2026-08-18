"""Promotion engine write operations.

Persistence layer for promotion engine configuration, order tiers and ledger
entries. No controller imports, keeping the dependency graph acyclic.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.governance.models.admin import PromotionEngineConfig
from domains.governance.models.admin import PromotionLedgerEntry
from domains.governance.models.admin import PromotionOrderTier
from infrastructure.utils.soft_delete import soft_delete
import structlog
logger = structlog.get_logger(__name__)


def _apply_updates(row, updates: dict) -> None:
    for key, value in updates.items():
        if hasattr(row, key):
            setattr(row, key, value)


def create_promotion_ledger_entry(
    db: Session,
    *,
    order_id: Optional[int],
    user_id: Optional[int],
    tier: PromotionOrderTier,
    discount_amount: Any,
) -> PromotionLedgerEntry:
    entry = PromotionLedgerEntry(
        order_id=order_id,
        user_id=user_id,
        amount=discount_amount,
        entry_type="order_tier",
        promotion_id=getattr(tier, "id", None),
        country_code=getattr(tier, "country_code", None),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_promotion_order_tier(
    db: Session,
    *,
    tier_name: str,
    min_order_amount: Any,
    max_order_amount: Optional[Any],
    discount_type: str,
    discount_value: Any,
    stacking_allowed: bool = False,
    is_active: bool = True,
    sort_order: Optional[int] = 0,
    updated_by: Optional[int] = None,
) -> PromotionOrderTier:
    tier = PromotionOrderTier(
        tier_name=tier_name,
        min_order_amount=min_order_amount,
        max_order_amount=max_order_amount,
        discount_type=discount_type,
        discount_value=discount_value,
        stacking_allowed=stacking_allowed,
        is_active=is_active,
        sort_order=sort_order,
        updated_by=updated_by,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def update_promotion_order_tier(
    db: Session, row: PromotionOrderTier, updates: dict
) -> PromotionOrderTier:
    _apply_updates(row, updates)
    db.commit()
    db.refresh(row)
    return row


def delete_promotion_order_tier(db: Session, row: PromotionOrderTier) -> None:
    soft_delete(db, PromotionOrderTier, row.id, None, skip_audit=True)


def update_promotion_engine_config(
    db: Session, row: PromotionEngineConfig, updates: dict
) -> PromotionEngineConfig:
    _apply_updates(row, updates)
    db.commit()
    db.refresh(row)
    return row
