import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence, cast

from data.models import Order, OrderLogisticsAllocation, RefundLedger, ReturnRequest, Shipment, ShipmentConfirmation, ShipmentEvent, TransactionLedger, User
from sqlalchemy.orm import object_session
from utils.config import settings


TERMINAL_ORDER_STATUSES = {"cancelled", "failed", "refunded"}

DEFAULT_STATUS_LABELS = {
    "pending": "Pending",
    "confirmed": "Confirmed",
    "processing": "Processing",
    "prepared": "Prepared",
    "picking_up": "Picking Up",
    "shipped": "Shipped",
    "in_transit": "In Transit",
    "delivered": "Delivered",
    "failed": "Failed",
    "returned": "Returned",
    "cancelled": "Cancelled",
    "refunded": "Refunded",
    "completed": "Completed",
}

PROGRESS_EVENT_LABELS = {
    "supplier_prepared": "Prepared",
    "awaiting_pickup": "Awaiting Pickup",
    "pickup_confirmed": "Picking Up",
    "pickup_cancelled": "Prepared",
    "picked_from_supplier": "Picked From Supplier",
    "logistics_received": "Logistics Received",
    "distribution_checkpoint": "Distribution Checkpoint",
    "out_for_delivery": "Out for Delivery",
    "customer_received": "Delivered",
    "shipment_failed": "Shipment Failed",
    "shipment_returned": "Shipment Returned",
    "shipment_delayed": "Shipment Delayed",
    "shipment_rescheduled": "Shipment Rescheduled",
    "shipment_cancelled": "Shipment Cancelled",
}

CONFIRMATION_TYPE_LABELS = {
    "pickup": "Supplier Pickup Confirmation",
    "delivery": "Customer Delivery Confirmation",
}

EVENT_STATUS_COMPATIBILITY = {
    "supplier_prepared": {"processing"},
    "awaiting_pickup": {"prepared"},
    "pickup_confirmed": {"picking_up"},
    "pickup_cancelled": {"processing"},
    "picked_from_supplier": {"shipped"},
    "logistics_received": {"shipped"},
    "distribution_checkpoint": {"in_transit"},
    "out_for_delivery": {"in_transit"},
    "customer_received": {"delivered"},
    "shipment_failed": {"failed"},
    "shipment_returned": {"returned"},
    "shipment_delayed": {"shipped", "in_transit"},
    "shipment_rescheduled": {"shipped", "in_transit"},
    "shipment_cancelled": {"failed", "returned"},
}


def canonical_scan_code(shipment: Shipment) -> str:
    scan_code = cast(str | None, getattr(shipment, "scan_code", None))
    if scan_code and scan_code.strip():
        return scan_code.strip()
    return generated_scan_code(shipment)


def generated_tracking_number(shipment: Shipment) -> str:
    created_at = cast(datetime | None, getattr(shipment, "created_at", None)) or datetime.now(timezone.utc).replace(tzinfo=None)
    return f"ZOZI-TK-{created_at:%Y%m%d}-{cast(int, getattr(shipment, 'id', 0)):06d}"


def canonical_tracking_number(shipment: Shipment) -> str:
    tracking_number = cast(str | None, getattr(shipment, "tracking_number", None))
    if tracking_number and tracking_number.strip():
        return tracking_number.strip()
    return generated_tracking_number(shipment)


def generated_scan_code(shipment: Shipment) -> str:
    created_at = cast(datetime | None, getattr(shipment, "created_at", None)) or datetime.now(timezone.utc).replace(tzinfo=None)
    return f"ZOZI-QR-{created_at:%Y%m%d}-{cast(int, getattr(shipment, 'id', 0)):06d}"


def ensure_shipment_identifiers(shipment: Shipment) -> tuple[str, str]:
    tracking_number = canonical_tracking_number(shipment)
    scan_code = canonical_scan_code(shipment)
    if cast(str | None, getattr(shipment, "tracking_number", None)) != tracking_number:
        setattr(shipment, "tracking_number", tracking_number)
    if cast(str | None, getattr(shipment, "scan_code", None)) != scan_code:
        setattr(shipment, "scan_code", scan_code)
    return tracking_number, scan_code


