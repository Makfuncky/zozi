"""
Cash Management Service — core financial logic for the Zozi platform.

Responsibilities:
  - Create transaction ledger entries on order confirmation
  - Compute commission splits (product, delivery, VAT, Zozi fee)
  - Create supplier/logistics settlement records on delivery
  - Trigger automated payouts after holding period
  - Reconciliation engine for COD and card payments
  - Refund ledger creation on cancellation/return
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    BadgeBillingRecord,
    BankTransaction,
    FinanceBankAccount,
    LogisticsCODRemittanceReceipt,
    LogisticsPartner,
    LogisticsPartnerPayout,
    LogisticsPartnerServiceArea,
    LogisticsSettlement,
    Order,
    OrderItem,
    OrderLogisticsAllocation,
    PaymentReconciliationRun,
    PaymentGatewayConnection,
    Payout,
    Product,
    ProcessedWebhookEvent,
    RefundLedger,
    ReturnRequest,
    Shipment,
    SupplierSettlement,
    TransactionLedger,
    VATRemittance,
)
from services.logistics_partner_pricing import (
    _build_service_area_pricing_breakdown,
    lookup_city_distance_km,
    normalize_pricing_breakdown_payload,
    normalize_country_code,
    normalize_vehicle_type,
    resolve_category_rules_for_area,
    resolve_pricing_profile_for_area,
    resolve_vehicle_rule_for_area,
    vehicle_baseline_multiplier,
)
from services.finance_transfer_service import (
    build_logistics_cod_remittance_instruction,
    build_supplier_payout_instruction,
    build_transfer_reference,
    execute_transfer_batch,
    get_default_transfer_provider,
    list_transfer_export_providers,
)
from utils.config import settings
from utils.datetime_utils import utcnow as _utcnow
from utils.money import round_money, to_decimal
from services import commission_engine as _commission_engine

logger = logging.getLogger(__name__)

_SETTLEMENT_CYCLE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _record_payment_reconciliation_run(db: Session, reconciliation: dict[str, Any]) -> dict[str, Any]:
    now = _utcnow()
    stale_threshold = now - timedelta(hours=2)
    stale_pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == "pending",
        Order.payment_intent_id.isnot(None),
        Order.created_at <= stale_threshold,
    ).scalar() or 0
    recent_webhook_count = db.query(func.count(ProcessedWebhookEvent.id)).filter(
        ProcessedWebhookEvent.processed_at >= now - timedelta(days=1)
    ).scalar() or 0

    payload = {
        "processed": int(reconciliation.get("processed", 0) or 0),
        "reconciled": int(reconciliation.get("reconciled", 0) or 0),
        "unmatched": int(reconciliation.get("unmatched", 0) or 0),
        "stale_pending_orders": int(stale_pending_orders or 0),
        "recent_webhook_count": int(recent_webhook_count or 0),
        "reconciled_items": reconciliation.get("reconciled_items", []),
        "unmatched_items": reconciliation.get("unmatched_items", []),
    }
    run = PaymentReconciliationRun(
        status="completed",
        run_date=now,
        processed_count=payload["processed"],
        reconciled_count=payload["reconciled"],
        unmatched_count=payload["unmatched"],
        stale_pending_orders=payload["stale_pending_orders"],
        recent_webhook_count=payload["recent_webhook_count"],
        result_json=json.dumps(payload, default=str),
        started_at=now,
        completed_at=now,
    )
    db.add(run)
    db.flush()
    payload["run_id"] = cast(int, getattr(run, "id"))
    return payload


def _allocate_proportional_amounts(total_amount: Decimal, supplier_totals: dict[int, Decimal]) -> dict[int, Decimal]:
    supplier_ids = list(supplier_totals.keys())
    total_base = sum(supplier_totals.values(), Decimal(0))
    if not supplier_ids:
        return {}
    if total_base <= 0:
        equal_share = round_money(total_amount / Decimal(len(supplier_ids))) if supplier_ids else Decimal(0)
        allocations = {supplier_id: equal_share for supplier_id in supplier_ids}
        remainder = round_money(total_amount - sum(allocations.values(), Decimal(0)))
        allocations[supplier_ids[-1]] = round_money(allocations[supplier_ids[-1]] + remainder)
        return allocations

    allocations: dict[int, Decimal] = {}
    running_total = Decimal(0)
    for index, supplier_id in enumerate(supplier_ids):
        if index == len(supplier_ids) - 1:
            allocations[supplier_id] = round_money(total_amount - running_total)
            continue
        share = round_money(total_amount * (supplier_totals[supplier_id] / total_base))
        allocations[supplier_id] = share
        running_total += share
    return allocations


def _build_order_logistics_allocations(
    order: Order,
    db: Session,
    items: list[OrderItem],
    shipment_quotes: list[dict[str, object]] | None = None,
) -> list[OrderLogisticsAllocation]:
    supplier_items: dict[int, list[OrderItem]] = {}
    for item in items:
        product = item.product or db.query(Product).filter(Product.id == item.product_id).first()
        supplier_id = product.supplier_id if product else None
        if supplier_id:
            supplier_items.setdefault(supplier_id, []).append(item)

    if not supplier_items:
        return []

    shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
    selected_area = None
    if getattr(order, "selected_service_area_id", None):
        selected_area = db.query(LogisticsPartnerServiceArea).filter(
            LogisticsPartnerServiceArea.id == order.selected_service_area_id
        ).first()

    partner = None
    logistics_partner_id = (
        getattr(order, "selected_partner_id", None)
        or (shipment.assigned_partner_id if shipment else None)
    )
    if logistics_partner_id:
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == logistics_partner_id).first()

    supplier_subtotals: dict[int, Decimal] = {}
    for supplier_id, supplier_order_items in supplier_items.items():
        supplier_subtotals[supplier_id] = sum(
            to_decimal(order_item.price) * to_decimal(order_item.quantity)
            for order_item in supplier_order_items
        )

    quotes_by_supplier = {
        int(quote["supplier_id"]): quote
        for quote in (shipment_quotes or [])
        if quote.get("supplier_id") is not None
    }
    shipping_amounts = _allocate_proportional_amounts(to_decimal(order.shipping_amount or 0), supplier_subtotals)
    area_pickup = to_decimal(getattr(selected_area, "pickup_charge", None) or 0)
    area_dropoff = to_decimal(getattr(selected_area, "dropoff_charge", None) or 0)
    area_total = area_pickup + area_dropoff
    use_area_split = area_total > 0
    service_area_label = cast(str | None, getattr(selected_area, "zone_label", None)) or cast(
        str | None,
        getattr(selected_area, "city_name", None),
    )

    allocations: list[OrderLogisticsAllocation] = []
    supplier_ids = list(supplier_subtotals.keys())
    for supplier_id in supplier_ids:
        quote = quotes_by_supplier.get(supplier_id)
        if quote is not None:
            shipping_amount = round_money(to_decimal(quote.get("shipping_amount") or 0))
            breakdown = cast(dict[str, object] | None, quote.get("pricing_breakdown")) or {}
            pickup_charge = round_money(to_decimal(breakdown.get("pickup_fee") or 0))
            dropoff_charge = round_money(to_decimal(breakdown.get("dropoff_fee") or 0))
            if pickup_charge + dropoff_charge <= 0 and shipping_amount > 0:
                pickup_charge = round_money(shipping_amount / 2)
                dropoff_charge = round_money(shipping_amount - pickup_charge)
            pricing_breakdown_json = None
            if breakdown:
                try:
                    pricing_breakdown_json = json.dumps(breakdown)
                except (TypeError, ValueError):
                    pricing_breakdown_json = None
            quote_service_area = cast(dict[str, object] | None, quote.get("service_area")) or {}
            allocations.append(
                OrderLogisticsAllocation(
                    order_id=order.id,
                    supplier_id=supplier_id,
                    partner_id=cast(int | None, quote.get("partner_id")),
                    service_area_id=cast(int | None, quote.get("service_area_id")),
                    shipment_id=shipment.id if shipment else None,
                    allocation_source=str(quote.get("source") or "fallback"),
                    partner_name_snapshot=cast(str | None, quote.get("partner_name")),
                    partner_code_snapshot=cast(str | None, quote.get("partner_code")),
                    service_area_label_snapshot=cast(str | None, quote_service_area.get("zone_label") or quote_service_area.get("city_name")),
                    destination_country=cast(str | None, getattr(order, "shipping_country", None)),
                    destination_city=cast(str | None, getattr(order, "shipping_city", None)),
                    shipping_amount=shipping_amount,
                    pickup_charge=pickup_charge,
                    dropoff_charge=dropoff_charge,
                    estimated_delivery_min=cast(int | None, quote.get("estimated_delivery_min")),
                    estimated_delivery_max=cast(int | None, quote.get("estimated_delivery_max")),
                    currency=str(quote.get("currency") or settings.default_currency),
                    pricing_breakdown_json=pricing_breakdown_json,
                )
            )
            continue

        shipping_amount = shipping_amounts.get(supplier_id, Decimal(0))
        if use_area_split:
            pickup_charge = round_money(shipping_amount * (area_pickup / area_total))
            dropoff_charge = round_money(shipping_amount - pickup_charge)
        else:
            pickup_charge = round_money(shipping_amount / 2)
            dropoff_charge = round_money(shipping_amount - pickup_charge)

        allocations.append(
            OrderLogisticsAllocation(
                order_id=order.id,
                supplier_id=supplier_id,
                partner_id=logistics_partner_id,
                service_area_id=getattr(order, "selected_service_area_id", None),
                shipment_id=shipment.id if shipment else None,
                allocation_source="approved_partner_quote" if selected_area else "fallback",
                partner_name_snapshot=cast(str | None, getattr(partner, "name", None)),
                partner_code_snapshot=cast(str | None, getattr(partner, "code", None)),
                service_area_label_snapshot=service_area_label,
                destination_country=cast(str | None, getattr(order, "shipping_country", None)),
                destination_city=cast(str | None, getattr(order, "shipping_city", None)),
                shipping_amount=shipping_amount,
                pickup_charge=pickup_charge,
                dropoff_charge=dropoff_charge,
                estimated_delivery_min=getattr(order, "estimated_delivery_min", None),
                estimated_delivery_max=getattr(order, "estimated_delivery_max", None),
                currency=settings.default_currency,
                pricing_breakdown_json=_compute_allocation_pricing_breakdown_json(order, selected_area, db),
            )
        )

    return allocations


def _compute_allocation_pricing_breakdown_json(
    order: Order,
    selected_area: LogisticsPartnerServiceArea | None,
    db: Session,
) -> str | None:
    """Re-compute the pricing breakdown at allocation time and return it as a JSON string."""
    if selected_area is None:
        return None
    total_weight: Decimal = Decimal("0")
    items = list(order.items or [])
    if not items:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        product = item.product or db.query(Product).filter(Product.id == item.product_id).first()
        weight = to_decimal(getattr(product, "weight", None) or 0)
        qty = to_decimal(getattr(item, "quantity", 1) or 1)
        total_weight += weight * qty
    dest_city = cast(str | None, getattr(order, "shipping_city", None))
    dest_country = cast(str | None, getattr(order, "shipping_country", None))
    area_cc = cast(str | None, getattr(selected_area, "country_code", None))
    area_origin = cast(str | None, getattr(selected_area, "origin_city", None))
    pricing_profile = resolve_pricing_profile_for_area(db, selected_area)
    per_km_rate = getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(selected_area, "per_km_rate", None)
    distance_km: Decimal | None = None
    if per_km_rate and area_origin and dest_city:
        distance_km = lookup_city_distance_km(
            db,
            origin_country_code=area_cc,
            origin_city_name=area_origin,
            destination_country_code=normalize_country_code(dest_country or ""),
            destination_city_name=dest_city,
        )
    breakdown = _build_service_area_pricing_breakdown(
        selected_area,
        pricing_profile=pricing_profile,
        apply_vehicle_multiplier=False,
        total_weight_kg=total_weight,
        distance_km=distance_km,
        destination_country_code=normalize_country_code(dest_country or ""),
        destination_city_name=dest_city,
    )
    try:
        return json.dumps(breakdown)
    except (TypeError, ValueError):
        return None


def deserialize_pricing_breakdown_json(payload: str | None) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return {}
    return normalize_pricing_breakdown_payload(data if isinstance(data, dict) else {})


def effective_allocation_delivery_amounts(
    allocation: OrderLogisticsAllocation | None,
    *,
    fallback_shipping: Decimal | float | int | None = None,
    fallback_pickup: Decimal | float | int | None = None,
    fallback_dropoff: Decimal | float | int | None = None,
) -> dict[str, Decimal]:
    shipping = to_decimal(fallback_shipping or 0)
    pickup = to_decimal(fallback_pickup or 0)
    dropoff = to_decimal(fallback_dropoff or 0)
    if allocation is None:
        return {
            "shipping_amount": round_money(shipping),
            "pickup_charge": round_money(pickup),
            "dropoff_charge": round_money(dropoff),
        }
    accepted_shipping = getattr(allocation, "accepted_shipping_amount", None)
    accepted_pickup = getattr(allocation, "accepted_pickup_charge", None)
    accepted_dropoff = getattr(allocation, "accepted_dropoff_charge", None)
    return {
        "shipping_amount": round_money(to_decimal(accepted_shipping if accepted_shipping is not None else getattr(allocation, "shipping_amount", None) or shipping)),
        "pickup_charge": round_money(to_decimal(accepted_pickup if accepted_pickup is not None else getattr(allocation, "pickup_charge", None) or pickup)),
        "dropoff_charge": round_money(to_decimal(accepted_dropoff if accepted_dropoff is not None else getattr(allocation, "dropoff_charge", None) or dropoff)),
    }


def _find_order_logistics_allocation_for_shipment(shipment: Shipment, db: Session) -> OrderLogisticsAllocation | None:
    shipment_id = cast(int | None, getattr(shipment, "id", None))
    if shipment_id is not None:
        exact = (
            db.query(OrderLogisticsAllocation)
            .filter(OrderLogisticsAllocation.shipment_id == shipment_id)
            .order_by(OrderLogisticsAllocation.id.desc())
            .first()
        )
        if exact is not None:
            return exact
    return (
        db.query(OrderLogisticsAllocation)
        .filter(
            OrderLogisticsAllocation.order_id == shipment.order_id,
            OrderLogisticsAllocation.supplier_id == shipment.supplier_id,
        )
        .order_by(OrderLogisticsAllocation.id.desc())
        .first()
    )


def apply_shipment_vehicle_selection(
    shipment: Shipment,
    db: Session,
    *,
    vehicle_type: str | None,
) -> dict[str, Any] | None:
    allocation = _find_order_logistics_allocation_for_shipment(shipment, db)
    if allocation is None:
        return None

    normalized_vehicle = normalize_vehicle_type(vehicle_type)
    if not normalized_vehicle:
        setattr(shipment, "accepted_vehicle_rule_id", None)
        setattr(shipment, "accepted_vehicle_type", None)
        setattr(shipment, "accepted_vehicle_multiplier", None)
        setattr(shipment, "accepted_vehicle_selected_at", None)

        setattr(allocation, "accepted_vehicle_rule_id", None)
        setattr(allocation, "accepted_vehicle_type", None)
        setattr(allocation, "accepted_vehicle_multiplier", None)
        setattr(allocation, "accepted_shipping_amount", None)
        setattr(allocation, "accepted_pickup_charge", None)
        setattr(allocation, "accepted_dropoff_charge", None)
        setattr(allocation, "accepted_pricing_breakdown_json", None)
        setattr(allocation, "accepted_at", None)
        setattr(allocation, "updated_at", _utcnow())
        return None

    order = shipment.order or db.query(Order).filter(Order.id == shipment.order_id).first()
    if order is None:
        raise HTTPException(status_code=409, detail="Shipment order could not be resolved")

    area_id = cast(int | None, getattr(allocation, "service_area_id", None) or getattr(order, "selected_service_area_id", None))
    if area_id is None:
        raise HTTPException(status_code=409, detail="Shipment has no approved service area pricing snapshot")

    area = db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == area_id).first()
    if area is None:
        raise HTTPException(status_code=409, detail="Service area for the shipment could not be resolved")

    base_breakdown = deserialize_pricing_breakdown_json(cast(str | None, getattr(allocation, "pricing_breakdown_json", None)))
    matched_categories = [
        str(category)
        for category in cast(list[Any], base_breakdown.get("matched_handling_labels") or [])
        if str(category).strip()
    ]
    total_weight_kg = base_breakdown.get("total_weight_kg", 0)
    total_volume_cm3 = base_breakdown.get("total_volume_cm3", 0)
    pickup_count = int(base_breakdown.get("pickup_count") or 1)
    dropoff_count = int(base_breakdown.get("dropoff_count") or 1)
    route_type = str(base_breakdown.get("route_type") or "in_city").strip().lower() or "in_city"
    destination_country_code = str(
        getattr(allocation, "destination_country", None)
        or getattr(order, "shipping_country", None)
        or ""
    )
    destination_city_name = cast(str | None, getattr(allocation, "destination_city", None) or getattr(order, "shipping_city", None))
    distance_km = base_breakdown.get("distance_km")

    pricing_profile = resolve_pricing_profile_for_area(db, area)
    category_rules = resolve_category_rules_for_area(db, area, matched_categories)
    vehicle_rule = resolve_vehicle_rule_for_area(
        db,
        area,
        route_type=route_type,
        total_weight_kg=total_weight_kg,
        total_volume_cm3=total_volume_cm3,
        preferred_vehicle_type=normalized_vehicle,
    )
    if vehicle_rule is None and normalized_vehicle not in {"bike", "car", "van", "truck"}:
        raise HTTPException(status_code=422, detail="Unsupported vehicle_type for shipment acceptance")

    selected_vehicle_type = cast(str | None, getattr(vehicle_rule, "vehicle_type", None)) or normalized_vehicle.title()
    selected_multiplier = (
        to_decimal(getattr(vehicle_rule, "cost_multiplier", None))
        if vehicle_rule is not None
        else vehicle_baseline_multiplier(normalized_vehicle)
    )
    breakdown = _build_service_area_pricing_breakdown(
        area,
        pricing_profile=pricing_profile,
        category_rules=category_rules,
        vehicle_rule=vehicle_rule,
        vehicle_type_override=selected_vehicle_type,
        vehicle_multiplier_override=selected_multiplier,
        vehicle_rule_id_override=cast(int | None, getattr(vehicle_rule, "id", None)),
        categories=matched_categories,
        total_weight_kg=total_weight_kg,
        total_volume_cm3=total_volume_cm3,
        pickup_count=pickup_count,
        dropoff_count=dropoff_count,
        distance_km=distance_km,
        destination_country_code=normalize_country_code(destination_country_code),
        destination_city_name=destination_city_name,
    )

    selected_at = _utcnow()
    setattr(shipment, "accepted_vehicle_rule_id", getattr(vehicle_rule, "id", None))
    setattr(shipment, "accepted_vehicle_type", selected_vehicle_type)
    setattr(shipment, "accepted_vehicle_multiplier", selected_multiplier.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    setattr(shipment, "accepted_vehicle_selected_at", selected_at)

    setattr(allocation, "accepted_vehicle_rule_id", getattr(vehicle_rule, "id", None))
    setattr(allocation, "accepted_vehicle_type", selected_vehicle_type)
    setattr(allocation, "accepted_vehicle_multiplier", selected_multiplier.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    setattr(allocation, "accepted_shipping_amount", round_money(to_decimal(breakdown.get("shipping_amount") or 0)))
    setattr(allocation, "accepted_pickup_charge", round_money(to_decimal(breakdown.get("pickup_fee") or 0)))
    setattr(allocation, "accepted_dropoff_charge", round_money(to_decimal(breakdown.get("dropoff_fee") or 0)))
    setattr(allocation, "accepted_pricing_breakdown_json", json.dumps(breakdown))
    setattr(allocation, "accepted_at", selected_at)
    setattr(allocation, "updated_at", selected_at)
    return breakdown


def persist_order_logistics_allocations(
    order: Order,
    db: Session,
    items: list[OrderItem] | None = None,
    shipment_quotes: list[dict[str, object]] | None = None,
) -> list[OrderLogisticsAllocation]:
    existing = (
        db.query(OrderLogisticsAllocation)
        .filter(OrderLogisticsAllocation.order_id == order.id)
        .order_by(OrderLogisticsAllocation.id.asc())
        .all()
    )
    if existing:
        return existing

    order_items = items or list(order.items or [])
    if not order_items:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    if not order_items:
        return []

    allocations = _build_order_logistics_allocations(order, db, order_items, shipment_quotes=shipment_quotes)
    for allocation in allocations:
        db.add(allocation)
    db.flush()
    return allocations


def _gateway_settlement_delay_days(order: Order, db: Session) -> int:
    gateway_code = str(getattr(order, "payment_gateway_code", "") or "").strip().lower()
    if not gateway_code:
        return settings.payout_holding_days

    gateway = (
        db.query(PaymentGatewayConnection)
        .filter(PaymentGatewayConnection.provider_code == gateway_code)
        .first()
    )
    cycle = str(getattr(gateway, "settlement_cycle", "") or "").strip().lower()
    return _SETTLEMENT_CYCLE_DAYS.get(cycle, settings.payout_holding_days)


def _supplier_gateway_fee_allocations(order: Order, ledger_entries: list[TransactionLedger]) -> dict[int, Decimal]:
    gateway_fee = to_decimal(getattr(order, "payment_gateway_fee_amount", None) or 0)
    pass_fee_to_customer = bool(getattr(order, "payment_gateway_fee_passed_to_customer", False))
    if gateway_fee <= 0 or pass_fee_to_customer:
        return {}

    supplier_bases: dict[int, Decimal] = {}
    for entry in ledger_entries:
        supplier_id = cast(int | None, getattr(entry, "supplier_id", None))
        if not supplier_id:
            continue
        supplier_bases[supplier_id] = supplier_bases.get(supplier_id, Decimal(0)) + max(
            to_decimal(getattr(entry, "product_subtotal", None) or 0) - to_decimal(getattr(entry, "discount_amount", None) or 0),
            Decimal(0),
        )
    return _allocate_proportional_amounts(gateway_fee, supplier_bases)


def _normalized_return_window_days(raw_value: object) -> int:
    try:
        parsed = int(raw_value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        parsed = 10
    return max(10, parsed)


def _supplier_return_window_days(order: Order, db: Session) -> dict[int, int]:
    items = list(order.items or [])
    if not items:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    supplier_windows: dict[int, int] = {}
    for item in items:
        product = item.product or db.query(Product).filter(Product.id == item.product_id).first()
        supplier_id = cast(int | None, getattr(product, "supplier_id", None)) if product else None
        if not supplier_id:
            continue
        supplier_windows[supplier_id] = max(
            supplier_windows.get(supplier_id, 10),
            _normalized_return_window_days(getattr(product, "return_window_days", None) if product else None),
        )
    return supplier_windows


# ── Ledger Creation (triggered on order confirmation) ─────────────────────────

def create_ledger_entries_for_order(order: Order, db: Session) -> list[TransactionLedger]:
    """Create transaction ledger entries for every supplier involved in the order.

    Called when an order transitions to 'confirmed' status (COD immediate,
    card/tap after successful payment webhook).
    """
    existing = db.query(TransactionLedger).filter(
        TransactionLedger.order_id == order.id
    ).first()
    if existing:
        logger.info("Ledger entries already exist for order %s — skipping", order.id)
        return []

    items: list[OrderItem] = order.items or []
    if not items:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    if not items:
        logger.warning("No order items found for order %s — cannot create ledger", order.id)
        return []

    # Group items by supplier
    supplier_items: dict[int, list[OrderItem]] = {}
    for item in items:
        product = item.product or db.query(Product).filter(Product.id == item.product_id).first()
        supplier_id = product.supplier_id if product else None
        if supplier_id:
            supplier_items.setdefault(supplier_id, []).append(item)

    # Get shipment for logistics partner link
    shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
    allocations = persist_order_logistics_allocations(order, db, items=items)
    allocations_by_supplier = {allocation.supplier_id: allocation for allocation in allocations}

    payment_method = str(getattr(order, "payment_method", "card") or "card").lower()
    order_total = to_decimal(order.total_amount or 0)
    order_shipping = to_decimal(order.shipping_amount or 0)
    order_vat = to_decimal(order.vat_amount or 0)
    order_discount = to_decimal(order.discount_amount or 0)

    # Resolve per-supplier commission rates via the engine (seeding defaults if needed)
    _global_config = _commission_engine.get_global_config(db)

    # Calculate per-supplier subtotals to proportionally split shipping/VAT/discount
    total_product_subtotal = Decimal(0)
    supplier_subtotals: dict[int, Decimal] = {}
    for sid, sitems in supplier_items.items():
        subtotal = sum(to_decimal(i.price) * to_decimal(i.quantity) for i in sitems)
        supplier_subtotals[sid] = subtotal
        total_product_subtotal += subtotal

    entries: list[TransactionLedger] = []

    for supplier_id, sitems in supplier_items.items():
        product_subtotal = supplier_subtotals[supplier_id]
        # Proportional split based on supplier's share of product subtotal
        ratio = (product_subtotal / total_product_subtotal) if total_product_subtotal > 0 else Decimal(1)

        discount_share = round_money(order_discount * ratio)
        vat_share = round_money(order_vat * ratio)
        allocation = allocations_by_supplier.get(supplier_id)
        shipping_share = to_decimal(allocation.shipping_amount) if allocation else round_money(order_shipping * ratio)
        pickup_charge = to_decimal(allocation.pickup_charge) if allocation else round_money(shipping_share / 2)
        dropoff_charge = to_decimal(allocation.dropoff_charge) if allocation else round_money(shipping_share - pickup_charge)
        logistics_partner_id = (
            allocation.partner_id
            if allocation and allocation.partner_id
            else getattr(order, "selected_partner_id", None)
            or (shipment.assigned_partner_id if shipment else None)
        )

        # Commission on product revenue after discount — use commission engine per item
        taxable_product = round_money(product_subtotal - discount_share)
        # Compute per-item commission amounts then sum for the supplier group
        item_commissions: list[tuple] = []   # (item, commission_amount, rate_result, eng_result)
        for item in sitems:
            item_value = round_money(to_decimal(item.price) * to_decimal(item.quantity))
            # Proportion of discourse for this item
            item_discount = round_money(discount_share * (item_value / product_subtotal)) if product_subtotal > 0 else Decimal(0)
            item_taxable = round_money(item_value - item_discount)
            # Resolve category slug from product.category (tolower + spaces→hyphens)
            prod = item.product or db.query(Product).filter(Product.id == item.product_id).first()
            raw_category = str(getattr(prod, "category", "") or "").lower().replace(" & ", "-").replace(" ", "-")
            category_slug = raw_category if raw_category else None
            rate_result = _commission_engine.get_effective_rate(
                supplier_id=supplier_id,
                product_id=item.product_id,
                category_slug=category_slug,
                db=db,
                country_code=getattr(order, "shipping_country", None),
            )
            eng_result = _commission_engine.compute_commission(item_taxable, rate_result, _global_config)
            item_commissions.append((item, eng_result.commission_amount, rate_result, eng_result))

        commission = round_money(sum(ic[1] for ic in item_commissions))
        # Persist a blended effective rate so finance views and settlements reflect the actual deduction.
        commission_rate = (
            (commission / taxable_product).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if taxable_product > 0
            else Decimal("0.0000")
        )

        # Net amounts
        net_supplier = round_money(taxable_product - commission)
        net_logistics = shipping_share
        net_zozi = round_money(commission + vat_share)

        # COD specifics
        cod_collected = None
        cod_remittance_due = None
        if payment_method == "cod":
            # Logistics collects the full customer payment
            supplier_order_portion = round_money(taxable_product + vat_share + shipping_share)
            cod_collected = supplier_order_portion
            # Logistics retains delivery fee, remits the rest to Zozi
            cod_remittance_due = round_money(supplier_order_portion - net_logistics)

        entry = TransactionLedger(
            order_id=order.id,
            supplier_id=supplier_id,
            logistics_partner_id=logistics_partner_id,
            shipment_id=shipment.id if shipment else None,
            payment_method=payment_method,
            product_subtotal=product_subtotal,
            discount_amount=discount_share,
            delivery_pickup_charge=pickup_charge,
            delivery_dropoff_charge=dropoff_charge,
            delivery_total=shipping_share,
            vat_amount=vat_share,
            zozi_commission_rate=commission_rate,
            zozi_commission=commission,
            net_supplier_amount=net_supplier,
            net_logistics_amount=net_logistics,
            net_zozi_amount=net_zozi,
            cod_collected_amount=cod_collected,
            cod_remittance_due=cod_remittance_due,
            settlement_status="pending",
            currency=settings.default_currency,
            country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
        )
        db.add(entry)
        entries.append(entry)

        # Persist immutable CommissionLedgerEntry records (one per order item)
        try:
            for item, _item_commission, rate_result, eng_result in item_commissions:
                prod = item.product or db.query(Product).filter(Product.id == item.product_id).first()
                item_value = round_money(to_decimal(item.price) * to_decimal(item.quantity))
                item_discount = round_money(discount_share * (item_value / product_subtotal)) if product_subtotal > 0 else Decimal(0)
                item_taxable = round_money(item_value - item_discount)
                _commission_engine.create_commission_ledger_entry(
                    order_id=order.id,
                    supplier_id=supplier_id,
                    order_value=item_taxable,
                    result=eng_result,
                    db=db,
                    order_item_id=item.id,
                    product_id=item.product_id,
                    currency=settings.default_currency,
                    country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
                )
        except Exception as _cle_exc:  # noqa: BLE001
            logger.warning("CommissionLedgerEntry creation failed for order %s: %s", order.id, _cle_exc)

    db.flush()
    logger.info("Created %d ledger entries for order %s", len(entries), order.id)
    return entries


# ── Settlement Creation (triggered when order is delivered) ───────────────────

def create_settlements_on_delivery(order: Order, db: Session) -> None:
    """Create supplier and logistics settlement records when order is delivered.

    Called when the order/shipment status transitions to 'delivered'.
    """
    ledger_entries = db.query(TransactionLedger).filter(
        TransactionLedger.order_id == order.id
    ).all()

    if not ledger_entries:
        logger.warning("No ledger entries for delivered order %s — creating now", order.id)
        ledger_entries = create_ledger_entries_for_order(order, db)

    now = _utcnow()
    gateway_delay_days = _gateway_settlement_delay_days(order, db)
    supplier_return_windows = _supplier_return_window_days(order, db)
    logistics_return_window = max(supplier_return_windows.values(), default=10)
    logistics_eligible_date = now + timedelta(days=max(gateway_delay_days, logistics_return_window))
    gateway_fee_allocations = _supplier_gateway_fee_allocations(order, ledger_entries)
    allocations_by_supplier = {
        allocation.supplier_id: allocation
        for allocation in db.query(OrderLogisticsAllocation).filter(OrderLogisticsAllocation.order_id == order.id).all()
    }

    for entry in ledger_entries:
        allocation = allocations_by_supplier.get(cast(int, entry.supplier_id))
        logistics_amounts = effective_allocation_delivery_amounts(
            allocation,
            fallback_shipping=entry.delivery_total,
            fallback_pickup=entry.delivery_pickup_charge,
            fallback_dropoff=entry.delivery_dropoff_charge,
        )
        payout_delivery_total = logistics_amounts["shipping_amount"]
        payout_pickup_charge = logistics_amounts["pickup_charge"]
        payout_dropoff_charge = logistics_amounts["dropoff_charge"]
        # Supplier settlement
        existing_ss = db.query(SupplierSettlement).filter(
            SupplierSettlement.order_id == order.id,
            SupplierSettlement.supplier_id == entry.supplier_id,
        ).first()
        if not existing_ss:
            gateway_fee_deducted = gateway_fee_allocations.get(entry.supplier_id, Decimal(0))
            supplier_return_window = supplier_return_windows.get(cast(int, entry.supplier_id), 10)
            supplier_eligible_date = now + timedelta(days=max(gateway_delay_days, supplier_return_window))
            ss = SupplierSettlement(
                supplier_id=entry.supplier_id,
                order_id=order.id,
                ledger_id=entry.id,
                gross_amount=round_money(to_decimal(entry.product_subtotal) - to_decimal(entry.discount_amount)),
                commission_rate=entry.zozi_commission_rate,
                commission_amount=entry.zozi_commission,
                commission_deducted=entry.zozi_commission,
                vat_on_commission=round_money(to_decimal(entry.zozi_commission) * to_decimal(settings.vat_rate)),
                net_amount=round_money(max(to_decimal(entry.net_supplier_amount) - gateway_fee_deducted, Decimal(0))),
                status="eligible",
                eligible_at=supplier_eligible_date,
                currency=entry.currency,
                country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
            )
            db.add(ss)

        # Logistics settlement
        if entry.logistics_partner_id:
            existing_ls = db.query(LogisticsSettlement).filter(
                LogisticsSettlement.order_id == order.id,
                LogisticsSettlement.partner_id == entry.logistics_partner_id,
            ).first()
            if not existing_ls:
                payment_method = str(entry.payment_method or "card").lower()
                ls = LogisticsSettlement(
                    partner_id=entry.logistics_partner_id,
                    order_id=order.id,
                    ledger_id=entry.id,
                    shipment_id=entry.shipment_id,
                    pickup_charge=payout_pickup_charge,
                    dropoff_charge=payout_dropoff_charge,
                    total_delivery_fee=payout_delivery_total,
                    cod_collected=entry.cod_collected_amount if payment_method == "cod" else None,
                    cod_remitted=Decimal(0) if payment_method == "cod" else None,
                    cod_retained=payout_delivery_total if payment_method == "cod" else None,
                    cod_remittance_status="pending" if payment_method == "cod" else None,
                    status="eligible",
                    eligible_at=logistics_eligible_date,
                    currency=entry.currency,
                    country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
                )
                db.add(ls)
            else:
                existing_ls.pickup_charge = round_money(to_decimal(existing_ls.pickup_charge or 0) + payout_pickup_charge)
                existing_ls.dropoff_charge = round_money(to_decimal(existing_ls.dropoff_charge or 0) + payout_dropoff_charge)
                existing_ls.total_delivery_fee = round_money(to_decimal(existing_ls.total_delivery_fee or 0) + payout_delivery_total)
                existing_ls.eligible_at = max(cast(datetime, existing_ls.eligible_at), logistics_eligible_date)
                if str(entry.payment_method or "card").lower() == "cod":
                    existing_ls.cod_collected = round_money(to_decimal(existing_ls.cod_collected or 0) + to_decimal(entry.cod_collected_amount or 0))
                    existing_ls.cod_retained = round_money(to_decimal(existing_ls.cod_retained or 0) + payout_delivery_total)

    db.flush()
    logger.info("Settlements created for delivered order %s", order.id)


# ── Automated Bank Transaction logging ────────────────────────────────────────

def log_bank_transaction(
    source: str,
    transaction_type: str,
    category: str,
    amount: Decimal,
    db: Session,
    currency: str = "OMR",
    order_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    logistics_id: Optional[int] = None,
    payout_id: Optional[int] = None,
    refund_id: Optional[int] = None,
    description: Optional[str] = None,
    transaction_ref: Optional[str] = None,
    transaction_date: Optional[datetime] = None,
    country_code: Optional[str] = None,
) -> BankTransaction:
    """Log a bank transaction for reconciliation tracking."""
    if not transaction_ref:
        transaction_ref = f"ZOZI-{uuid.uuid4().hex[:12].upper()}"

    txn = BankTransaction(
        transaction_ref=transaction_ref,
        source=source,
        transaction_type=transaction_type,
        category=category,
        amount=round_money(amount),
        currency=currency,
        linked_order_id=order_id,
        linked_supplier_id=supplier_id,
        linked_logistics_id=logistics_id,
        linked_payout_id=payout_id,
        linked_refund_id=refund_id,
        description=description,
        reconciled=False,
        transaction_date=transaction_date or _utcnow(),
        country_code=country_code,
    )
    db.add(txn)
    db.flush()
    return txn


def log_card_payment_received(order: Order, db: Session) -> BankTransaction:
    """Log a card payment received into Zozi's merchant account."""
    gateway_code = str(getattr(order, "payment_gateway_code", "") or "").strip().lower()
    source = gateway_code or ("stripe" if order.payment_intent_id and order.payment_intent_id.startswith("pi_") else "tap")
    return log_bank_transaction(
        source=source,
        transaction_type="inflow",
        category="card_payment",
        amount=to_decimal(order.total_amount or 0),
        db=db,
        order_id=order.id,
        description=f"Card payment for order #{order.id}",
        transaction_ref=order.payment_intent_id,
        country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
    )


