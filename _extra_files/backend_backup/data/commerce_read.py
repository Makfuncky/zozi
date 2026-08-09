"""Read access for commerce (promotions/coupons) queries.

Kept in the ``data`` layer so routers never execute ``db.query`` directly
(layer-contract LC1). Routers call these helpers and keep presentation/
serialisation logic.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from data.models import Coupon


def list_coupons_by_country(
    db: Session,
    code: str,
    include_deleted: bool = False,
    limit: int = 100,
) -> List[Coupon]:
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if code != "*":
        q = q.filter(Coupon.country_code == code.upper())
    return q.limit(limit).all()
