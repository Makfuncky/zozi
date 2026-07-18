"""
Address Controller — business logic for normalised address book.

Endpoints exposed at /users/me/addresses:
  GET    /                → list all addresses for current user
  POST   /                → create new address
  PUT    /{id}            → update address fields
  DELETE /{id}            → delete address
  POST   /{id}/set-default → make address the default
"""
from typing import List, cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from controllers.audit_controller import audit_log, AuditAction
from models import Address
from db.schemas import AddressCreate, AddressOut, AddressUpdate


def list_addresses(user_id: int, db: Session) -> List[Address]:
    return (
        db.query(Address)
        .filter(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .all()
    )


def create_address(user_id: int, body: AddressCreate, current_user: dict, db: Session) -> Address:
    if body.is_default:
        # Clear existing default for this user
        db.query(Address).filter(
            Address.user_id == user_id, Address.is_default == True  # noqa: E712
        ).update({"is_default": False})

    addr = Address(
        user_id=user_id,
        label=body.label,
        street=body.street,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country=body.country,
        is_default=body.is_default,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    audit_log(
        db,
        action=AuditAction.ADDRESS_CREATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"label": addr.label, "is_default": addr.is_default},
    )
    return addr


def update_address(address_id: int, user_id: int, body: AddressUpdate, current_user: dict, db: Session) -> Address:
    addr = _get_own_address(address_id, user_id, db)
    updates = body.model_dump(exclude_unset=True)

    if body.is_default is True:
        db.query(Address).filter(
            Address.user_id == user_id, Address.is_default == True  # noqa: E712
        ).update({"is_default": False})

    for field, value in updates.items():
        setattr(addr, field, value)

    db.commit()
    db.refresh(addr)
    audit_log(
        db,
        action=AuditAction.ADDRESS_UPDATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"updated_fields": sorted(updates.keys())},
    )
    return addr


def delete_address(address_id: int, user_id: int, current_user: dict, db: Session) -> None:
    addr = _get_own_address(address_id, user_id, db)
    address_label = addr.label
    db.delete(addr)
    db.commit()
    audit_log(
        db,
        action=AuditAction.ADDRESS_DELETED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=address_id,
        details={"label": address_label},
    )


def set_default_address(address_id: int, user_id: int, current_user: dict, db: Session) -> Address:
    # Clear old default
    db.query(Address).filter(
        Address.user_id == user_id, Address.is_default == True  # noqa: E712
    ).update({"is_default": False})

    addr = _get_own_address(address_id, user_id, db)
    setattr(addr, "is_default", True)
    db.commit()
    db.refresh(addr)
    audit_log(
        db,
        action=AuditAction.ADDRESS_SET_DEFAULT,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"label": addr.label},
    )
    return addr


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_own_address(address_id: int, user_id: int, db: Session) -> Address:
    addr = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id,
    ).first()
    if not addr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found.",
        )
    return addr

