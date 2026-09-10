"""Shared Pydantic schemas — leave/shift/role/org-unit/hierarchy/matrix/payroll."""
from typing import Optional

from pydantic import BaseModel, Field


class EmployeeRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = None
    permissions: Optional[dict] = None


class LeaveStatusUpdate(BaseModel):
    status: str = Field(..., description="approved or rejected")


class LeaveCreate(BaseModel):
    employee_id: Optional[int] = None
    leave_type: str = 'annual'
    start_date: str
    end_date: str
    notes: Optional[str] = None


class ShiftCreate(BaseModel):
    employee_id: int
    shift_date: str
    start_time: str
    end_time: str
    shift_type: str = 'scheduled'
    status: str = 'scheduled'


class OrgUnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None
    country_code: str
    level: int = 1


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None


class ManagerReassign(BaseModel):
    employee_user_id: int
    new_manager_user_id: int


class MatrixAssign(BaseModel):
    employee_id: int
    matrix_manager_id: int
    relation_type: str = "matrix_manager"
    notes: Optional[str] = None


class ApprovalChainQuery(BaseModel):
    employee_id: int
    resource_type: str = "leave"
    min_authority_level: Optional[int] = None


class PayrollApproveBody(BaseModel):
    batch_id: str
    approved: bool = True
    notes: Optional[str] = None