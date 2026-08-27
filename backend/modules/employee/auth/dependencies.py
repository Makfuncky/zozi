"""Canonical auth dependencies for the employee module.

Per ``ARCHITECTURE_DIAGRAM.md`` the employee module keeps a thin HTTP surface;
the actual role/session gates live here (re-exported from the platform-wide
sources) so every employee router imports its auth from one place.
"""
from domains.security.services.iam.security_dependencies import require_employee, require_roles, get_current_user  # noqa: F401

__all__ = ["require_employee", "require_roles", "get_current_user"]