def shipment_scan_codes(shipment: Shipment) -> set[str]:
    return {
        code
        for code in {
            canonical_scan_code(shipment),
            f"ORDER-{shipment.order_id}",
            canonical_tracking_number(shipment),
        }
        if code
    }


def default_status_label(status: str | None) -> str:
    if not status:
        return "Pending"
    return DEFAULT_STATUS_LABELS.get(status, status.replace("_", " ").title())


def normalize_shipment_event_type(
    event_type: str | ShipmentEvent,
    status_after: str | None = None,
    actor_role: str | None = None,
) -> str:
    if isinstance(event_type, ShipmentEvent):
        actor_role = cast(str | None, getattr(event_type, "actor_role", None))
        status_after = cast(str | None, getattr(event_type, "status_after", None))
        event_type = cast(str, getattr(event_type, "event_type", ""))

    if event_type == "picked_from_supplier" and status_after in {"processing", "prepared"}:
        return "supplier_prepared"
    if event_type == "picked_from_supplier" and actor_role == "supplier" and status_after != "shipped":
        return "supplier_prepared"
    return event_type


def shipment_event_label(event: ShipmentEvent | None) -> str | None:
    if event is None:
        return None
    normalized_type = normalize_shipment_event_type(event)
    if normalized_type in PROGRESS_EVENT_LABELS:
        return PROGRESS_EVENT_LABELS[normalized_type]
    event_type = cast(str, getattr(event, "event_type", ""))
    return event_type.replace("_", " ").title() if event_type else None


def _sort_events_desc(events: Sequence[ShipmentEvent]) -> list[ShipmentEvent]:
    return sorted(
        events,
        key=lambda event: (
            cast(datetime | None, getattr(event, "created_at", None)) or datetime.min,
            cast(int, getattr(event, "id", 0)),
        ),
        reverse=True,
    )


def latest_progress_event(
    shipment: Shipment | None = None,
    events: Sequence[ShipmentEvent] | None = None,
) -> ShipmentEvent | None:
    ordered_events: Sequence[ShipmentEvent]
    if events is not None:
        ordered_events = _sort_events_desc(events)
    elif shipment is not None:
        session = object_session(shipment)
        if session is None:
            ordered_events = []
        else:
            ordered_events = (
                session.query(ShipmentEvent)
                .filter(ShipmentEvent.shipment_id == shipment.id)
                .order_by(ShipmentEvent.created_at.desc(), ShipmentEvent.id.desc())
                .all()
            )
    else:
        ordered_events = []

    for event in ordered_events:
        if normalize_shipment_event_type(event) in PROGRESS_EVENT_LABELS:
            return event
    return None


def shipment_status_label(
    status: str,
    shipment: Shipment | None = None,
    events: Sequence[ShipmentEvent] | None = None,
    latest_event: ShipmentEvent | None = None,
) -> str:
    progress_event = latest_event or latest_progress_event(shipment=shipment, events=events)
    if progress_event is not None:
        normalized_type = normalize_shipment_event_type(progress_event)
        compatible_statuses = EVENT_STATUS_COMPATIBILITY.get(normalized_type, set())
        if status in compatible_statuses:
            label = PROGRESS_EVENT_LABELS.get(normalized_type)
            if label:
                return label
    return default_status_label(status)


def order_status_label(
    order_status: str,
    shipments: Sequence[Shipment],
    events: Sequence[ShipmentEvent],
) -> str:
    if order_status == "processing":
        return "Processing"

    if order_status == "prepared":
        latest_event = latest_progress_event(events=events)
        if latest_event is not None and normalize_shipment_event_type(latest_event) == "supplier_prepared":
            return PROGRESS_EVENT_LABELS["supplier_prepared"]
        return "Prepared"

    if order_status == "picking_up":
        latest_event = latest_progress_event(events=events)
        if latest_event is not None and normalize_shipment_event_type(latest_event) == "pickup_confirmed":
            return PROGRESS_EVENT_LABELS["pickup_confirmed"]
        return "Picking Up"

    if order_status in {"pending", "confirmed", "delivered", "refunded", "completed"}:
        return default_status_label(order_status)

    if order_status in {"cancelled", "failed"}:
        latest_event = latest_progress_event(events=events)
        if latest_event is not None:
            normalized_type = normalize_shipment_event_type(latest_event)
            if normalized_type in {"shipment_cancelled", "shipment_returned", "shipment_failed"}:
                label = PROGRESS_EVENT_LABELS.get(normalized_type)
                if label:
                    return label
        return default_status_label(order_status)

    if order_status == "shipped":
        latest_event = latest_progress_event(events=events)
        if latest_event is not None:
            normalized_type = normalize_shipment_event_type(latest_event)
            if normalized_type in {
                "picked_from_supplier",
                "logistics_received",
                "distribution_checkpoint",
                "out_for_delivery",
                "shipment_delayed",
                "shipment_rescheduled",
                "shipment_cancelled",
                "shipment_failed",
                "shipment_returned",
            }:
                label = PROGRESS_EVENT_LABELS.get(normalized_type)
                if label:
                    return label
        if any(cast(str, getattr(shipment, "status", "")) == "in_transit" for shipment in shipments):
            return default_status_label("in_transit")

    return default_status_label(order_status)


