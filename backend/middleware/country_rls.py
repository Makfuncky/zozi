from __future__ import annotations

from typing import Optional, Set
from contextvars import ContextVar

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db
from models import CountryStaffAssignment, User, LogisticsPartner, SupplierProfile, CommissionAgreement

_rls_models = [LogisticsPartner, SupplierProfile, CommissionAgreement]

_country_scope_var: ContextVar[Set[str]] = ContextVar('country_scope', default=set())


def set_country_scope(scope: Set[str]) -> None:
    _country_scope_var.set(scope)


def get_current_country_scope() -> Set[str]:
    return _country_scope_var.get()


class CountryAccessScope:
    def __init__(self, country_codes: Set[str], role: str = "customer"):
        self.country_codes = country_codes
        self.role = role
    
    def has_access(self, country_code: str) -> bool:
        if not country_code:
            return False
        upper_code = country_code.upper()
        if "ALL" in self.country_codes:
            return True
        return upper_code in self.country_codes
    
    def get_allowed_countries(self) -> Set[str]:
        return self.country_codes


def get_country_access_scope(
    request: Request,
    db: Session = Depends(get_db)
) -> CountryAccessScope:
    user = getattr(request.state, 'user', None)
    if not user:
        return CountryAccessScope(set(), "customer")
    
    role = str(user.get("role") or "").lower()
    if role == "admin":
        return CountryAccessScope({"ALL"}, role)
    
    user_id = user.get("id")
    if not user_id:
        return CountryAccessScope(set(), role)
    
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    
    country_codes = {a.country_code for a in assignments}
    return CountryAccessScope(country_codes, role)


def require_country_access(country_code: str, scope: CountryAccessScope = Depends(get_country_access_scope)) -> None:
    if not scope.has_access(country_code):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


def get_country_scope(current_user: Optional[dict] = None) -> CountryAccessScope:
    if not current_user:
        return CountryAccessScope(set(), "customer")
    
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return CountryAccessScope({"ALL"}, role)
    
    codes = current_user.get("staff_country_codes", [])
    return CountryAccessScope(set(c.upper() for c in codes) if codes else set(), role)


def check_country_access_decorator(current_user: dict, country_code: str) -> None:
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return
    
    codes = current_user.get("staff_country_codes", [])
    if not codes:
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    
    if country_code.upper() not in [str(c).strip().upper() for c in codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


def enforce_rls_on_model(db: Session, model_instance, current_user: dict) -> bool:
    """Check if user has access to the given model instance based on country_code."""
    if not model_instance or not hasattr(model_instance, 'country_code'):
        return True
    
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return True
    
    instance_country = getattr(model_instance, 'country_code', None)
    if not instance_country:
        return True
    
    allowed_codes = current_user.get("staff_country_codes", [])
    if not allowed_codes:
        return False
    
    return instance_country.upper() in [str(c).strip().upper() for c in allowed_codes]


def filter_by_country(db: Session, query, model_class, current_user: dict):
    """Apply country-based filtering to a query."""
    if not issubclass(model_class, tuple(_rls_models)):
        return query
    
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return query
    
    allowed_codes = current_user.get("staff_country_codes", [])
    if not allowed_codes:
        return query.filter(False)
    
    country_codes = [str(c).strip().upper() for c in allowed_codes]
    return query.filter(model_class.country_code.in_(country_codes))

