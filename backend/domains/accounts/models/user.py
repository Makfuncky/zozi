"""Governance domain user models.

Pure re-export shim — converts duplicate inline table definitions to lazy
re-export shims so SQLAlchemy registry conflicts (InvalidRequestError) are
avoided. Canonical homes:
  - User, UserDevice, UserLoginHistory, PasswordResetToken,
    EmailVerificationToken, RevokedToken, OtpCode, SocialIdentity
    -> domains.accounts.models.user (canonical)
  - Referral, ReferralPointEvent -> domains.customers.models.customer_schema_models (canonical)
"""
from __future__ import annotations

__all__ = [
    "User",
    "UserDevice",
    "Referral",
    "ReferralPointEvent",
    "PasswordResetToken",
    "EmailVerificationToken",
    "RevokedToken",
    "UserLoginHistory",
    "OtpCode",
    "SocialIdentity",
]

# Canonical export map: class name -> (module_path, class_name)
_CANONICAL_EXPORTS = {
    # accounts domain (canonical home)
    "User": ("domains.accounts.models.user", "User"),
    "UserLoginHistory": ("domains.accounts.models.user", "UserLoginHistory"),
    "UserDevice": ("domains.accounts.models.user", "UserDevice"),
    "PasswordResetToken": ("domains.accounts.models.user", "PasswordResetToken"),
    "EmailVerificationToken": ("domains.accounts.models.user", "EmailVerificationToken"),
    "RevokedToken": ("domains.accounts.models.user", "RevokedToken"),
    "OtpCode": ("domains.accounts.models.user", "OtpCode"),
    "SocialIdentity": ("domains.accounts.models.user", "SocialIdentity"),
    # customers domain (canonical home)
    "Referral": ("domains.customers.models.customer_schema_models", "Referral"),
    "ReferralPointEvent": ("domains.customers.models.customer_schema_models", "ReferralPointEvent"),
}

_IMPORTED: dict[str, object] = {}


def __getattr__(name: str):
    """Lazy import of canonical models to avoid circular imports and InvalidRequestError."""
    if name in _IMPORTED:
        return _IMPORTED[name]
    if name in _CANONICAL_EXPORTS:
        module_path, class_name = _CANONICAL_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
