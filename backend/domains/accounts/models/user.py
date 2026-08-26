"""Governance & accounts domain user models.

Pure re-export shim — converts duplicate inline table definitions to lazy
re-export shims so SQLAlchemy registry conflicts (InvalidRequestError) are
avoided. Canonical homes:
  - User, UserDevice, UserLoginHistory, PasswordResetToken,
    EmailVerificationToken
    -> domains.governance.models.user (canonical)
  - OtpCode -> domains.accounts.models.otp (canonical)
  - SocialIdentity -> domains.accounts.models.social (canonical)
  - Referral, ReferralPointEvent -> domains.customers.models.customer_schema_models (canonical)
"""
from __future__ import annotations

__all__ = [
    "User",
    "UserDevice",
    "UserLoginHistory",
    "Referral",
    "ReferralPointEvent",
    "PasswordResetToken",
    "EmailVerificationToken",
    "OtpCode",
    "SocialIdentity",
]

# Canonical export map: class name -> (module_path, class_name)
_CANONICAL_EXPORTS = {
    # governance domain (canonical home for user/account models)
    "User": ("domains.governance.models.user", "User"),
    "UserLoginHistory": ("domains.governance.models.user", "UserLoginHistory"),
    "UserDevice": ("domains.governance.models.user", "UserDevice"),
    "PasswordResetToken": ("domains.governance.models.user", "PasswordResetToken"),
    "EmailVerificationToken": ("domains.governance.models.user", "EmailVerificationToken"),
    # accounts domain (canonical home)
    "OtpCode": ("domains.accounts.models.otp", "OtpCode"),
    "SocialIdentity": ("domains.accounts.models.social", "SocialIdentity"),
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
