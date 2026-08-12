"""Admin payouts controller (CONTROLLERS layer).

Canonical coordinator for admin payout verification. Delegates to
``services.admin.payouts_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import get, post

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.payouts_service import list_pending_payouts, verify_payout


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
    "/api/v1/admin/payouts/{country_code}/pending",
    deps=["db", "admin"],
    query=["page", "page_size"],
    tags=["admin-payouts"],
)
def list_pending_payouts_route(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return list_pending_payouts(db, limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/payouts/{country_code}/{payout_id}/verify",
    deps=["db", "admin"],
    tags=["admin-payouts"],
)
def verify_payout_route(
    country_code: str,
    payout_id: int,
    status: str = "completed",
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        data = {
            "status": status,
            "reference": reference,
            "notes": notes,
        }
        return verify_payout(payout_id, data, _actor(current_user), db)
    finally:
        clear_rls_context()
