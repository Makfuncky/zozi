"""Admin bank-account verification controller (CONTROLLERS layer).

Canonical coordinator for supplier / logistics-partner bank-account verification.
Delegates to ``services.admin.users_service`` (bank-account helpers).

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import delete, get, post

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.users_service import (
    delete_bank_account_record,
    list_pending_bank_accounts,
    verify_bank_account,
)


def _actor(current_user) -> dict:
    if isinstance(current_user, dict):
        return {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
        }
    return {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }


def _with_rls(country_code: str, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/bank-accounts/{country_code}/pending",
    deps=["db", "admin"],
    query=["kind", "page", "page_size"],
    tags=["admin-bank-accounts"],
)
def list_pending_bank_accounts_route(
    country_code: str,
    kind: str = "supplier",
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return list_pending_bank_accounts(kind, db, _actor(current_user), limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/bank-accounts/{country_code}/{kind}/{account_id}/verify",
    deps=["db", "admin"],
    tags=["admin-bank-accounts"],
)
def verify_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    action: str = "approve",
    note: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return verify_bank_account(kind, account_id, action, note, _actor(current_user), db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/bank-accounts/{country_code}/{kind}/{account_id}",
    deps=["db", "admin"],
    tags=["admin-bank-accounts"],
)
def delete_bank_account_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return delete_bank_account_record(kind, account_id, _actor(current_user), db)
    finally:
        clear_rls_context()
