"""Admin support tickets controller (CONTROLLERS layer).

Canonical coordinator for admin support ticket management. Enforces country
RLS and delegates to ``services.admin.tickets_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import get, post, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.tickets_service import (
    get_ticket_detail,
    list_tickets,
    reply_to_ticket,
    update_ticket_status,
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
    "/api/v1/admin/tickets/{country_code}",
    deps=["db", "admin"],
    query=["status", "page", "page_size"],
    tags=["admin-tickets"],
)
def list_tickets_route(
    country_code: str,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return list_tickets(db, status=status, limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/tickets/{country_code}/{ticket_id}",
    deps=["db", "admin"],
    tags=["admin-tickets"],
)
def ticket_detail(
    country_code: str,
    ticket_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_ticket_detail(ticket_id, db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/tickets/{country_code}/{ticket_id}/reply",
    deps=["db", "admin"],
    tags=["admin-tickets"],
)
def reply_ticket(
    country_code: str,
    ticket_id: int,
    message: str = "",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return reply_to_ticket(ticket_id, message, _actor(current_user), db)
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/tickets/{country_code}/{ticket_id}/status",
    deps=["db", "admin"],
    tags=["admin-tickets"],
)
def update_ticket_status_route(
    country_code: str,
    ticket_id: int,
    status: str = "open",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return update_ticket_status(ticket_id, status, _actor(current_user), db)
    finally:
        clear_rls_context()
