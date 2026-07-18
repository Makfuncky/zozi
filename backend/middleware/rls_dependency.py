from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from services.coi_service import check_approval_blocked
from db.database import get_db


class CountryAccessScope:
    def __init__(self, country_codes: list[str]):
        self.country_codes = country_codes
    
    def has_access(self, country_code: str) -> bool:
        return country_code.upper() in [c.upper() for c in self.country_codes]


def get_country_access_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    if not current_user:
        return CountryAccessScope([])
    
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return CountryAccessScope(["ALL"])
    
    codes = current_user.get("staff_country_codes", [])
    return CountryAccessScope(codes or [])


def get_country_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    return get_country_access_scope(current_user)


def check_coi_before_approval(
    approver_user_id: int,
    employee_id: int,
    db: Session,
) -> None:
    blocked, reason = check_approval_blocked(approver_user_id, employee_id, db)
    if blocked:
        raise HTTPException(
            status_code=403,
            detail=f"Approval blocked due to Conflict of Interest: {reason}"
        )