def derive_order_financials(order: Order) -> dict[str, float]:
    subtotal = float(cast(Any, getattr(order, "subtotal_amount", 0)) or 0)
    shipping = float(cast(Any, getattr(order, "shipping_amount", 0)) or 0)
    vat = float(cast(Any, getattr(order, "vat_amount", 0)) or 0)
    discount = float(cast(Any, getattr(order, "discount_amount", 0)) or 0)
    total = float(cast(Any, getattr(order, "total_amount", 0)) or 0)

    after_discount = round(max(subtotal - discount, 0), 2)
    legacy_zero_charges = (
        settings.app_env != "test"
        and subtotal > 0
        and shipping <= 0
        and vat <= 0
        and total <= after_discount
    )
    if legacy_zero_charges:
        shipping = round(float(settings.shipping_flat_rate or 0), 2)
        vat = round(after_discount * float(settings.vat_rate or 0), 2)
        total = round(after_discount + shipping + vat, 2)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "vat": vat,
        "total": total,
    }


def _normalized_return_window_days(raw_value: Any) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = 10
    return max(10, parsed)


def _return_delivery_reference(order: Order, shipments: Sequence[Shipment]) -> datetime | None:
    if cast(str | None, getattr(order, "status", None)) != "delivered":
        return None

    actual_deliveries = [
        cast(datetime | None, getattr(shipment, "actual_delivery", None))
        for shipment in shipments
        if cast(datetime | None, getattr(shipment, "actual_delivery", None)) is not None
    ]
    if actual_deliveries:
        return max(actual_deliveries)

    return cast(datetime | None, getattr(order, "updated_at", None)) or cast(datetime | None, getattr(order, "created_at", None))


def _build_return_eligibility(order: Order, items: list[dict[str, Any]], shipments: Sequence[Shipment]) -> dict[str, Any] | None:
    if not items:
        return None

    delivered_at = _return_delivery_reference(order, shipments)
    order_window_days = max((int(item["return_window_days"]) for item in items), default=10)
    deadline = delivered_at + timedelta(days=order_window_days) if delivered_at is not None else None
    days_remaining = (deadline.date() - datetime.now(timezone.utc).replace(tzinfo=None).date()).days if deadline is not None else None

    return {
        "eligible": delivered_at is not None and (deadline is None or datetime.now(timezone.utc).replace(tzinfo=None) <= deadline),
        "delivered_at": delivered_at.isoformat() if delivered_at is not None else None,
        "return_window_days": order_window_days,
        "deadline": deadline.isoformat() if deadline is not None else None,
        "days_remaining": days_remaining,
        "items": items,
    }


