"""
Commission Engine Service.
Core commission calculation logic for supplier product sales.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, NamedTuple

from sqlalchemy.orm import Session

from data.models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    ProductCommissionOverride,
    Product,
    SupplierProfile,
)
from utils.audit_log import AuditAction, audit_log
from data.services_write_helpers import commit_and_refresh

logger = logging.getLogger(__name__)

_DEFAULT_RATE = Decimal("0.1500")
_LOW_VALUE_THRESHOLD = Decimal("5.00")
_FIXED_CAP_AMOUNT = Decimal("0.50")


class RateResult(NamedTuple):
    applied_rate: Decimal
    supplier_rate: Decimal
    supplier_rate_source: str
    badge_level: Optional[str]
    global_default_rate: Decimal
    category_base_rate: Decimal
    product_override_rate: Optional[Decimal]
    cap_applied: bool
    commission_amount: Decimal
    low_value_threshold_used: Optional[float]
    fixed_cap_used: Optional[float]
    override_flag: bool
    is_adjusted: bool
    adjusted_by: Optional[int]
    adjusted_at: Optional[datetime]
    adjustment_reason: Optional[str]
    original_commission_amount: Optional[Decimal]
    currency: str
    created_at: datetime


def get_global_config(db: Session) -> CommissionGlobalConfig:
    config = db.query(CommissionGlobalConfig).order_by(CommissionGlobalConfig.id.desc()).first()
    if not config:
        config = seed_defaults(db)
    return config


def seed_defaults(db: Session) -> CommissionGlobalConfig:
    existing = db.query(CommissionGlobalConfig).first()
    if existing:
        return existing
    
    config = CommissionGlobalConfig(
        default_rate=_DEFAULT_RATE,
        low_value_threshold=_LOW_VALUE_THRESHOLD,
        fixed_cap_amount=_FIXED_CAP_AMOUNT,
        fixed_cap_enabled=True,
        margin_protection_enabled=False,
        margin_threshold=Decimal("0.10"),
        updated_by=None,
    )
    db.add(config)
    commit_and_refresh(db, config)
    
    category = CommissionCategoryRate(
        category_slug="general",
        category_display_name="General",
        rate=Decimal("0.0500"),
        is_active=True,
        country_code=None,
        updated_by=None,
    )
    db.add(category)
    commit_and_refresh(db, category)
    
    for tier_data in [
        {"badge_level": "bronze", "commission_rate": Decimal("0.08"), "sort_order": 1},
        {"badge_level": "silver", "commission_rate": Decimal("0.06"), "sort_order": 2},
        {"badge_level": "gold", "commission_rate": Decimal("0.04"), "sort_order": 3},
        {"badge_level": "platinum", "commission_rate": Decimal("0.02"), "sort_order": 4},
    ]:
        tier = CommissionBadgeTier(**tier_data)
        db.add(tier)
    commit_and_refresh(db, CommissionBadgeTier)
    
    audit_log(
        db=db, action=AuditAction.SYSTEM_SETUP,
        user_id=None, username=None, user_role="system",
        resource_type="commission_global_config", resource_id=config.id,
        details={"action": "seed_defaults"}, status="success",
    )
    
    return config


def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int],
    category_slug: Optional[str],
    db: Session,
    order_value: Optional[float] = None,
    currency: str = "OMR",
) -> RateResult:
    config = get_global_config(db)
    
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    badge_level = supplier.badge_level if supplier else None
    
    supplier_rate = _get_supplier_rate(supplier_id, badge_level, db)
    supplier_rate_source = "badge_tier" if supplier_rate else "default"
    
    category_base_rate = _get_category_rate(category_slug, db)
    
    product_override = None
    if product_id:
        product_override = _get_product_override(product_id, db)
    
    global_default = config.default_rate or _DEFAULT_RATE
    
    if product_override_rate := product_override:
        base_rate = product_override_rate
    elif category_base_rate:
        base_rate = category_base_rate
    else:
        base_rate = global_default
    
    total_base = base_rate
    supplier_component = supplier_rate if supplier_rate else global_default * Decimal("0.5")
    applied_rate = total_base + supplier_component
    
    applied_rate = min(applied_rate, Decimal("0.90"))
    
    cap_applied = False
    cap_used = None
    commission_amount = Decimal("0")
    original_commission = None
    low_value_threshold_used = None
    fixed_cap_used = None
    
    if order_value is not None:
        order_val = Decimal(str(order_value))
        original_commission = applied_rate * order_val
        original_commission = original_commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        if config.low_value_threshold and order_val < config.low_value_threshold:
            low_value_threshold_used = float(order_val)
            fixed_cap = config.fixed_cap_amount or _FIXED_CAP_AMOUNT
            commission_amount = min(original_commission, fixed_cap)
            cap_applied = True
        else:
            commission_amount = original_commission
        
        fixed_cap_used = None
    
    override_flag = product_override is not None or category_slug is None
    
    return RateResult(
        applied_rate=applied_rate,
        supplier_rate=supplier_rate if supplier_rate else Decimal("0"),
        supplier_rate_source=supplier_rate_source,
        badge_level=badge_level,
        global_default_rate=global_default,
        category_base_rate=category_base_rate or Decimal("0"),
        product_override_rate=product_override,
        cap_applied=cap_applied,
        commission_amount=commission_amount,
        low_value_threshold_used=low_value_threshold_used,
        fixed_cap_used=fixed_cap_used,
        override_flag=override_flag,
        is_adjusted=False,
        adjusted_by=None,
        adjusted_at=None,
        adjustment_reason=None,
        original_commission_amount=original_commission,
        currency=currency,
        created_at=datetime.now(timezone.utc),
    )


def _get_supplier_rate(supplier_id: int, badge_level: Optional[str], db: Session) -> Optional[Decimal]:
    agreement = db.query(CommissionAgreement).filter(
        CommissionAgreement.supplier_id == supplier_id,
        CommissionAgreement.is_active == True,
    ).first()
    
    if agreement and agreement.commission_rate:
        return agreement.commission_rate
    
    if badge_level:
        tier = db.query(CommissionBadgeTier).filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,
        ).first()
        if tier and tier.commission_rate:
            return tier.commission_rate
    
    return None


def _get_category_rate(category_slug: Optional[str], db: Session) -> Optional[Decimal]:
    if not category_slug:
        return Decimal("0.0500")
    
    rate = db.query(CommissionCategoryRate).filter(
        CommissionCategoryRate.category_slug == category_slug,
        CommissionCategoryRate.is_active == True,
    ).first()
    
    return rate.rate if rate else None


def _get_product_override(product_id: int, db: Session) -> Optional[Decimal]:
    override = db.query(ProductCommissionOverride).filter(
        ProductCommissionOverride.product_id == product_id,
        ProductCommissionOverride.is_active == True,
    ).first()
    
    return override.base_rate if override else None


def preview_commission(
    supplier_id: int,
    order_value: float,
    category_slug: Optional[str],
    db: Session,
    currency: str = "OMR",
) -> dict:
    result = get_effective_rate(
        supplier_id=supplier_id,
        product_id=None,
        category_slug=category_slug,
        db=db,
        order_value=order_value,
        currency=currency,
    )
    
    return {
        "applied_rate": float(result.applied_rate),
        "supplier_rate": float(result.supplier_rate),
        "badge_level": result.badge_level,
        "global_default_rate": float(result.global_default_rate),
        "category_base_rate": float(result.category_base_rate),
        "cap_applied": result.cap_applied,
        "commission_amount": float(result.commission_amount),
        "low_value_threshold_used": result.low_value_threshold_used,
        "fixed_cap_used": result.fixed_cap_used,
        "currency": result.currency,
        "preview_at": result.created_at.isoformat(),
    }