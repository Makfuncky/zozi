"""HR permission helpers — standalone wrappers around RBACService."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def check_permission(user_id: int, permission: str, country_code: str, db) -> bool:
    """Check if user has a specific permission for a country.

    Wraps ``RBACService.check_permission`` for use in domain services
    that need a standalone function call.

    Returns True if the user has the permission (and country scope if provided),
    False otherwise. Failures are logged and return False (fail-closed).
    """
    try:
        from domains.accounts.services.permissions.permission_service import RBACService

        svc = RBACService(db)
        return svc.check_permission(user_id, permission, country_code)
    except Exception as exc:
        logger.warning("check_permission failed for user %s perm %s: %s", user_id, permission, exc)
        return False
