"""Admin order management controller."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional, cast

from fastapi import HTTPException
from sqlalchemy import exists, or_, String
from sqlalchemy.orm import Session, selectinload

from models import Order, OrderItem, Product, AuditLog, Notification, User, Shipment, ShipmentEvent
from utils.auth import require_permission
from utils.audit import audit_log, AuditAction
from utils.constants import ORDER_STATUSES, STAFF_ROLES, _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE
from utils.order_tracking import reconcile_order_status, order_status_label
from services.orders import apply_order_status_change

from services.write_helpers import add_and_flush, commit_only, rollback_only

def _build_list_page_payload(items: list, total: int, offset: int, page_size: int) -> dict:
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }

def bulk_update_order_status_admin(
    order_ids: List[int], status: str, acting_user: dict, db: Session
) -> dict:
    """Bulk update status of multiple orders (admin / sub_admin). Skips invalid transitions."""
    require_permission("orders.manage", acting_user)
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    if len(order_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 orders at once")

    valid_statuses = (
        "pending", "confirmed", "processing", "prepared", "picking_up",
        "shipped", "delivered", "cancelled", "failed",
    )
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    if status == "refunded":
        raise HTTPException(status_code=409, detail="Use the refund action instead of the status endpoint")

    updated: List[dict] = []
    skipped: List[dict] = []

    for oid in order_ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if not order:
            skipped.append({"id": oid, "reason": "Not found"})
            continue
        old_status = cast(str, getattr(order, "status"))
        if old_status == status:
            skipped.append({"id": oid, "reason": "Status unchanged"})
            continue
        if not _can_staff_override_order_status(old_status, status):
            skipped.append({"id": oid, "reason": f"Cannot transition from '{old_status}' to '{status}'"})
            continue
        apply_order_status_change(order, status, db)
        updated.append({"id": oid, "old_status": old_status, "new_status": status})

    if updated:
        commit_only(db)
        audit_log(
            db=db,
            action=AuditAction.ORDER_STATUS_CHANGED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=0,
            details={"bulk": True, "updated_count": len(updated), "new_status": status, "orders": updated},
            status="success",
        )
    return {
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def bulk_delete_orders_admin(order_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk delete multiple orders (admin only)."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete orders")
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    if len(order_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 orders at once")

    deleted: List[dict] = []
    skipped: List[dict] = []

    for oid in order_ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if not order:
            skipped.append({"id": oid, "reason": "Not found"})
            continue
        try:
            with db.begin_nested():
                info = _delete_order_records(order, db)
            deleted.append(info)
        except IntegrityError:
            logger.warning("admin bulk order delete blocked by remaining related records", extra={"order_id": oid})
            skipped.append(
                {
                    "id": oid,
                    "reason": "Order has related records that must be archived or removed before deletion.",
                }
            )

    if deleted:
        commit_only(db)
        audit_log(
            db=db,
            action=AuditAction.ORDER_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "orders": deleted},
            status="success",
        )
    else:
        rollback_only(db)
    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


# â”€â”€ Bulk Product Operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def delete_order_admin(order_id: int, acting_user: dict, db: Session) -> dict:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete orders")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        deleted_order = _delete_order_records(order, db)
        commit_only(db)
    except IntegrityError:
        rollback_only(db)
        logger.warning("admin order delete blocked by remaining related records", extra={"order_id": order_id})
        raise HTTPException(
            status_code=409,
            detail="Order has related records that must be archived or removed before deletion.",
        )

    audit_log(
        db=db,
        action=AuditAction.ORDER_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details=deleted_order,
        status="success",
    )
    return {"message": f"Order #{order_id} deleted successfully"}


def get_all_orders(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_range: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    missing_tracking_only: bool = False,
) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
    if status and status != "all":
        query = query.filter(Order.status == status)
    if min_amount is not None:
        query = query.filter(Order.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Order.total_amount <= max_amount)
    if date_range and date_range != "all":
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if date_range == "7d":
            query = query.filter(Order.created_at >= now - timedelta(days=7))
        elif date_range == "30d":
            query = query.filter(Order.created_at >= now - timedelta(days=30))
        elif date_range == "month":
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Order.created_at >= month_start)
    if missing_tracking_only:
        query = query.filter(
            Order.status.in_(["shipped", "delivered"]),
            ~exists().where(Shipment.order_id == Order.id),
        )
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.outerjoin(User, User.id == Order.user_id).filter(
            or_(
                func.cast(Order.id, String).ilike(term),
                func.cast(Order.user_id, String).ilike(term),
                User.username.ilike(term),
                User.email.ilike(term),
            )
        )
    query = query.order_by(Order.created_at.desc(), Order.id.desc())
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    orders = query.all()
    if not orders:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    order_ids = [cast(int, o.id) for o in orders]

    # Batch-load customer usernames (avoid N+1 queries)
    user_ids = list({cast(int, o.user_id) for o in orders if o.user_id is not None})
    username_map: dict[int, str] = {}
    if user_ids:
        user_rows = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        username_map = {r.id: r.username for r in user_rows}

    # Batch-load shipments for all orders at once (avoid N+1)
    all_shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id.in_(order_ids))
        .order_by(Shipment.order_id.asc(), Shipment.created_at.asc(), Shipment.id.asc())
        .all()
    )
    shipments_by_order: dict[int, list] = {}
    for s in all_shipments:
        shipments_by_order.setdefault(cast(int, s.order_id), []).append(s)

    # Batch-load events for all shipments at once
    all_shipment_ids = [cast(int, s.id) for s in all_shipments]
    events_by_shipment: dict[int, list] = {}
    if all_shipment_ids:
        all_events = (
            db.query(ShipmentEvent)
            .filter(ShipmentEvent.shipment_id.in_(all_shipment_ids))
            .order_by(ShipmentEvent.created_at.asc())
            .all()
        )
        for e in all_events:
            events_by_shipment.setdefault(cast(int, e.shipment_id), []).append(e)

    for order in orders:
        for item in cast(list[Any], getattr(order, "items", []) or []):
            product = getattr(item, "product", None)
            if not getattr(item, "product_name", None):
                fallback_product_name = getattr(product, "name", None) or f"Product #{getattr(item, 'product_id', 'unknown')}"
                setattr(item, "product_name", str(fallback_product_name))

            unit_price_raw = getattr(item, "unit_price", None)
            if unit_price_raw is None:
                unit_price_raw = getattr(item, "price", 0) or 0
                setattr(item, "unit_price", unit_price_raw)

            total_price_raw = getattr(item, "total_price", None)
            if total_price_raw is None:
                quantity_value = int(getattr(item, "quantity", 0) or 0)
                safe_unit_price = float(unit_price_raw or 0)
                setattr(item, "total_price", round(safe_unit_price * max(quantity_value, 0), 2))

        shipments = shipments_by_order.get(cast(int, order.id), [])
        events: list = []
        for s in shipments:
            events.extend(events_by_shipment.get(cast(int, s.id), []))
        reconciled_status = reconcile_order_status(order, shipments)
        if order.status != reconciled_status:
            order.status = reconciled_status
        setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
        setattr(order, "customer_username", username_map.get(cast(int, order.user_id)) if order.user_id is not None else None)
    return _build_list_page_payload([_order_to_dict(o, include_items=False) for o in orders], total, offset=offset, page_size=resolved_limit)


def _order_to_dict(order: Order, include_items: bool = False) -> dict[str, Any]:
    cols = [c.name for c in Order.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(order, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    for attr in ("status_label", "customer_username"):
        if hasattr(order, attr):
            d[attr] = getattr(order, attr)
    if include_items and hasattr(order, "items") and order.items:
        d["items"] = []
        for item in order.items:
            item_dict = {c.name: getattr(item, c.name, None) for c in item.__table__.columns}
            for k, v in item_dict.items():
                if isinstance(v, Decimal):
                    item_dict[k] = float(v)
            if hasattr(item, "product_name"):
                item_dict["product_name"] = getattr(item, "product_name")
            d["items"].append(item_dict)
    return d


def _can_staff_override_order_status(current_status: str, target_status: str) -> bool:
    if target_status == "refunded":
        return False
    if current_status in {"cancelled", "failed", "refunded"}:
        return False
    return True


def update_order_status(order_id: int, status: str, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid_statuses = (
        "pending", "confirmed", "processing", "prepared", "picking_up", "shipped",
        "delivered", "cancelled", "failed", "refunded",
    )
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    if status == "refunded":
        raise HTTPException(
            status_code=409,
            detail="Use the refund action for this order instead of the status endpoint",
        )

    old_status = order.status
    if status == old_status:
        return {"message": "Order status unchanged", "old_status": old_status, "new_status": status}

    allowed_transitions = {
        "pending": {"confirmed", "cancelled", "failed"},
        "confirmed": {"processing", "prepared", "shipped", "delivered", "cancelled"},
        "processing": {"prepared", "shipped", "delivered", "cancelled"},
        "prepared": {"picking_up", "shipped", "delivered", "cancelled"},
        "picking_up": {"prepared", "shipped", "delivered", "cancelled"},
        "shipped": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
        "failed": set(),
        "refunded": set(),
    }
    order_status = cast(str, getattr(order, "status"))
    order_paid_at = cast(datetime | None, getattr(order, "paid_at"))
    if order_status == "confirmed" and order_paid_at is None:
        allowed_transitions["confirmed"].add("failed")

    is_admin_override = False
    if status not in allowed_transitions.get(order_status, set()):
        if acting_user.get("role") in STAFF_ROLES and _can_staff_override_order_status(order_status, status):
            is_admin_override = True
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot change order status from '{order_status}' to '{status}'",
            )

    if is_admin_override and order_status == "delivered" and status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Delivered orders cannot be cancelled through status override",
        )

    apply_order_status_change(order, status, db)
    commit_only(db)
    try:
        from services.transactional_email_service import enqueue_order_status_email

        enqueue_order_status_email(cast(int, order.id), status=status)
    except Exception:
        logger.exception("Failed to enqueue order-status email for order %s", order.id)

    audit_log(
        db=db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details={"old_status": old_status, "new_status": status, "forced_override": is_admin_override},
        status="success",
    )
    return {
        "message": "Order status updated",
        "old_status": old_status,
        "new_status": status,
        "forced_override": is_admin_override,
    }


def refund_order(order_id: int, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    payment_intent_id = cast(str | None, getattr(order, "payment_intent_id"))
    order_status = cast(str, getattr(order, "status"))
    order_paid_at = cast(datetime | None, getattr(order, "paid_at"))
    if not payment_intent_id:
        raise HTTPException(status_code=422, detail="Order has no associated payment â€” cannot refund")

    allowed_statuses = {"confirmed", "processing", "prepared", "picking_up", "delivered", "shipped", "cancelled"}
    if order_status == "failed" and order_paid_at is not None:
        allowed_statuses.add("failed")
    if order_status not in allowed_statuses:
        raise HTTPException(status_code=409, detail=f"Cannot refund order in '{order_status}' status")

    from services.finance import _apply_stripe_runtime_key

    stripe.api_key = _apply_stripe_runtime_key(db) or os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    try:
        refund = stripe.Refund.create(payment_intent=payment_intent_id)
        apply_order_status_change(order, "refunded", db)
        try:
            from services.cash_management_service import log_refund_bank_transaction

            log_refund_bank_transaction(
                order,
                db,
                source="stripe_refund",
                transaction_ref=refund.id,
                description=f"Admin-issued Stripe refund for order #{order.id}",
                refund_amount=cast(Any, getattr(order, "total_amount", 0)),
            )
        except Exception:
            logger.exception("Failed to log refund bank transaction for order %s", order.id)
        add_and_flush(db, 
   Notification(
                user_id=order.user_id,
                type="order_update",
                title="Refund Issued",
                message=f"A full refund for Order #{order.id} has been issued by admin.",
                link=f"/orders/{order.id}",
            )
        )
        commit_only(db)
        try:
            from services.transactional_email_service import enqueue_refund_processed_email

            enqueue_refund_processed_email(cast(int, order.id), source="admin")
        except Exception:
            logger.exception("Failed to enqueue admin refund email for order %s", order.id)
        audit_log(
            db=db,
            action=AuditAction.ORDER_REFUNDED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="order",
            resource_id=order_id,
            details={"refund_id": refund.id, "amount": order.total_amount},
            status="success",
        )
        logger.info("Admin refund issued: order %s refund %s", order.id, refund.id)
        return {"detail": "Refund issued", "refund_id": refund.id, "status": refund.status}
    except Exception as exc:
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        logger.error("Refund error: %s", exc)
        raise HTTPException(status_code=500, detail="Refund service error")


def update_order_tracking(order_id: int, tracking_number: str, acting_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_status = cast(str, getattr(order, "status"))
    if order_status not in ("confirmed", "processing", "prepared", "picking_up", "shipped"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot add tracking to order in '{order_status}' status",
        )

    setattr(order, "tracking_number", tracking_number)
    setattr(order, "status", "shipped")
    add_and_flush(db, 
   Notification(
            user_id=order.user_id,
            type="order_update",
            title="Order Shipped",
            message=f"Order #{order.id} has been shipped. Tracking: {tracking_number}",
            link=f"/orders/{order.id}",
        )
    )
    commit_only(db)
    audit_log(
        db=db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="order",
        resource_id=order_id,
        details={"new_status": "shipped", "tracking_number": tracking_number},
        status="success",
    )
    return {"detail": "Tracking updated", "status": "shipped", "tracking_number": tracking_number}


