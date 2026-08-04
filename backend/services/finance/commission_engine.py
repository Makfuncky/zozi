"""
Commission Engine — deterministic hybrid commission calculation.

Combined flow:
    1. Resolve supplier commission component from active supplier override or badge tier.
    2. Resolve base commission component from product override, else category rate, else global default.
    3. Final commission rate = supplier component + base component.

After combining the rate, the low-value cap is applied:
  If order_item_value < low_value_threshold (5 OMR):
      final_commission = min(rate * order_value, fixed_cap_amount)

Also seeds the default category rates and badge tiers on first use (idempotent).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    SupplierProfile,
)
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Default seed data (applied once if tables are empty)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_CATEGORY_RATES: list[dict] = [
    {"category_slug": "electronics",   "category_display_name": "Electronics",   "rate": Decimal("0.0800"), "notes": "High ticket — low % to stay competitive"},
    {"category_slug": "fashion",       "category_display_name": "Fashion",       "rate": Decimal("0.1400"), "notes": "Mid margin; supports promotions"},
    {"category_slug": "accessories",   "category_display_name": "Accessories",   "rate": Decimal("0.1400"), "notes": "Similar to fashion"},
    {"category_slug": "furniture",     "category_display_name": "Furniture",     "rate": Decimal("0.0800"), "notes": "High ticket; lower % preserves supplier margin"},
    {"category_slug": "beauty",        "category_display_name": "Beauty",        "rate": Decimal("0.1200"), "notes": "Mid margin; frequent promotions"},
    {"category_slug": "sports",        "category_display_name": "Sports",        "rate": Decimal("0.1200"), "notes": "Mid margin"},
    {"category_slug": "home-living",   "category_display_name": "Home & Living", "rate": Decimal("0.1000"), "notes": "Mixed margins"},
    {"category_slug": "books",         "category_display_name": "Books",         "rate": Decimal("0.0600"), "notes": "Low margin — keep low to avoid price increases"},
    {"category_slug": "baby-kids",     "category_display_name": "Baby & Kids",   "rate": Decimal("0.1200"), "notes": "Stable mid margin"},
    {"category_slug": "automotive",    "category_display_name": "Automotive",    "rate": Decimal("0.0800"), "notes": "High ticket, lower %"},
    {"category_slug": "crafts",        "category_display_name": "Crafts",        "rate": Decimal("0.1800"), "notes": "Higher margin, smaller volumes"},
    {"category_slug": "grocery",       "category_display_name": "Grocery",       "rate": Decimal("0.0500"), "notes": "Very low margin — minimize % or rely on cap"},
]

_DEFAULT_BADGE_TIERS: list[dict] = [
    {
        "badge_level": "none", "commission_rate": Decimal("0.1600"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 0,
        "benefits_json": json.dumps(["Basic listing", "Monthly payouts", "Basic support"]),
        "min_fulfilled_orders": None, "min_monthly_revenue": None,
    },
    {
        "badge_level": "bronze", "commission_rate": Decimal("0.1500"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 1,
        "benefits_json": json.dumps(["Standard listing", "Monthly payouts", "Basic analytics"]),
        "min_fulfilled_orders": 0, "min_monthly_revenue": None,
    },
    {
        "badge_level": "silver", "commission_rate": Decimal("0.1200"),
        "setup_fee": Decimal("50.000"), "recurring_fee": Decimal("5.000"),
        "recurring_interval": "monthly", "sort_order": 2,
        "benefits_json": json.dumps(["Priority search placement", "Weekly payouts", "Reduced gateway fee share"]),
        "min_fulfilled_orders": 50, "min_monthly_revenue": Decimal("2000.00"),
    },
    {
        "badge_level": "gold", "commission_rate": Decimal("0.1000"),
        "setup_fee": Decimal("100.000"), "recurring_fee": Decimal("10.000"),
        "recurring_interval": "monthly", "sort_order": 3,
        "benefits_json": json.dumps(["Featured promotions", "Advanced analytics", "Faster dispute handling"]),
        "min_fulfilled_orders": 200, "min_monthly_revenue": Decimal("10000.00"),
    },
    {
        "badge_level": "platinum", "commission_rate": Decimal("0.0800"),
        "setup_fee": Decimal("200.000"), "recurring_fee": Decimal("20.000"),
        "recurring_interval": "monthly", "sort_order": 4,
        "benefits_json": json.dumps(["Next-day payouts", "Dedicated account manager", "Exclusive campaigns"]),
        "min_fulfilled_orders": 500, "min_monthly_revenue": Decimal("25000.00"),
    },
    {
        "badge_level": "membership", "commission_rate": Decimal("0.0800"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 5,
        "benefits_json": json.dumps(["Negotiated lower rate", "Co-op marketing", "SLA", "Premium placement"]),
        "min_fulfilled_orders": None, "min_monthly_revenue": None,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Seeding
# ─────────────────────────────────────────────────────────────────────────────

def seed_defaults(db: Session) -> None:
    """Idempotently seed global config, default category rates, and badge tiers."""
    # Global config singleton
    config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    if not config:
        db.add(CommissionGlobalConfig(
            id=1,
            default_rate=Decimal("0.1500"),
            low_value_threshold=Decimal("5.00"),
            fixed_cap_amount=Decimal("0.500"),
            fixed_cap_enabled=True,
            margin_protection_enabled=False,
            margin_threshold=Decimal("0.10"),
        ))
        logger.info("Commission engine: seeded global config")

    # Category rates
    existing_slugs = {r[0] for r in db.query(CommissionCategoryRate.category_slug).all()}
    for cr in _DEFAULT_CATEGORY_RATES:
        if cr["category_slug"] not in existing_slugs:
            db.add(CommissionCategoryRate(
                category_slug=cr["category_slug"],
                category_display_name=cr["category_display_name"],
                rate_percent=cr["rate"],
                is_active=True,
            ))
    if len(existing_slugs) < len(_DEFAULT_CATEGORY_RATES):
        logger.info("Commission engine: seeded category rates")

    # Badge tiers
    existing_badges = {r[0] for r in db.query(CommissionBadgeTier.badge_level).all()}
    for bt in _DEFAULT_BADGE_TIERS:
        if bt["badge_level"] not in existing_badges:
            db.add(CommissionBadgeTier(
                name=bt["badge_level"],
                badge_level=bt["badge_level"],
                commission_rate=bt["commission_rate"],
                setup_fee=bt["setup_fee"],
                recurring_fee=bt["recurring_fee"],
                recurring_interval=bt.get("recurring_interval"),
                benefits_json=bt.get("benefits_json"),
                min_fulfilled_orders=bt.get("min_fulfilled_orders"),
                min_monthly_revenue=bt.get("min_monthly_revenue"),
                sort_order=bt.get("sort_order", 0),
                is_active=True,
            ))
    if len(existing_badges) < len(_DEFAULT_BADGE_TIERS):
        logger.info("Commission engine: seeded badge tiers")

    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Global config helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_global_config(db: Session) -> CommissionGlobalConfig:
    """Return the singleton global commission config, seeding it if absent."""
    config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    if not config:
        seed_defaults(db)
        config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    return config  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────────────────────────
# Rate resolution
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RateResult:
    """Result of rate resolution for a single supplier/product/category combo."""
    applied_rate: Decimal
    calculation_method: str          # override | badge
    override_rate: Optional[Decimal]
    category_rate: Optional[Decimal]
    country_rate: Optional[Decimal]
    badge_rate: Optional[Decimal]
    global_default_rate: Decimal
    badge_level: Optional[str]
    category_slug: Optional[str]
    country_code: Optional[str]
    override_flag: bool
    supplier_rate: Decimal
    supplier_rate_source: str
    base_rate: Decimal
    base_rate_source: str
    product_override_rate: Optional[Decimal]


def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int],
    category_slug: Optional[str],
    db: Session,
    country_code: Optional[str] = None,
) -> RateResult:
    """
    Resolve the effective commission rate for a supplier/product/category.

    Final rate = supplier commission component + base commission component.
    """
    config = get_global_config(db)
    global_default = Decimal(str(config.default_rate))

    # 1. Supplier commission component: active supplier override or badge tier.
    override_rate: Optional[Decimal] = None
    supplier_rate = Decimal("0.0000")
    supplier_rate_source = "badge"
    agreement = (
        db.query(CommissionAgreement)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )
    badge_lvl = _get_supplier_badge_level(supplier_id, db)
    if agreement:
        override_rate = Decimal(str(agreement.rate))
        supplier_rate = override_rate
        supplier_rate_source = "override"

    # Badge still matters for reporting even when an override is active.
    badge_rate: Optional[Decimal] = None
    if badge_lvl:
        badge_row = (
            db.query(CommissionBadgeTier)
            .filter(
                CommissionBadgeTier.badge_level == badge_lvl,
                CommissionBadgeTier.is_active == True,  # noqa: E712
            )
            .first()
        )
        if badge_row:
            badge_rate = Decimal(str(badge_row.commission_rate))
            if override_rate is None:
                supplier_rate = badge_rate

    # 2. Base commission component: product override, else category, else global.
    product_override_rate = None
    if product_id is not None:
        from models import ProductCommissionOverride

        product_override_row = (
            db.query(ProductCommissionOverride)
            .filter(
                ProductCommissionOverride.product_id == product_id,
                ProductCommissionOverride.is_active == True,  # noqa: E712
            )
            .first()
        )
        if product_override_row:
            product_override_rate = Decimal(str(product_override_row.rate))

    country_rate: Optional[Decimal] = None
    normalized_country_code = str(country_code or "").strip().upper() or None
    if normalized_country_code and category_slug:
        country_row = (
            db.query(CommissionCategoryRate)
            .filter(
                CommissionCategoryRate.country_code == normalized_country_code,
                CommissionCategoryRate.category_slug == category_slug,
                CommissionCategoryRate.is_active == True,
            )
            .first()
        )
        if country_row:
            country_rate = Decimal(str(country_row.rate_percent))

    cat_rate: Optional[Decimal] = None
    if category_slug and country_rate is None:
        cat_row = (
            db.query(CommissionCategoryRate)
            .filter(
                CommissionCategoryRate.country_code == None,
                CommissionCategoryRate.category_slug == category_slug,
                CommissionCategoryRate.is_active == True,
            )
            .first()
        )
        if cat_row:
            cat_rate = Decimal(str(cat_row.rate_percent))
    if product_override_rate is not None:
        base_rate = product_override_rate
        base_rate_source = "product_override"
    elif country_rate is not None:
        base_rate = country_rate
        base_rate_source = "country_category"
    elif cat_rate is not None:
        base_rate = cat_rate
        base_rate_source = "category"
    else:
        base_rate = global_default
        base_rate_source = "global_default"

    applied_rate = (supplier_rate + base_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return RateResult(
        applied_rate=applied_rate,
        calculation_method="override" if override_rate is not None else "badge",
        override_rate=override_rate,
        category_rate=cat_rate,
        country_rate=country_rate,
        badge_rate=badge_rate,
        global_default_rate=global_default,
        badge_level=badge_lvl,
        category_slug=category_slug,
        country_code=normalized_country_code,
        override_flag=override_rate is not None,
        supplier_rate=supplier_rate,
        supplier_rate_source=supplier_rate_source,
        base_rate=base_rate,
        base_rate_source=base_rate_source,
        product_override_rate=product_override_rate,
    )


def _get_supplier_badge_level(supplier_id: int, db: Session) -> Optional[str]:
    profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == supplier_id)
        .first()
    )
    badge_level = getattr(profile, "badge_level", None) if profile is not None else None
    if badge_level not in (None, ""):
        return str(badge_level).lower()
    return "none"


# ─────────────────────────────────────────────────────────────────────────────
# Commission computation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CommissionResult:
    rate: Decimal
    calculation_method: str
    order_value: Decimal
    commission_pct_amount: Decimal      # rate * order_value (before cap)
    cap_applied: bool
    commission_amount: Decimal          # final after cap
    low_value_threshold_used: Optional[Decimal]
    fixed_cap_used: Optional[Decimal]
    rate_result: RateResult             # full metadata


def compute_commission(
    order_value: Decimal,
    rate_result: RateResult,
    global_config: CommissionGlobalConfig,
) -> CommissionResult:
    """
    Apply the rate to the order value and apply the low-value cap if needed.

    Low-value cap: if order_value < low_value_threshold AND fixed_cap_enabled:
        final_commission = min(rate * order_value, fixed_cap_amount)
    """
    rate = rate_result.applied_rate
    commission_pct = (rate * order_value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    cap_applied = False
    commission_amount = commission_pct
    low_value_threshold_used: Optional[Decimal] = None
    fixed_cap_used: Optional[Decimal] = None

    fixed_cap_enabled = bool(getattr(global_config, "fixed_cap_enabled"))
    if fixed_cap_enabled:
        threshold = Decimal(str(getattr(global_config, "low_value_threshold")))
        cap = Decimal(str(getattr(global_config, "fixed_cap_amount")))
        if order_value < threshold:
            commission_amount = min(commission_pct, cap)
            cap_applied = commission_amount < commission_pct
            low_value_threshold_used = threshold
            fixed_cap_used = cap

    return CommissionResult(
        rate=rate,
        calculation_method=rate_result.calculation_method,
        order_value=order_value,
        commission_pct_amount=commission_pct,
        cap_applied=cap_applied,
        commission_amount=commission_amount,
        low_value_threshold_used=low_value_threshold_used,
        fixed_cap_used=fixed_cap_used,
        rate_result=rate_result,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Persist ledger entry
# ─────────────────────────────────────────────────────────────────────────────

def create_commission_ledger_entry(
    order_id: int,
    supplier_id: int,
    order_value: Decimal,
    result: CommissionResult,
    db: Session,
    order_item_id: Optional[int] = None,
    product_id: Optional[int] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> CommissionLedgerEntry:
    """Persist an immutable CommissionLedgerEntry for a single order item."""
    rr = result.rate_result
    entry = CommissionLedgerEntry(
        order_id=order_id,
        order_item_id=order_item_id,
        supplier_id=supplier_id,
        product_id=product_id,
        category_slug=rr.category_slug,
        badge_level=rr.badge_level,
        global_default_rate=rr.global_default_rate,
        category_rate=rr.category_rate,
        badge_rate=rr.badge_rate,
        override_rate=rr.override_rate,
        applied_rate=result.rate,
        calculation_method=result.calculation_method,
        order_value=order_value,
        commission_pct=result.commission_pct_amount,
        cap_applied=result.cap_applied,
        commission_amount=result.commission_amount,
        low_value_threshold_used=result.low_value_threshold_used,
        fixed_cap_used=result.fixed_cap_used,
        override_flag=rr.override_flag,
        is_adjusted=False,
        currency=currency,
        country_code=country_code,
    )
    db.add(entry)
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# Preview (no DB writes)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Country value-based commission tiers
# ─────────────────────────────────────────────────────────────────────────────

import json as _json

from models import CountryConfig
from services.logistics_partner_pricing import normalize_country_code as _normalize_country


def resolve_country_commission_tiers(
    country_code: str,
    order_value: Decimal,
    db: Session,
) -> dict[str, Decimal | None] | None:
    """Resolve commission from a country's value-based ``commission_tiers_json``.

    Returns ``{commission_percentage, fixed_fee}`` if a matching tier is found,
    ``None`` if no tiers are configured for the country.
    """
    code = _normalize_country(country_code)
    if not code:
        return None
    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return None
    raw = country.commission_tiers_json
    if not raw:
        return None
    try:
        tiers = _json.loads(raw) if isinstance(raw, str) else raw
    except (_json.JSONDecodeError, TypeError):
        return None
    if not isinstance(tiers, list):
        return None

    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        min_val = Decimal(str(tier.get("min_order_value", 0)))
        max_raw = tier.get("max_order_value")
        max_val = Decimal(str(max_raw)) if max_raw is not None else None
        if order_value >= min_val:
            if max_val is None or order_value <= max_val:
                pct = Decimal(str(tier.get("commission_percentage", 0)))
                fee = Decimal(str(tier.get("fixed_fee", 0)))
                return {
                    "commission_percentage": pct / Decimal("100"),
                    "fixed_fee": fee,
                    "min_order_value": min_val,
                    "max_order_value": max_val,
                }
    return None


def preview_commission(
    supplier_id: int,
    order_value: float,
    category_slug: Optional[str],
    db: Session,
) -> dict:
    """Preview commission calculation without persisting anything."""
    ov = Decimal(str(order_value))
    rate_result = get_effective_rate(supplier_id=supplier_id, product_id=None, category_slug=category_slug, db=db)
    config = get_global_config(db)
    result = compute_commission(ov, rate_result, config)
    fixed_cap_enabled = bool(getattr(config, "fixed_cap_enabled"))

    return {
        "order_value": float(ov),
        "applied_rate": float(result.rate),
        "applied_rate_pct": f"{float(result.rate) * 100:.2f}%",
        "calculation_method": result.calculation_method,
        "commission_pct_amount": float(result.commission_pct_amount),
        "cap_applied": result.cap_applied,
        "commission_amount": float(result.commission_amount),
        "low_value_threshold": float(getattr(config, "low_value_threshold")) if fixed_cap_enabled else None,
        "fixed_cap": float(getattr(config, "fixed_cap_amount")) if fixed_cap_enabled else None,
        "snapshot": {
            "supplier_rate": float(rate_result.supplier_rate),
            "supplier_rate_source": rate_result.supplier_rate_source,
            "base_rate": float(rate_result.base_rate),
            "base_rate_source": rate_result.base_rate_source,
            "country_rate": float(rate_result.country_rate) if rate_result.country_rate else None,
            "country_code": rate_result.country_code,
            "product_override_rate": float(rate_result.product_override_rate) if rate_result.product_override_rate else None,
            "override_rate": float(rate_result.override_rate) if rate_result.override_rate else None,
            "category_rate": float(rate_result.category_rate) if rate_result.category_rate else None,
            "badge_rate": float(rate_result.badge_rate) if rate_result.badge_rate else None,
            "global_default_rate": float(rate_result.global_default_rate),
            "badge_level": rate_result.badge_level,
            "category_slug": rate_result.category_slug,
        },
    }

