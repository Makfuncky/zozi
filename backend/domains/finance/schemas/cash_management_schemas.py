"""Finance cash-management request/response DTOs (domain schemas).

These Pydantic body classes were migrated out of ``finance_service.py`` so
the service contains only pure business logic (Law 14, Law 90).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FlagRequest(BaseModel):
    reason: str


class CodRemittanceRequest(BaseModel):
    # Law 19: Decimal for money — avoids binary-float artifacts (e.g. 0.1+0.2).
    # Law 42: Pydantic validation with non-negative bound.
    amount: Decimal = Field(..., ge=Decimal("0"), description="COD remittance amount")

    @field_validator("amount", mode="before")
    @classmethod
    def _coerce_amount(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        # Decimal(str()) keeps float/int/str callers compatible with identical business values.
        return Decimal(str(v))


class BadgeBillingPaymentRequest(BaseModel):
    payment_method: str
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None


class PayoutProcessRequest(BaseModel):
    settlement_ids: list[int] = []


class ReceiptReviewRequest(BaseModel):
    note: Optional[str] = None


class CommissionRateBody(BaseModel):
    # Law 19: Decimal for rates (Numeric(5,4) in DB) — Decimal(str()) avoids 0.1 float artifacts.
    # Law 42: Pydantic range validation preserved with Decimal bounds.
    rate: Decimal = Field(..., ge=Decimal("0"), le=Decimal("1"), description="Commission rate as decimal, e.g. 0.12 for 12%")
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("rate", mode="before")
    @classmethod
    def _coerce_rate(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class GlobalConfigBody(BaseModel):
    # Law 19: Decimal for money/rates (DB Numeric); Law 42: Decimal bounds.
    default_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    low_value_threshold: Optional[Decimal] = Field(None, ge=Decimal("0"))
    fixed_cap_amount: Optional[Decimal] = Field(None, ge=Decimal("0"))
    fixed_cap_enabled: Optional[bool] = None
    margin_protection_enabled: Optional[bool] = None
    margin_threshold: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))

    @field_validator("default_rate", "low_value_threshold", "fixed_cap_amount", "margin_threshold", mode="before")
    @classmethod
    def _coerce_decimals(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class CategoryRateBody(BaseModel):
    # Law 19: Decimal for rate; Law 42: Decimal bounds.
    rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    category_display_name: Optional[str] = Field(None, max_length=150)

    @field_validator("rate", mode="before")
    @classmethod
    def _coerce_rate(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class BadgeTierBody(BaseModel):
    # Law 19: Decimal for money/rates (DB Numeric(5,4) rates, Numeric(12,2)/(15,2) money).
    # Law 42: Decimal bounds; min_monthly_revenue newly bounded ge=0 (money is non-negative).
    commission_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    setup_fee: Optional[Decimal] = Field(None, ge=Decimal("0"))
    recurring_fee: Optional[Decimal] = Field(None, ge=Decimal("0"))
    recurring_interval: Optional[str] = Field(None, max_length=20)
    benefits_json: Optional[str] = None
    min_fulfilled_orders: Optional[int] = None
    min_monthly_revenue: Optional[Decimal] = Field(None, ge=Decimal("0"))
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("commission_rate", "setup_fee", "recurring_fee", "min_monthly_revenue", mode="before")
    @classmethod
    def _coerce_decimals(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class LedgerAdjustmentBody(BaseModel):
    # Law 19: Decimal for money (DB Numeric(12,2)); Law 42: non-negative bound.
    new_amount: Decimal = Field(..., ge=Decimal("0"))
    reason: str = Field(..., min_length=5, max_length=1000)

    @field_validator("new_amount", mode="before")
    @classmethod
    def _coerce_new_amount(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class PreviewBody(BaseModel):
    supplier_id: int
    # Law 19: Decimal for money; Law 42: positive bound.
    order_value: Decimal = Field(..., gt=Decimal("0"))
    category_slug: Optional[str] = None

    @field_validator("order_value", mode="before")
    @classmethod
    def _coerce_order_value(cls, v):
        if v is None or isinstance(v, Decimal):
            return v
        return Decimal(str(v))
