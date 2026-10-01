from __future__ import annotations

"""Waterfall Commission Engine.

Calculates commission using a waterfall approach:
1. Check SKU exact match (Level 7)
2. Check Supplier + Brand (Level 5)
3. Check Supplier + Product Type (Level 4)
4. Check Supplier + Sub-Category (Level 3)
5. Check Commission Group base rate
6. Check Global default rate

First match wins.
"""
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.catalog.models.commission import (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
)

logger = logging.getLogger(__name__)

# Global default commission rate (fallback)
_GLOBAL_DEFAULT_RATE = Decimal("15.00")


@dataclass
class CommissionResult:
    """Result of commission calculation."""

    rate: Decimal
    amount: Decimal
    net_amount: Decimal
    rule_name: str
    rule_id: Optional[int] = None
    max_commission_amount: Optional[Decimal] = None


@dataclass
class ProductContext:
    """Context for commission calculation."""

    product_id: int
    supplier_id: int
    coc_node_id: int  # Level 3 CoC node
    product_type_id: Optional[int] = None  # Level 4
    brand: Optional[str] = None  # Level 5
    attributes: Optional[dict] = None  # Level 6 attributes
    gross_amount: Decimal = Decimal("0")
    db: Optional[Session] = None  # For path lookups
    coc_path_prefix: Optional[str] = None  # Materialized path of coc_node_id
    country_code: Optional[str] = None  # Country dimension for commission lookup


def calculate_commission(
    db: Session,
    context: ProductContext,
    profile_id: Optional[int] = None,
) -> CommissionResult:
    """Calculate commission using waterfall logic.

    Args:
        db: Database session.
        context: Product context with all classification levels.
        profile_id: Optional specific profile to use.

    Returns:
        CommissionResult with rate, amount, and rule info.
    """
    # Step 1: Get supplier's active profile
    profile = _get_supplier_profile(db, context.supplier_id, profile_id)
    if not profile:
        logger.warning("No commission profile for supplier %s", context.supplier_id)
        return _default_result(context.gross_amount)

    # Step 2: Get all active rules for this profile, ordered by priority
    rules = (
        db.query(CommissionRule)
        .filter(
            CommissionRule.profile_id == profile.id,
            CommissionRule.is_active.is_(True),
        )
        .order_by(CommissionRule.priority.asc())
        .all()
    )

    # Step 3: Evaluate each rule in priority order
    for rule in rules:
        if not _is_rule_effective(rule, date.today()):
            continue

        if _rule_matches(rule, context):
            return _apply_rule(rule, context)

    # Step 4: Fall back to commission group base rate
    group_result = _check_commission_group(db, context)
    if group_result:
        return group_result

    # Step 5: Fall back to global default
    return _default_result(context.gross_amount)


def _get_supplier_profile(
    db: Session,
    supplier_id: int,
    profile_id: Optional[int] = None,
) -> Optional[CommissionProfile]:
    """Get the active commission profile for a supplier."""
    query = db.query(CommissionProfile).filter(
        CommissionProfile.supplier_id == supplier_id,
        CommissionProfile.is_active.is_(True),
    )

    if profile_id:
        query = query.filter(CommissionProfile.id == profile_id)
    else:
        query = query.filter(CommissionProfile.is_default.is_(True))

    return query.first()


def _is_rule_effective(rule: CommissionRule, today: date) -> bool:
    """Check if a rule is currently effective."""
    if rule.effective_from and today < rule.effective_from:
        return False
    if rule.effective_to and today > rule.effective_to:
        return False
    return True


def _rule_matches(rule: CommissionRule, context: ProductContext) -> bool:
    """Check if a rule matches the product context.

    For CoC node matching, checks if the rule's node is an ancestor
    of (or equal to) the product's CoC node using the materialized path.
    Country matching: if rule has country_code, it must match context.
    """
    # Check country code (orthogonal dimension — Law 5)
    if rule.country_code and rule.country_code != context.country_code:
        return False

    # Check CoC node (Level 1-3) - match if rule node is ancestor of product node
    if rule.coc_node_id:
        if rule.coc_node_id == context.coc_node_id:
            return True  # Exact match
        # Check if rule node is an ancestor in the path
        if context.coc_path_prefix and context.coc_path_prefix.startswith(
            _get_node_path_prefix(context.db, rule.coc_node_id)
        ):
            return True
        return False

    # Check product type (Level 4)
    if rule.product_type_id and rule.product_type_id != context.product_type_id:
        return False

    # Check brand (Level 5)
    if rule.brand and rule.brand.lower() != (context.brand or "").lower():
        return False

    # Check attribute (Level 6)
    if rule.attribute_key and rule.attribute_value:
        attr_val = (context.attributes or {}).get(rule.attribute_key)
        if attr_val != rule.attribute_value:
            return False

    return True


