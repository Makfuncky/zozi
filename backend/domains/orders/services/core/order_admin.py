"""Order admin operations — tracking, scan receipt, confirmations."""

from domains.orders.services.core.order_engine import *

def confirm_order_scan_receipt(order_id: int, data: dict, current_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    role = current_user.get("role")
    user_id = current_user.get("id")
    if role not in STAFF_ROLES and order.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this order")

    scan_code = str(data.get("scan_code") or "").strip()
    if not scan_code:
        raise HTTPException(status_code=422, detail="scan_code is required")

    shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id)
        .order_by(Shipment.created_at.asc(), Shipment.id.asc())
        .all()
    )
    if not shipments:
        raise HTTPException(status_code=404, detail="Shipment not found")

    matched_shipment = next(
        (shipment for shipment in shipments if scan_code in shipment_scan_codes(shipment)),
        None,
    )
    if matched_shipment is None:
        raise HTTPException(status_code=404, detail="Invalid shipment scan code")

    now = _utcnow()
    matched_shipment.status = "delivered"
    matched_shipment.actual_delivery = cast(datetime, getattr(matched_shipment, "actual_delivery", None) or now)
    if data.get("location"):
        matched_shipment.current_hub = str(data.get("location"))

    event = ShipmentEvent(
        shipment_id=matched_shipment.id,
        order_id=order.id,
        supplier_id=matched_shipment.supplier_id,
        actor_user_id=user_id,
        actor_role=role or "customer",
        event_type=normalize_shipment_event_type("customer_received"),
        status_after="delivered",
        distribution_channel=matched_shipment.distribution_channel,
        location=data.get("location"),
        scan_code=scan_code,
        notes=data.get("notes") or "Customer confirmed delivery by scan",
        created_at=now,
    )
    db.add(event)

    reconciled_status = reconcile_order_status(order, shipments)
    order.status = reconciled_status
    if reconciled_status == "delivered" and not getattr(order, "delivered_at", None):
        order.delivered_at = now

    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "shipment_id": matched_shipment.id,
        "status": order.status,
        "scan_code": scan_code,
    }


def get_order_tracking(order_id: int, current_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    role = current_user.get("role")
    user_id = current_user.get("id")
    partner: LogisticsPartner | None = None
    if role in STAFF_ROLES:
        pass
    elif role == "supplier":
        if not _supplier_can_access_order(order, user_id):
            raise HTTPException(status_code=403, detail="You do not have access to this order tracking")
    elif role == "logistics_partner":
        partner = _get_logistics_partner_for_user(user_id, db)
    elif order.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this order tracking")

    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).order_by(Shipment.created_at.asc()).all()
    if partner is not None:
        shipments = [shipment for shipment in shipments if shipment.assigned_partner_id == partner.id]
        if not shipments:
            raise HTTPException(status_code=403, detail="You do not have access to this order tracking")

    shipment_ids = [shipment.id for shipment in shipments]
    events = (
        db.query(ShipmentEvent)
        .filter(ShipmentEvent.shipment_id.in_(shipment_ids))
        .order_by(ShipmentEvent.created_at.asc())
        .all()
        if shipment_ids
        else []
    )
    confirmations = (
        db.query(ShipmentConfirmation)
        .filter(ShipmentConfirmation.shipment_id.in_(shipment_ids))
        .order_by(ShipmentConfirmation.created_at.desc(), ShipmentConfirmation.id.desc())
        .all()
        if shipment_ids
        else []
    )
    return_request = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.order_id == order_id)
        .order_by(ReturnRequest.created_at.desc())
        .first()
    )

    reconciled_status = reconcile_order_status(order, shipments)
    if order.status != reconciled_status:
        order.status = reconciled_status
        db.commit()
        db.refresh(order)

    visible_supplier_ids = {shipment.supplier_id for shipment in shipments if shipment.supplier_id is not None}
    return build_order_tracking_payload(
        order,
        shipments,
        events,
        confirmations=confirmations,
        return_request=return_request,
        visible_supplier_ids=visible_supplier_ids if partner is not None else None,
        include_financials=partner is None,
        include_return_request=partner is None,
    )


