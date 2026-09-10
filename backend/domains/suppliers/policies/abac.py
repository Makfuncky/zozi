"""ABAC policies for the suppliers domain."""
from __future__ import annotations

from typing import Any, Optional

from rbac.resolution import (
    build_abac_context,
    effective_features,
)


def get_supplier_abac_context(
    *,
    supplier_id: Optional[int] = None,
    user_id: Optional[int] = None,
    country_code: Optional[str] = None,
    action: str = "read",
    current_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Build ABAC context for supplier operations."""
    context = build_abac_context(
        region=country_code,
        resource_owner=user_id,
        organization=f"supplier_{supplier_id}" if supplier_id else None,
        current_user_id=current_user_id,
        action=action,
        resource_type="supplier",
    )
    return context


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
    abac_context = get_supplier_abac_context(
        supplier_id=supplier_id,
        user_id=user_id,
        country_code=country_code,
        action=action,
        current_user_id=current_user_id,
    )
    
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
        abac_context=abac_context,
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
    abac_context = get_supplier_abac_context(
        supplier_id=supplier_id,
        user_id=user_id,
        country_code=country_code,
        action="write",
        current_user_id=current_user_id,
    )
    
    features = effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
        abac_context=abac_context,
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
    abac_context = get_supplier_abac_context(**abac_kwargs)
    return effective_features(
        role_features=role_features,
        db_grants=db_grants,
        overrides=overrides,
        catalog=catalog,
        abac_context=abac_context,
    )