def _build_order_finance_breakdown(order: Order) -> dict[str, Any]:
    financials = derive_order_financials(order)
    session = object_session(order)
    allocations: list[dict[str, Any]] = []
    service_fee_amount = 0.0
    refund_payload = None

    if session is not None:
        allocation_rows = (
            session.query(OrderLogisticsAllocation)
            .filter(OrderLogisticsAllocation.order_id == order.id)
            .order_by(OrderLogisticsAllocation.supplier_id.asc())
            .all()
        )
        supplier_ids = sorted({allocation.supplier_id for allocation in allocation_rows})
        supplier_names: dict[int, str | None] = {}
        if supplier_ids:
            supplier_names = {
                supplier.id: supplier.username
                for supplier in session.query(User).filter(User.id.in_(supplier_ids)).all()
            }
        allocations = [
            {
                "supplier_id": allocation.supplier_id,
                "supplier_name": supplier_names.get(allocation.supplier_id),
                "partner_id": allocation.partner_id,
                "partner_name": allocation.partner_name_snapshot,
                "partner_code": allocation.partner_code_snapshot,
                "service_area_id": allocation.service_area_id,
                "service_area_label": allocation.service_area_label_snapshot,
                "allocation_source": allocation.allocation_source,
                "destination_country": allocation.destination_country,
                "destination_city": allocation.destination_city,
                "shipping_amount": float(cast(Any, allocation.shipping_amount or 0)),
                "pickup_charge": float(cast(Any, allocation.pickup_charge or 0)),
                "dropoff_charge": float(cast(Any, allocation.dropoff_charge or 0)),
                "estimated_delivery_min": allocation.estimated_delivery_min,
                "estimated_delivery_max": allocation.estimated_delivery_max,
                "currency": allocation.currency,
                "pricing_breakdown": json.loads(allocation.pricing_breakdown_json) if getattr(allocation, "pricing_breakdown_json", None) else None,
            }
            for allocation in allocation_rows
        ]

        ledgers = session.query(TransactionLedger).filter(TransactionLedger.order_id == order.id).all()
        if ledgers:
            service_fee_amount = sum(float(cast(Any, ledger.zozi_commission or 0)) for ledger in ledgers)
        else:
            taxable_amount = max(financials["subtotal"] - financials["discount"], 0)
            service_fee_amount = round(taxable_amount * float(settings.zozi_commission_rate or 0), 2)

        refund = (
            session.query(RefundLedger)
            .filter(RefundLedger.order_id == order.id)
            .order_by(RefundLedger.created_at.desc(), RefundLedger.id.desc())
            .first()
        )
        if refund is not None:
            refund_payload = {
                "id": refund.id,
                "status": refund.status,
                "refund_reason": refund.refund_reason,
                "refund_method": refund.refund_method,
                "customer_refund_amount": float(cast(Any, refund.customer_refund_amount or 0)),
                "supplier_reversal": float(cast(Any, refund.supplier_reversal or 0)),
                "logistics_reversal": float(cast(Any, refund.logistics_reversal or 0)),
                "commission_reversal": float(cast(Any, refund.commission_reversal or 0)),
                "vat_adjustment": float(cast(Any, refund.vat_adjustment or 0)),
                "created_at": refund.created_at.isoformat() if refund.created_at else None,
                "processed_at": refund.processed_at.isoformat() if refund.processed_at else None,
            }

    return {
        "payment_method": cast(str | None, getattr(order, "payment_method", None)),
        "subtotal_amount": financials["subtotal"],
        "discount_amount": financials["discount"],
        "shipping_amount": financials["shipping"],
        "vat_amount": financials["vat"],
        "service_fee_amount": service_fee_amount,
        "total_amount": financials["total"],
        "selected_partner_id": cast(int | None, getattr(order, "selected_partner_id", None)),
        "selected_service_area_id": cast(int | None, getattr(order, "selected_service_area_id", None)),
        "estimated_delivery_min": cast(int | None, getattr(order, "estimated_delivery_min", None)),
        "estimated_delivery_max": cast(int | None, getattr(order, "estimated_delivery_max", None)),
        "allocations": allocations,
        "refund": refund_payload,
    }


def reconcile_order_status(order: Order, shipments: Sequence[Shipment]) -> str:
    current_status = cast(str, getattr(order, "status", "pending"))
    if getattr(order, "paid_at", None) is not None and current_status == "pending":
        current_status = "confirmed"

    if not shipments:
        return current_status

    statuses = {cast(str, getattr(shipment, "status", "pending")) for shipment in shipments}
    if statuses and statuses == {"delivered"}:
        return "delivered"
    if statuses and statuses.issubset({"returned"}):
        return "cancelled"
    if statuses and statuses.issubset({"failed", "returned"}):
        return "failed"
    if any(status in {"shipped", "in_transit"} for status in statuses):
        return "shipped"
    if any(status == "picking_up" for status in statuses):
        return "picking_up"
    if any(status == "processing" for status in statuses):
        return "processing" if current_status == "processing" else "prepared"
    if any(status == "pending" for status in statuses):
        return "confirmed" if current_status not in TERMINAL_ORDER_STATUSES else current_status
    return current_status


