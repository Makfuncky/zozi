"""Accounts domain — public facade.

Exports the public API for the accounts domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domains.accounts.services.auth.auth_service import AuthService
    from domains.accounts.services.permissions.permission_service import RBACService

# Lazy module-level attribute access — delegates to sub-modules without
# importing them at package load time (avoids circular imports).
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "AuthService": ("domains.accounts.services.auth.auth_service", "AuthService"),
    "RBACService": ("domains.accounts.services.permissions.permission_service", "RBACService"),
    "SessionService": ("domains.accounts.services.sessions.session_service", "SessionService"),
    "IdentityAdminService": ("domains.accounts.services.identity.identity_admin_service", "IdentityAdminService"),
    "BiometricAuthService": ("domains.accounts.services.auth.auth_service", "BiometricAuthService"),
    "TripleAuthService": ("domains.accounts.services.auth.auth_service", "TripleAuthService"),
    # functions
    "load_role_permission_settings": ("domains.accounts.services.permissions.permission_service", "load_role_permission_settings"),
    "check_user_permission": ("domains.accounts.services.permissions.permission_service", "check_user_permission"),
    "get_role_permissions": ("domains.accounts.services.permissions.permission_service", "get_role_permissions"),
    "create_rbac_service": ("domains.accounts.services.permissions.permission_service", "create_rbac_service"),
    "create_user": ("domains.accounts.services.auth.auth_service", "create_user"),
    "get_user_by_id": ("domains.accounts.services.auth.auth_service", "get_user_by_id"),
    # models
    "User": ("domains.accounts.models.user", "User"),
    "UserProfile": ("domains.accounts.models.user", "UserProfile"),
    "UserSession": ("domains.accounts.models.user", "UserSession"),
    "EmailVerificationToken": ("domains.accounts.models.user", "EmailVerificationToken"),
    "PasswordResetToken": ("domains.accounts.models.user", "PasswordResetToken"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.accounts' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
