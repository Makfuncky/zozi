"""suppliers domain - Pydantic response/request schemas.

Defines the serialization contracts for supplier-facing and admin-facing
endpoints. Services build these schema instances; routers return them directly.
All schemas are read models — they never map to ORM columns directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupplierProfileSchema(BaseModel):
    """Public supplier profile view (storefront and admin)."""

    id: int
    user_id: int
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    slug: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    verification_status: str = "unverified"
    badge_level: Optional[str] = None
    credibility_score: float = 0.0
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SupplierSummarySchema(BaseModel):
    """Lightweight supplier summary for list endpoints."""

    id: int
    username: str
    email: str
    is_active: bool = True
    is_verified: bool = False
    product_count: int = 0
    order_count: int = 0
    revenue: float = 0.0
    verification_status: str = "pending"
    badge_level: Optional[str] = None
    created_at: Optional[datetime] = None


class SupplierVerificationRequest(BaseModel):
    """Payload for verifying or rejecting a supplier."""

    action: str = Field(..., pattern="^(verify|reject)$")
    note: Optional[str] = None


class SupplierBulkVerificationRequest(BaseModel):
    """Payload for bulk supplier verification operations."""

    supplier_ids: list[int] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern="^(verify|reject)$")
    note: Optional[str] = None


class SupplierStatusFilter(BaseModel):
    """Filter parameters for supplier list endpoints."""

    q: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(all|pending|approved|rejected|suspended|active|archived)$")
    badge: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


__all__ = [
    "SupplierProfileSchema",
    "SupplierSummarySchema",
    "SupplierVerificationRequest",
    "SupplierBulkVerificationRequest",
    "SupplierStatusFilter",
]
