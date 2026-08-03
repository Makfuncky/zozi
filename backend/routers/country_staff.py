"""
Country Staff Assignments Router
Handles assigning/removing users as country_head, country_manager, etc.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from data.dependencies_auth import get_current_user
from data.controllers_admin_controller import require_admin
from data.services_country_staff_service import (
    list_country_staff,
    assign_staff_to_country,
    update_staff_assignment,
    remove_staff_from_country,
    get_my_assigned_countries,
    list_all_staff_assignments,
)

router = APIRouter()


class StaffAssignBody(BaseModel):
    user_id: int
    role_in_country: str = Field(
        default="country_manager",
        description="One of: country_head, country_manager, country_finance, country_moderator",
    )
    notes: Optional[str] = None


class StaffUpdateBody(BaseModel):
    role_in_country: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/countries/{code}/staff")
def list_country_staff_endpoint(
    code: str,
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return list_country_staff(code, active_only, skip, limit)


@router.post("/countries/{code}/staff")
def assign_staff_to_country_endpoint(
    code: str,
    body: StaffAssignBody,
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)
    return assign_staff_to_country(code, body, current_user)


@router.patch("/countries/{code}/staff/{assignment_id}")
def update_staff_assignment_endpoint(
    code: str,
    assignment_id: int,
    body: StaffUpdateBody,
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)
    return update_staff_assignment(code, assignment_id, body)


@router.delete("/countries/{code}/staff/{user_id}")
def remove_staff_from_country_endpoint(
    code: str,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)
    return remove_staff_from_country(code, user_id)


@router.get("/staff/my-countries")
def get_my_assigned_countries_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return get_my_assigned_countries(current_user.get("id"), skip, limit)


@router.get("/staff/all-assignments")
def list_all_staff_assignments_endpoint(
    role: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)
    return list_all_staff_assignments(role, active_only, limit)
