"""
Admin Router Service — Database operations for admin routers.
All SQLAlchemy DB access is centralized here.
"""

from typing import Optional, List, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from data.models import User, Product, Order, Payout
from data.services_write_helpers import add_and_flush, commit_only
from utils.pagination import cursor_paginate_desc, paginated_response
from utils.audit import audit_log


def list_users_by_country(
    db: Session,
    country_code: str,
    page: int = 1,
    size: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(User).filter(User.country_code == country_code.upper())
        if role:
            q = q.filter(User.role == role)
        if search:
            q = q.filter(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        if not include_deleted:
            q = q.filter(User.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()


def get_user_by_id(
    db: Session,
    country_code: str,
    user_id: int,
) -> Optional[User]:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(User).filter(User.id == user_id, User.country_code == country_code.upper()).first()
    finally:
        clear_rls_context()


def update_user_in_db(
    db: Session,
    country_code: str,
    user_id: int,
    updates: dict,
) -> User:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        u = db.query(User).filter(User.id == user_id, User.country_code == country_code.upper()).first()
        if not u:
            raise HTTPException(404, "User not found")
        for k, v in updates.items():
            setattr(u, k, v)
        commit_only(db)
        return u
    finally:
        clear_rls_context()


def toggle_user_active_in_db(
    db: Session,
    country_code: str,
    user_id: int,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        u = db.query(User).filter(User.id == user_id, User.country_code == country_code.upper()).first()
        if not u:
            raise HTTPException(404, "User not found")
        u.is_active = not u.is_active
        updated = 1
        commit_only(db)
        return {"message": "Updated " + str(updated) + " users", "updated": updated}
    finally:
        clear_rls_context()


def bulk_toggle_users_active_in_db(
    db: Session,
    country_code: str,
    user_ids: List[int],
    is_active: bool,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        updated = 0
        for uid in user_ids:
            u = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if u:
                u.is_active = is_active
                updated += 1
        commit_only(db)
        return {"message": "Updated " + str(updated) + " users", "updated": updated}
    finally:
        clear_rls_context()


def get_payout_for_verification(db: Session, payout_id: int) -> Optional[Payout]:
    return db.query(Payout).filter(Payout.id == payout_id).first()


def get_payout_amount(payout: Optional[Payout]) -> Optional[float]:
    if payout and payout.amount is not None:
        return float(payout.amount)
    return None


def admin_logistics_overview(db: Session) -> dict:
    from data.models import Shipment, ShippingCarrier, ShippingZone
    
    shipment_counts = db.query(
        Shipment.status,
        sqlfunc.count(Shipment.id).label("count"),
    ).group_by(Shipment.status).all()

    channel_counts = db.query(
        Shipment.distribution_channel,
        sqlfunc.count(Shipment.id).label("count"),
    ).filter(Shipment.distribution_channel.isnot(None)).group_by(
        Shipment.distribution_channel
    ).all()

    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()

    recent_shipments = db.query(Shipment).order_by(
        Shipment.updated_at.desc()
    ).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {
            "id": s.id,
            "order_id": s.order_id,
            "supplier_id": s.supplier_id,
            "carrier_name": s.carrier_name,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        }

    return {
        "shipment_by_status": {s: c for s, c in shipment_counts},
        "shipment_by_channel": {ch: c for ch, c in channel_counts},
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code, "is_global": c.supplier_id is None}
            for c in carriers
        ],
        "active_zones": zones,
        "recent_shipments": [_ser_shipment(s) for s in recent_shipments],
    }


def list_products_by_country(
    db: Session,
    country_code: str,
    cursor: Optional[str] = None,
    limit: int = 50,
    moderation_status: Optional[str] = None,
    include_deleted: bool = False,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status:
            q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted:
            q = q.filter(Product.is_deleted == False)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


def get_product_by_id(
    db: Session,
    country_code: str,
    product_id: int,
) -> Optional[Product]:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(Product).filter(
            Product.id == product_id,
            Product.country_code == country_code.upper()
        ).first()
    finally:
        clear_rls_context()


def approve_product_in_db(
    db: Session,
    country_code: str,
    product_id: int,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(
            Product.id == product_id,
            Product.country_code == country_code.upper()
        ).first()
        if not p:
            raise HTTPException(404, "Product not found")
        p.moderation_status = "approved"
        p.is_verified = True
        commit_only(db)
        return {"message": "Product approved"}
    finally:
        clear_rls_context()


def reject_product_in_db(
    db: Session,
    country_code: str,
    product_id: int,
    reason: Optional[str] = None,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(
            Product.id == product_id,
            Product.country_code == country_code.upper()
        ).first()
        if not p:
            raise HTTPException(404, "Product not found")
        p.moderation_status = "rejected"
        p.moderation_notes = reason
        commit_only(db)
        return {"message": "Product rejected"}
    finally:
        clear_rls_context()


def update_product_badge_in_db(
    db: Session,
    country_code: str,
    product_id: int,
    field: str,
    value: bool,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(
            Product.id == product_id,
            Product.country_code == country_code.upper()
        ).first()
        if not p:
            raise HTTPException(404, "Product not found")
        if field not in ("is_hot", "is_featured"):
            raise HTTPException(400, "field must be 'is_hot' or 'is_featured'")
        setattr(p, field, value)
        commit_only(db)
        return {"message": "Product badge updated", "field": field, "value": value}
    finally:
        clear_rls_context()


def list_orders_by_country(
    db: Session,
    country_code: str,
    cursor: Optional[str] = None,
    limit: int = 50,
    status: Optional[str] = None,
    include_deleted: bool = False,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Order)
        if status:
            q = q.filter(Order.status == status)
        if not include_deleted:
            q = q.filter(Order.is_deleted == False)
        return cursor_paginate_desc(q.order_by(Order.id.desc()), cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


def get_order_by_id_in_db(
    db: Session,
    country_code: str,
    order_id: int,
) -> Optional[Order]:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(Order).filter(Order.id == order_id).first()
    finally:
        clear_rls_context()


def update_order_status_in_db(
    db: Session,
    country_code: str,
    order_id: int,
    status: str,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(404, "Order not found")
        order.status = status
        commit_only(db)
        return {"message": "Order " + str(order_id) + " status updated to " + str(status)}
    finally:
        clear_rls_context()


def bulk_update_order_status_in_db(
    db: Session,
    country_code: str,
    order_ids: List[int],
    status: str,
) -> dict:
    from utils.rls_interceptor import set_rls_context, clear_rls_context
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from sqlalchemy.orm import Session
        updated = 0
        for oid in order_ids:
            o = db.query(Order).filter(Order.id == oid).first()
            if o:
                o.status = status
                updated += 1
        commit_only(db)
        return {"message": "Status updated for " + str(updated) + " orders", "updated": updated}
    finally:
        clear_rls_context()


def get_payout_by_id(db: Session, payout_id: int) -> Optional[Payout]:
    return db.query(Payout).filter(Payout.id == payout_id).first()


def verify_payout_in_db(db: Session, payout_id: int, payout_data: dict) -> dict:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(404, "Payout not found")
    if payout.amount:
        amount = float(payout.amount)
    else:
        amount = None
    return {"payout": payout, "amount": amount}