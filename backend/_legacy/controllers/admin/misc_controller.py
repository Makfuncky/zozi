"""Admin system/misc controller (CONTROLLERS layer).

Canonical coordinator for admin system endpoints (database overview, etc.).
Delegates to ``services.admin.database_service``.

HTTP contract declared with ``core.route_contract`` decorators.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from core.route_contract import get

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.database_service import get_database_overview


def _with_rls(country_code: str, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/system/database-overview/{country_code}",
    deps=["db", "admin"],
    tags=["admin-system"],
)
def database_overview(
    country_code: str,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_database_overview(db)
    finally:
        clear_rls_context()
