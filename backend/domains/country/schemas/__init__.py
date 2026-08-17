"""Country domain Pydantic DTOs (schemas slice).

Sliced from the legacy ``db/schemas.py`` country portion. Routers and services use
these for request/response shaping. ORM models live in ``domains/country/models``.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class CityResponse(BaseModel):
    id: int
    name: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None


class CountryDropdownResponse(BaseModel):
    code: str
    name: str
    currency: str
    currency_symbol: Optional[str] = None
    phone_code: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
