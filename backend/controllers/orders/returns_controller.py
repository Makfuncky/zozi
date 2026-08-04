"""Returns Controller — customer return requests business logic."""
import importlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, cast

import httpx
import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from data.models import Notification, Order, OrderItem, Product, ReturnRequest, Shipment, User
from data.schemas import ReturnRequestCreate, ReturnRequestUpdate, SupplierReturnReviewUpdate
from utils.audit_log import audit_log, AuditAction
from data.services_orders import _order_holds_inventory, apply_order_status_change
from utils.config import settings
from data.services_write_helpers import (    add_and_flush,
    commit_and_refresh,
)
from services.orders.orders_router_service import get_return_by_id as get_return_request_by_id


logger = logging.getLogger(__name__)

_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }


def _supplier_ids_for_order(order: Order) -> list[int]:
    supplier_ids = {
        int(item.product.supplier_id)
        for item in order.items
        if item.product and item.product.supplier_id is not None
    }
    return sorted(supplier_ids)


def _normalized_return_window_days(raw_value: Any) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = 10
    return max(10, parsed)


def _order_items(order: Order, db: Session) -> list[OrderItem]:
    items = list(order.items or [])
    if items:
        return items
    _db_orderitem_all_0(db, id, order, order_id)


def _order_return_window_days(order: Order, db: Session) -> int:
    items = _order_items(order, db)
    product_ids = [item.product_id for item in items if item.product_id]
    products = (
        _db_product_all_1(db, id, in_, product_ids)
        if product_ids
        else {}
    )
    return max(
        (
            _normalized_return_window_days(
                getattr(item.product, "return_window_days", None)
                if item.product is not None
                else getattr(products.get(item.product_id), "return_window_days", None)
            )
            for item in items
        ),
        default=10,
    )


def _order_delivery_reference(order: Order, db: Session) -> datetime | None:
    if cast(str | None, getattr(order, "status", None)) != "delivered":
        return None

    delivered_shipments = (
        _db_shipment_query_2(db)
        .filter(Shipment.order_id == order.id, Shipment.actual_delivery.isnot(None))
        .order_by(Shipment.actual_delivery.desc())
        .all()
    )
    if delivered_shipments:
        return cast(datetime | None, getattr(delivered_shipments[0], "actual_delivery", None))

    return cast(datetime | None, getattr(order, "updated_at", None)) or cast(datetime | None, getattr(order, "created_at", None))


def _return_request_item_summaries(req: ReturnRequest, db: Session) -> list[dict[str, Any]]:
    order = cast(Optional[Order], getattr(req, "order", None))
    if order is None:
        order = (
            _db_order_query_3(db)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .filter(Order.id == req.order_id)
            .first()
        )
        if order is not None:
            setattr(req, "order", order)
    if order is None:
        return []

    summaries: list[dict[str, Any]] = []
    for item in _order_items(order, db):
        if req.order_item_id is not None and cast(int | None, getattr(item, "id", None)) != req.order_item_id:
            continue
        product = cast(Optional[Product], getattr(item, "product", None))
        summaries.append(
            {
                "order_item_id": cast(int | None, getattr(item, "id", None)),
                "product_id": item.product_id,
                "product_name": cast(str | None, getattr(product, "name", None)) or f"Product #{item.product_id}",
                "quantity": int(item.quantity or 0),
                "price": float(item.price or 0),
                "return_window_days": _normalized_return_window_days(
                    cast(Any, getattr(product, "return_window_days", None))
                    if product is not None
                    else db.query(Product.return_window_days).filter(Product.id == item.product_id).scalar()
                ),
            }
        )
    return summaries


def _attach_return_request_context(req: ReturnRequest, db: Session) -> ReturnRequest:
    order = cast(Optional[Order], getattr(req, "order", None))
    if order is None:
        order = (
            _db_order_query_4(db)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .filter(Order.id == req.order_id)
            .first()
        )
        if order is not None:
            setattr(req, "order", order)

    item_summaries = _return_request_item_summaries(req, db)
    delivered_at = _order_delivery_reference(order, db) if order is not None else None
    return_window_days = (
        item_summaries[0]["return_window_days"]
        if req.order_item_id is not None and item_summaries
        else _order_return_window_days(order, db)
        if order is not None
        else 10
    )
    return_deadline = delivered_at + timedelta(days=return_window_days) if delivered_at is not None else None

    setattr(req, "items", item_summaries)
    setattr(req, "return_window_days", return_window_days)
    setattr(req, "delivered_at", delivered_at)
    setattr(req, "return_deadline", return_deadline)
    return req


