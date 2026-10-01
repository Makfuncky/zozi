"""Shared admin constants and helpers.

Extracted from ``controllers.admin`` so that admin controller submodules do not
import one another (W4) and to break the circular controller dependency (DG2).
These symbols back admin user/role/bank-account validation and are intentionally
free of any controller or ORM dependencies.
"""
from __future__ import annotations

from fastapi import HTTPException
import structlog
logger = structlog.get_logger(__name__)

VALID_USER_ROLES = {"customer", "supplier", "admin", "sub_admin", "moderator", "support"}

ALLOWED_BANK_ACCOUNT_KINDS = {"supplier", "logistics_partner"}


def require_admin_role(current_user: dict) -> None:
    """Raise 403 unless the acting user holds an admin or sub_admin role."""
    role = current_user["role"]
    if role not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required.")
