"""Reconstructed admin support handlers (audit + bank accounts + db overview).

During the `controllers -> domains/*/services` migration the original
`controllers.admin.*_controller` modules were removed. The auto-generated admin
routers still expect the `*_route` handler names. This module is the canonical
(domain-owned) home for those handlers: each one is a thin delegation to the
real domain service (`misc_service`, `users_service`) so the routers stay thin
and Law 1 (domains own logic, modules stay thin) is respected.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from infrastructure.utils.dependencies import require_admin
from domains.governance.services.settings.misc_service import (
    get_audit_log_page,
    get_available_audit_actions,
)
from domains.governance.services.users_service import (
    list_pending_bank_accounts,
    verify_bank_account,
)
from domains.governance.models.admin import SupplierBankAccount, LogisticsPartnerBankAccount
from domains.governance.models.user import User
from domains.orders.ports import Order
from domains.catalog.models.products import Product
from domains.suppliers.models import SupplierProfile


def audit_log_page(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
) -> dict:
    return get_audit_log_page(
        db=db,
        page=page,
        page_size=page_size,
        action_filter=action_filter,
        user_id_filter=user_id_filter,
        resource_type_filter=resource_type_filter,
        status_filter=status_filter,
        search=search,
    )


def audit_actions(
    country_code: str,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
) -> list:
    return get_available_audit_actions(db=db)


def list_pending_bank_accounts_route(
    country_code: str,
    kind: str = "supplier",
    page: int = 1,
    page_size: int = 50,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
) -> list:
    return list_pending_bank_accounts(
        kind=kind,
        db=db,
        current_user=current_user,
        limit=page_size,
        offset=max(0, (page - 1) * page_size),
    )


def verify_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
    action: str = "approve",
    note: Optional[str] = None,
) -> dict:
    return verify_bank_account(
        kind=kind,
        account_id=account_id,
        action=action,
        note=note,
        current_user=current_user,
        db=db,
    )


def delete_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
) -> dict:
    if current_user is not None and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete bank accounts")

    if kind == "supplier":
        record = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    else:
        record = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    db.delete(record)
    db.commit()
    return {"message": f"Bank account {account_id} deleted", "id": account_id}


def database_overview(
    country_code: str,
    current_user: Optional[dict] = None,
    db: Optional[Session] = None,
) -> dict:
    """Lightweight per-country table counts for the admin system dashboard."""
    cc = country_code.upper() if country_code and country_code != "*" else None

    def _count(model):
        q = db.query(func.count()).select_from(model)
        col = getattr(model, "country_code", None)
        if cc and col is not None:
            q = q.filter(col == cc)
        return q.scalar() or 0

    return {
        "country_code": country_code,
        "counts": {
            "users": _count(User),
            "orders": _count(Order),
            "products": _count(Product),
            "suppliers": _count(SupplierProfile),
        },
    }