def serialize_tracking_event(event: ShipmentEvent) -> dict[str, Any]:
    created_at = cast(datetime | None, getattr(event, "created_at", None))
    return {
        "id": event.id,
        "shipment_id": event.shipment_id,
        "order_id": event.order_id,
        "supplier_id": event.supplier_id,
        "actor_user_id": event.actor_user_id,
        "actor_role": event.actor_role,
        "event_type": event.event_type,
        "event_label": shipment_event_label(event),
        "status_after": event.status_after,
        "distribution_channel": event.distribution_channel,
        "location": event.location,
        "latitude": getattr(event, "latitude", None),
        "longitude": getattr(event, "longitude", None),
        "scan_code": event.scan_code,
        "notes": event.notes,
        "created_at": created_at.isoformat() if created_at else None,
    }


def serialize_shipment_confirmation(confirmation: ShipmentConfirmation) -> dict[str, Any]:
    created_at = cast(datetime | None, getattr(confirmation, "created_at", None))
    responded_at = cast(datetime | None, getattr(confirmation, "responded_at", None))
    requested_status = cast(str, getattr(confirmation, "requested_status", "pending"))
    requested_event_type = cast(str, getattr(confirmation, "requested_event_type", ""))
    return {
        "id": confirmation.id,
        "shipment_id": confirmation.shipment_id,
        "order_id": confirmation.order_id,
        "supplier_id": confirmation.supplier_id,
        "requester_user_id": getattr(confirmation, "requester_user_id", None),
        "requester_role": getattr(confirmation, "requester_role", None),
        "target_user_id": confirmation.target_user_id,
        "target_role": confirmation.target_role,
        "confirmation_type": confirmation.confirmation_type,
        "confirmation_label": CONFIRMATION_TYPE_LABELS.get(
            confirmation.confirmation_type,
            confirmation.confirmation_type.replace("_", " ").title(),
        ),
        "status": confirmation.status,
        "requested_status": requested_status,
        "requested_status_label": PROGRESS_EVENT_LABELS.get(requested_event_type) or default_status_label(requested_status),
        "requested_event_type": requested_event_type,
        "current_hub": getattr(confirmation, "current_hub", None),
        "tracking_number": getattr(confirmation, "tracking_number", None),
        "delivery_signature_name": getattr(confirmation, "delivery_signature_name", None),
        "delivery_signature_data_url": getattr(confirmation, "delivery_signature_data_url", None),
        "notes": getattr(confirmation, "notes", None),
        "response_notes": getattr(confirmation, "response_notes", None),
        "created_at": created_at.isoformat() if created_at else None,
        "responded_at": responded_at.isoformat() if responded_at else None,
    }


def _shipment_tracking_url(shipment: Shipment) -> str | None:
    tracking_number = cast(str | None, getattr(shipment, "tracking_number", None))
    carrier = getattr(shipment, "carrier", None)
    tracking_template = cast(str | None, getattr(carrier, "tracking_url", None)) if carrier else None
    if tracking_number and tracking_template:
        return tracking_template.replace("{number}", tracking_number)
    return None