def log_refund_bank_transaction(
    order: Order,
    db: Session,
    *,
    source: str,
    transaction_ref: Optional[str] = None,
    refund_amount: Optional[Decimal] = None,
    description: Optional[str] = None,
    return_request_id: Optional[int] = None,
    transaction_date: Optional[datetime] = None,
) -> BankTransaction:
    """Create or reuse a refund bank transaction and attach it to the matching refund ledger."""
    refund = db.query(RefundLedger).filter(RefundLedger.order_id == order.id)
    if return_request_id is not None:
        refund = refund.filter(RefundLedger.return_request_id == return_request_id)
    refund = refund.order_by(RefundLedger.created_at.desc()).first()
    if refund is None:
        refund = create_refund_ledger_entry(order, db, reason="refund", return_request_id=return_request_id)

    amount = round_money(refund_amount if refund_amount is not None else to_decimal(order.total_amount or 0))

    txn = None
    if transaction_ref:
        txn = db.query(BankTransaction).filter(BankTransaction.transaction_ref == transaction_ref).first()

    if txn is None:
        txn_query = db.query(BankTransaction).filter(
            BankTransaction.category == "refund",
            BankTransaction.linked_order_id == order.id,
            BankTransaction.amount == amount,
        )
        if return_request_id is not None:
            txn_query = txn_query.filter(BankTransaction.linked_refund_id == return_request_id)
        txn = txn_query.order_by(BankTransaction.created_at.desc()).first()

    if txn is None:
        txn = log_bank_transaction(
            source=source,
            transaction_type="outflow",
            category="refund",
            amount=amount,
            db=db,
            currency=getattr(order, "currency", None) or settings.default_currency,
            order_id=order.id,
            refund_id=return_request_id,
            description=description or f"Refund for order #{order.id}",
            transaction_ref=transaction_ref,
            transaction_date=transaction_date,
            country_code=getattr(order, "shipping_country", None) or getattr(order, "country_code", None),
        )
    else:
        txn.linked_order_id = txn.linked_order_id or order.id
        if return_request_id is not None and txn.linked_refund_id is None:
            txn.linked_refund_id = return_request_id
        if description and not txn.description:
            txn.description = description
        if transaction_date and txn.transaction_date is None:
            txn.transaction_date = transaction_date

    if refund is not None:
        refund.status = "processing"
        refund.bank_transaction_id = txn.id
        refund.processed_at = refund.processed_at or _utcnow()

    db.flush()
    return txn


