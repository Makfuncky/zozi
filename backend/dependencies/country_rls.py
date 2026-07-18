from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import CountryConfig, CountryStaffAssignment
from utils.rls_interceptor import set_rls_context, clear_rls_context
from services.logistics_partner_pricing import normalize_country_code

logger = logging.getLogger(__name__)


def get_country_scope_from_db(user_id: int, db: Session) -> Optional[set[str]]:
    assignments = (
        db.query(CountryStaffAssignment.country_code)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    codes = {normalize_country_code(row[0]) for row in assignments if row[0]}
    return codes if codes else None


def get_current_country_scope(request: Request, db: Session = Depends(get_db)) -> Optional[set[str]]:
    user = getattr(request.state, "user", None)
    if user is None:
        return None

    user_id = getattr(user, "id", None)
    if user_id is None:
        return None

    role = str(getattr(user, "role", "") or "").lower()
    if role in ("admin", "super_admin"):
        return None

    staff_codes = getattr(user, "staff_country_codes", None)
    if staff_codes and isinstance(staff_codes, (list, tuple)):
        codes = {normalize_country_code(str(c)) for c in staff_codes if c}
        if codes:
            return codes

    scope = get_country_scope_from_db(user_id, db)
    if scope:
        request.state.country_scope = scope
        request.state.country_is_restricted = True
        return scope

    return None


def enforce_country_access(country_code: str, request: Request, db: Session = Depends(get_db)) -> str:
    scope = getattr(request.state, "country_scope", None)
    is_restricted = getattr(request.state, "country_is_restricted", False)

    normalized = normalize_country_code(country_code)

    if is_restricted and scope is not None:
        if normalized not in scope:
            raise HTTPException(
                status_code=403,
                detail=f"You do not have access to country '{country_code}'",
            )
        return normalized

    user = getattr(request.state, "user", None)
    if user is not None:
        role = str(getattr(user, "role", "") or "").lower()
        if role in ("admin", "super_admin"):
            return normalized

        staff_codes = getattr(user, "staff_country_codes", None)
        if staff_codes and isinstance(staff_codes, (list, tuple)):
            if normalized not in {normalize_country_code(str(c)) for c in staff_codes if c}:
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have access to country '{country_code}'",
                )
            return normalized

    return normalized


def get_country_or_404(code: str, db: Session) -> CountryConfig:
    normalized = normalize_country_code(code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country config not found")
    return country


def set_rls_context_for_request(scope: Optional[set[str]]) -> None:
    clear_rls_context()
    if scope:
        set_rls_context(scope, is_restricted=True)


def clear_rls_context_for_request() -> None:
    clear_rls_context()
