from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

from db.database import SessionLocal
from models import User
from utils.rls_interceptor import clear_rls_context, set_rls_context

logger = logging.getLogger(__name__)


@contextmanager
def rls_context_for_user(
    user_id: int | None = None,
    country_codes: set[str] | None = None,
    role: str | None = None,
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
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                set_rls_context(None, is_restricted=False)
            else:
                staff_codes = getattr(user, "staff_country_codes", None)
                if staff_codes and isinstance(staff_codes, (list, set)):
                    codes = {str(c).upper().strip() for c in staff_codes if c}
                    set_rls_context(codes if codes else None, is_restricted=bool(codes))
                else:
                    preferred = getattr(user, "preferred_country", None)
                    if preferred:
                        set_rls_context({preferred.upper().strip()}, is_restricted=True)
                    else:
                        role = getattr(user, "role", "customer") or "customer"
                        if role in {"admin", "super_admin"}:
                            set_rls_context(None, is_restricted=False)
                        else:
                            set_rls_context(None, is_restricted=True)
            try:
                yield
            finally:
                clear_rls_context()
        finally:
            db.close()
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

