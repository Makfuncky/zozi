"""Admin audit controller (CONTROLLERS layer).

Canonical coordinator for admin audit-log browsing. Delegates to
``services.admin.misc_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import get

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.misc_service import get_audit_log_page, get_available_audit_actions


def _with_rls(country_code: str, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/audit/{country_code}",
    deps=["db", "admin"],
    permissions=["audit.view"],
    query=["page", "page_size", "action_filter", "user_id_filter", "resource_type_filter", "status_filter", "search"],
    tags=["admin-audit"],
)
def audit_log_page(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_audit_log_page(
            db,
            page=page,
            page_size=page_size,
            action_filter=action_filter,
            user_id_filter=user_id_filter,
            resource_type_filter=resource_type_filter,
            status_filter=status_filter,
            search=search,
        )
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/audit/{country_code}/actions",
    deps=["db", "admin"],
    tags=["admin-audit"],
)
def audit_actions(
    country_code: str,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_available_audit_actions(db)
    finally:
        clear_rls_context()