# ── Refund Ledger ─────────────────────────────────────────────────────────────

def create_refund_ledger_entry(
    order: Order,
    db: Session,
    reason: str = "cancellation",
    return_request_id: Optional[int] = None,
) -> Optional[RefundLedger]:
    """Create refund ledger entries reversing the financial impact of an order."""
    existing = db.query(RefundLedger).filter(
        RefundLedger.order_id == order.id,
        RefundLedger.reason == reason,
    ).first()
    if existing:
        logger.info("Refund ledger already exists for order %s reason=%s", order.id, reason)
        return existing

    ledger_entries = db.query(TransactionLedger).filter(
        TransactionLedger.order_id == order.id
    ).all()

    total_supplier_reversal = Decimal(0)
    total_logistics_reversal = Decimal(0)
    total_commission_reversal = Decimal(0)
    total_vat_adjustment = Decimal(0)

    for entry in ledger_entries:
        total_supplier_reversal += to_decimal(entry.net_supplier_amount)
        total_logistics_reversal += to_decimal(entry.net_logistics_amount)
        total_commission_reversal += to_decimal(entry.zozi_commission)
        total_vat_adjustment += to_decimal(entry.vat_amount)

        # Mark ledger as refunded
        entry.settlement_status = "refunded"

    # Determine refund method
    payment_method = str(getattr(order, "payment_method", "card") or "card").lower()
    refund_method = "card_reversal" if payment_method in ("card", "tap", "paytabs", "thawani", "paypal", "stripe", "hyperpay", "omannet") else "cod_cash"

    customer_refund = to_decimal(order.total_amount or 0)

    refund = RefundLedger(
        order_id=order.id,
        return_request_id=return_request_id,
        ledger_id=ledger_entries[0].id if ledger_entries else None,
        refund_reason=reason,
        refund_method=refund_method,
        customer_refund_amount=round_money(customer_refund),
        supplier_reversal=round_money(total_supplier_reversal),
        logistics_reversal=round_money(total_logistics_reversal),
        commission_reversal=round_money(total_commission_reversal),
        vat_adjustment=round_money(total_vat_adjustment),
        status="pending",
        currency=settings.default_currency,
    )
    db.add(refund)

    # Reverse settlements if any
    _reverse_settlements(order.id, db)

    db.flush()

    # Post general-ledger reversal leg for the refund
    try:
        from services.general_ledger_service import post_refund_journal

        post_refund_journal(db, refund)
    except Exception:
        logger.exception("Failed to post refund journal for order %s", order.id)

    logger.info("Created refund ledger for order %s reason=%s", order.id, reason)
    return refund