def respond_to_shipment_confirmation(
    order_id: int,
    confirmation_id: int,
    data: dict,
    current_user: dict,
    db: Session,
) -> dict:
    confirmation = db.query(ShipmentConfirmation).filter(
        ShipmentConfirmation.id == confirmation_id,
        ShipmentConfirmation.order_id == order_id,
    ).first()
    if not confirmation:
        raise HTTPException(status_code=404, detail="Confirmation request not found")

    role = current_user.get("role")
    user_id = current_user.get("id")
    if role not in STAFF_ROLES and user_id != confirmation.target_user_id:
        raise HTTPException(status_code=403, detail="You cannot respond to this confirmation request")

    if confirmation.status != "pending":
        raise HTTPException(status_code=409, detail="This confirmation request has already been resolved")

    decision = str(data.get("decision", "")).strip().lower()
    if decision not in {"accepted", "rejected"}:
        raise HTTPException(status_code=422, detail="decision must be one of: accepted, rejected")

    response_notes = str(data.get("response_notes") or data.get("notes") or "").strip() or None
    shipment = db.query(Shipment).filter(Shipment.id == confirmation.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    confirmation.status = decision
    confirmation.response_notes = response_notes
    confirmation.responded_at = _utcnow()

    if decision == "accepted":
        current_status = cast(str, getattr(shipment, "status", "pending"))
        requested_status = cast(str, getattr(confirmation, "requested_status", current_status))

        if confirmation.confirmation_type == "pickup" and current_status != "picking_up":
            raise HTTPException(status_code=409, detail="Shipment is no longer awaiting pickup confirmation")
        if confirmation.confirmation_type == "delivery" and current_status not in {"shipped", "in_transit"}:
            raise HTTPException(status_code=409, detail="Shipment is no longer awaiting delivery confirmation")

        shipment.status = requested_status
        if confirmation.current_hub:
            shipment.current_hub = confirmation.current_hub
        if confirmation.tracking_number:
            shipment.tracking_number = confirmation.tracking_number
        if not cast(str | None, getattr(shipment, "scan_code", None)):
            shipment.scan_code = f"SHIP-{shipment.id}"
        if requested_status == "shipped" and not cast(datetime | None, getattr(shipment, "shipped_at", None)):
            shipment.shipped_at = _utcnow()
        if requested_status == "delivered":
            shipment.delivery_signature_name = confirmation.delivery_signature_name
            shipment.delivery_signature_data_url = confirmation.delivery_signature_data_url
            shipment.delivery_signature_captured_at = confirmation.responded_at
            if not cast(datetime | None, getattr(shipment, "actual_delivery", None)):
                shipment.actual_delivery = confirmation.responded_at
        shipment.updated_at = _utcnow()

        event_notes = confirmation.notes or response_notes
        db.add(
            ShipmentEvent(
                shipment_id=shipment.id,
                order_id=shipment.order_id,
                supplier_id=shipment.supplier_id,
                actor_user_id=current_user["id"],
                actor_role=role,
                event_type=confirmation.requested_event_type,
                status_after=requested_status,
                distribution_channel=shipment.distribution_channel,
                location=confirmation.current_hub,
                scan_code=shipment.scan_code or f"SHIP-{shipment.id}",
                notes=event_notes,
            )
        )

        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order is not None:
            order_shipments = db.query(Shipment).filter(Shipment.order_id == order.id).all()
            new_order_status = reconcile_order_status(order, order_shipments)
            order.status = new_order_status

            # ── Cash Management: create settlements when order is delivered ──
            if new_order_status == "delivered":
                try:
                    from domains.finance.ports import create_settlements_on_delivery
                    create_settlements_on_delivery(order, db)
                except Exception:
                    logger.exception("Failed to create settlements for delivered order %s", order.id)

        if confirmation.requester_user_id is not None:
            db.add(
                Notification(
                    user_id=confirmation.requester_user_id,
                    type="shipment_update",
                    title="Confirmation Accepted",
                    message=(
                        f"{confirmation.confirmation_type.title()} confirmation accepted for Order #{shipment.order_id}."
                    ),
                    link=f"/tracking/{shipment.order_id}",
                )
            )
    else:
        if confirmation.requester_user_id is not None:
            db.add(
                Notification(
                    user_id=confirmation.requester_user_id,
                    type="shipment_update",
                    title="Confirmation Rejected",
                    message=(
                        f"{confirmation.confirmation_type.title()} confirmation rejected for Order #{shipment.order_id}."
                    ),
                    link=f"/tracking/{shipment.order_id}",
                )
            )

    db.commit()
    db.refresh(confirmation)
    if decision == "accepted":
        try:
            from domains.comms.ports import enqueue_shipment_status_email

            enqueue_shipment_status_email(cast(int, shipment.id), event_type=cast(str, confirmation.requested_event_type))
        except Exception:
            logger.exception("Failed to enqueue shipment confirmation email for shipment %s", shipment.id)
    return {
        "id": confirmation.id,
        "status": confirmation.status,
        "responded_at": confirmation.responded_at.isoformat() if confirmation.responded_at else None,
        "response_notes": confirmation.response_notes,
        "shipment_id": confirmation.shipment_id,
        "order_id": confirmation.order_id,
        "requested_status": confirmation.requested_status,
    }


def confirm_order_receipt_scan(order_id: int, data: dict, current_user: dict, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    role = current_user.get("role")
    if role not in STAFF_ROLES and order.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="You cannot confirm receipt for this order")

    scan_code = str(data.get("scan_code", "")).strip()
    if not scan_code:
        raise HTTPException(status_code=422, detail="scan_code is required")

    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    if not shipments:
        raise HTTPException(status_code=404, detail="No shipments found for this order")

    matched = None
    for shipment in shipments:
        if scan_code in shipment_scan_codes(shipment):
            matched = shipment
            break
    if not matched:
        raise HTTPException(status_code=409, detail="scan_code does not match this order shipments")

    matched.status = "delivered"
    matched.actual_delivery = matched.actual_delivery or _utcnow()
    matched.updated_at = matched.actual_delivery
    order_shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    order.status = reconcile_order_status(order, order_shipments)

    db.add(
        ShipmentEvent(
            shipment_id=matched.id,
            order_id=matched.order_id,
            supplier_id=matched.supplier_id,
            actor_user_id=current_user.get("id"),
            actor_role=role or "customer",
            event_type="customer_received",
            status_after="delivered",
            distribution_channel=matched.distribution_channel,
            location=str(data.get("location", "")).strip() or matched.current_hub,
            scan_code=scan_code,
            notes=str(data.get("notes", "")).strip() or "Customer receipt confirmed by scan",
        )
    )
    db.add(
        Notification(
            user_id=order.user_id,
            type="order_update",
            title="Delivery Confirmed",
            message=f"Order #{order.id} has been confirmed as received.",
            link=f"/orders/{order.id}",
        )
    )

    db.commit()
    return {
        "message": "Receipt confirmed",
        "order_id": order.id,
        "shipment_id": matched.id,
        "status": order.status,
    }


def cancel_order(order_id: int, current_user: dict, db: Session) -> Order:
    with request_context(user_id=str(current_user.get("id"))):
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user["id"],
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if not validate_order_transition(order.status, "cancelled"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel order in '{order.status}' status. Only pending or confirmed orders can be cancelled.",
            )
        logger.info(
            "order_cancellation",
            order_id=order.id,
            user_id=current_user.get("id"),
            previous_status=order.status,
            correlation_id=get_correlation_id(),
        )
        apply_order_status_change(order, "cancelled", db)
        db.add(
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Order Cancelled",
                message=f"Order #{order.id} has been cancelled.",
                link=f"/orders/{order.id}",
            )
        )
        db.commit()
        db.refresh(order)
        setattr(order, "status_label", order_status_label(order.status, [], []))
        return order


# === RELIABILITY: Health & Metrics ===


def get_orders_health() -> dict:
    """Return health status of the orders service for monitoring."""
    from infrastructure.database.database import check_connection_health, get_pool_metrics

    db_healthy = check_connection_health()
    pool_metrics = get_pool_metrics()

    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "connection_pool": pool_metrics,
        "valid_transitions": {k: list(v) for k, v in VALID_ORDER_TRANSITIONS.items()},
    }
