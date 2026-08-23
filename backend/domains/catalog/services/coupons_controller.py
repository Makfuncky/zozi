"""controllers.commerce.coupons_controller controller.

Business logic is delegated to services.commerce.coupons_service (routers -> controllers -> services)."""  # noqa: E501

from domains.catalog.services.coupons_service import _calculate_discount
from domains.catalog.services.coupons_service import _calculate_total_from_items
from domains.catalog.services.coupons_service import _delete_coupon_record
from domains.catalog.services.coupons_service import _get_coupon_by_code
from domains.catalog.services.coupons_service import _normalize_coupon_code
from domains.catalog.services.coupons_service import _validate_coupon_for_total
from domains.catalog.services.coupons_service import build_coupon_quote
from domains.catalog.services.coupons_service import create_coupon
from domains.catalog.services.coupons_service import delete_coupon
from domains.catalog.services.coupons_service import delete_coupon_by_code
from domains.catalog.services.coupons_service import list_coupons
from domains.catalog.services.coupons_service import logger
from domains.catalog.services.coupons_service import validate_coupon

__all__ = [
    "_calculate_discount", "_calculate_total_from_items", "_delete_coupon_record", "_get_coupon_by_code", "_normalize_coupon_code", "_validate_coupon_for_total",
    "build_coupon_quote", "create_coupon", "delete_coupon", "delete_coupon_by_code", "list_coupons", "logger",
    "validate_coupon"
]


from fastapi import HTTPException
from domains.payments.ports import Coupon as _Coupon

def delete_coupon_route(country_code, coupon_id, current_user, db):
    return delete_coupon(coupon_id, current_user, db)

def list_coupons_route(country_code, search=None, page=1, page_size=50, current_user=None, db=None):
    return list_coupons(current_user, db)

def update_coupon_route(country_code, coupon_id, current_user, db, **fields):
    coupon = db.query(_Coupon).filter(_Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    _allowed = {"code","title","description","discount_type","discount_value","maximum_discount","minimum_order","usage_limit","per_user_limit","is_active","starts_at","expires_at"}
    for _k, _v in fields.items():
        if _v is None or _v == "":
            continue
        if _k in _allowed:
            setattr(coupon, _k, _v)
    db.commit()
    return {"message": "Coupon updated", "coupon_id": coupon_id}

# === migration bridge (architecture realignment): write now calls owning accounts service directly (ports is read-only) ===
def create_coupon(*args, **kwargs):
    from domains.catalog.admin_promotions_service import create_coupon as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): write now calls owning accounts service directly (ports is read-only) ===
def delete_coupon(*args, **kwargs):
    from domains.orders.customer_coupons_create_service import delete_coupon as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): re-export from domains.governance.services.customer_coupons_create_service ===
def list_coupons(*args, **kwargs):
    from domains.governance.ports import list_coupons as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): re-export from domains.governance.services.customer_coupons_mgmt_service ===
def validate_coupon(*args, **kwargs):
    from domains.governance.ports import validate_coupon as _impl
    return _impl(*args, **kwargs)