def _get_node_path_prefix(db: Session, node_id: int) -> str:
    """Get the materialized path prefix for a CoC node."""
    from domains.catalog.models.chart_of_categories import ChartOfCategory
    node = db.query(ChartOfCategory.path).filter(ChartOfCategory.id == node_id).first()
    return node.path if node else ""


def _apply_rule(rule: CommissionRule, context: ProductContext) -> CommissionResult:
    """Apply a commission rule to calculate the result."""
    rate = rule.rate
    amount = (context.gross_amount * rate) / Decimal("100")

    # Apply max commission cap if set
    if rule.max_commission_amount and amount > rule.max_commission_amount:
        amount = rule.max_commission_amount

    net_amount = context.gross_amount - amount

    return CommissionResult(
        rate=rate,
        amount=amount.quantize(Decimal("0.01")),
        net_amount=net_amount.quantize(Decimal("0.01")),
        rule_name=rule.name,
        rule_id=rule.id,
        max_commission_amount=rule.max_commission_amount,
    )


def _check_commission_group(
    db: Session,
    context: ProductContext,
) -> Optional[CommissionResult]:
    """Check commission group base rate."""
    from domains.catalog.models.chart_of_categories import ChartOfCategory

    # Get the CoC node and its commission group
    coc_node = db.query(ChartOfCategory).filter(
        ChartOfCategory.id == context.coc_node_id,
    ).first()

    if not coc_node or not coc_node.commission_group_id:
        return None

    group = db.query(CommissionGroup).filter(
        CommissionGroup.id == coc_node.commission_group_id,
        CommissionGroup.is_active.is_(True),
    ).first()

    if not group:
        return None

    rate = group.base_rate
    amount = (context.gross_amount * rate) / Decimal("100")

    # Apply max commission cap if set
    if group.max_commission_amount and amount > group.max_commission_amount:
        amount = group.max_commission_amount

    net_amount = context.gross_amount - amount

    return CommissionResult(
        rate=rate,
        amount=amount.quantize(Decimal("0.01")),
        net_amount=net_amount.quantize(Decimal("0.01")),
        rule_name=f"Group: {group.name}",
        max_commission_amount=group.max_commission_amount,
    )


def _default_result(gross_amount: Decimal) -> CommissionResult:
    """Return the global default commission result."""
    rate = _GLOBAL_DEFAULT_RATE
    amount = (gross_amount * rate) / Decimal("100")
    net_amount = gross_amount - amount

    return CommissionResult(
        rate=rate,
        amount=amount.quantize(Decimal("0.01")),
        net_amount=net_amount.quantize(Decimal("0.01")),
        rule_name="Global Default",
    )


def preview_commission(
    db: Session,
    supplier_id: int,
    coc_node_id: int,
    gross_amount: Decimal,
    product_type_id: Optional[int] = None,
    brand: Optional[str] = None,
    attributes: Optional[dict] = None,
    country_code: Optional[str] = None,
) -> CommissionResult:
    """Preview commission for a supplier before listing a product.

    This is used in the supplier listing flow to show real-time
    commission calculation.
    """
    # Get the CoC node's path for ancestor matching
    from domains.catalog.models.chart_of_categories import ChartOfCategory
    coc_node = db.query(ChartOfCategory).filter(ChartOfCategory.id == coc_node_id).first()
    coc_path = coc_node.path if coc_node else None

    context = ProductContext(
        product_id=0,  # Not yet created
        supplier_id=supplier_id,
        coc_node_id=coc_node_id,
        product_type_id=product_type_id,
        brand=brand,
        attributes=attributes,
        gross_amount=gross_amount,
        db=db,
        coc_path_prefix=coc_path,
        country_code=country_code,
    )

    return calculate_commission(db, context)


def set_global_default_rate(rate: Decimal) -> None:
    """Update the global default commission rate."""
    global _GLOBAL_DEFAULT_RATE
    _GLOBAL_DEFAULT_RATE = rate


def get_global_default_rate() -> Decimal:
    """Get the current global default commission rate."""
    return _GLOBAL_DEFAULT_RATE
