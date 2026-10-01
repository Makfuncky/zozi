"""Canonical auth dependencies for the supplier module.

Per ``ARCHITECTURE_DIAGRAM.md`` the supplier module keeps a thin HTTP surface;
the actual role/session gates live here (re-exported from the platform-wide
sources) so every supplier router imports its auth from one place.
"""
from domains.accounts.services.auth.security_dependencies import require_admin, require_supplier, get_current_user  # noqa: F401
from domains.accounts.services.auth.security_dependencies import require_roles

__all__ = ["require_supplier", "require_admin", "require_roles", "get_current_user"]
