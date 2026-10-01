"""Canonical auth dependencies for the customer module.

Per ``ARCHITECTURE_DIAGRAM.md`` the customer module keeps a thin HTTP surface;
the actual role/session gates live here (re-exported from the platform-wide
sources) so every customer router imports its auth from one place.
"""
from domains.accounts.services.auth.security_dependencies import require_customer, require_roles, get_current_user  # noqa: F401

__all__ = ["require_customer", "require_roles", "get_current_user"]
