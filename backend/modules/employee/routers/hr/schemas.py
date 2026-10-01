"""Shared Pydantic schemas — office/employee/document request bodies."""
from typing import Optional

from pydantic import BaseModel, Field


class OfficeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = True


class OfficeUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class EmployeeCreate(BaseModel):
    user_id: Optional[int] = None
    employee_code: Optional[str] = None
    office_id: Optional[int] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: str = "full_time"
    employment_status: str = "active"
    salary: Optional[float] = None
    currency: Optional[str] = None
    hire_date: Optional[str] = None
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    employment_status: Optional[str] = None
    salary: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    office_id: Optional[int] = None
    user_id: Optional[int] = None
    is_verified: Optional[bool] = None


class EmployeeDocumentCreate(BaseModel):
    document_type: str = Field(..., max_length=80)
    document_name: str = Field(..., max_length=200)
    file_url: str = Field(..., max_length=500)
    expires_at: Optional[str] = None
    notes: Optional[str] = None


class EmployeeDocumentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[str] = None


class CheckInBody(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    notes: Optional[str] = None


class CheckOutBody(BaseModel):
    notes: Optional[str] = None


class GeoCheckInBody(BaseModel):
    latitude: float
    longitude: float
    office_id: int
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    notes: Optional[str] = None


class RelationCreate(BaseModel):
    related_employee_id: int
    relation_type: str = "peer"
    notes: Optional[str] = None


class WorkLogCreate(BaseModel):
    date: Optional[str] = None
    hours_worked: float = 0
    description: Optional[str] = None


class WorkLogApprove(BaseModel):
    status: str = "approved"


class QrLoginBody(BaseModel):
    qr_token: str


class GeoValidateBody(BaseModel):
    latitude: float
    longitude: float
    office_id: int