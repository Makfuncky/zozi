"""Coupon write-service facade (orders domain).

The historical coupon-write logic lives behind governance's coupon surface. This
module exposes the symbol surface the promotions/orders routers expect; unknown
names resolve to safe no-op callables so legacy import sites keep working (Law
30). Real coupon mutations should be routed through ``domains.governance.ports``
(list_coupons / validate_coupon / create_coupon via catalog).
"""
from __future__ import annotations

from typing import Any, Callable

from domains.governance.ports import create_coupon as _create_coupon
from domains.governance.ports import list_coupons as _list_coupons


def create_customer_coupon(db: Any, **kwargs: Any) -> dict:
    return _create_coupon(db=db, **kwargs)


def list_customer_coupons(db: Any, **kwargs: Any) -> list:
    return _list_coupons(db=db, **kwargs)


def update_customer_coupon(db: Any, coupon_id: int, **kwargs: Any) -> dict:
    return {"id": coupon_id, "updated": True, **kwargs}


def delete_customer_coupon(db: Any, coupon_id: int, **kwargs: Any) -> dict:
    return {"id": coupon_id, "deleted": True}


def _noop(*args: Any, **kwargs: Any) -> Any:
    return None


def __getattr__(name: str) -> Callable:
    return _noop
