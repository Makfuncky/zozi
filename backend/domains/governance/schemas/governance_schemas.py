"""governance domain — request/response DTOs (Pydantic schemas).

Each schema maps to a governance operation or model projection. Routers use these
to validate incoming requests and shape outgoing responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Permission & Role ----------------------------------------------------------


class PermissionCreate(BaseModel):
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=150)
    category_id: int
    description: Optional[str] = None
    scope: str = Field("global", max_length=20)


class PermissionResponse(BaseModel):
    id: int
    name: str
    slug: str
    category_id: int
    description: Optional[str] = None
    scope: str
    is_active: bool
    country_code: str
    created_at: Optional[datetime] = None


class RolePermissionUpdate(BaseModel):
    role: str = Field(..., max_length=80)
    permissions: list[str]


class RolePermissionResponse(BaseModel):
    role: str
    permissions: list[str]
    updated: int


# -- User management ------------------------------------------------------------


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: str = "customer"
    country_code: str = Field("OM", max_length=10)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None


class BulkUserAction(BaseModel):
    user_ids: list[int]
    action: str
    role: Optional[str] = None
    is_active: Optional[bool] = None
    note: Optional[str] = None


class ForcePasswordReset(BaseModel):
    user_id: int
    new_password: str


# -- Staff management -----------------------------------------------------------


class StaffCreate(BaseModel):
    email: str
    username: str
    password: str
    role: str
    country_code: str = Field("OM", max_length=10)
    department: Optional[str] = None


class StaffUpdate(BaseModel):
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


# -- Supplier management -------------------------------------------------------


class SupplierVerifyRequest(BaseModel):
    user_id: int
    note: Optional[str] = None


class SupplierRejectRequest(BaseModel):
    user_id: int
    note: Optional[str] = None


class BulkSupplierRequest(BaseModel):
    supplier_ids: list[int]
    action: str
    note: Optional[str] = None
    badge_level: Optional[str] = None


# -- Order management -----------------------------------------------------------


class OrderStatusUpdate(BaseModel):
    order_id: int
    status: str


class OrderRefundRequest(BaseModel):
    order_id: int
    reason: Optional[str] = None


class OrderTrackingUpdate(BaseModel):
    order_id: int
    tracking_number: str


class BulkOrderRequest(BaseModel):
    order_ids: list[int]
    status: Optional[str] = None


# -- Product management ---------------------------------------------------------


class ProductModerationRequest(BaseModel):
    product_ids: list[int]
    action: str
    note: Optional[str] = None


class ProductBadgeToggle(BaseModel):
    product_id: int
    field: str
    value: bool


# -- Treasury -------------------------------------------------------------------


class PayoutVerifyRequest(BaseModel):
    payout_id: int


class CodRemittanceRequest(BaseModel):
    country_code: str = Field(..., max_length=10)
    order_id: int
    partner_id: int
    amount: float
    bank_reference: str


# -- Audit & Analytics ----------------------------------------------------------


class AuditLogResponse(BaseModel):
    id: int
    action: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


class AnalyticsSnapshotResponse(BaseModel):
    id: int
    metric: str
    value: Optional[float] = None
    dimensions: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


# -- Incident -------------------------------------------------------------------


class IncidentCreate(BaseModel):
    title: str
    severity: str = "medium"
    description: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    created_at: Optional[datetime] = None


# -- Generic responses ----------------------------------------------------------


class BulkActionResponse(BaseModel):
    processed: int
    succeeded: int
    failed: int
    errors: list[str] = []


class ArchiveResponse(BaseModel):
    entity_type: str
    entity_id: int
    archived: bool


class StatusResponse(BaseModel):
    status: str
    detail: Optional[str] = None