def _default_supplier_review_entry(timestamp: datetime | None = None) -> dict[str, Any]:
    iso_timestamp = timestamp.isoformat() if timestamp else None
    return {
        "decision": "pending",
        "notes": None,
        "updated_at": iso_timestamp,
        "restocked_at": None,
        "restock_applied": False,
    }


def _build_supplier_review_state(order: Order, timestamp: datetime) -> dict[str, dict[str, Any]]:
    return {
        str(supplier_id): _default_supplier_review_entry(timestamp)
        for supplier_id in _supplier_ids_for_order(order)
    }


def _build_supplier_review_state_for_item(order_item: OrderItem, timestamp: datetime) -> dict[str, dict[str, Any]]:
    product = cast(Optional[Product], getattr(order_item, "product", None))
    supplier_id = cast(int | None, getattr(product, "supplier_id", None)) if product is not None else None
    if supplier_id is None:
        return {}
    return {str(supplier_id): _default_supplier_review_entry(timestamp)}


def _parse_supplier_review_state(req: ReturnRequest) -> dict[str, dict[str, Any]]:
    raw_state = cast(Optional[str], getattr(req, "supplier_review_state", None))
    if not raw_state:
        return {}
    try:
        parsed = json.loads(raw_state)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for supplier_key, value in parsed.items():
        if not isinstance(value, dict):
            continue
        normalized[str(supplier_key)] = {
            "decision": str(value.get("decision") or "pending").strip().lower() or "pending",
            "notes": str(value.get("notes")).strip() if value.get("notes") else None,
            "updated_at": value.get("updated_at"),
            "restocked_at": value.get("restocked_at"),
            "restock_applied": bool(value.get("restock_applied", False)),
        }
    return normalized


def _supplier_owned_items(order: Order, supplier_id: int, order_item_id: int | None = None) -> list[dict[str, Any]]:
    owned_items: list[dict[str, Any]] = []
    for item in order.items:
        if order_item_id is not None and cast(int | None, getattr(item, "id", None)) != order_item_id:
            continue
        product = item.product
        if not product or product.supplier_id != supplier_id:
            continue
        owned_items.append(
            {
                "order_item_id": cast(int | None, getattr(item, "id", None)),
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": int(item.quantity or 0),
                "price": float(item.price or 0),
            }
        )
    return owned_items


