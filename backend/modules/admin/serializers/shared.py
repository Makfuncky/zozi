"""Admin serializers and shared view helpers.

Per ARCHITECTURE_DIAGRAM.md §3, modules/{actor}/serializers/ holds per-actor
view models (response shaping, field filtering). This module provides shared
admin validation helpers used by admin serializers and routers.
"""
from __future__ import annotations

import structlog

from pydantic import BaseModel

logger = structlog.get_logger(__name__)

VALID_USER_ROLES = {"customer", "supplier", "admin", "sub_admin", "moderator", "support"}

ALLOWED_BANK_ACCOUNT_KINDS = {"supplier", "logistics_partner"}


class AdminRoleCheckRequest(BaseModel):
    """Request model for admin role validation."""
    role: str


def is_admin_role(role: str) -> bool:
    """Return True if the role is an admin-level role."""
    return role in {"admin", "sub_admin"}


def validate_user_role(role: str) -> bool:
    """Return True if the role is a valid user role."""
    return role in VALID_USER_ROLES


__all__ = [
    "VALID_USER_ROLES",
    "ALLOWED_BANK_ACCOUNT_KINDS",
    "AdminRoleCheckRequest",
    "is_admin_role",
    "validate_user_role",
]
