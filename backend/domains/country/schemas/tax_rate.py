"""Country tax rate request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CountryTaxRateCreate(BaseModel):
    """Request DTO for creating a country tax rate."""
    country_code: str = Field(..., min_length=2, max_length=3)
    tax_type: str = Field(default="VAT", max_length=20)
    tax_rate: float = Field(default=0.0, ge=0, le=1)
    tax_name: str = Field(default="VAT", max_length=50)


class CountryTaxRateUpdate(BaseModel):
    """Request DTO for updating a country tax rate."""
    tax_type: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    tax_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
