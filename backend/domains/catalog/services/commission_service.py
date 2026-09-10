from __future__ import annotations

"""Commission management service.

Handles CRUD operations for CommissionGroup, CommissionProfile, and CommissionRule.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.catalog.models.commission import (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
)


# ── Commission Groups ──────────────────────────────────────────────────────


def list_commission_groups(db: Session) -> list[CommissionGroup]:
    """Get all active commission groups."""
    return db.query(CommissionGroup).filter(CommissionGroup.is_active.is_(True)).all()


def create_commission_group(
    db: Session,
    *,
    name: str,
    slug: str,
    base_rate: float,
    max_commission_amount: Optional[float] = None,
    description: Optional[str] = None,
) -> CommissionGroup:
    """Create a new commission group."""
    group = CommissionGroup(
        name=name,
        slug=slug,
        base_rate=Decimal(str(base_rate)),
        max_commission_amount=Decimal(str(max_commission_amount)) if max_commission_amount else None,
        description=description,
    )
    db.add(group)
    db.commit()
    return group


def update_commission_group(
    db: Session,
    group_id: int,
    **updates,
) -> Optional[CommissionGroup]:
    """Update a commission group."""
    group = db.query(CommissionGroup).filter(
        CommissionGroup.id == group_id,
        CommissionGroup.is_deleted.is_(False),
    ).first()
    if not group:
        return None

    for key, value in updates.items():
        if value is not None and hasattr(group, key):
            if key in ("base_rate", "max_commission_amount") and value is not None:
                setattr(group, key, Decimal(str(value)))
            else:
                setattr(group, key, value)

    db.commit()
    return group


def archive_commission_group(db: Session, group_id: int) -> bool:
    """Archive (soft-delete) a commission group."""
    group = db.query(CommissionGroup).filter(
        CommissionGroup.id == group_id,
        CommissionGroup.is_deleted.is_(False),
    ).first()
    if not group:
        return False

    group.is_deleted = True
    group.is_active = False
    db.commit()
    return True


# ── Commission Profiles ───────────────────────────────────────────────────


def list_commission_profiles(
    db: Session,
    supplier_id: Optional[int] = None,
) -> list[CommissionProfile]:
    """List commission profiles, optionally filtered by supplier."""
    query = db.query(CommissionProfile).filter(CommissionProfile.is_deleted.is_(False))
    if supplier_id is not None:
        query = query.filter(CommissionProfile.supplier_id == supplier_id)
    return query.order_by(CommissionProfile.name).all()


def create_commission_profile(
    db: Session,
    *,
    supplier_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    is_default: bool = False,
    country_code: Optional[str] = None,
) -> CommissionProfile:
    """Create a new commission profile."""
    profile = CommissionProfile(
        supplier_id=supplier_id,
        name=name,
        slug=slug,
        description=description,
        is_default=is_default,
        country_code=country_code,
    )
    db.add(profile)
    db.commit()
    return profile


def update_commission_profile(
    db: Session,
    profile_id: int,
    **updates,
) -> Optional[CommissionProfile]:
    """Update a commission profile."""
    profile = db.query(CommissionProfile).filter(
        CommissionProfile.id == profile_id,
        CommissionProfile.is_deleted.is_(False),
    ).first()
    if not profile:
        return None

    for key, value in updates.items():
        if value is not None and hasattr(profile, key):
            setattr(profile, key, value)

    db.commit()
    return profile


# ── Commission Rules ───────────────────────────────────────────────────────


def list_commission_rules(
    db: Session,
    *,
    profile_id: Optional[int] = None,
    commission_group_id: Optional[int] = None,
    country_code: Optional[str] = None,
    product_type_id: Optional[int] = None,
) -> list[CommissionRule]:
    """List commission rules with optional filters."""
    query = db.query(CommissionRule).filter(CommissionRule.is_deleted.is_(False))
    if profile_id is not None:
        query = query.filter(CommissionRule.profile_id == profile_id)
    if commission_group_id is not None:
        query = query.filter(CommissionRule.commission_group_id == commission_group_id)
    if country_code is not None:
        query = query.filter(CommissionRule.country_code == country_code)
    if product_type_id is not None:
        query = query.filter(CommissionRule.product_type_id == product_type_id)
    return query.order_by(CommissionRule.priority.asc(), CommissionRule.name).all()


def create_commission_rule(
    db: Session,
    *,
    profile_id: int,
    name: str,
    rate: float,
    commission_group_id: Optional[int] = None,
    coc_node_id: Optional[int] = None,
    product_type_id: Optional[int] = None,
    brand: Optional[str] = None,
    attribute_key: Optional[str] = None,
    attribute_value: Optional[str] = None,
    max_commission_amount: Optional[float] = None,
    priority: int = 100,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    country_code: Optional[str] = None,
) -> CommissionRule:
    """Create a new commission rule."""
    eff_from = date.fromisoformat(effective_from) if effective_from else None
    eff_to = date.fromisoformat(effective_to) if effective_to else None

    rule = CommissionRule(
        profile_id=profile_id,
        commission_group_id=commission_group_id,
        name=name,
        coc_node_id=coc_node_id,
        product_type_id=product_type_id,
        brand=brand,
        attribute_key=attribute_key,
        attribute_value=attribute_value,
        rate=Decimal(str(rate)),
        max_commission_amount=Decimal(str(max_commission_amount)) if max_commission_amount else None,
        priority=priority,
        effective_from=eff_from,
        effective_to=eff_to,
        country_code=country_code,
    )
    db.add(rule)
    db.commit()
    return rule


def update_commission_rule(
    db: Session,
    rule_id: int,
    **updates,
) -> Optional[CommissionRule]:
    """Update a commission rule."""
    rule = db.query(CommissionRule).filter(
        CommissionRule.id == rule_id,
        CommissionRule.is_deleted.is_(False),
    ).first()
    if not rule:
        return None

    for key, value in updates.items():
        if value is not None and hasattr(rule, key):
            if key == "rate" and value is not None:
                setattr(rule, key, Decimal(str(value)))
            elif key == "max_commission_amount" and value is not None:
                setattr(rule, key, Decimal(str(value)))
            elif key == "effective_from":
                setattr(rule, key, date.fromisoformat(value) if value else None)
            elif key == "effective_to":
                setattr(rule, key, date.fromisoformat(value) if value else None)
            else:
                setattr(rule, key, value)

    db.commit()
    return rule


def archive_commission_rule(db: Session, rule_id: int) -> bool:
    """Archive (soft-delete) a commission rule."""
    rule = db.query(CommissionRule).filter(
        CommissionRule.id == rule_id,
        CommissionRule.is_deleted.is_(False),
    ).first()
    if not rule:
        return False

    rule.is_deleted = True
    rule.is_active = False
    db.commit()
    return True


# ── Bulk Attribute Generation ─────────────────────────────────────────────


def bulk_generate_attributes(db: Session) -> dict:
    """Auto-generate generic L5 (Brand) and L6 (Variant) attributes for all L4 product types."""
    from domains.catalog.models.chart_of_categories import ProductType, CategoryAttribute

    generic_brands = ["Generic", "Store Brand", "White Label", "Unbranded"]
    generic_specs = ["Standard", "Premium", "Economy", "Limited Edition"]

    product_types = db.query(ProductType).filter(
        ProductType.is_active.is_(True),
        ProductType.is_deleted.is_(False),
    ).all()

    brands_created = 0
    specs_created = 0

    for pt in product_types:
        has_brand = db.query(CategoryAttribute).filter(
            CategoryAttribute.product_type_id == pt.id,
            CategoryAttribute.layer == 5,
        ).first()

        if not has_brand:
            attr = CategoryAttribute(
                product_type_id=pt.id, name="Brand", key="brand",
                layer=5, value_type="select",
                options=",".join(generic_brands),
            )
            db.add(attr)
            brands_created += 1

        has_spec = db.query(CategoryAttribute).filter(
            CategoryAttribute.product_type_id == pt.id,
            CategoryAttribute.layer == 6,
        ).first()

        if not has_spec:
            attr = CategoryAttribute(
                product_type_id=pt.id, name="Variant", key="variant",
                layer=6, value_type="select",
                options=",".join(generic_specs),
            )
            db.add(attr)
            specs_created += 1

    db.commit()

    return {
        "brands_created": brands_created,
        "specs_created": specs_created,
        "total_product_types": len(product_types),
    }
