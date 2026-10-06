"""ABAC policies for the suppliers domain."""
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


def get_supplier_abac_context(
    *,
    supplier_id: Optional[int] = None,
    user_id: Optional[int] = None,
    country_code: Optional[str] = None,
    action: str = "read",
    current_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Build ABAC context for supplier operations."""
    return {
        "region": country_code,
        "resource_owner": user_id,
        "organization": f"supplier_{supplier_id}" if supplier_id else None,
        "current_user_id": current_user_id,
        "action": action,
        "resource_type": "supplier",
    }


def can_access_supplier(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    *,
    supplier_id: Optional[int] = None,
    user_id: Optional[int] = None,
    country_code: Optional[str] = None,
    current_user_id: Optional[int] = None,
    action: str = "read",
) -> bool:
    """Check if a user can access a supplier based on RBAC + ABAC."""
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )

    required_feature = f"suppliers.{action}"
    return required_feature in features


def can_manage_supplier_products(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    *,
    supplier_id: Optional[int] = None,
    user_id: Optional[int] = None,
    country_code: Optional[str] = None,
    current_user_id: Optional[int] = None,
) -> bool:
    """Check if a user can manage products for a supplier."""
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )

    return "suppliers.products.write" in features


def get_supplier_features_with_abac(
    role_features: list[str],
    db_grants: list[str],
    overrides: list[str],
    catalog: dict,
    **abac_kwargs: Any,
) -> set[str]:
    """Get effective features for suppliers with ABAC context."""
    return effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
    )