def _reverse_settlements(order_id: int, db: Session) -> None:
    """Mark relevant settlements as reversed."""
    db.query(SupplierSettlement).filter(
        SupplierSettlement.order_id == order_id,
        SupplierSettlement.status.in_(["pending", "eligible"]),
    ).update({"status": "reversed"}, synchronize_session="fetch")
    db.query(LogisticsSettlement).filter(
        LogisticsSettlement.order_id == order_id,
        LogisticsSettlement.status.in_(["pending", "eligible"]),
    ).update({"status": "reversed"}, synchronize_session="fetch")


def _vat_totals_for_period(
    period_start: datetime,
    period_end: datetime,
    db: Session,
) -> tuple[Decimal, Decimal, Decimal]:
    collected = to_decimal(
        db.query(func.coalesce(func.sum(TransactionLedger.vat_amount), 0))
        .filter(
            TransactionLedger.created_at >= period_start,
            TransactionLedger.created_at <= period_end,
        )
        .scalar()
        or 0
    )
    adjustments = to_decimal(
        db.query(func.coalesce(func.sum(RefundLedger.vat_adjustment), 0))
        .filter(
            RefundLedger.created_at >= period_start,
            RefundLedger.created_at <= period_end,
        )
        .scalar()
        or 0
    )
    amount_due = round_money(max(collected - adjustments, Decimal(0)))
    return round_money(collected), round_money(adjustments), amount_due


