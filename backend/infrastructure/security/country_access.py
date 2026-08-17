"""Country access gate — platform-layer security primitive.

This is the canonical home for ``require_country_access`` (previously defined in
``modules/admin/routers/auth.py``). Domains must NOT import from ``modules/``
(NEW_STRUCTURE.md Law 1); they import this primitive from ``infrastructure/security``
instead. Routers may still call the module copy; both must stay behaviour-identical.
"""

from __future__ import annotations

from fastapi import HTTPException


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
