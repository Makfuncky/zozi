"""Finance request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    """Request DTO for creating an invoice."""
    customer_id: int
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Response DTO for an invoice."""
    id: int
    customer_id: int
    amount: float
    status: str


class PaymentCreate(BaseModel):
    """Request DTO for recording a payment."""
    invoice_id: int
    amount: float = Field(..., gt=0)


class PayoutCreate(BaseModel):
    """Request DTO for creating a payout."""
    recipient_id: int
    amount: float = Field(..., gt=0)