def list_vat_remittances(db: Session, *, skip: int = 0, limit: int = 50) -> list[VATRemittance]:
    return (
        db.query(VATRemittance)
        .order_by(VATRemittance.period_end.desc(), VATRemittance.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_finance_bank_settings(db: Session) -> Optional[FinanceBankAccount]:
    return (
        db.query(FinanceBankAccount)
        .filter(FinanceBankAccount.scope == "zozi_primary")
        .order_by(FinanceBankAccount.id.desc())
        .first()
    )


def upsert_finance_bank_settings(
    *,
    data: dict,
    admin_id: Optional[int],
    db: Session,
) -> FinanceBankAccount:
    record = get_finance_bank_settings(db)
    if record is None:
        record = FinanceBankAccount(scope="zozi_primary", created_by=admin_id)
        db.add(record)

    for field in (
        "account_label",
        "beneficiary_name",
        "bank_name",
        "branch_name",
        "account_number",
        "iban",
        "swift_code",
        "routing_number",
        "currency",
        "support_email",
        "support_phone",
        "remittance_reference_prefix",
        "instructions",
        "is_active",
    ):
        if field in data:
            setattr(record, field, data.get(field))

    record.updated_by = admin_id
    db.flush()
    return record


def record_vat_remittance(
    *,
    period_start: datetime,
    period_end: datetime,
    amount_remitted: Decimal,
    admin_id: Optional[int],
    db: Session,
    notes: Optional[str] = None,
    transaction_ref: Optional[str] = None,
    remitted_at: Optional[datetime] = None,
) -> VATRemittance:
    collected, adjustments, amount_due = _vat_totals_for_period(period_start, period_end, db)
    remitted_value = round_money(amount_remitted)
    status = "remitted" if remitted_value >= amount_due else "partial"

    txn = log_bank_transaction(
        source="bank_transfer",
        transaction_type="outflow",
        category="vat_remittance",
        amount=remitted_value,
        db=db,
        currency=settings.default_currency,
        description=(
            f"VAT remittance for {period_start.date().isoformat()} to {period_end.date().isoformat()}"
            if notes is None
            else notes
        ),
        transaction_ref=transaction_ref,
        transaction_date=remitted_at or _utcnow(),
    )

    record = VATRemittance(
        period_start=period_start,
        period_end=period_end,
        vat_collected_amount=collected,
        vat_adjustment_amount=adjustments,
        amount_due=amount_due,
        amount=remitted_value,
        amount_remitted=remitted_value,
        status=status,
        bank_transaction_id=txn.id,
        remitted_at=remitted_at or _utcnow(),
        remitted_by=admin_id,
        notes=notes,
        currency=settings.default_currency,
    )
    db.add(record)
    db.flush()
    return record


# ── Financial Summary / Dashboard ─────────────────────────────────────────────

def get_financial_summary(db: Session) -> dict:
    """Aggregate financial metrics for the admin dashboard."""
    from sqlalchemy import case

    total_revenue = db.query(func.coalesce(func.sum(TransactionLedger.product_subtotal), 0)).scalar()
    total_commission = db.query(func.coalesce(func.sum(TransactionLedger.zozi_commission), 0)).scalar()
    total_badge_fees = db.query(func.coalesce(func.sum(BadgeBillingRecord.amount), 0)).filter(
        BadgeBillingRecord.status == "paid"
    ).scalar()
    total_vat = db.query(func.coalesce(func.sum(TransactionLedger.vat_amount), 0)).scalar()
    total_delivery = db.query(func.coalesce(func.sum(TransactionLedger.delivery_total), 0)).scalar()
    total_supplier_payable = db.query(func.coalesce(func.sum(TransactionLedger.net_supplier_amount), 0)).filter(
        TransactionLedger.settlement_status != "refunded"
    ).scalar()
    total_logistics_payable = db.query(func.coalesce(func.sum(TransactionLedger.net_logistics_amount), 0)).filter(
        TransactionLedger.settlement_status != "refunded"
    ).scalar()
    total_refunds = db.query(func.coalesce(func.sum(RefundLedger.customer_refund_amount), 0)).scalar()
    total_vat_adjusted = db.query(func.coalesce(func.sum(RefundLedger.vat_adjustment), 0)).scalar()
    total_vat_remitted = db.query(func.coalesce(func.sum(VATRemittance.amount_remitted), 0)).scalar()

    pending_cnt = db.query(func.count(TransactionLedger.id)).filter(
        TransactionLedger.settlement_status == "pending"
    ).scalar()
    settled_cnt = db.query(func.count(TransactionLedger.id)).filter(
        TransactionLedger.settlement_status == "fully_settled"
    ).scalar()

    pending_cod = db.query(func.coalesce(func.sum(TransactionLedger.cod_remittance_due), 0)).filter(
        TransactionLedger.settlement_status.in_(["pending", "supplier_settled"]),
        TransactionLedger.payment_method == "cod",
    ).scalar()

    unreconciled = db.query(func.count(BankTransaction.id)).filter(
        BankTransaction.reconciled == False  # noqa: E712
    ).scalar()
    vat_liability_outstanding = round_money(
        max(
            to_decimal(total_vat or 0) - to_decimal(total_vat_adjusted or 0) - to_decimal(total_vat_remitted or 0),
            Decimal(0),
        )
    )

    return {
        "total_revenue": float(total_revenue or 0),
        "total_commission": float(total_commission or 0),
        "total_badge_fee_revenue": float(total_badge_fees or 0),
        "total_vat_collected": float(total_vat or 0),
        "total_vat_adjusted": float(total_vat_adjusted or 0),
        "total_vat_remitted": float(total_vat_remitted or 0),
        "vat_liability_outstanding": float(vat_liability_outstanding),
        "total_delivery_fees": float(total_delivery or 0),
        "total_supplier_payable": float(total_supplier_payable or 0),
        "total_logistics_payable": float(total_logistics_payable or 0),
        "total_refunds": float(total_refunds or 0),
        "net_zozi_revenue": float((total_commission or 0) + (total_vat or 0) + (total_badge_fees or 0) - (total_refunds or 0)),
        "pending_settlements": pending_cnt or 0,
        "completed_settlements": settled_cnt or 0,
        "pending_cod_remittances": float(pending_cod or 0),
        "unreconciled_bank_txns": unreconciled or 0,
        "currency": settings.default_currency,
    }


def get_supplier_financial_summary(supplier_id: int, db: Session) -> dict:
    """Get financial summary for a specific supplier."""
    entries = db.query(TransactionLedger).filter(
        TransactionLedger.supplier_id == supplier_id,
        TransactionLedger.settlement_status != "refunded",
    ).all()

    total_earned = sum(float(e.net_supplier_amount or 0) for e in entries)
    total_commission = sum(float(e.zozi_commission or 0) for e in entries)
    total_gross = sum(float(e.product_subtotal or 0) for e in entries)

    settlements = db.query(SupplierSettlement).filter(
        SupplierSettlement.supplier_id == supplier_id,
    ).all()
    refunds = db.query(RefundLedger).join(TransactionLedger, TransactionLedger.order_id == RefundLedger.order_id).filter(
        TransactionLedger.supplier_id == supplier_id,
    ).all()

    pending_amount = sum(float(s.net_amount or 0) for s in settlements if s.status in ("pending", "eligible"))
    settled_amount = sum(float(s.net_amount or 0) for s in settlements if s.status == "settled")
    refund_reversal = sum(float(r.supplier_reversal or 0) for r in refunds)
    vat_on_orders = sum(float(e.vat_amount or 0) for e in entries)

    return {
        "total_gross_revenue": total_gross,
        "total_commission_deducted": total_commission,
        "total_net_earnings": total_earned,
        "total_vat_on_orders": vat_on_orders,
        "total_refund_reversals": refund_reversal,
        "pending_settlement": pending_amount,
        "total_settled": settled_amount,
        "total_orders": len(entries),
        "currency": settings.default_currency,
        "bank_instruction": build_supplier_payout_instruction(supplier_id, db),
    }


def get_logistics_financial_summary(partner_id: int, db: Session) -> dict:
    """Get financial summary for a specific logistics partner."""
    settlements = db.query(LogisticsSettlement).filter(
        LogisticsSettlement.partner_id == partner_id,
    ).all()

    total_fees = sum(float(s.total_delivery_fee or 0) for s in settlements)
    total_pickup_fees = sum(float(s.pickup_charge or 0) for s in settlements)
    total_dropoff_fees = sum(float(s.dropoff_charge or 0) for s in settlements)
    total_cod = sum(float(s.cod_collected or 0) for s in settlements if s.cod_collected)
    total_remitted = sum(float(s.cod_remitted or 0) for s in settlements if s.cod_remitted)
    refunds = db.query(RefundLedger).join(TransactionLedger, TransactionLedger.order_id == RefundLedger.order_id).filter(
        TransactionLedger.logistics_partner_id == partner_id,
    ).all()
    refund_reversal = sum(float(r.logistics_reversal or 0) for r in refunds)
    pending_remittance = sum(
        float((s.cod_collected or 0) - (s.cod_remitted or 0) - (s.cod_retained or 0))
        for s in settlements
        if s.cod_remittance_status == "pending"
    )

    return {
        "total_delivery_fees": total_fees,
        "total_pickup_fees": total_pickup_fees,
        "total_dropoff_fees": total_dropoff_fees,
        "total_cod_collected": total_cod,
        "total_cod_remitted": total_remitted,
        "total_refund_reversals": refund_reversal,
        "pending_cod_remittance": pending_remittance,
        "total_deliveries": len(settlements),
        "currency": settings.default_currency,
        "bank_instruction": build_logistics_cod_remittance_instruction(partner_id, db),
    }


def get_reconciliation_summary(db: Session) -> dict:
    """Return a compact admin-facing overview of reconciliation state."""
    unreconciled_q = db.query(BankTransaction).filter(BankTransaction.reconciled == False)  # noqa: E712
    unreconciled = unreconciled_q.all()
    unreconciled_inflows = [txn for txn in unreconciled if str(txn.transaction_type or "") == "inflow"]
    unreconciled_outflows = [txn for txn in unreconciled if str(txn.transaction_type or "") == "outflow"]

    supplier_processing = db.query(Payout).filter(Payout.status == "processing").all()
    logistics_processing = db.query(LogisticsPartnerPayout).filter(
        LogisticsPartnerPayout.status == "processing"
    ).all()
    pending_refunds = db.query(RefundLedger).filter(RefundLedger.status == "pending").all()
    cod_settlements = db.query(LogisticsSettlement).filter(
        LogisticsSettlement.cod_remittance_status.in_(["pending", "partial"])
    ).all()

    pending_cod_amount = Decimal("0")
    for settlement in cod_settlements:
        due = to_decimal(settlement.cod_collected or 0) - to_decimal(settlement.cod_retained or 0)
        remaining = due - to_decimal(settlement.cod_remitted or 0)
        if remaining > 0:
            pending_cod_amount += remaining

    return {
        "unreconciled_count": len(unreconciled),
        "unreconciled_inflow_count": len(unreconciled_inflows),
        "unreconciled_outflow_count": len(unreconciled_outflows),
        "unreconciled_inflow_amount": float(round_money(sum((to_decimal(txn.amount) for txn in unreconciled_inflows), Decimal("0")))),
        "unreconciled_outflow_amount": float(round_money(sum((to_decimal(txn.amount) for txn in unreconciled_outflows), Decimal("0")))),
        "flagged_count": db.query(func.count(BankTransaction.id)).filter(BankTransaction.flagged == True).scalar() or 0,  # noqa: E712
        "supplier_payouts_processing": len(supplier_processing),
        "supplier_payouts_processing_amount": float(round_money(sum((to_decimal(p.amount) for p in supplier_processing), Decimal("0")))),
        "logistics_payouts_processing": len(logistics_processing),
        "logistics_payouts_processing_amount": float(round_money(sum((to_decimal(p.amount) for p in logistics_processing), Decimal("0")))),
        "pending_cod_remittance_count": len(cod_settlements),
        "pending_cod_remittance_amount": float(round_money(pending_cod_amount)),
        "pending_refund_count": len(pending_refunds),
        "pending_refund_amount": float(round_money(sum((to_decimal(r.customer_refund_amount) for r in pending_refunds), Decimal("0")))),
        "currency": settings.default_currency,
    }


# ── Payout Processing ────────────────────────────────────────────────────────

def process_supplier_payout_batch(db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Find all eligible supplier settlements and create payout records."""
    now = _utcnow()
    eligible_query = db.query(SupplierSettlement).filter(
        SupplierSettlement.status == "eligible",
        SupplierSettlement.eligible_at <= now,
    )
    if settlement_ids:
        eligible_query = eligible_query.filter(SupplierSettlement.id.in_(settlement_ids))
    eligible = eligible_query.all()

    # Group by supplier
    supplier_totals: dict[int, Decimal] = {}
    supplier_settlements: dict[int, list[SupplierSettlement]] = {}
    for s in eligible:
        sid = s.supplier_id
        supplier_totals[sid] = supplier_totals.get(sid, Decimal(0)) + to_decimal(s.net_amount)
        supplier_settlements.setdefault(sid, []).append(s)

    results = []
    for supplier_id, total in supplier_totals.items():
        payout_country_code = None
        sample_settlement = supplier_settlements[supplier_id][0] if supplier_settlements.get(supplier_id) else None
        if sample_settlement is not None:
            sample_order = db.query(Order).filter(Order.id == sample_settlement.order_id).first()
            if sample_order is not None:
                payout_country_code = getattr(sample_order, "shipping_country", None) or getattr(sample_order, "country_code", None)

        payout = Payout(
            supplier_id=supplier_id,
            amount=float(round_money(total)),
            status="processing",
            method="bank",
            notes=f"Auto-payout for {len(supplier_settlements[supplier_id])} delivered orders",
        )
        db.add(payout)
        db.flush()
        payout.reference = build_transfer_reference(
            db,
            kind="supplier_payout",
            entity_id=supplier_id,
            record_id=int(payout.id),
        )

        for settlement in supplier_settlements[supplier_id]:
            settlement.status = "processing"
            settlement.payout_id = payout.id

        # Log bank transaction
        log_bank_transaction(
            source="bank_transfer",
            transaction_type="outflow",
            category="supplier_payout",
            amount=total,
            db=db,
            supplier_id=supplier_id,
            payout_id=payout.id,
            description=f"Supplier payout #{payout.id} for {len(supplier_settlements[supplier_id])} orders",
            country_code=payout_country_code,
        )

        # Post general-ledger leg for supplier payout (Supplier Payables -> Cash)
        try:
            from services.general_ledger_service import post_payout_journal

            post_payout_journal(db, payout, total)
        except Exception:
            logger.exception("Failed to post payout journal for payout %s", payout.id)

        results.append({
            "payout_id": payout.id,
            "supplier_id": supplier_id,
            "amount": float(round_money(total)),
            "order_count": len(supplier_settlements[supplier_id]),
            "reference": payout.reference,
        })

    db.flush()
    logger.info("Processed %d supplier payouts", len(results))
    return results


def process_logistics_payout_batch(db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Find all eligible logistics settlements and create payout records."""
    now = _utcnow()
    eligible_query = db.query(LogisticsSettlement).filter(
        LogisticsSettlement.status == "eligible",
        LogisticsSettlement.eligible_at <= now,
    )
    if settlement_ids:
        eligible_query = eligible_query.filter(LogisticsSettlement.id.in_(settlement_ids))
    eligible = eligible_query.all()

    # Group by partner
    partner_totals: dict[int, Decimal] = {}
    partner_settlements: dict[int, list[LogisticsSettlement]] = {}
    for s in eligible:
        pid = s.partner_id
        partner_totals[pid] = partner_totals.get(pid, Decimal(0)) + to_decimal(s.total_delivery_fee)
        partner_settlements.setdefault(pid, []).append(s)

    results = []
    for partner_id, total in partner_totals.items():
        payout = LogisticsPartnerPayout(
            partner_id=partner_id,
            amount=float(round_money(total)),
            status="processing",
            method="bank",
            notes=f"Auto-payout for {len(partner_settlements[partner_id])} deliveries",
        )
        db.add(payout)
        db.flush()
        payout.reference = build_transfer_reference(
            db,
            kind="logistics_payout",
            entity_id=partner_id,
            record_id=int(payout.id),
        )

        for settlement in partner_settlements[partner_id]:
            settlement.status = "processing"
            settlement.payout_id = payout.id

        log_bank_transaction(
            source="bank_transfer",
            transaction_type="outflow",
            category="logistics_payout",
            amount=total,
            db=db,
            logistics_id=partner_id,
            payout_id=payout.id,
            description=f"Logistics payout #{payout.id} for {len(partner_settlements[partner_id])} deliveries",
        )

        results.append({
            "payout_id": payout.id,
            "partner_id": partner_id,
            "amount": float(round_money(total)),
            "delivery_count": len(partner_settlements[partner_id]),
            "reference": payout.reference,
        })

    db.flush()
    logger.info("Processed %d logistics payouts", len(results))
    return results


def _refresh_order_ledger_settlement_status(order_id: int, db: Session) -> None:
    entries = db.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).all()
    if not entries:
        return

    for entry in entries:
        if str(entry.settlement_status or "") == "refunded":
            continue

        supplier_settlement = db.query(SupplierSettlement).filter(
            SupplierSettlement.order_id == order_id,
            SupplierSettlement.supplier_id == entry.supplier_id,
        ).first()
        logistics_settlement = None
        if entry.logistics_partner_id:
            logistics_settlement = db.query(LogisticsSettlement).filter(
                LogisticsSettlement.order_id == order_id,
                LogisticsSettlement.partner_id == entry.logistics_partner_id,
            ).first()

        supplier_done = bool(supplier_settlement and supplier_settlement.status == "settled")
        logistics_done = True if entry.logistics_partner_id is None else bool(
            logistics_settlement and logistics_settlement.status == "settled"
        )

        if supplier_done and logistics_done:
            entry.settlement_status = "fully_settled"
        elif supplier_done:
            entry.settlement_status = "supplier_settled"
        elif logistics_done:
            entry.settlement_status = "logistics_settled"
        else:
            entry.settlement_status = "pending"


def _mark_supplier_payout_completed(payout_id: int, txn: BankTransaction, db: Session) -> None:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout:
        payout.status = "completed"
        payout.processed_at = txn.reconciled_at or _utcnow()
        payout.reference = txn.transaction_ref

    settlements = db.query(SupplierSettlement).filter(SupplierSettlement.payout_id == payout_id).all()
    touched_order_ids: set[int] = set()
    for settlement in settlements:
        settlement.status = "settled"
        settlement.settled_at = txn.reconciled_at or _utcnow()
        settlement.bank_transaction_id = txn.id
        touched_order_ids.add(settlement.order_id)

    for order_id in touched_order_ids:
        _refresh_order_ledger_settlement_status(order_id, db)


def _mark_logistics_payout_completed(payout_id: int, txn: BankTransaction, db: Session) -> None:
    payout = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id == payout_id).first()
    if payout:
        payout.status = "completed"
        payout.processed_at = txn.reconciled_at or _utcnow()
        payout.reference = txn.transaction_ref

    settlements = db.query(LogisticsSettlement).filter(LogisticsSettlement.payout_id == payout_id).all()
    touched_order_ids: set[int] = set()
    for settlement in settlements:
        settlement.status = "settled"
        settlement.settled_at = txn.reconciled_at or _utcnow()
        settlement.bank_transaction_id = txn.id
        touched_order_ids.add(settlement.order_id)

    for order_id in touched_order_ids:
        _refresh_order_ledger_settlement_status(order_id, db)


def _mark_cod_remittance_reconciled(txn: BankTransaction, db: Session) -> None:
    if txn.linked_order_id is None:
        return
    q = db.query(LogisticsSettlement).filter(LogisticsSettlement.order_id == txn.linked_order_id)
    if txn.linked_logistics_id is not None:
        q = q.filter(LogisticsSettlement.partner_id == txn.linked_logistics_id)
    settlements = q.all()
    for settlement in settlements:
        due = round_money(to_decimal(settlement.cod_collected or 0) - to_decimal(settlement.cod_retained or 0))
        already_remitted = round_money(to_decimal(settlement.cod_remitted or 0))
        if txn.source != "cod_remittance":
            updated_remitted = round_money(already_remitted + to_decimal(txn.amount or 0))
            settlement.cod_remitted = updated_remitted
            settlement.cod_remittance_status = "complete" if updated_remitted >= due else "partial"
        settlement.bank_transaction_id = txn.id


def _mark_refund_reconciled(txn: BankTransaction, db: Session) -> None:
    q = db.query(RefundLedger)
    if txn.linked_order_id is not None:
        q = q.filter(RefundLedger.order_id == txn.linked_order_id)
    if txn.linked_refund_id is not None:
        q = q.filter(RefundLedger.return_request_id == txn.linked_refund_id)
    refund = q.order_by(RefundLedger.created_at.desc()).first()
    if refund:
        refund.status = "completed"
        refund.bank_transaction_id = txn.id
        refund.processed_at = txn.reconciled_at or _utcnow()
        refund.processed_by = txn.reconciled_by


def _apply_reconciliation_effects(txn: BankTransaction, db: Session) -> None:
    category = str(txn.category or "")
    if category == "supplier_payout" and txn.linked_payout_id:
        _mark_supplier_payout_completed(txn.linked_payout_id, txn, db)
    elif category == "logistics_payout" and txn.linked_payout_id:
        _mark_logistics_payout_completed(txn.linked_payout_id, txn, db)
    elif category == "cod_remittance":
        _mark_cod_remittance_reconciled(txn, db)
    elif category == "refund":
        _mark_refund_reconciled(txn, db)


def _infer_transaction_links(txn: BankTransaction, db: Session) -> bool:
    category = str(txn.category or "")

    if category == "supplier_payout" and txn.linked_payout_id is None:
        candidates = db.query(Payout).filter(Payout.status == "processing").all()
        matched = [
            payout for payout in candidates
            if round_money(to_decimal(payout.amount)) == round_money(to_decimal(txn.amount))
            and (txn.linked_supplier_id is None or payout.supplier_id == txn.linked_supplier_id)
        ]
        if len(matched) == 1:
            txn.linked_payout_id = matched[0].id
            txn.linked_supplier_id = txn.linked_supplier_id or matched[0].supplier_id
            return True

    if category == "logistics_payout" and txn.linked_payout_id is None:
        candidates = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.status == "processing").all()
        matched = [
            payout for payout in candidates
            if round_money(to_decimal(payout.amount)) == round_money(to_decimal(txn.amount))
            and (txn.linked_logistics_id is None or payout.partner_id == txn.linked_logistics_id)
        ]
        if len(matched) == 1:
            txn.linked_payout_id = matched[0].id
            txn.linked_logistics_id = txn.linked_logistics_id or matched[0].partner_id
            return True

    if category == "card_payment" and txn.linked_order_id is None and txn.transaction_ref:
        order = db.query(Order).filter(Order.payment_intent_id == txn.transaction_ref).first()
        if order:
            txn.linked_order_id = order.id
            return True

    if category == "refund":
        refund_query = db.query(RefundLedger).filter(RefundLedger.status.in_(["pending", "processing"]))
        if txn.linked_refund_id is not None:
            refund_query = refund_query.filter(RefundLedger.return_request_id == txn.linked_refund_id)
        if txn.linked_order_id is not None:
            refund_query = refund_query.filter(RefundLedger.order_id == txn.linked_order_id)
        elif txn.linked_refund_id is None:
            refund_query = refund_query.filter(RefundLedger.customer_refund_amount == round_money(to_decimal(txn.amount)))

        refunds = refund_query.order_by(RefundLedger.created_at.asc()).all()
        if len(refunds) == 1:
            refund = refunds[0]
            txn.linked_order_id = txn.linked_order_id or refund.order_id
            txn.linked_refund_id = txn.linked_refund_id or refund.return_request_id
            return True

    if category == "cod_remittance":
        candidates = db.query(LogisticsSettlement).filter(
            LogisticsSettlement.cod_collected.isnot(None),
            LogisticsSettlement.cod_remittance_status.in_(["pending", "partial"]),
        )
        if txn.linked_order_id is not None:
            candidates = candidates.filter(LogisticsSettlement.order_id == txn.linked_order_id)
        if txn.linked_logistics_id is not None:
            candidates = candidates.filter(LogisticsSettlement.partner_id == txn.linked_logistics_id)

        matches: list[LogisticsSettlement] = []
        txn_amount = round_money(to_decimal(txn.amount or 0))
        for settlement in candidates.all():
            remaining_due = round_money(
                to_decimal(settlement.cod_collected or 0)
                - to_decimal(settlement.cod_retained or 0)
                - to_decimal(settlement.cod_remitted or 0)
            )
            if remaining_due <= 0:
                continue
            if remaining_due == txn_amount or (
                (txn.linked_order_id is not None or txn.linked_logistics_id is not None)
                and txn_amount <= remaining_due
            ):
                matches.append(settlement)

        if len(matches) == 1:
            settlement = matches[0]
            txn.linked_order_id = txn.linked_order_id or settlement.order_id
            txn.linked_logistics_id = txn.linked_logistics_id or settlement.partner_id
            return True

    return bool(txn.linked_order_id or txn.linked_payout_id or txn.linked_supplier_id or txn.linked_logistics_id)