def serialize_tracking_shipment(
    shipment: Shipment,
    events: Sequence[ShipmentEvent] | None = None,
    confirmations: Sequence[ShipmentConfirmation] | None = None,
) -> dict[str, Any]:
    shipped_at = cast(datetime | None, getattr(shipment, "shipped_at", None))
    estimated_delivery = cast(datetime | None, getattr(shipment, "estimated_delivery", None))
    actual_delivery = cast(datetime | None, getattr(shipment, "actual_delivery", None))
    packaged_at = cast(datetime | None, getattr(shipment, "packaged_at", None))
    created_at = cast(datetime | None, getattr(shipment, "created_at", None))
    updated_at = cast(datetime | None, getattr(shipment, "updated_at", None))
    supplier = getattr(shipment, "supplier", None)
    carrier = getattr(shipment, "carrier", None)
    assigned_partner = getattr(shipment, "assigned_partner", None)
    status = cast(str, getattr(shipment, "status", "pending"))
    recent_confirmations = [serialize_shipment_confirmation(confirmation) for confirmation in confirmations] if confirmations is not None else []
    active_confirmation = next((confirmation for confirmation in recent_confirmations if confirmation["status"] == "pending"), None)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "supplier_id": shipment.supplier_id,
        "supplier_name": cast(str | None, getattr(supplier, "username", None)) if supplier else None,
        "assigned_partner_id": shipment.assigned_partner_id,
        "assigned_partner_name": cast(str | None, getattr(assigned_partner, "name", None)) if assigned_partner else None,
        "assigned_partner_code": cast(str | None, getattr(assigned_partner, "code", None)) if assigned_partner else None,
        "carrier_id": shipment.carrier_id,
        "carrier_name": shipment.carrier_name or (cast(str | None, getattr(carrier, "name", None)) if carrier else None),
        "tracking_number": shipment.tracking_number,
        "tracking_url": _shipment_tracking_url(shipment),
        "status": status,
        "status_label": shipment_status_label(status, shipment=shipment, events=events),
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
        "scan_code": canonical_scan_code(shipment),
        "package_count": shipment.package_count,
        "package_weight_kg": shipment.package_weight_kg,
        "package_dimensions": shipment.package_dimensions,
        "packaged_at": packaged_at.isoformat() if packaged_at else None,
        "packaged_by_user_id": shipment.packaged_by_user_id,
        "packaging_notes": shipment.packaging_notes,
        "shipping_address": shipment.order.shipping_address if shipment.order else None,
        "shipped_at": shipped_at.isoformat() if shipped_at else None,
        "estimated_delivery": estimated_delivery.isoformat() if estimated_delivery else None,
        "actual_delivery": actual_delivery.isoformat() if actual_delivery else None,
        "delivery_signature_name": getattr(shipment, "delivery_signature_name", None),
        "delivery_signature_data_url": getattr(shipment, "delivery_signature_data_url", None),
        "delivery_signature_captured_at": (
            cast(datetime | None, getattr(shipment, "delivery_signature_captured_at", None)).isoformat()
            if cast(datetime | None, getattr(shipment, "delivery_signature_captured_at", None))
            else None
        ),
        "active_confirmation_request": active_confirmation,
        "recent_confirmation_requests": recent_confirmations,
        "notes": shipment.notes,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "events": [serialize_tracking_event(event) for event in events] if events is not None else None,
    }


