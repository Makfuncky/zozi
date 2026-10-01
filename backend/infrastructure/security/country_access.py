"""Country access gate — platform-layer security primitive.

This is the canonical home for ``require_country_access`` (previously defined in
``modules/admin/routers/auth.py``). Domains must NOT import from ``modules/``
(NEW_STRUCTURE.md Law 1); they import this primitive from ``infrastructure/security``
instead. Routers may still call the module copy; both must stay behaviour-identical.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException


class CountryAccessScope:
    """Orthogonal country scope (Law 5): the set of country codes an actor may act on."""

    def __init__(self, country_codes: list[str]):
        self.country_codes = country_codes

    def has_access(self, country_code: str) -> bool:
        return country_code.upper() in [c.upper() for c in self.country_codes]


def get_country_access_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    """Resolve the caller's country scope (admin → ALL, else staff_country_codes)."""
    if not current_user:
        return CountryAccessScope([])

    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return CountryAccessScope(["ALL"])

    codes = current_user.get("staff_country_codes", [])
    return CountryAccessScope(codes or [])


def get_country_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    """Backward-compatible alias for ``get_country_access_scope``."""
    return get_country_access_scope(current_user)


def require_country_access(country_code: str, current_user) -> None:
    """Ensure the current user can manage the given country.

    Full admins can access any country. Country-heads and country-managers
    are restricted to their ``staff_country_codes`` list.
    """
    role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if role == "admin":
        return
    if role not in ("country_head", "country_manager"):
        raise HTTPException(status_code=403, detail="Country-level access required")
    allowed_codes = (
        current_user.get("staff_country_codes")
        if isinstance(current_user, dict)
        else getattr(current_user, "staff_country_codes", None)
    )
    if not allowed_codes or not isinstance(allowed_codes, (list, tuple)):
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    if country_code not in [str(c).strip().upper() for c in allowed_codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )
