# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Canonical shared address service -- single source of truth (Law 7 dedupe of accounts/customers/country triplicate)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user

from infrastructure.database.database import get_db

from domains.governance.ports import Address

# Lazy-loaded cross-domain services (Law 3: avoid direct cross-domain imports at module level)
# TODO: This module is archived. When reactivating, move these calls through ports/events.
_LAZY_CROSS_DOMAIN_SERVICES: dict[str, tuple[str, str]] = {
    "_serialize_address": ("domains.orders.services.customer_router_service", "_serialize_address"),
    "_normalize_address_payload": ("domains.orders.services.customer_router_service", "_normalize_address_payload"),
    "create_address": ("domains.orders.services.commerce_write_service", "create_address"),
    "update_address": ("domains.orders.services.commerce_write_service", "update_address"),
    "delete_address": ("domains.orders.services.commerce_write_service", "delete_address"),
    "set_default_address": ("domains.orders.services.commerce_write_service", "set_default_address"),
    "unset_other_default_addresses": ("domains.orders.services.commerce_write_service", "unset_other_default_addresses"),
    "list_user_addresses": ("domains.orders.services.commerce_read_service", "list_user_addresses"),
    "get_user_address": ("domains.orders.services.commerce_read_service", "get_user_address"),
}
_IMPORTED_CROSS_DOMAIN_SERVICES: dict[str, object] = {}


def _get_cross_domain_service(name: str):
    """Lazily import a cross-domain service function to avoid import-time coupling."""
    if name in _IMPORTED_CROSS_DOMAIN_SERVICES:
        return _IMPORTED_CROSS_DOMAIN_SERVICES[name]
    if name in _LAZY_CROSS_DOMAIN_SERVICES:
        module_path, symbol = _LAZY_CROSS_DOMAIN_SERVICES[name]
        import importlib
        mod = importlib.import_module(module_path)
        func = getattr(mod, name)
        _IMPORTED_CROSS_DOMAIN_SERVICES[name] = func
        return func
    raise AttributeError(f"Cross-domain service {name!r} not registered")



def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    return _get_cross_domain_service("get_user_address")(db, address_id, user_id)

def list_addresses(limit: int, offset: int, current_user: dict, db: Session):
    rows = _get_cross_domain_service("list_user_addresses")(db, current_user["id"], limit, offset)
    return [_get_cross_domain_service("_serialize_address")(row) for row in rows]

def create_address(payload: dict, current_user: dict, db: Session):
    normalized = _get_cross_domain_service("_normalize_address_payload")(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        _get_cross_domain_service("unset_other_default_addresses")(db, user_id)
    address_data = {
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
    }
    if normalized.get("label"):
        address_data["label"] = normalized["label"]
    if normalized.get("phone"):
        address_data["phone"] = normalized["phone"]
    address = _get_cross_domain_service("create_address")(db, **address_data)
    return _get_cross_domain_service("_serialize_address")(address)

def update_address(address_id: int, payload: dict, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _get_cross_domain_service("_normalize_address_payload")(payload, partial=True)
    if updates.get("is_default") is True:
        _get_cross_domain_service("unset_other_default_addresses")(db, int(current_user["id"]), address_id)
    if "street" in updates:
        updates.pop("street")
    address = _get_cross_domain_service("update_address")(db, address, updates)
    return _get_cross_domain_service("_serialize_address")(address)

def delete_address(address_id: int, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    _get_cross_domain_service("delete_address")(db, address)
    return {"detail": "Deleted"}

def set_default_address(address_id: int, current_user: dict, db: Session):
    user_id = int(current_user["id"])
    _get_cross_domain_service("unset_other_default_addresses")(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    address = _get_cross_domain_service("set_default_address")(db, address)
    return _get_cross_domain_service("_serialize_address")(address)


