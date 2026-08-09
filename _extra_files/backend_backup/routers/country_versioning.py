"""Country versioning router.

Placeholder router retained so ``routers.public_countries_access`` can attach its
``versioning_router`` without a hard import dependency. Endpoints can be added
here as the country-versioning feature is implemented.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["country_versioning"])
