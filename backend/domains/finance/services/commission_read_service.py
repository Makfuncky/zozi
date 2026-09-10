"""Commission Read Service — supplier-facing commission rate queries.

Deep module: owns the logic for querying and formatting commission rates
that suppliers see. Extracted from the coc.py router to improve testability.

Locality: commission display logic lives here, not in a router.
Leverage: one interface for commission reads, called by the supplier router.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def get_supplier_commission_rates(db: Session, supplier_id: int) -> list[dict[str, Any]]:
    """Get commission rates for a supplier, grouped by profile and category.

    Returns a list of commission profiles with their associated rules,
    including resolved category and group names.
    """
    from domains.finance.models.general_ledger import CommissionProfile, CommissionRule, ChartOfCategory, CommissionGroup

    profiles = db.query(CommissionProfile).filter(
        CommissionProfile.supplier_id == supplier_id,
        CommissionProfile.is_active.is_(True),
        CommissionProfile.is_deleted.is_(False),
    ).all()

    profile_ids = [p.id for p in profiles]
    rules = []
    if profile_ids:
        rules = db.query(CommissionRule).filter(
            CommissionRule.profile_id.in_(profile_ids),
            CommissionRule.is_active.is_(True),
            CommissionRule.is_deleted.is_(False),
        ).order_by(CommissionRule.priority.asc()).all()

    coc_node_ids = {r.coc_node_id for r in rules if r.coc_node_id}
    group_ids = {r.commission_group_id for r in rules if r.commission_group_id}

    coc_nodes = {}
    if coc_node_ids:
        coc_nodes = {
            n.id: n.name for n in
            db.query(ChartOfCategory).filter(ChartOfCategory.id.in_(coc_node_ids)).all()
        }
    groups = {}
    if group_ids:
        groups = {
            g.id: g.name for g in
            db.query(CommissionGroup).filter(CommissionGroup.id.in_(group_ids)).all()
        }

    rules_by_profile: dict[int, list] = {}
    for rule in rules:
        rules_by_profile.setdefault(rule.profile_id, []).append(rule)

    result = []
    for profile in profiles:
        profile_rules = rules_by_profile.get(profile.id, [])
        rules_data = []
        for rule in profile_rules:
            category_name = coc_nodes.get(rule.coc_node_id) if rule.coc_node_id else None
            group_name = groups.get(rule.commission_group_id) if rule.commission_group_id else None

            rules_data.append({
                "id": rule.id,
                "name": rule.name,
                "rate": float(rule.rate),
                "category": category_name,
                "group": group_name,
                "brand": rule.brand,
                "product_type_id": rule.product_type_id,
                "country_code": rule.country_code,
                "priority": rule.priority,
                "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
                "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
                "source": "Specific Rule",
            })

        if profile.is_default:
            rules_data.append({
                "id": 0,
                "name": "Default Profile Rate",
                "rate": 0,
                "category": None,
                "group": None,
                "brand": None,
                "product_type_id": None,
                "country_code": profile.country_code,
                "priority": 999,
                "effective_from": None,
                "effective_to": None,
                "source": "Default Profile",
            })

        result.append({
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "is_default": profile.is_default,
                "country_code": profile.country_code,
            },
            "rules": rules_data,
        })

    return result
