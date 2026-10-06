"""ABAC policies for the orders domain.

These policies extend the base RBAC features with attribute-based access control.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional, Set


def expand_wildcards(features: Iterable[str], catalog: dict) -> Set[str]:
    out: Set[str] = set()
    for f in features:
        if f == "*":
            out.update(catalog.keys())
        elif f.endswith(".*"):
            prefix = f[:-2]
            out.update(k for k in catalog if k.startswith(prefix))
        else:
            out.add(f)
    return out


def effective_features(
    role_features: Iterable[str] = (),
    db_grants: Iterable[str] = (),
    overrides: Iterable[str] = (),
    catalog: dict | None = None,
) -> Set[str]:
    feats = set(role_features) | set(db_grants) | set(overrides)
    return expand_wildcards(feats, catalog or {})


def get_order_abac_context(
    *,
    order_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    action: str = "read",
    current_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Build ABAC context for order operations.

    Args:
        order_id: The order being accessed
        customer_id: The customer who owns the order
        supplier_id: The supplier fulfilling the order
        country_code: The country context (e.g., "OM", "AE")
        action: The action being performed ("read", "write", "cancel", "refund")
        current_user_id: The ID of the user making the request

    Returns:
        ABAC context dictionary
    """
    context = {
        "region": country_code,
        "resource_owner": customer_id,
        "current_user_id": current_user_id,
        "action": action,
        "resource_type": "order",
    }

    if supplier_id:
        context["organization"] = f"supplier_{supplier_id}"

    return context


def can_access_order(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    *,
    customer_id: Optional[int] = None,
    country_code: Optional[str] = None,
    current_user_id: Optional[int] = None,
    action: str = "read",
) -> bool:
    """Check if a user can access an order based on RBAC + ABAC.

    This combines role-based features with attribute-based policies.
    """
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )

    required_feature = f"orders.{action}"
    return required_feature in features


def can_modify_order(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    *,
    customer_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    current_user_id: Optional[int] = None,
) -> bool:
    """Check if a user can modify (write/cancel) an order.

    Suppliers can modify their own orders, customers can cancel their own.
    """
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )

    # Check for write permission
    return "orders.write" in features or "orders.cancel" in features


def get_order_features_with_abac(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    **abac_kwargs: Any,
) -> set[str]:
    """Get effective features for orders with ABAC context.

    This is a convenience function that builds the ABAC context and
    evaluates the effective features in one call.
    """
    return effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )
