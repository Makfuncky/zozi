# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Canonical shared address service -- single source of truth (Law 7 dedupe of accounts/customers/country triplicate)."""
from __future__ import annotations
from domains.orders.services.customer_router_service import _serialize_address
from domains.orders.services.customer_router_service import _normalize_address_payload

from fastapi import Depends, HTTPException, status

from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user

from infrastructure.database.database import get_db

from domains.accounts.ports import Address

from domains.orders.services.commerce_write_service import create_address as create_address_model
from domains.orders.services.commerce_write_service import update_address as update_address_model
from domains.orders.services.commerce_write_service import delete_address as delete_address_model
from domains.orders.services.commerce_write_service import set_default_address as set_default_address_model
from domains.orders.services.commerce_write_service import unset_other_default_addresses

from domains.orders.services.commerce_read_service import list_user_addresses
from domains.orders.services.commerce_read_service import get_user_address



def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    return get_user_address(db, address_id, user_id)

def list_addresses(limit: int, offset: int, current_user: dict, db: Session):
    rows = list_user_addresses(db, current_user["id"], limit, offset)
    return [_serialize_address(row) for row in rows]

def create_address(payload: dict, current_user: dict, db: Session):
    normalized = _normalize_address_payload(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
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
    address = create_address_model(db, **address_data)
    return _serialize_address(address)

def update_address(address_id: int, payload: dict, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, int(current_user["id"]), address_id)
    if "street" in updates:
        updates.pop("street")
    address = update_address_model(db, address, updates)
    return _serialize_address(address)

def delete_address(address_id: int, current_user: dict, db: Session):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    delete_address_model(db, address)
    return {"detail": "Deleted"}

def set_default_address(address_id: int, current_user: dict, db: Session):
    user_id = int(current_user["id"])
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    address = set_default_address_model(db, address)
    return _serialize_address(address)