def build_tracking_timeline(
    order: Order,
    shipments: Sequence[Shipment],
    events: Sequence[ShipmentEvent],
) -> list[dict[str, Any]]:
    order_created_at = cast(datetime | None, getattr(order, "created_at", None))
    sorted_events = sorted(events, key=lambda event: cast(datetime | None, getattr(event, "created_at", None)) or datetime.min)

    def first_event(*event_types: str) -> ShipmentEvent | None:
        for event in sorted_events:
            if event.event_type in event_types:
                return event
        return None

    def first_shipment_with_status(statuses: Iterable[str]) -> Shipment | None:
        status_set = set(statuses)
        for shipment in shipments:
            if shipment.status in status_set:
                return shipment
        return None

    order_status = cast(str, getattr(order, "status", "pending"))
    preparing_event = first_event("supplier_prepared", "picked_from_supplier", "pickup_cancelled")
    preparing_shipment = first_shipment_with_status({"processing", "picking_up", "shipped", "in_transit", "delivered"})
    if preparing_event and normalize_shipment_event_type(preparing_event) != "supplier_prepared":
        preparing_event = None

    pickup_progress_event = None
    picked_from_supplier_event = None
    for event in sorted_events:
        normalized_type = normalize_shipment_event_type(event)
        if pickup_progress_event is None and normalized_type == "pickup_confirmed":
            pickup_progress_event = event
        if normalized_type in {"picked_from_supplier", "logistics_received"}:
            picked_from_supplier_event = event
            break
    picked_up_shipment = first_shipment_with_status({"shipped", "in_transit", "delivered"})
    transit_event = first_event("distribution_checkpoint", "out_for_delivery")
    transit_shipment = first_shipment_with_status({"in_transit", "delivered"})
    delivered_event = first_event("customer_received")
    has_prepared_stage = (
        preparing_event is not None
        or order_status in {"prepared", "picking_up", "shipped", "in_transit", "delivered", "failed", "cancelled"}
    )
    pickup_in_progress = (
        any(cast(str, getattr(shipment, "status", "pending")) == "picking_up" for shipment in shipments)
        or pickup_progress_event is not None
    )
    picked_from_supplier = (
        any(cast(str, getattr(shipment, "status", "pending")) in {"shipped", "in_transit", "delivered"} for shipment in shipments)
        or picked_from_supplier_event is not None
    )
    pickup_step_label = "Awaiting Pickup" if has_prepared_stage and not pickup_in_progress and not picked_from_supplier else "Picking Up" if pickup_in_progress and not picked_from_supplier else "Picked From Supplier"

    all_shipments_delivered = bool(shipments) and all(shipment.status == "delivered" for shipment in shipments)
    delivery_timestamp = delivered_event.created_at if delivered_event else None
    if not delivery_timestamp and all_shipments_delivered:
        delivery_times = [cast(datetime | None, getattr(shipment, "actual_delivery", None)) for shipment in shipments]
        delivery_timestamp = max((value for value in delivery_times if value), default=None)

    timeline = [
        {
            "key": "placed",
            "label": "Order Placed",
            "completed": True,
            "active": not shipments and order_status not in {"processing", "prepared", "picking_up", "shipped", "in_transit", "delivered", "failed", "cancelled"},
            "timestamp": order_created_at.isoformat() if order_created_at else None,
            "notes": None,
        },
        {
            "key": "preparing",
            "label": "Supplier Preparing" if not has_prepared_stage else "Prepared",
            "completed": preparing_event is not None or has_prepared_stage,
            "active": (order_status == "processing" or (preparing_shipment is not None and not has_prepared_stage)) and not has_prepared_stage,
            "timestamp": (
                cast(datetime | None, getattr(preparing_event, "created_at", None)).isoformat()
                if preparing_event and getattr(preparing_event, "created_at", None)
                else cast(datetime | None, getattr(preparing_shipment, "created_at", None)).isoformat()
                if preparing_shipment and getattr(preparing_shipment, "created_at", None)
                else None
            ),
            "notes": cast(str | None, getattr(preparing_event, "notes", None)) if preparing_event else None,
        },
        {
            "key": "picked_up",
            "label": pickup_step_label,
            "completed": picked_from_supplier,
            "active": has_prepared_stage and not picked_from_supplier,
            "timestamp": (
                cast(datetime | None, getattr(picked_from_supplier_event, "created_at", None)).isoformat()
                if picked_from_supplier_event and getattr(picked_from_supplier_event, "created_at", None)
                else cast(datetime | None, getattr(picked_up_shipment, "shipped_at", None)).isoformat()
                if picked_up_shipment and getattr(picked_up_shipment, "shipped_at", None)
                else None
            ),
            "notes": (
                cast(str | None, getattr(picked_from_supplier_event, "location", None))
                or cast(str | None, getattr(picked_up_shipment, "current_hub", None))
                if picked_from_supplier_event or picked_up_shipment
                else None
            ),
        },
        {
            "key": "in_transit",
            "label": "Out for Delivery",
            "completed": transit_event is not None or transit_shipment is not None,
            "active": False,
            "timestamp": (
                cast(datetime | None, getattr(transit_event, "created_at", None)).isoformat()
                if transit_event and getattr(transit_event, "created_at", None)
                else cast(datetime | None, getattr(transit_shipment, "updated_at", None)).isoformat()
                if transit_shipment and getattr(transit_shipment, "updated_at", None)
                else None
            ),
            "notes": (
                cast(str | None, getattr(transit_event, "location", None))
                or cast(str | None, getattr(transit_shipment, "distribution_channel", None))
                if transit_event or transit_shipment
                else None
            ),
        },
        {
            "key": "delivered",
            "label": "Delivered",
            "completed": all_shipments_delivered or cast(str, getattr(order, "status", "pending")) == "delivered",
            "active": False,
            "timestamp": delivery_timestamp.isoformat() if delivery_timestamp else None,
            "notes": cast(str | None, getattr(delivered_event, "notes", None)) if delivered_event else None,
        },
    ]

    if not all_shipments_delivered:
        for index, step in enumerate(timeline[1:], start=1):
            if not step["completed"]:
                step["active"] = True
                break

    return timeline