def auto_reconcile_bank_transactions(
    admin_id: Optional[int],
    db: Session,
    *,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """Attempt to auto-match and reconcile unreconciled bank transactions."""
    query = db.query(BankTransaction).filter(
        BankTransaction.reconciled == False,  # noqa: E712
        BankTransaction.flagged == False,  # noqa: E712
    )
    if source:
        query = query.filter(BankTransaction.source == source)
    if category:
        query = query.filter(BankTransaction.category == category)

    transactions = query.order_by(BankTransaction.transaction_date.asc(), BankTransaction.id.asc()).limit(limit).all()
    reconciled_items: list[dict] = []
    unmatched_items: list[dict] = []

    for txn in transactions:
        matched = _infer_transaction_links(txn, db)
        if matched:
            reconcile_bank_transaction(txn.id, admin_id, db)
            reconciled_items.append({
                "id": txn.id,
                "transaction_ref": txn.transaction_ref,
                "category": txn.category,
                "amount": float(round_money(to_decimal(txn.amount))),
            })
        else:
            unmatched_items.append({
                "id": txn.id,
                "transaction_ref": txn.transaction_ref,
                "category": txn.category,
                "amount": float(round_money(to_decimal(txn.amount))),
            })

    return {
        "processed": len(transactions),
        "reconciled": len(reconciled_items),
        "unmatched": len(unmatched_items),
        "reconciled_items": reconciled_items,
        "unmatched_items": unmatched_items,
    }


# ── Reconciliation ────────────────────────────────────────────────────────────

def reconcile_bank_transaction(txn_id: int, admin_id: int, db: Session) -> BankTransaction:
    """Mark a bank transaction as reconciled by an admin."""
    txn = db.query(BankTransaction).filter(BankTransaction.id == txn_id).first()
    if not txn:
        raise ValueError(f"Bank transaction {txn_id} not found")
    if txn.reconciled:
        return txn
    txn.reconciled = True
    txn.reconciled_at = _utcnow()
    txn.reconciled_by = admin_id
    txn.flagged = False
    _apply_reconciliation_effects(txn, db)
    db.flush()
    return txn


def flag_bank_transaction(txn_id: int, reason: str, db: Session) -> BankTransaction:
    """Flag a bank transaction for manual review."""
    txn = db.query(BankTransaction).filter(BankTransaction.id == txn_id).first()
    if not txn:
        raise ValueError(f"Bank transaction {txn_id} not found")
    txn.flagged = True
    txn.flag_reason = reason
    db.flush()
    return txn


def resolve_bank_transaction_exception(
    txn_id: int,
    db: Session,
    *,
    admin_id: Optional[int],
    order_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    logistics_id: Optional[int] = None,
    payout_id: Optional[int] = None,
    refund_id: Optional[int] = None,
    resolution_note: Optional[str] = None,
    mark_reconciled: bool = True,
    clear_flag: bool = True,
) -> BankTransaction:
    txn = db.query(BankTransaction).filter(BankTransaction.id == txn_id).first()
    if not txn:
        raise ValueError(f"Bank transaction {txn_id} not found")

    if order_id is not None:
        txn.linked_order_id = order_id
    if supplier_id is not None:
        txn.linked_supplier_id = supplier_id
    if logistics_id is not None:
        txn.linked_logistics_id = logistics_id
    if payout_id is not None:
        txn.linked_payout_id = payout_id
    if refund_id is not None:
        txn.linked_refund_id = refund_id

    if resolution_note:
        note_line = f"Resolution: {resolution_note.strip()}"
        txn.description = f"{txn.description}\n{note_line}" if txn.description else note_line

    if clear_flag:
        txn.flagged = False
        txn.flag_reason = None

    db.flush()

    if mark_reconciled:
        return reconcile_bank_transaction(txn_id, admin_id, db)
    return txn


def import_bank_transactions(
    entries: list[dict],
    db: Session,
    *,
    admin_id: Optional[int] = None,
    auto_reconcile: bool = False,
) -> dict:
    created_items: list[dict] = []
    duplicate_items: list[dict] = []
    reconciled_items: list[dict] = []
    unmatched_items: list[dict] = []

    for entry in entries:
        transaction_ref = entry["transaction_ref"]
        existing = db.query(BankTransaction).filter(BankTransaction.transaction_ref == transaction_ref).first()
        if existing:
            duplicate_items.append({
                "id": existing.id,
                "transaction_ref": existing.transaction_ref,
            })
            continue

        txn = log_bank_transaction(
            source=entry["source"],
            transaction_type=entry["transaction_type"],
            category=entry["category"],
            amount=to_decimal(entry["amount"]),
            db=db,
            currency=entry.get("currency", settings.default_currency),
            order_id=entry.get("linked_order_id"),
            supplier_id=entry.get("linked_supplier_id"),
            logistics_id=entry.get("linked_logistics_id"),
            payout_id=entry.get("linked_payout_id"),
            refund_id=entry.get("linked_refund_id"),
            description=entry.get("description"),
            transaction_ref=transaction_ref,
            transaction_date=entry.get("transaction_date"),
        )
        if entry.get("flag_reason"):
            txn.flagged = True
            txn.flag_reason = entry["flag_reason"]

        created_items.append({
            "id": txn.id,
            "transaction_ref": txn.transaction_ref,
            "category": txn.category,
            "amount": float(round_money(to_decimal(txn.amount))),
        })

        if auto_reconcile and not txn.flagged:
            matched = _infer_transaction_links(txn, db)
            if matched:
                reconcile_bank_transaction(txn.id, admin_id, db)
                reconciled_items.append({
                    "id": txn.id,
                    "transaction_ref": txn.transaction_ref,
                    "category": txn.category,
                    "amount": float(round_money(to_decimal(txn.amount))),
                })
            else:
                unmatched_items.append({
                    "id": txn.id,
                    "transaction_ref": txn.transaction_ref,
                    "category": txn.category,
                    "amount": float(round_money(to_decimal(txn.amount))),
                })

    return {
        "created": len(created_items),
        "duplicates": len(duplicate_items),
        "reconciled": len(reconciled_items),
        "unmatched": len(unmatched_items),
        "created_items": created_items,
        "duplicate_items": duplicate_items,
        "reconciled_items": reconciled_items,
        "unmatched_items": unmatched_items,
    }


def run_scheduled_reconciliation_cycle(db: Session) -> dict:
    """Execute the periodic finance reconciliation pass used by the background scheduler."""
    return auto_reconcile_bank_transactions(
        None,
        db,
        limit=settings.finance_auto_reconcile_batch_limit,
    )


def _run_scheduled_dispatch_batch(
    export_type: str,
    db: Session,
    *,
    provider: str,
    dry_run: bool,
) -> dict:
    providers = {
        str(item.get("key") or "").strip().lower(): item
        for item in list_transfer_export_providers()
    }
    provider_meta = providers.get(provider)
    if provider_meta is None:
        return {
            "status": "skipped_unknown_provider",
            "provider": provider,
            "submitted": False,
        }
    if not bool(provider_meta.get("supports_direct_execution")):
        return {
            "status": "skipped_provider_not_dispatchable",
            "provider": provider,
            "provider_name": provider_meta.get("name"),
            "submitted": False,
        }
    if not dry_run and not bool(provider_meta.get("configured")):
        return {
            "status": "skipped_provider_not_configured",
            "provider": provider,
            "provider_name": provider_meta.get("name"),
            "submitted": False,
        }

    try:
        return execute_transfer_batch(
            export_type,
            db=db,
            provider=provider,
            dry_run=dry_run,
        )
    except HTTPException as exc:
        logger.warning("Scheduled finance dispatch failed for %s via %s: %s", export_type, provider, exc.detail)
        return {
            "status": "dispatch_error",
            "provider": provider,
            "provider_name": provider_meta.get("name"),
            "submitted": False,
            "detail": str(exc.detail),
        }
    except Exception as exc:
        logger.exception("Scheduled finance dispatch failed for %s via %s", export_type, provider)
        return {
            "status": "dispatch_error",
            "provider": provider,
            "provider_name": provider_meta.get("name"),
            "submitted": False,
            "detail": str(exc),
        }


def run_scheduled_finance_cycle(db: Session) -> dict:
    """Execute the periodic finance cycle used by the background scheduler."""
    supplier_payouts: list[dict] = []
    logistics_payouts: list[dict] = []
    badge_recalculation: dict[str, Any] = {
        "suppliers_processed": 0,
        "badges_changed": 0,
        "billings_created": 0,
        "recurring_billings_created": 0,
    }
    analytics_refresh: dict[str, Any] = {"refreshed": 0, "keys": []}
    retention: dict[str, Any] = {"targets": []}

    from controllers.supplier_controller import run_badge_recalculation_cycle
    from controllers.admin_controller import refresh_admin_analytics_snapshots
    from services.retention_service import run_operational_retention_cycle

    badge_recalculation = run_badge_recalculation_cycle(db)
    analytics_refresh = refresh_admin_analytics_snapshots(db)

    if settings.finance_scheduler_process_payouts:
        supplier_payouts = process_supplier_payout_batch(db)
        logistics_payouts = process_logistics_payout_batch(db)

    provider = str(settings.finance_scheduler_dispatch_provider or "").strip().lower() or get_default_transfer_provider()
    if settings.finance_scheduler_dispatch_payouts:
        supplier_dispatch = _run_scheduled_dispatch_batch(
            "supplier-payout-transfers",
            db,
            provider=provider,
            dry_run=settings.finance_scheduler_dispatch_dry_run,
        )
        logistics_dispatch = _run_scheduled_dispatch_batch(
            "logistics-payout-transfers",
            db,
            provider=provider,
            dry_run=settings.finance_scheduler_dispatch_dry_run,
        )
    else:
        supplier_dispatch = {
            "status": "disabled",
            "provider": provider,
            "submitted": False,
        }
        logistics_dispatch = {
            "status": "disabled",
            "provider": provider,
            "submitted": False,
        }

    reconciliation = auto_reconcile_bank_transactions(
        None,
        db,
        limit=settings.finance_auto_reconcile_batch_limit,
    )
    reconciliation_run = _record_payment_reconciliation_run(db, reconciliation)
    retention = run_operational_retention_cycle(db)

    return {
        "supplier_payouts_processed": len(supplier_payouts),
        "logistics_payouts_processed": len(logistics_payouts),
        "supplier_payouts": supplier_payouts,
        "logistics_payouts": logistics_payouts,
        "badge_recalculation": badge_recalculation,
        "analytics_refresh": analytics_refresh,
        "dispatch_provider": provider,
        "dispatch_dry_run": settings.finance_scheduler_dispatch_dry_run,
        "supplier_dispatch": supplier_dispatch,
        "logistics_dispatch": logistics_dispatch,
        "processed": reconciliation.get("processed", 0),
        "reconciled": reconciliation.get("reconciled", 0),
        "unmatched": reconciliation.get("unmatched", 0),
        "reconciliation": reconciliation,
        "reconciliation_run": reconciliation_run,
        "retention": retention,
    }


def record_cod_remittance(
    settlement_id: int,
    amount: float,
    admin_id: int,
    db: Session,
    *,
    transaction_ref: Optional[str] = None,
    description: Optional[str] = None,
) -> LogisticsSettlement:
    """Record partial or full COD remittance from logistics partner."""
    settlement = db.query(LogisticsSettlement).filter(
        LogisticsSettlement.id == settlement_id
    ).first()
    if not settlement:
        raise ValueError(f"Logistics settlement {settlement_id} not found")

    remitted = to_decimal(settlement.cod_remitted or 0) + to_decimal(amount)
    due = to_decimal(settlement.cod_collected or 0) - to_decimal(settlement.cod_retained or 0)

    settlement.cod_remitted = round_money(remitted)
    if remitted >= due:
        settlement.cod_remittance_status = "complete"
    else:
        settlement.cod_remittance_status = "partial"

    # Log transaction
    txn = log_bank_transaction(
        source="cod_remittance",
        transaction_type="inflow",
        category="cod_remittance",
        amount=to_decimal(amount),
        db=db,
        order_id=settlement.order_id,
        logistics_id=settlement.partner_id,
        description=description or f"COD remittance from logistics partner for order #{settlement.order_id}",
        transaction_ref=transaction_ref,
        country_code=settlement.country_code,
    )
    settlement.bank_transaction_id = txn.id

    # Post general-ledger leg for COD remittance (COD Receivable -> Cash)
    try:
        from services.general_ledger_service import post_logistics_cod_remittance_journal

        post_logistics_cod_remittance_journal(db, settlement.id, to_decimal(amount))
    except Exception:
        logger.exception("Failed to post COD remittance journal for settlement %s", settlement.id)

    db.flush()
    return settlement


def list_cod_remittance_receipts(
    db: Session,
    *,
    partner_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[LogisticsCODRemittanceReceipt]:
    q = db.query(LogisticsCODRemittanceReceipt)
    if partner_id is not None:
        q = q.filter(LogisticsCODRemittanceReceipt.partner_id == partner_id)
    if settlement_id is not None:
        q = q.filter(LogisticsCODRemittanceReceipt.settlement_id == settlement_id)
    if status:
        q = q.filter(LogisticsCODRemittanceReceipt.status == status)
    return q.order_by(LogisticsCODRemittanceReceipt.created_at.desc(), LogisticsCODRemittanceReceipt.id.desc()).offset(skip).limit(limit).all()


def create_cod_remittance_receipt(
    settlement_id: int,
    partner_id: int,
    amount: Decimal,
    receipt_file_url: str,
    db: Session,
    *,
    bank_reference: Optional[str] = None,
    notes: Optional[str] = None,
) -> LogisticsCODRemittanceReceipt:
    settlement = db.query(LogisticsSettlement).filter(LogisticsSettlement.id == settlement_id).first()
    if settlement is None:
        raise ValueError(f"Logistics settlement {settlement_id} not found")
    if settlement.partner_id != partner_id:
        raise ValueError("Settlement does not belong to this logistics partner")

    due = round_money(to_decimal(settlement.cod_collected or 0) - to_decimal(settlement.cod_retained or 0))
    already_remitted = round_money(to_decimal(settlement.cod_remitted or 0))
    pending_pending = round_money(sum(
        to_decimal(row.amount or 0)
        for row in db.query(LogisticsCODRemittanceReceipt)
        .filter(
            LogisticsCODRemittanceReceipt.settlement_id == settlement_id,
            LogisticsCODRemittanceReceipt.status == "pending",
        )
        .all()
    ))
    remaining = round_money(due - already_remitted - pending_pending)

    if due <= 0:
        raise ValueError("This settlement has no COD remittance due")
    if amount <= 0:
        raise ValueError("Receipt amount must be positive")
    if remaining <= 0:
        raise ValueError("COD remittance is already fully covered for this settlement")
    if amount > remaining:
        raise ValueError(f"Receipt amount exceeds remaining COD due ({float(remaining):.2f})")

    receipt = LogisticsCODRemittanceReceipt(
        settlement_id=settlement_id,
        partner_id=partner_id,
        amount=round_money(amount),
        currency=getattr(settlement, "currency", None) or settings.default_currency,
        bank_reference=(bank_reference or "").strip() or None,
        receipt_file_url=receipt_file_url,
        notes=(notes or "").strip() or None,
        status="pending",
    )
    db.add(receipt)
    db.flush()
    return receipt


def verify_cod_remittance_receipt(
    receipt_id: int,
    admin_id: int,
    db: Session,
    *,
    review_note: Optional[str] = None,
) -> LogisticsCODRemittanceReceipt:
    receipt = db.query(LogisticsCODRemittanceReceipt).filter(LogisticsCODRemittanceReceipt.id == receipt_id).first()
    if receipt is None:
        raise ValueError(f"COD remittance receipt {receipt_id} not found")
    if receipt.status != "pending":
        raise ValueError("Only pending COD remittance receipts can be verified")

    transaction_ref = receipt.bank_reference or f"COD-RECEIPT-{receipt.id}"
    settlement = record_cod_remittance(
        receipt.settlement_id,
        float(receipt.amount),
        admin_id,
        db,
        transaction_ref=transaction_ref,
        description=f"Verified COD remittance receipt #{receipt.id} for order #{receipt.settlement.order_id if receipt.settlement else 'unknown'}",
    )
    txn = db.query(BankTransaction).filter(BankTransaction.transaction_ref == transaction_ref).first()

    receipt.status = "verified"
    receipt.review_note = (review_note or "").strip() or "Verified by finance"
    receipt.reviewed_by = admin_id
    receipt.reviewed_at = _utcnow()
    receipt.bank_transaction_id = getattr(txn, "id", None)
    if settlement.bank_transaction_id is None and txn is not None:
        settlement.bank_transaction_id = txn.id
    db.flush()
    return receipt


def reject_cod_remittance_receipt(
    receipt_id: int,
    admin_id: int,
    db: Session,
    *,
    review_note: str,
) -> LogisticsCODRemittanceReceipt:
    receipt = db.query(LogisticsCODRemittanceReceipt).filter(LogisticsCODRemittanceReceipt.id == receipt_id).first()
    if receipt is None:
        raise ValueError(f"COD remittance receipt {receipt_id} not found")
    if receipt.status != "pending":
        raise ValueError("Only pending COD remittance receipts can be rejected")

    note = (review_note or "").strip()
    if not note:
        raise ValueError("Rejection reason is required")

    receipt.status = "rejected"
    receipt.review_note = note
    receipt.reviewed_by = admin_id
    receipt.reviewed_at = _utcnow()
    db.flush()
    return receipt


def serialize_cod_remittance_receipt(receipt: LogisticsCODRemittanceReceipt, db: Session) -> dict[str, object]:
    settlement = receipt.settlement or db.query(LogisticsSettlement).filter(LogisticsSettlement.id == receipt.settlement_id).first()
    partner = receipt.partner or db.query(LogisticsPartner).filter(LogisticsPartner.id == receipt.partner_id).first()
    due = round_money(to_decimal(getattr(settlement, "cod_collected", 0) or 0) - to_decimal(getattr(settlement, "cod_retained", 0) or 0))
    remitted_after = round_money(to_decimal(getattr(settlement, "cod_remitted", 0) or 0))
    remitted_before = remitted_after if receipt.status != "verified" else round_money(remitted_after - to_decimal(receipt.amount or 0))
    remaining = round_money(max(Decimal("0"), due - remitted_before - to_decimal(receipt.amount or 0 if receipt.status == "verified" else 0)))
    return {
        "id": receipt.id,
        "settlement_id": receipt.settlement_id,
        "partner_id": receipt.partner_id,
        "order_id": getattr(settlement, "order_id", None),
        "amount": receipt.amount,
        "currency": receipt.currency,
        "bank_reference": receipt.bank_reference,
        "receipt_file_url": receipt.receipt_file_url,
        "notes": receipt.notes,
        "status": receipt.status,
        "review_note": receipt.review_note,
        "bank_transaction_id": receipt.bank_transaction_id,
        "reviewed_at": receipt.reviewed_at,
        "reviewed_by": receipt.reviewed_by,
        "created_at": receipt.created_at,
        "partner_name": getattr(partner, "name", None),
        "partner_code": getattr(partner, "code", None),
        "due_amount": due,
        "remitted_before_receipt": remitted_before,
        "remaining_amount": remaining,
        "settlement_status": getattr(settlement, "status", None),
        "cod_remittance_status": getattr(settlement, "cod_remittance_status", None),
    }