def _serialize_supplier_return_request(req: ReturnRequest, supplier_id: int) -> dict[str, Any] | None:
    order = req.order
    if not order:
        return None

    owned_items = _supplier_owned_items(order, supplier_id, cast(int | None, getattr(req, "order_item_id", None)))
    if not owned_items:
        return None

    state = _parse_supplier_review_state(req)
    supplier_state = state.get(str(supplier_id), _default_supplier_review_entry())
    customer = cast(Optional[User], getattr(order, "user", None))
    created_at = cast(Optional[datetime], getattr(req, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(req, "updated_at", None))
    resolved_at = cast(Optional[datetime], getattr(req, "resolved_at", None))
    return {
        "id": req.id,
        "order_id": req.order_id,
        "order_item_id": cast(int | None, getattr(req, "order_item_id", None)),
        "user_id": req.user_id,
        "customer_name": cast(Optional[str], getattr(customer, "username", None)) if customer else None,
        "customer_email": cast(Optional[str], getattr(customer, "email", None)) if customer else None,
        "intent": req.intent,
        "reason": req.reason,
        "status": req.status,
        "resolution_notes": req.resolution_notes,
        "shipping_address": cast(Optional[str], getattr(order, "shipping_address", None)),
        "supplier_owned_items": owned_items,
        "supplier_review": supplier_state,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "resolved_at": resolved_at.isoformat() if resolved_at else None,
    }


def _capture_exc(exc: Exception) -> None:
    """Non-blocking Sentry capture — ignores missing sentry_sdk."""
    try:
        sentry_sdk = importlib.import_module("sentry_sdk")
        sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def create_return_request(current_user: dict, payload: ReturnRequestCreate, db: Session) -> ReturnRequest:
    order = _db_order_first_5(db, current_user, id, order_id, payload, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    target_order_item: OrderItem | None = None
    if payload.order_item_id is not None:
        target_order_item = (
            _db_orderitem_query_6(db)
            .options(selectinload(OrderItem.product))
            .filter(OrderItem.id == payload.order_item_id, OrderItem.order_id == order.id)
            .first()
        )
        if target_order_item is None:
            raise HTTPException(status_code=404, detail="Order item not found")

    delivery_reference = _order_delivery_reference(order, db)
    if delivery_reference is None:
        raise HTTPException(status_code=422, detail="Returns can only be requested after the order is delivered")

    existing_query = _db_returnrequest_query_7(db, order_id, payload)
    if payload.order_item_id is not None:
        existing_query = existing_query.filter(ReturnRequest.order_item_id == payload.order_item_id)
    else:
        existing_query = existing_query.filter(ReturnRequest.order_item_id.is_(None))
    existing = existing_query.first()
    if existing:
        raise HTTPException(status_code=400, detail="Return request already exists for this order item")

    created_at = _utcnow()
    return_window_days = _order_return_window_days(order, db)
    return_deadline = delivery_reference + timedelta(days=return_window_days)
    if created_at > return_deadline:
        raise HTTPException(
            status_code=422,
            detail=f"Return window expired for this order after {return_window_days} days from delivery",
        )

    return_request = ReturnRequest(
        order_id=payload.order_id,
        order_item_id=payload.order_item_id,
        user_id=current_user["id"],
        intent=payload.intent,
        reason=payload.reason.strip(),
        status="pending",
        supplier_review_state=json.dumps(
            _build_supplier_review_state_for_item(target_order_item, created_at)
            if target_order_item is not None
            else _build_supplier_review_state(order, created_at)
        ),
        created_at=created_at,
        updated_at=created_at,
    )
    add_and_flush(db, return_request)
    commit_and_refresh(db, return_request)

    audit_log(
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        action=AuditAction.RETURN_REQUEST_CREATED,
        resource_type="order",
        resource_id=str(payload.order_id),
        details={"reason": payload.reason, "intent": payload.intent, "order_item_id": payload.order_item_id},
        db=db,
    )
    try:
        from services.transactional_email_service import enqueue_return_created_email

        enqueue_return_created_email(cast(int, return_request.id))
    except Exception:
        logger.exception("Failed to enqueue return-created email for return %s", return_request.id)

    return _attach_return_request_context(return_request, db)


def list_return_requests(current_user: dict, db: Session, *, limit: int = 50, offset: int = 0) -> List[ReturnRequest]:
    query = _db_returnrequest_query_8(db)


    if current_user.get("role") not in ("admin", "support"):
        query = query.filter(ReturnRequest.customer_id == current_user.get("id"))
    requests = query.order_by(ReturnRequest.created_at.desc()).offset(offset).limit(limit).all()
    return [_attach_return_request_context(req, db) for req in requests]


def get_return_request(return_id: int, current_user: dict, db: Session) -> ReturnRequest:
    req = (
        _db_returnrequest_query_9(db)
        .options(selectinload(ReturnRequest.order).selectinload(Order.items).selectinload(OrderItem.product))
        .filter(ReturnRequest.id == return_id)
        .first()
    )
    if req is None:
        raise HTTPException(status_code=404, detail="Return request not found")

    if current_user.get("role") not in ("admin", "support") and req.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")

    return _attach_return_request_context(req, db)


def update_return_request(return_id: int, payload: ReturnRequestUpdate, current_user: dict, db: Session) -> ReturnRequest:
    if current_user.get("role") not in ("admin", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")

    req = get_return_request_by_id(db, return_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Return request not found")

    if payload.status not in ("pending", "approved", "rejected", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status")

    intent = cast(str, getattr(req, "intent", ""))
    resolution_notes = getattr(payload, "resolution_notes", None)
    if resolution_notes is None:
        resolution_notes = getattr(payload, "notes", None)

    setattr(req, "status", payload.status)
    setattr(req, "resolution_notes", resolution_notes)
    setattr(req, "updated_at", _utcnow())
    setattr(req, "resolved_at", _utcnow() if payload.status in ("approved", "rejected", "completed") else None)

    # Auto-issue refund only for actual returns, not replacement intent.
    if payload.status == "completed" and intent == "return":
        order = _db_order_first_10(db, id, order_id, req)
        payment_id = cast(str | None, getattr(order, "payment_intent_id")) if order else None
        if order is not None and payment_id:

            if payment_id.startswith("pi_") or payment_id.startswith("py_"):
                # ── Stripe refund ────────────────────────────────────────────
                stripe.api_key = settings.stripe_secret_key or os.getenv("STRIPE_SECRET_KEY", "")
                if stripe.api_key:
                    try:
                        refund = stripe.Refund.create(payment_intent=payment_id)
                        apply_order_status_change(order, "refunded", db)
                        try:
                            from services.cash_management_service import log_refund_bank_transaction

                            log_refund_bank_transaction(
                                order,
                                db,
                                source="stripe_refund",
                                transaction_ref=refund.id,
                                description=f"Return refund issued for order #{order.id}",
                                return_request_id=return_id,
                            )
                        except Exception:
                            logger.exception("Failed to log Stripe return refund transaction for order %s", order.id)
                        add_and_flush(db, Notification(
                            user_id=req.user_id,
                            type="order_update",
                            title="Return Refund Issued",
                            message=f"Your return for Order #{order.id} has been processed and a refund has been issued via Stripe.",
                            link=f"/orders/{order.id}",
                        ))
                        logger.info("Stripe auto-refund issued for return %s: refund %s", return_id, refund.id)
                    except Exception as exc:
                        logger.error("Stripe auto-refund failed for return %s: %s", return_id, exc)
                        _capture_exc(exc)

            elif payment_id.startswith("chg_"):
                # ── Tap Payments refund ──────────────────────────────────────
                tap_key = settings.tap_secret_key if hasattr(settings, "tap_secret_key") else os.getenv("TAP_SECRET_KEY", "")
                if tap_key:
                    try:
                        import asyncio
                        _tap_refund_amount = float(cast(Any, getattr(order, "total_amount")) or 0)
                        async def _do_tap_refund() -> dict:
                            async with httpx.AsyncClient(timeout=15) as client:
                                resp = await client.post(
                                    "https://api.tap.company/v2/refunds",
                                    headers={
                                        "Authorization": f"Bearer {tap_key}",
                                        "Content-Type": "application/json",
                                    },
                                    json={
                                        "charge_id": payment_id,
                                        "amount": _tap_refund_amount,
                                        "reason": "return_refund",
                                    },
                                )
                                return resp.json()

                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                        tap_data = loop.run_until_complete(_do_tap_refund())

                        if tap_data.get("status") in ("REFUNDED", "CAPTURED"):
                            apply_order_status_change(order, "refunded", db)
                            try:
                                from services.cash_management_service import log_refund_bank_transaction

                                log_refund_bank_transaction(
                                    order,
                                    db,
                                    source="tap_refund",
                                    transaction_ref=tap_data.get("id") or f"{payment_id}:return-refund",
                                    description=f"Tap return refund issued for order #{order.id}",
                                    return_request_id=return_id,
                                )
                            except Exception:
                                logger.exception("Failed to log Tap return refund transaction for order %s", order.id)
                            add_and_flush(db, Notification(
                                user_id=req.user_id,
                                type="order_update",
                                title="Return Refund Issued",
                                message=f"Your return for Order #{order.id} has been processed and a refund has been issued via Tap Payments.",
                                link=f"/orders/{order.id}",
                            ))
                            logger.info("Tap auto-refund issued for return %s: %s", return_id, tap_data.get("id"))
                        else:
                            logger.error("Tap refund returned unexpected status for return %s: %s", return_id, tap_data)
                    except Exception as exc:
                        logger.error("Tap auto-refund failed for return %s: %s", return_id, exc)
                        _capture_exc(exc)
    elif payload.status == "completed" and intent == "replacement":
        order = _db_order_first_11(db, id, order_id, req)
        if order is not None:
            add_and_flush(db, Notification(
                user_id=req.user_id,
                type="order_update",
                title="Replacement Request Completed",
                message=f"Your replacement workflow for Order #{order.id} has been marked as completed.",
                link=f"/orders/{order.id}",
            ))

    commit_and_refresh(db, req)

    audit_log(
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        action=AuditAction.RETURN_REQUEST_UPDATED,
        resource_type="return_request",
        resource_id=str(return_id),
        details={"status": payload.status, "notes": resolution_notes, "intent": intent},
        db=db,
    )
    try:
        from services.transactional_email_service import enqueue_return_status_email

        enqueue_return_status_email(cast(int, req.id))
    except Exception:
        logger.exception("Failed to enqueue return-status email for return %s", req.id)

    return _attach_return_request_context(req, db)


def bulk_update_return_requests(
    return_ids: list[int],
    payload: ReturnRequestUpdate,
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    if current_user.get("role") not in ("admin", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if not return_ids:
        raise HTTPException(status_code=400, detail="No return IDs provided")

    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for return_id in list(dict.fromkeys(return_ids)):
        try:
            updated = update_return_request(return_id, payload, current_user, db)
            processed.append({"id": updated.id, "status": updated.status, "order_id": updated.order_id})
        except HTTPException as exc:
            skipped.append({"id": return_id, "reason": exc.detail})

    return {
        "processed": len(processed),
        "skipped": len(skipped),
        "status": payload.status,
        "details": processed,
        "skipped_details": skipped,
    }


def list_supplier_return_requests(
    current_user: dict,
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
) -> dict[str, Any]:
    if current_user.get("role") != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required")

    supplier_id = int(cast(Any, current_user.get("id")))
    base_query = (
        _db_returnrequest_query_12(db)
        .options(
            selectinload(ReturnRequest.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.product),
            selectinload(ReturnRequest.order).selectinload(Order.user),
        )
        .order_by(ReturnRequest.created_at.desc())
    )
    total = base_query.count()
    query = base_query
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    requests = query.all()
    queue_items: list[dict[str, Any]] = []
    for req in requests:
        serialized = _serialize_supplier_return_request(req, supplier_id)
        if serialized is not None:
            queue_items.append(serialized)
    resolved_page_size = limit if limit is not None else len(queue_items)
    return _build_list_page_payload(queue_items, total, offset=offset, page_size=resolved_page_size)


def update_supplier_return_request(
    return_id: int,
    payload: SupplierReturnReviewUpdate,
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    if current_user.get("role") != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required")

    req = get_return_request_by_id(db, return_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Return request not found")

    order = req.order
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    supplier_id = int(cast(Any, current_user.get("id")))
    owned_items = _supplier_owned_items(order, supplier_id, cast(int | None, getattr(req, "order_item_id", None)))
    if not owned_items:
        raise HTTPException(status_code=403, detail="Forbidden")

    supplier_state = _parse_supplier_review_state(req)
    state_key = str(supplier_id)
    current_state = supplier_state.get(state_key, _default_supplier_review_entry())

    decision = str(payload.supplier_decision)
    notes_raw = payload.supplier_notes
    notes = str(notes_raw).strip() if notes_raw is not None else None
    timestamp = _utcnow()
    intent = cast(str, getattr(req, "intent", ""))
    request_status = cast(str, getattr(req, "status", ""))

    if decision == "restocked":
        if intent != "return":
            raise HTTPException(status_code=422, detail="Only return requests can be restocked")
        if request_status == "rejected":
            raise HTTPException(status_code=409, detail="Rejected return requests cannot be restocked")
        if current_state.get("decision") not in {"approved", "restocked"}:
            raise HTTPException(status_code=409, detail="Approve the return before applying restock")
        if not current_state.get("restock_applied"):
            for item in owned_items:
                product = _db_product_first_13(db, id, item, product_id, supplier_id)


                if product is not None:
                    cast(Any, product).stock = int(cast(Any, getattr(product, "stock", 0)) or 0) + int(item["quantity"])
            current_state["restock_applied"] = True
            current_state["restocked_at"] = timestamp.isoformat()
    elif current_state.get("restock_applied"):
        raise HTTPException(status_code=409, detail="Restocked returns cannot be moved back to another supplier state")

    current_state["decision"] = decision
    current_state["notes"] = notes
    current_state["updated_at"] = timestamp.isoformat()
    supplier_state[state_key] = current_state

    setattr(req, "supplier_review_state", json.dumps(supplier_state))
    setattr(req, "updated_at", timestamp)

    commit_and_refresh(db, req)

    audit_log(
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        action=AuditAction.RETURN_REQUEST_UPDATED,
        resource_type="return_request",
        resource_id=str(return_id),
        details={
            "supplier_id": supplier_id,
            "supplier_decision": decision,
            "supplier_notes": notes,
            "intent": intent,
        },
        db=db,
    )

    serialized = _serialize_supplier_return_request(req, supplier_id)
    if serialized is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    return serialized

