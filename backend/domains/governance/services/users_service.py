"""Governance domain — user administration service (keyset pagination)."""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from domains.accounts.models.user import User
from domains.governance.models.admin import SupplierBankAccount, LogisticsPartnerBankAccount
from domains.suppliers.models.suppliers import SupplierProfile
from domains.logistics.models.logistics_entities import LogisticsPartner
from domains.governance.ports import FinanceBankAccount
from infrastructure.utils.pagination import keyset_paginate, keyset_offset_window


def list_users_keyset(
    db: Session,
    cursor: str | None = None,
    page_size: int = 50,
    role: str | None = None,
    search: str | None = None,
    country_code: str | None = None,
) -> dict:
    """Keyset-paginated user list (never OFFSET)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if country_code:
        query = query.filter(User.country_code == country_code)
    return keyset_paginate(
        query,
        sort_keys=[(User.id, "asc")],
        cursor=cursor,
        page_size=page_size,
    )


def get_all_users(
    db: Session,
    offset: int = 0,
    limit: int = 50,
    role: str | None = None,
    search: str | None = None,
) -> dict:
    """Adoption-layer user list using keyset_offset_window."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))
    items = keyset_offset_window(
        query,
        sort_keys=[(User.id, "asc")],
        offset=offset,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "country_code": u.country_code,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in items
        ],
        "count": len(items),
    }


def list_pending_bank_accounts(
    kind: str,
    db: Session,
    current_user: dict,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    """Adoption-layer pending bank accounts using keyset_offset_window."""
    if kind == "supplier":
        query = (
            db.query(SupplierBankAccount, User.email, SupplierProfile.business_name)
            .join(User, SupplierBankAccount.supplier_id == User.id)
            .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
            .filter(SupplierBankAccount.verification_status == "pending")
        )
        sort_keys = [(SupplierBankAccount.created_at, "asc")]
        items = keyset_offset_window(query, sort_keys=sort_keys, offset=offset, limit=limit)
        return {
            "items": [
                {
                    "id": r.SupplierBankAccount.id,
                    "supplier_id": r.SupplierBankAccount.supplier_id,
                    "entity_name": r.business_name or r.email or str(r.SupplierBankAccount.supplier_id),
                    "bank_name": r.SupplierBankAccount.bank_name,
                    "verification_status": r.SupplierBankAccount.verification_status,
                    "created_at": r.SupplierBankAccount.created_at.isoformat() if r.SupplierBankAccount.created_at else None,
                }
                for r in items
            ],
            "count": len(items),
        }
    else:
        query = (
            db.query(LogisticsPartnerBankAccount, LogisticsPartner.name)
            .join(LogisticsPartner, LogisticsPartnerBankAccount.partner_id == LogisticsPartner.id)
            .filter(LogisticsPartnerBankAccount.verification_status == "pending")
        )
        sort_keys = [(LogisticsPartnerBankAccount.created_at, "asc")]
        items = keyset_offset_window(query, sort_keys=sort_keys, offset=offset, limit=limit)
        return {
            "items": [
                {
                    "id": r.LogisticsPartnerBankAccount.id,
                    "partner_id": r.LogisticsPartnerBankAccount.partner_id,
                    "entity_name": r.name or str(r.LogisticsPartnerBankAccount.partner_id),
                    "bank_name": r.LogisticsPartnerBankAccount.bank_name,
                    "verification_status": r.LogisticsPartnerBankAccount.verification_status,
                    "created_at": r.LogisticsPartnerBankAccount.created_at.isoformat() if r.LogisticsPartnerBankAccount.created_at else None,
                }
                for r in items
            ],
            "count": len(items),
        }


def list_users_basic(
    db: Session,
    offset: int = 0,
    limit: int = 50,
    is_active: bool | None = None,
) -> dict:
    """Adoption-layer basic user list using keyset_offset_window."""
    query = db.query(User)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    items = keyset_offset_window(
        query,
        sort_keys=[(User.id, "asc")],
        offset=offset,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
            }
            for u in items
        ],
        "count": len(items),
    }
