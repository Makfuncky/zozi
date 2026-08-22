"""CountryConfig request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CountryConfigCreate(BaseModel):
    """Request DTO for creating a country config."""
    code: str = Field(..., min_length=2, max_length=3)
    name: str = Field(..., min_length=1, max_length=200)
    currency: str = Field(default="USD", max_length=3)
    currency_symbol: Optional[str] = None
    phone_code: Optional[str] = None
    language: str = Field(default="en", max_length=10)
    timezone: Optional[str] = None
    tax_type: str = Field(default="VAT", max_length=20)
    tax_rate: float = Field(default=0.0, ge=0, le=1)


class CountryConfigUpdate(BaseModel):
    """Request DTO for updating a country config."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    currency: Optional[str] = Field(None, max_length=3)
    currency_symbol: Optional[str] = None
    phone_code: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = None
    tax_type: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
