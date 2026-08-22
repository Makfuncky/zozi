"""CountryStaffAssignment request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CountryStaffAssignmentCreate(BaseModel):
    """Request DTO for assigning staff to a country."""
    user_id: int
    country_code: str = Field(..., min_length=2, max_length=3)
    role_in_country: str = Field(default="country_manager", max_length=40)
    notes: Optional[str] = None


class CountryStaffAssignmentUpdate(BaseModel):
    """Request DTO for updating a staff assignment."""
    role_in_country: Optional[str] = Field(None, max_length=40)
    is_active: Optional[bool] = None
    notes: Optional[str] = None