def build_order_tracking_payload(
    order: Order,
    shipments: Sequence[Shipment],
    events: Sequence[ShipmentEvent],
    confirmations: Sequence[ShipmentConfirmation] | None = None,
    return_request: ReturnRequest | None = None,
    visible_supplier_ids: set[int] | None = None,
    include_financials: bool = True,
    include_return_request: bool = True,
) -> dict[str, Any]:
    events_by_shipment: dict[int, list[ShipmentEvent]] = defaultdict(list)
    confirmations_by_shipment: dict[int, list[ShipmentConfirmation]] = defaultdict(list)
    for event in sorted(events, key=lambda current: cast(datetime | None, getattr(current, "created_at", None)) or datetime.min):
        events_by_shipment[event.shipment_id].append(event)
    for confirmation in sorted(
        confirmations or [],
        key=lambda current: cast(datetime | None, getattr(current, "created_at", None)) or datetime.min,
        reverse=True,
    ):
        confirmations_by_shipment[confirmation.shipment_id].append(confirmation)

    reconciled_status = reconcile_order_status(order, shipments)
    delivered_shipments = sum(1 for shipment in shipments if shipment.status == "delivered")
    available_scan_codes = [canonical_scan_code(shipment) for shipment in shipments]
    tracking_numbers = [shipment.tracking_number for shipment in shipments if shipment.tracking_number]
    order_items = [
        item
        for item in order.items
        if visible_supplier_ids is None
        or (
            item.product is not None
            and getattr(item.product, "supplier_id", None) in visible_supplier_ids
        )
    ]
    financials = derive_order_financials(order) if include_financials else None
    finance_breakdown = _build_order_finance_breakdown(order) if include_financials else None

    tracking_items = [
        {
            "order_item_id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else f"Product #{item.product_id}",
            "quantity": item.quantity,
            "price": float(item.price or 0),
            "supplier_id": item.product.supplier_id if item.product else None,
            "return_window_days": _normalized_return_window_days(
                cast(Any, getattr(item.product, "return_window_days", None)) if item.product is not None else None
            ),
        }
        for item in order_items
    ]

    active_return_items = []
    if return_request is not None:
        active_return_items = [
            item for item in tracking_items
            if return_request.order_item_id is None or item["order_item_id"] == return_request.order_item_id
        ]

    return {
        "order_id": order.id,
        "order_status": reconciled_status,
        "order_status_label": order_status_label(reconciled_status, shipments, events),
        "payment_method": cast(str | None, getattr(order, "payment_method", None)) if include_financials else None,
        "subtotal_amount": financials["subtotal"] if financials else None,
        "discount_amount": financials["discount"] if financials else None,
        "shipping_amount": financials["shipping"] if financials else None,
        "vat_amount": financials["vat"] if financials else None,
        "total_amount": financials["total"] if financials else None,
        "finance_breakdown": finance_breakdown,
        "shipment_count": len(shipments),
        "delivered_shipments": delivered_shipments,
        "pending_shipments": max(len(shipments) - delivered_shipments, 0),
        "all_shipments_delivered": bool(shipments) and delivered_shipments == len(shipments),
        "tracking_numbers": tracking_numbers,
        "available_scan_codes": available_scan_codes,
        "shipping_address": order.shipping_address,
        "customer_phone": order.customer_phone,
        "delivery_location": order.delivery_location,
        "delivery_note": order.delivery_note,
        "return_eligibility": _build_return_eligibility(order, tracking_items, shipments),
        "active_return_request": (
            {
                "id": return_request.id,
                "order_item_id": return_request.order_item_id,
                "intent": return_request.intent,
                "status": return_request.status,
                "reason": return_request.reason,
                "resolution_notes": return_request.resolution_notes,
                "items": active_return_items,
                "created_at": return_request.created_at.isoformat() if return_request.created_at else None,
                "updated_at": return_request.updated_at.isoformat() if return_request.updated_at else None,
            }
            if include_return_request and return_request is not None
            else None
        ),
        "items": tracking_items,
        "timeline": build_tracking_timeline(order, shipments, events),
        "shipments": [
            serialize_tracking_shipment(
                shipment,
                events_by_shipment.get(shipment.id, []),
                confirmations_by_shipment.get(shipment.id, []),
            )
            for shipment in shipments
        ],
    }

