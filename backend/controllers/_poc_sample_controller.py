"""POC sample controller — demonstrates controller-first routing.

In real code this would call a service and use ``require_admin`` from
``utils.dependencies``. Kept dependency-free here so the proof-of-concept runs
in any environment without a live DB.
"""
from __future__ import annotations

from fastapi import Body, Depends, Path
from pydantic import BaseModel

from utils.route import get, post


class CouponOut(BaseModel):
    created: bool
    code: str
    coupon: str


# Placeholder for require_admin so the POC has no external import surface.
# Real controllers pass ``auth=require_admin`` from utils.dependencies.
def _require_admin() -> bool:
    return True


@post(
    "/{code}/coupons",
    auth=_require_admin,
    prefix="/api/v1/promotions",
    response_model=CouponOut,
    status_code=201,
    tags=["promotions"],
)
def create_coupon_by_country(
    code: str = Path(..., description="ISO country code"),
    coupon_code: str = Body(...),
) -> CouponOut:
    """Create a coupon scoped to a country (delegates to service in prod)."""
    return CouponOut(created=True, code=code, coupon=coupon_code)


@get(
    "/{code}/coupons",
    auth=_require_admin,
    prefix="/api/v1/promotions",
    tags=["promotions"],
)
def list_coupons_by_country(code: str = Path(...)):
    """List coupons for a country."""
    return {"code": code, "coupons": []}
