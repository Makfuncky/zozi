from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Callable, Generator

from utils.rls_interceptor import clear_rls_context, set_rls_context

logger = logging.getLogger(__name__)


def _resolve_user_scope(user_id: int, session_factory: Callable) -> tuple[set[str] | None, bool]:
    """Resolve user's country scope from DB. Called by service layer."""
    db = session_factory()
    try:
        from data.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return None, False

        staff_codes = getattr(user, "staff_country_codes", None)
        if staff_codes and isinstance(staff_codes, (list, set)):
            codes = {str(c).upper().strip() for c in staff_codes if c}
            return (codes if codes else None), bool(codes)

        preferred = getattr(user, "preferred_country", None)
        if preferred:
            return {preferred.upper().strip()}, True

        role = getattr(user, "role", "customer") or "customer"
        if role in {"admin", "super_admin"}:
            return None, False
        return None, True
    finally:
        db.close()


@contextmanager
def rls_context_for_user(
    user_id: int | None = None,
    country_codes: set[str] | None = None,
    role: str | None = None,
    session_factory: Callable | None = None,
) -> Generator[None, Any, None]:
    """Provide an RLS security context for non-HTTP code (cron, celery, scripts).

    Usage:
        with rls_context_for_user(user_id=42):
            orders = db.query(Order).all()  # auto-filtered by user's country scope

        with rls_context_for_user(country_codes={"SA", "AE"}):
            suppliers = db.query(SupplierProfile).all()

        with rls_context_for_user(role="admin"):
            db.query(Order).all()  # unrestricted
    """
    if country_codes is not None:
        set_rls_context(country_codes, is_restricted=True)
        try:
            yield
        finally:
            clear_rls_context()
        return

    if role in {"admin", "super_admin"}:
        set_rls_context(None, is_restricted=False)
        try:
            yield
        finally:
            clear_rls_context()
        return

    if user_id is not None:
        if session_factory is None:
            from data.db import SessionLocal
            session_factory = SessionLocal
        codes, is_restricted = _resolve_user_scope(user_id, session_factory)
        set_rls_context(codes, is_restricted=is_restricted)
        try:
            yield
        finally:
            clear_rls_context()
        return

    set_rls_context(None, is_restricted=True)
    try:
        yield
    finally:
        clear_rls_context()


@contextmanager
def rls_context_global_admin() -> Generator[None, Any, None]:
    """Convenience: unrestricted access for system-level operations."""
    set_rls_context(None, is_restricted=False)
    try:
        yield
    finally:
        clear_rls_context()
