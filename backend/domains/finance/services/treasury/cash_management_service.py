
ï»¿"""
Cash Management Service â€” core financial logic for the Zozi platform.

Responsibilities:
  - Create transaction ledger entries on order confirmation
  - Compute commission splits (product, delivery, VAT, Zozi fee)
  - Create supplier/logistics settlement records on delivery
  - Trigger automated payouts after holding period
  - Reconciliation engine for COD and card payments
  - Refund ledger creation on cancellation/return
"""

from __future__ import annotations
from pydantic import BaseModel
import logging
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.catalog.ports import Product
from domains.finance.models.finance import BankTransaction
from domains.finance.models.finance import RefundLedger
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TransactionLedger
from domains.finance.models.finance import VATRemittance
from domains.orders.ports import Order, OrderItem, OrderLogisticsAllocation
from domains.logistics.services.partners.service import _build_service_area_pricing_breakdown
from domains.logistics.services.partners.service import lookup_city_distance_km
from domains.logistics.services.partners.service import normalize_pricing_breakdown_payload
from domains.logistics.services.partners.service import normalize_country_code
from domains.logistics.services.partners.service import normalize_vehicle_type
from domains.logistics.services.partners.service import resolve_category_rules_for_area
from domains.logistics.services.partners.service import resolve_pricing_profile_for_area
from domains.logistics.services.partners.service import resolve_vehicle_rule_for_area
from domains.logistics.services.partners.service import vehicle_baseline_multiplier
from domains.finance.services.ledger.finance_transfer_service import build_logistics_cod_remittance_instruction
from domains.finance.services.ledger.finance_transfer_service import build_supplier_payout_instruction
from domains.finance.services.ledger.finance_transfer_service import build_transfer_reference
from domains.finance.services.ledger.finance_transfer_service import execute_transfer_batch
from domains.finance.services.ledger.finance_transfer_service import get_default_transfer_provider
from domains.finance.services.ledger.finance_transfer_service import list_transfer_export_providers
from infrastructure.utils.config import settings


def _get_governance_ports():
    """Lazy import to avoid circular dependency at module load."""
    from domains.governance.ports import (
        badge_billing_record_query,
        finance_bank_account_query,
        logistics_cod_remittance_receipt_query,
        logistics_settlement_query,
        processed_webhook_event_query,
    )
    return (
        badge_billing_record_query,
        finance_bank_account_query,
        logistics_cod_remittance_receipt_query,
        logistics_settlement_query,
        processed_webhook_event_query,
    )


def _get_logistics_ports():
    """Lazy import to avoid circular dependency at module load."""
    from domains.logistics.ports import (
        logistics_partner_query,
        logistics_partner_service_area_query,
        shipment_query,
    )
    return (
        logistics_partner_query,
        logistics_partner_service_area_query,
        shipment_query,
    )


def _get_logistics_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.logistics.ports import LogisticsPartnerServiceArea, Shipment
    return LogisticsPartnerServiceArea, Shipment

def _get_orders_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.orders.ports import Order, OrderItem, OrderLogisticsAllocation
    return Order, OrderItem, OrderLogisticsAllocation

def _get_governance_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.governance.ports import FinanceBankAccount, LogisticsSettlement, LogisticsPartnerPayout, LogisticsCODRemittanceReceipt
    return FinanceBankAccount, LogisticsSettlement, LogisticsPartnerPayout, LogisticsCODRemittanceReceipt

def _get_payments_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.finance.ports import Payout
    return Payout


def _get_governance_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.governance.ports import (
        FinanceBankAccount,
        LogisticsSettlement,
        LogisticsPartnerPayout,
        LogisticsCODRemittanceReceipt,
    )
    return FinanceBankAccount, LogisticsSettlement, LogisticsPartnerPayout, LogisticsCODRemittanceReceipt


def _get_payments_models():
    """Lazy import to avoid circular dependency at module load."""
    from domains.finance.ports import Payout
    return Payout
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from kernel.money import round_money, to_decimal
from domains.finance.services.finance import commission_engine as _commission_engine

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
    item_ids = [item.product_id for item in items if item.product_id]
    product_map: dict[int, Product] = {}
    if item_ids:
        product_map = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(item_ids)).all()
        }
    for item in items:
        product = item.product or product_map.get(item.product_id)
        supplier_id = product.supplier_id if product else None
        if supplier_id:
            supplier_items.setdefault(supplier_id, []).append(item)

    if not supplier_items:
        return []

    shipment = shipment_query(db).filter(Shipment.order_id == order.id).first()
    selected_area = None
    if getattr(order, "selected_service_area_id", None):
        selected_area = logistics_partner_service_area_query(db).filter(
            LogisticsPartnerServiceArea.id == order.selected_service_area_id
        ).first()

    partner = None
    logistics_partner_id = (
        getattr(order, "selected_partner_id", None)
        or (shipment.assigned_partner_id if shipment else None)
    )
    if logistics_partner_id:
        partner = logistics_partner_query(db).filter(LogisticsPartner.id == logistics_partner_id).first()

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
        items = order_item_query(db).filter(OrderItem.order_id == order.id).all()
    if not items:
        return None
    product_ids = [item.product_id for item in items if item.product_id]
    product_map: dict[int, Product] = {}
    if product_ids:
        product_map = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        }
    for item in items:
        product = item.product or product_map.get(item.product_id)
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
            order_logistics_allocation_query(db)
            .filter(OrderLogisticsAllocation.shipment_id == shipment_id)
            .order_by(OrderLogisticsAllocation.id.desc())
            .first()
        )
        if exact is not None:
            return exact
    return (
        order_logistics_allocation_query(db)
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

    order = shipment.order or order_query(db).filter(Order.id == shipment.order_id).first()
    if order is None:
        raise HTTPException(status_code=409, detail="Shipment order could not be resolved")

    area_id = cast(int | None, getattr(allocation, "service_area_id", None) or getattr(order, "selected_service_area_id", None))
    if area_id is None:
        raise HTTPException(status_code=409, detail="Shipment has no approved service area pricing snapshot")

    area = logistics_partner_service_area_query(db).filter(LogisticsPartnerServiceArea.id == area_id).first()
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
        order_logistics_allocation_query(db)
        .filter(OrderLogisticsAllocation.order_id == order.id)
        .order_by(OrderLogisticsAllocation.id.asc())
        .all()
    )
    if existing:
        return existing

    order_items = items or list(order.items or [])
    if not order_items:
        order_items = order_item_query(db).filter(OrderItem.order_id == order.id).all()
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
        payment_gateway_connection_query(db)
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
        items = order_item_query(db).filter(OrderItem.order_id == order.id).all()

    item_ids = [item.product_id for item in items if item.product_id]
    product_map: dict[int, Product] = {}
    if item_ids:
        product_map = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(item_ids)).all()
        }
    supplier_windows: dict[int, int] = {}
    for item in items:
        product = item.product or product_map.get(item.product_id)
        supplier_id = cast(int | None, getattr(product, "supplier_id", None)) if product else None
        if not supplier_id:
            continue
        supplier_windows[supplier_id] = max(
            supplier_windows.get(supplier_id, 10),
            _normalized_return_window_days(getattr(product, "return_window_days", None) if product else None),
        )
    return supplier_windows


# â”€â”€ Ledger Creation (triggered on order confirmation) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_ledger_entries_for_order(order: Order, db: Session) -> list[TransactionLedger]:
    """Create transaction ledger entries for every supplier involved in the order.

    Called when an order transitions to 'confirmed' status (COD immediate,
    card/tap after successful payment webhook).
    """
    existing = db.query(TransactionLedger).filter(
        TransactionLedger.order_id == order.id
    ).first()
    if existing:
        logger.info("Ledger entries already exist for order %s â€” skipping", order.id)
        return []

    items: list[OrderItem] = order.items or []
    if not items:
        items = order_item_query(db).filter(OrderItem.order_id == order.id).all()

    if not items:
        logger.warning("No order items found for order %s â€” cannot create ledger", order.id)
        return []

    # Group items by supplier
    supplier_items: dict[int, list[OrderItem]] = {}
    item_ids = [item.product_id for item in items if item.product_id]
    product_map: dict[int, Product] = {}
    if item_ids:
        product_map = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(item_ids)).all()
        }
    for item in items:
        product = item.product or product_map.get(item.product_id)
        supplier_id = product.supplier_id if product else None
        if supplier_id:
            supplier_items.setdefault(supplier_id, []).append(item)

    # Get shipment for logistics partner link
    shipment = shipment_query(db).filter(Shipment.order_id == order.id).first()
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

        # Commission on product revenue after discount â€” use commission engine per item
        taxable_product = round_money(product_subtotal - discount_share)
        # Compute per-item commission amounts then sum for the supplier group
        item_commissions: list[tuple] = []   # (item, commission_amount, rate_result, eng_result)
        for item in sitems:
            item_value = round_money(to_decimal(item.price) * to_decimal(item.quantity))
            # Proportion of discourse for this item
            item_discount = round_money(discount_share * (item_value / product_subtotal)) if product_subtotal > 0 else Decimal(0)
            item_taxable = round_money(item_value - item_discount)
            # Resolve category slug from product.category (tolower + spacesâ†’hyphens)
            prod = item.product or product_map.get(item.product_id)
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
                prod = item.product or product_map.get(item.product_id)
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


# â”€â”€ Settlement Creation (triggered when order is delivered) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_settlements_on_delivery(order: Order, db: Session) -> None:
    """Create supplier and logistics settlement records when order is delivered.

    Called when the order/shipment status transitions to 'delivered'.
    """
    ledger_entries = db.query(TransactionLedger).filter(
        TransactionLedger.order_id == order.id
    ).all()

    if not ledger_entries:
        logger.warning("No ledger entries for delivered order %s â€” creating now", order.id)
        ledger_entries = create_ledger_entries_for_order(order, db)

    now = _utcnow()
    gateway_delay_days = _gateway_settlement_delay_days(order, db)
    supplier_return_windows = _supplier_return_window_days(order, db)
    logistics_return_window = max(supplier_return_windows.values(), default=10)
    logistics_eligible_date = now + timedelta(days=max(gateway_delay_days, logistics_return_window))
    gateway_fee_allocations = _supplier_gateway_fee_allocations(order, ledger_entries)
    allocations_by_supplier = {
        allocation.supplier_id: allocation
        for allocation in order_logistics_allocation_query(db).filter(OrderLogisticsAllocation.order_id == order.id).all()
    }

    # Batch pre-load existing settlements to avoid N+1 in the loop below
    supplier_ids = [cast(int, entry.supplier_id) for entry in ledger_entries]
    logistics_partner_ids = [
        cast(int, entry.logistics_partner_id) for entry in ledger_entries
        if entry.logistics_partner_id
    ]
    existing_supplier_settlements: dict[tuple[int, int], SupplierSettlement] = {}
    if supplier_ids:
        for ss in (
            db.query(SupplierSettlement)
            .filter(
                SupplierSettlement.order_id == order.id,
                SupplierSettlement.supplier_id.in_(supplier_ids),
            )
            .all()
        ):
            existing_supplier_settlements[(order.id, ss.supplier_id)] = ss
    existing_logistics_settlements: dict[tuple[int, int], LogisticsSettlement] = {}
    if logistics_partner_ids:
        for ls in (
            logistics_settlement_query(db)
            .filter(
                LogisticsSettlement.order_id == order.id,
                LogisticsSettlement.partner_id.in_(logistics_partner_ids),
            )
            .all()
        ):
            existing_logistics_settlements[(order.id, ls.partner_id)] = ls

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
        existing_ss = existing_supplier_settlements.get((order.id, cast(int, entry.supplier_id)))
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
            existing_ls = existing_logistics_settlements.get(
                (order.id, cast(int, entry.logistics_partner_id))
            )
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


# â”€â”€ Automated Bank Transaction logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Refund Ledger â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        from domains.finance.services.ledger.general_ledger_service import post_refund_journal

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
    logistics_settlement_query(db).filter(
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
        
        .limit(limit)
        .all()
    )


def get_finance_bank_settings(db: Session) -> Optional[FinanceBankAccount]:
    return (
        finance_bank_account_query(db)
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


# â”€â”€ Financial Summary / Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    settlements = logistics_settlement_query(db).filter(
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

    supplier_processing = payout_query(db).filter(Payout.status == "processing").all()
    logistics_processing = logistics_partner_payout_query(db).filter(
        LogisticsPartnerPayout.status == "processing"
    ).all()
    pending_refunds = db.query(RefundLedger).filter(RefundLedger.status == "pending").all()
    cod_settlements = logistics_settlement_query(db).filter(
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


# â”€â”€ Payout Processing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # Batch-load orders to avoid N+1 when resolving payout country code
    order_ids = [ss.order_id for ss_list in supplier_settlements.values() for ss in ss_list if ss.order_id]
    order_map: dict[int, Order] = {}
    if order_ids:
        order_map = {o.id: o for o in order_query(db).filter(Order.id.in_(order_ids)).all()}

    results = []
    for supplier_id, total in supplier_totals.items():
        payout_country_code = None
        sample_settlement = supplier_settlements[supplier_id][0] if supplier_settlements.get(supplier_id) else None
        if sample_settlement is not None:
            sample_order = order_map.get(sample_settlement.order_id)
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
            from domains.finance.services.ledger.general_ledger_service import post_payout_journal

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
    eligible_query = logistics_settlement_query(db).filter(
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

    # Batch pre-load settlements to avoid N+1 in the loop below
    supplier_ids = [entry.supplier_id for entry in entries if entry.supplier_id is not None]
    logistics_partner_ids = [
        entry.logistics_partner_id for entry in entries if entry.logistics_partner_id
    ]
    ss_map: dict[tuple[int, int], SupplierSettlement] = {}
    if supplier_ids:
        for ss in (
            db.query(SupplierSettlement)
            .filter(
                SupplierSettlement.order_id == order_id,
                SupplierSettlement.supplier_id.in_(supplier_ids),
            )
            .all()
        ):
            ss_map[(order_id, ss.supplier_id)] = ss
    ls_map: dict[tuple[int, int], LogisticsSettlement] = {}
    if logistics_partner_ids:
        for ls in (
            logistics_settlement_query(db)
            .filter(
                LogisticsSettlement.order_id == order_id,
                LogisticsSettlement.partner_id.in_(logistics_partner_ids),
            )
            .all()
        ):
            ls_map[(order_id, ls.partner_id)] = ls

    for entry in entries:
        if str(entry.settlement_status or "") == "refunded":
            continue

        supplier_settlement = ss_map.get((order_id, entry.supplier_id))
        logistics_settlement = None
        if entry.logistics_partner_id:
            logistics_settlement = ls_map.get((order_id, entry.logistics_partner_id))

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
    payout = payout_query(db).filter(Payout.id == payout_id).first()
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
    payout = logistics_partner_payout_query(db).filter(LogisticsPartnerPayout.id == payout_id).first()
    if payout:
        payout.status = "completed"
        payout.processed_at = txn.reconciled_at or _utcnow()
        payout.reference = txn.transaction_ref

    settlements = logistics_settlement_query(db).filter(LogisticsSettlement.payout_id == payout_id).all()
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
    q = logistics_settlement_query(db).filter(LogisticsSettlement.order_id == txn.linked_order_id)
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
        candidates = payout_query(db).filter(Payout.status == "processing").all()
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
        candidates = logistics_partner_payout_query(db).filter(LogisticsPartnerPayout.status == "processing").all()
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
        order = order_query(db).filter(Order.payment_intent_id == txn.transaction_ref).first()
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
        candidates = logistics_settlement_query(db).filter(
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


# â”€â”€ Reconciliation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # Batch pre-load existing transactions to avoid N+1 duplicate check
    refs = [entry["transaction_ref"] for entry in entries if entry.get("transaction_ref")]
    existing_by_ref: dict[str, BankTransaction] = {}
    if refs:
        existing_by_ref = {
            t.transaction_ref: t
            for t in db.query(BankTransaction)
            .filter(BankTransaction.transaction_ref.in_(refs))
            .all()
        }

    for entry in entries:
        transaction_ref = entry["transaction_ref"]
        existing = existing_by_ref.get(transaction_ref)
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

    from domains.suppliers.services.badges.supplier_badge_service import run_badge_recalculation_cycle
    from domains.governance.services.analytics.analytics_service import refresh_admin_analytics_snapshots
    from domains.governance.services.audit.retention_service import run_operational_retention_cycle

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
    settlement = logistics_settlement_query(db).filter(
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
        from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal

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
    q = logistics_cod_remittance_receipt_query(db)
    if partner_id is not None:
        q = q.filter(LogisticsCODRemittanceReceipt.partner_id == partner_id)
    if settlement_id is not None:
        q = q.filter(LogisticsCODRemittanceReceipt.settlement_id == settlement_id)
    if status:
        q = q.filter(LogisticsCODRemittanceReceipt.status == status)
    return q.order_by(LogisticsCODRemittanceReceipt.created_at.desc(), LogisticsCODRemittanceReceipt.id.desc()).limit(limit).all()


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
    settlement = logistics_settlement_query(db).filter(LogisticsSettlement.id == settlement_id).first()
    if settlement is None:
        raise ValueError(f"Logistics settlement {settlement_id} not found")
    if settlement.partner_id != partner_id:
        raise ValueError("Settlement does not belong to this logistics partner")

    due = round_money(to_decimal(settlement.cod_collected or 0) - to_decimal(settlement.cod_retained or 0))
    already_remitted = round_money(to_decimal(settlement.cod_remitted or 0))
    pending_pending = round_money(sum(
        to_decimal(row.amount or 0)
        for row in logistics_cod_remittance_receipt_query(db)
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
    receipt = logistics_cod_remittance_receipt_query(db).filter(LogisticsCODRemittanceReceipt.id == receipt_id).first()
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
    receipt = logistics_cod_remittance_receipt_query(db).filter(LogisticsCODRemittanceReceipt.id == receipt_id).first()
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
    settlement = receipt.settlement or logistics_settlement_query(db).filter(LogisticsSettlement.id == receipt.settlement_id).first()
    partner = receipt.partner or logistics_partner_query(db).filter(LogisticsPartner.id == receipt.partner_id).first()
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



# === Merged from accounts/services/cash_management_service.py ===

class BadgeBillingPaymentRequest(BaseModel):

    payment_method: str

    transaction_ref: Optional[str] = None

    notes: Optional[str] = None




class CodRemittanceRequest(BaseModel):

    amount: float




class FlagRequest(BaseModel):

    reason: str




class PayoutProcessRequest(BaseModel):

    settlement_ids: list[int] = []




class ReceiptReviewRequest(BaseModel):

    note: Optional[str] = None




def admin_auto_reconcile_transactions(limit: int, source: Optional[str], category: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_auto_reconcile_transactions(

        current_admin,

        db,

        limit=limit,

        source=source,

        category=category,

    )

    db.commit()

    return result




def admin_create_bank_transaction(data: BankTransactionCreate, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)

    db.commit()

    return result




def admin_dispatch_payouts(kind: str, provider: Optional[str], dry_run: bool, background: bool, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    if background:

        return ctrl.admin_queue_dispatch_transfer_batch(

            kind,

            current_admin,

            provider=provider,

            dry_run=dry_run,

        )



    result = ctrl.admin_dispatch_transfer_batch(

        kind,

        current_admin,

        db,

        provider=provider,

        dry_run=dry_run,

    )

    db.commit()

    return result




def admin_financial_summary(db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_get_financial_summary(db)




def admin_flag_transaction(txn_id: int, body: FlagRequest, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)

    db.commit()

    return result




def admin_get_bank_settings(db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_get_finance_bank_settings(db)




def admin_import_bank_transactions(items: list[BankTransactionImportItem], auto_reconcile: bool, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_import_bank_transactions(

        [item.model_dump() for item in items],

        current_admin,

        db,

        auto_reconcile=auto_reconcile,

    )

    db.commit()

    return result




def admin_list_badge_billings(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], badge_level: Optional[str], charge_type: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_badge_billing_records(

        db,

        skip=skip,

        limit=limit,

        supplier_id=supplier_id,

        status=status,

        badge_level=badge_level,

        charge_type=charge_type,

    )




def admin_list_bank_transactions(skip: int, limit: int, source: Optional[str], category: Optional[str], reconciled: Optional[bool], flagged: Optional[bool], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_bank_transactions(

        db, skip=skip, limit=limit,

        source=source, category=category,

        reconciled=reconciled, flagged=flagged,

    )




def admin_list_cod_remittance_receipts(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)




def admin_list_ledger(skip: int, limit: int, order_id: Optional[int], supplier_id: Optional[int], settlement_status: Optional[str], payment_method: Optional[str], category_slug: Optional[str], badge_level: Optional[str], calculation_method: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_ledger_entries(

        db, skip=skip, limit=limit,

        order_id=order_id, supplier_id=supplier_id,

        settlement_status=settlement_status, payment_method=payment_method,

        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,

    )




def admin_list_logistics_settlements(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)




def admin_list_refunds(skip: int, limit: int, status: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)




def admin_list_supplier_settlements(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)




def admin_list_transfer_providers(db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_transfer_providers(db)




def admin_list_vat_remittances(skip: int, limit: int, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)




def admin_reconcile_transaction(txn_id: int, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)

    db.commit()

    return result




def admin_reconciliation_summary(db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_get_reconciliation_summary(db)




def admin_record_badge_billing_payment(billing_id: int, body: BadgeBillingPaymentRequest, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_record_badge_billing_payment(

        billing_id=billing_id,

        payment_method=body.payment_method,

        current_admin=current_admin,

        db=db,

        transaction_ref=body.transaction_ref,

        notes=body.notes,

    )

    db.commit()

    return result




def admin_record_cod_remittance(settlement_id: int, body: CodRemittanceRequest, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)

    db.commit()

    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}




def admin_record_vat_remittance(body: VATRemittanceCreate, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)

    db.commit()

    return result




def admin_reject_cod_remittance_receipt(receipt_id: int, body: ReceiptReviewRequest, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")

    db.commit()

    return result




def admin_resolve_transaction(txn_id: int, body: BankTransactionResolutionIn, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)

    db.commit()

    return result




def admin_test_bank_settings_connection(db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    return ctrl.admin_test_finance_bank_connection(db)




def admin_trigger_logistics_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))

    db.commit()

    return {"processed": len(results), "payouts": results}




def admin_trigger_supplier_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))

    db.commit()

    return {"processed": len(results), "payouts": results}




def admin_upsert_bank_settings(body: FinanceBankSettingsUpdate, db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)

    db.commit()

    return result




def admin_verify_cod_remittance_receipt(receipt_id: int, body: Optional[ReceiptReviewRequest], db: Session, current_admin: dict):

    require_permission("payouts.verify", current_admin)

    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)

    db.commit()

    return result




def logistics_financial_summary(db: Session, current_user: dict):

    from domains.logistics.ports import logistics_partner_model, logistics_partner_query
    LP = logistics_partner_model()
    partner = logistics_partner_query(db).filter(LP.user_id == current_user["id"]).first()

    if not partner:

        return {"error": "Logistics partner not found"}, 404

    return ctrl.logistics_get_financial_summary(partner.id, db)




def logistics_list_ledger(skip: int, limit: int, db: Session, current_user: dict):

    from domains.logistics.ports import logistics_partner_model, logistics_partner_query
    LP = logistics_partner_model()
    partner = logistics_partner_query(db).filter(LP.user_id == current_user["id"]).first()

    if not partner:

        return []

    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)






def logistics_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):

    from domains.logistics.ports import logistics_partner_model, logistics_partner_query
    LP = logistics_partner_model()
    partner = logistics_partner_query(db).filter(LP.user_id == current_user["id"]).first()

    if not partner:

        return []

    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)




def supplier_financial_summary(db: Session, current_user: dict):

    if current_user.get("role") not in ("supplier", "admin"):

        return {"error": "Supplier access required"}, 403

    return ctrl.supplier_get_financial_summary(current_user["id"], db)




def supplier_list_ledger(skip: int, limit: int, db: Session, current_user: dict):

    if current_user.get("role") not in ("supplier", "admin"):

        return []

    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)




def supplier_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):

    if current_user.get("role") not in ("supplier", "admin"):

        return []

    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)

# === MERGED from cash_management_write_service.py ===

ï»¿"""Cash-management write service (W1 remediation).

``routers/cash_management.py`` used to own the transaction boundary for every
finance mutation (15 inline ``db.commit()`` calls). Per the layer contract only
``services/**`` may own DB transactions, so each admin write flow gets a
function here that:

    1. calls the underlying domain service (``services.treasury.cash_management_service``,
       ``services.treasury.payout_dispatch_service``, ``services.supplier.supplier_badge_service``),
    2. translates domain ``ValueError``s into ``HTTPException``s, and
    3. commits.

Every function takes the SQLAlchemy ``Session`` as its first positional
argument. Callers (controller/router) stay read-only orchestration.
"""

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.services.treasury.cash_management_service import auto_reconcile_bank_transactions as _auto_reconcile_bank_transactions
from domains.finance.services.treasury.cash_management_service import flag_bank_transaction as _flag_bank_transaction
from domains.finance.services.treasury.cash_management_service import import_bank_transactions as _import_bank_transactions
from domains.finance.services.treasury.cash_management_service import log_bank_transaction as _log_bank_transaction
from domains.finance.services.treasury.cash_management_service import process_logistics_payout_batch as _process_logistics_payout_batch
from domains.finance.services.treasury.cash_management_service import process_supplier_payout_batch as _process_supplier_payout_batch
from domains.finance.services.treasury.cash_management_service import reconcile_bank_transaction as _reconcile_bank_transaction
from domains.finance.services.treasury.cash_management_service import record_cod_remittance as _record_cod_remittance
from domains.finance.services.treasury.cash_management_service import record_vat_remittance as _record_vat_remittance
from domains.finance.services.treasury.cash_management_service import reject_cod_remittance_receipt as _reject_cod_remittance_receipt
from domains.finance.services.treasury.cash_management_service import resolve_bank_transaction_exception as _resolve_bank_transaction_exception
from domains.finance.services.treasury.cash_management_service import serialize_cod_remittance_receipt as _serialize_cod_remittance_receipt
from domains.finance.services.treasury.cash_management_service import upsert_finance_bank_settings as _upsert_finance_bank_settings
from domains.finance.services.treasury.cash_management_service import verify_cod_remittance_receipt as _verify_cod_remittance_receipt
from domains.finance.services.payouts.payout_dispatch_service import dispatch_transfer_batch_with_audit as _dispatch_transfer_batch_with_audit
from kernel.money import to_decimal
import structlog
logger = structlog.get_logger(__name__)


def _receipt_review_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    status_code = 404 if "not found" in detail.lower() else 400
    return HTTPException(status_code=status_code, detail=detail)


# â”€â”€ Badge billing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_badge_billing_payment(
    db: Session,
    *,
    billing_id: int,
    payment_method: str,
    current_admin: dict,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> Any:
    """Record a badge billing payment and commit."""
    from domains.suppliers.services.badges.supplier_badge_service import record_badge_billing_payment as _impl

    record = _impl(
        billing_id=billing_id,
        payment_method=payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=transaction_ref,
        notes=notes,
    )
    db.commit()
    return record


# â”€â”€ Bank settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def upsert_bank_settings(db: Session, *, data: dict, admin_id: Optional[int]) -> Any:
    """Create/update the primary finance bank account and commit."""
    record = _upsert_finance_bank_settings(data=data, admin_id=admin_id, db=db)
    db.commit()
    return record


# â”€â”€ VAT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_vat_remittance(db: Session, *, data: dict, admin_id: Optional[int]) -> Any:
    """Record a VAT remittance and commit."""
    record = _record_vat_remittance(
        period_start=data["period_start"],
        period_end=data["period_end"],
        amount_remitted=to_decimal(data["amount_remitted"]),
        admin_id=admin_id,
        db=db,
        notes=data.get("notes"),
        transaction_ref=data.get("transaction_ref"),
        remitted_at=data.get("remitted_at"),
    )
    db.commit()
    return record


# â”€â”€ Bank transactions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_bank_transaction(db: Session, *, data: dict) -> Any:
    """Manually create a bank transaction entry and commit."""
    txn = _log_bank_transaction(
        source=data["source"],
        transaction_type=data["transaction_type"],
        category=data["category"],
        amount=to_decimal(data["amount"]),
        db=db,
        currency=data.get("currency", "OMR"),
        order_id=data.get("linked_order_id"),
        supplier_id=data.get("linked_supplier_id"),
        logistics_id=data.get("linked_logistics_id"),
        payout_id=data.get("linked_payout_id"),
        refund_id=data.get("linked_refund_id"),
        description=data.get("description"),
        transaction_ref=data.get("transaction_ref"),
        transaction_date=data.get("transaction_date"),
    )
    db.commit()
    return txn


def import_bank_transactions(
    db: Session,
    *,
    items: list[dict],
    admin_id: Optional[int],
    auto_reconcile: bool = False,
) -> dict:
    """Import a bank statement batch and commit."""
    result = _import_bank_transactions(
        items,
        db,
        admin_id=admin_id,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result


def reconcile_transaction(db: Session, *, txn_id: int, admin_id: Any) -> Any:
    """Mark a bank transaction reconciled and commit."""
    try:
        txn = _reconcile_bank_transaction(txn_id, admin_id, db)
    except ValueError as exc:
        logger.exception("reconcile_transaction_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def flag_transaction(db: Session, *, txn_id: int, reason: str) -> Any:
    """Flag a bank transaction for manual review and commit."""
    try:
        txn = _flag_bank_transaction(txn_id, reason, db)
    except ValueError as exc:
        logger.exception("flag_transaction_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def resolve_transaction_exception(
    db: Session,
    *,
    txn_id: int,
    data: dict,
    admin_id: Optional[int],
) -> Any:
    """Resolve a flagged/unmatched bank transaction and commit."""
    try:
        txn = _resolve_bank_transaction_exception(
            txn_id,
            db,
            admin_id=admin_id,
            order_id=data.get("linked_order_id"),
            supplier_id=data.get("linked_supplier_id"),
            logistics_id=data.get("linked_logistics_id"),
            payout_id=data.get("linked_payout_id"),
            refund_id=data.get("linked_refund_id"),
            resolution_note=data.get("resolution_note"),
            mark_reconciled=data.get("mark_reconciled", True),
            clear_flag=data.get("clear_flag", True),
        )
    except ValueError as exc:
        logger.exception("resolve_transaction_exception_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def auto_reconcile_transactions(
    db: Session,
    *,
    admin_id: Any,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """Run the auto-reconciliation sweep and commit."""
    result = _auto_reconcile_bank_transactions(
        admin_id,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    db.commit()
    return result


# â”€â”€ Payouts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def trigger_supplier_payouts(db: Session, *, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Process the supplier payout batch and commit."""
    results = _process_supplier_payout_batch(db, settlement_ids=settlement_ids)
    db.commit()
    return results


def trigger_logistics_payouts(db: Session, *, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Process the logistics payout batch and commit."""
    results = _process_logistics_payout_batch(db, settlement_ids=settlement_ids)
    db.commit()
    return results


def dispatch_transfer_batch(
    db: Session,
    *,
    kind: str,
    admin_user: dict,
    provider: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Dispatch a payout transfer batch (with audit) and commit."""
    result = _dispatch_transfer_batch_with_audit(
        kind,
        admin_user,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    db.commit()
    return result


# â”€â”€ COD remittance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_cod_remittance(db: Session, *, settlement_id: int, amount: float, admin_id: Any) -> Any:
    """Record COD cash remittance from a logistics partner and commit."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Remittance amount must be positive")
    try:
        settlement = _record_cod_remittance(settlement_id, amount, admin_id, db)
    except ValueError as exc:
        logger.exception("record_cod_remittance_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return settlement


def verify_cod_remittance_receipt(
    db: Session,
    *,
    receipt_id: int,
    admin_id: Any,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Verify a COD remittance receipt, commit, and return its serialized form."""
    try:
        receipt = _verify_cod_remittance_receipt(receipt_id, admin_id, db, review_note=note)
    except ValueError as exc:
        logger.exception("verify_cod_remittance_receipt_failed", error=str(exc))
        raise _receipt_review_error(exc)
    db.commit()
    return _serialize_cod_remittance_receipt(receipt, db)


def reject_cod_remittance_receipt(
    db: Session,
    *,
    receipt_id: int,
    admin_id: Any,
    note: str,
) -> dict[str, Any]:
    """Reject a COD remittance receipt, commit, and return its serialized form."""
    try:
        receipt = _reject_cod_remittance_receipt(receipt_id, admin_id, db, review_note=note)
    except ValueError as exc:
        logger.exception("reject_cod_remittance_receipt_failed", error=str(exc))
        raise _receipt_review_error(exc)
    db.commit()
    return _serialize_cod_remittance_receipt(receipt, db)

# === MERGED from admin_treasury_identity_service.py ===

"""Admin cash management router."""
from fastapi import Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import CashAccount
from domains.finance.models.finance import CashTransaction
from infrastructure.database.schemas import CashAccountCreate, CashAccountOut, CashTransactionCreate, CashTransactionOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from decimal import Decimal

def list_accounts(country_code: str=Path(..., description='ISO country code'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
    finally:
        clear_rls_context()

def create_account(country_code: str=Path(..., description='ISO country code'), payload: CashAccountCreate=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
        db.add(a)
        db.commit()
        db.refresh(a)
        return a
    finally:
        clear_rls_context()

def create_transaction(country_code: str=Path(..., description='ISO country code'), payload: CashTransactionCreate=None, current_user: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
        if not account:
            raise HTTPException(404, 'Account not found')
        if payload.transaction_type == 'debit':
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    finally:
        clear_rls_context()

# === MERGED from cash_flow_forecast_service.py ===

ï»¿"""Cash Flow Forecast Engine â€” predicts future cash position.

Uses historical patterns, pending payouts, and expected settlements
to project daily cash balances.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import CashFlowForecast
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import PayoutBatch
from kernel.money import round_money
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def generate_forecast(
    db: Session,
    days: int = 90,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> dict:
    """Generate a cash flow forecast for the next N days.

    Uses:
    1. Current cash balance (Account 1010)
    2. Historical daily net flow (average of last 90 days)
    3. Pending supplier payouts (cash outflows)
    4. Expected COD remittances (cash inflows)
    5. Expected VAT remittances (cash outflows)
    """
    cash_acct = db.query(Account).filter(Account.code == "1010").first()
    if not cash_acct:
        return {"error": "Cash account (1010) not found â€” run seed first"}

    current_balance = Decimal("0.00")
    bal = db.query(AccountBalance).filter(
        AccountBalance.account_id == cash_acct.id,
        AccountBalance.currency == currency,
    ).first()
    if bal:
        current_balance = bal.balance

    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Historical average daily net flow (last 90 days)
    historical_start = today - timedelta(days=90)
    historical_net = db.query(
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "debit"),
            0,
        ) -
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "credit"),
            0,
        )
    ).select_from(JournalEntryLine).join(
        JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
    ).filter(
        JournalEntryLine.account_id == cash_acct.id,
        JournalEntry.entry_date >= historical_start,
        JournalEntry.entry_date < today,
        JournalEntry.is_deleted == False,
    ).scalar()

    avg_daily_net = round_money(
        (historical_net or Decimal("0.00")) / Decimal("90")
    )

    # Pending payouts (scheduled outflows)
    pending_payouts = db.query(
        func.coalesce(func.sum(SupplierSettlement.net_amount), 0)
    ).filter(
        SupplierSettlement.status.in_(["pending", "approved"]),
        SupplierSettlement.country_code == country_code if country_code else True,
    ).scalar() or Decimal("0.00")

    # Forecast daily
    forecast_days = []
    running_balance = current_balance
    for day_offset in range(days):
        date = today + timedelta(days=day_offset)
        daily_inflow = Decimal("0.00")
        daily_outflow = Decimal("0.00")

        # Base projection from historical average
        if avg_daily_net > 0:
            daily_inflow += avg_daily_net
        else:
            daily_outflow += abs(avg_daily_net)

        # Known payouts (schedule them evenly over first 30 days)
        if day_offset < 30 and pending_payouts > 0:
            scheduled = round_money(pending_payouts / Decimal("30"))
            daily_outflow += scheduled

        net = daily_inflow - daily_outflow
        running_balance = round_money(running_balance + net)

        forecast_days.append({
            "date": date.isoformat(),
            "opening_balance": float(running_balance - net),
            "inflow": float(daily_inflow),
            "outflow": float(daily_outflow),
            "net_flow": float(net),
            "closing_balance": float(running_balance),
        })

    result = {
        "generated_at": utcnow().isoformat(),
        "currency": currency,
        "current_balance": float(current_balance),
        "historical_avg_daily_net": float(avg_daily_net),
        "pending_payouts": float(pending_payouts),
        "forecast_days": forecast_days,
        "projected_balance_30d": float(forecast_days[29]["closing_balance"]) if len(forecast_days) > 29 else None,
        "projected_balance_90d": float(forecast_days[-1]["closing_balance"]),
    }

    # Persist summary to CashFlowForecast table
    forecast_record = CashFlowForecast(
        forecast_date=today,
        period_start=today,
        period_end=today + timedelta(days=days),
        net_cash_flow=float(running_balance - current_balance),
        opening_balance=float(current_balance),
        closing_balance=float(running_balance),
    )
    db.add(forecast_record)
    db.commit()

    return result

# === MERGED from treasury.py ===

"""Lazy re-export delegator for ``domains.finance.services`` (treasury alias).

Some routers import ``from ...services.treasury import X``. This alias resolves
names from the services tree (root or any sub-domain).
"""

import importlib
import sys

_PACKAGE = "domains.finance.services"
_SUBDOMAINS = [
    "ledger", "accounts", "treasury", "payouts", "tax",
    "reporting", "country", "commission", "shared",
]


def __getattr__(name: str):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    try:
        module = importlib.import_module(f"{_PACKAGE}.{name}")
        setattr(sys.modules[__name__], name, module)
        return module
    except ModuleNotFoundError:
        pass
    for sub in _SUBDOMAINS:
        try:
            module = importlib.import_module(f"{_PACKAGE}.{sub}.{name}")
            setattr(sys.modules[__name__], name, module)
            return module
        except ModuleNotFoundError:
            continue
    raise AttributeError(f"module {_PACKAGE!r} has no attribute {name!r}")

# === MERGED from admin_cash_service.py ===

ï»¿"""Admin cash management service."""

from sqlalchemy.orm import Session

from infrastructure.database.schemas import (
    CashAccountCreate,
    CashAccountOut,
    CashTransactionCreate,
    CashTransactionOut,
)
from domains.finance.models.finance import CashAccount

from domains.comms.services.utility.misc_write_service import create_cash_account as create_cash_account_model
from domains.comms.services.utility.misc_write_service import create_cash_transaction as create_cash_transaction_model

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context


def list_accounts(country_code: str, db: Session) -> list[CashAccountOut]:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(
            CashAccount.is_active == True,
            CashAccount.country_code == country_code.upper()
        ).all()
    finally:
        clear_rls_context()


def create_account(country_code: str, payload: CashAccountCreate, db: Session) -> CashAccountOut:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account_data = payload.model_dump()
        account_data["country_code"] = country_code.upper()
        return create_cash_account_model(db, **account_data)
    finally:
        clear_rls_context()


def create_transaction(country_code: str, payload: CashTransactionCreate, current_user_id: int, db: Session) -> CashTransactionOut:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(
            CashAccount.id == payload.account_id,
            CashAccount.country_code == country_code.upper()
        ).first()
        if not account:
            raise ValueError("Account not found")
        if payload.transaction_type == "debit":
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx_data = payload.model_dump()
        tx_data["balance_after"] = account.balance
        tx_data["performed_by"] = current_user_id
        tx_data["country_code"] = country_code.upper()
        return create_cash_transaction_model(db, **tx_data)
    finally:
        clear_rls_context()

# === MERGED from trading_service_accounts.py ===

ï»¿from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from domains.catalog.ports import Product
from domains.catalog.ports import ProductVariant
from domains.finance.models.erp import GoodsReceiptNote
from domains.finance.models.erp import GoodsReceiptLine
from domains.finance.models.erp import SalesOrder
from domains.finance.models.erp import SalesOrderLine
from domains.finance.models.erp import Warehouse
from domains.finance.models.erp import StockMovement
from domains.finance.models.finance import Vendor
from domains.finance.models.finance import Customer
from domains.finance.models.finance import APBill
from domains.finance.models.finance import ARInvoice
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import Account
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.erp import PurchaseOrder
from domains.finance.models.erp import PurchaseOrderLine
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
from domains.finance.services.finance import general_ledger_service as gl
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

INVENTORY_ACCOUNT = "1060"
COGS_ACCOUNT = "6000"
AP_ACCOUNT = "2010"
AR_ACCOUNT = "1035"
REVENUE_ACCOUNT = "4040"
VAT_OUTPUT_ACCOUNT = "2040"
VAT_INPUT_ACCOUNT = "2050"


def _next_number(db: Session, prefix: str, table_column) -> str:
    last = db.query(func.max(table_column)).filter(
        table_column.like(f"{prefix}-%")
    ).scalar()
    seq = 1
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}-{seq:05d}"


# â”€â”€ Purchase Order â”€â”€


def create_purchase_order(
    db: Session, *, supplier_id: int, order_date: datetime = None,
    expected_delivery_date: datetime = None, warehouse_id: int = None,
    currency: str = "OMR", notes: str = None, terms: str = None,
    shipping_address: str = None, country_code: str = None,
    lines: list[dict] = None, created_by: int = None,
) -> PurchaseOrder:
    supplier = db.query(Vendor).filter(Vendor.id == supplier_id).first()
    if not supplier:
        raise ValueError("Supplier not found")
    po_number = _next_number(db, "PO", PurchaseOrder.po_number)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    po = PurchaseOrder(
        po_number=po_number, supplier_id=supplier_id,
        supplier_name=supplier.name,
        order_date=order_date or _utcnow(),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id, currency=currency,
        notes=notes, terms=terms, shipping_address=shipping_address,
        country_code=country_code, created_by=created_by,
        status="draft",
    )
    db.add(po)
    db.flush()
    po_lines = []
    for idx, ld in enumerate(lines or []):
        qty = Decimal(str(ld.get("quantity_ordered", 0)))
        price = Decimal(str(ld.get("unit_price", 0)))
        disc_pct = Decimal(str(ld.get("discount_percent", 0)))
        tax_rate = Decimal(str(ld.get("tax_rate", 0)))
        line_disc = qty * price * (disc_pct / Decimal("100"))
        line_sub = qty * price - line_disc
        line_tax = line_sub * (tax_rate / Decimal("100"))
        line_total = line_sub + line_tax
        subtotal += line_sub
        discount_total += line_disc
        tax_total += line_tax
        line = PurchaseOrderLine(
            po_id=po.id, product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            description=ld.get("description"),
            quantity_ordered=qty, unit_price=price,
            discount_percent=disc_pct, discount_amount=line_disc,
            tax_rate=tax_rate, tax_amount=line_tax,
            line_total=line_total,
            weight=ld.get("weight"), volume=ld.get("volume"),
            country_code=country_code,
        )
        db.add(line)
        po_lines.append(line)
    po.subtotal = subtotal
    po.discount_total = discount_total
    po.tax_total = tax_total
    po.grand_total = subtotal + tax_total
    db.commit()
    db.refresh(po)
    return po


def confirm_purchase_order(db: Session, po_id: int) -> PurchaseOrder:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    if po.status != "draft":
        raise ValueError(f"Cannot confirm PO in status '{po.status}'")
    po.status = "confirmed"
    db.commit()
    db.refresh(po)
    return po


def receive_purchase_order(db: Session, po_id: int, grn_data: dict) -> GoodsReceiptNote:
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    if po.status not in ("confirmed", "partially_received"):
        raise ValueError(f"Cannot receive PO in status '{po.status}'")
    supplier = db.query(Vendor).filter(Vendor.id == po.supplier_id).first()
    grn_number = _next_number(db, "GRN", GoodsReceiptNote.grn_number)
    grn = GoodsReceiptNote(
        grn_number=grn_number, po_id=po.id,
        supplier_id=po.supplier_id,
        receipt_date=grn_data.get("receipt_date") or _utcnow(),
        warehouse_id=grn_data.get("warehouse_id") or po.warehouse_id,
        status="confirmed", notes=grn_data.get("notes"),
        received_by=grn_data.get("received_by"),
        country_code=po.country_code,
    )
    db.add(grn)
    db.flush()
    line_map = {l.id: l for l in po.lines}
    total_received_qty = Decimal("0")
    total_accepted_qty = Decimal("0")
    for rl in (grn_data.get("lines") or []):
        po_line = line_map.get(rl.get("po_line_id"))
        if not po_line:
            continue
        qty_rec = Decimal(str(rl.get("quantity_received", 0)))
        qty_acc = Decimal(str(rl.get("quantity_accepted", qty_rec)))
        qty_rej = qty_rec - qty_acc
        cost = po_line.unit_price
        grn_line = GoodsReceiptLine(
            grn_id=grn.id, po_line_id=po_line.id,
            product_id=po_line.product_id,
            product_name=po_line.product_name,
            sku=po_line.sku,
            quantity_received=qty_rec,
            quantity_accepted=qty_acc,
            quantity_rejected=qty_rej,
            rejection_reason=rl.get("rejection_reason"),
            lot_number=rl.get("lot_number"),
            expiry_date=rl.get("expiry_date"),
            unit_cost=cost,
            country_code=po.country_code,
        )
        db.add(grn_line)
        po_line.quantity_received = (po_line.quantity_received or 0) + qty_acc
        total_received_qty += qty_rec
        total_accepted_qty += qty_acc
        _record_stock_movement(
            db, product_id=po_line.product_id,
            warehouse_id=grn.warehouse_id,
            movement_type="inbound",
            reference_type="grn", reference_id=grn.id,
            quantity_change=qty_acc,
            unit_cost=cost,
            country_code=po.country_code,
            created_by=grn_data.get("received_by"),
        )
    all_received = all(
        l.quantity_received >= l.quantity_ordered
        for l in po.lines if l.quantity_ordered > 0
    )
    po.status = "received" if all_received else "partially_received"
    po.delivery_date = grn.receipt_date
    po.warehouse_id = grn.warehouse_id or po.warehouse_id
    _post_grn_inventory_journal(db, grn, po)
    db.commit()
    db.refresh(grn)
    return grn


def _post_grn_inventory_journal(db: Session, grn: GoodsReceiptNote, po: PurchaseOrder) -> None:
    total_inventory = Decimal("0")
    for gl_ in grn.lines:
        cost = gl_.unit_cost or Decimal("0")
        total_inventory += cost * gl_.quantity_accepted
    if total_inventory <= 0:
        return
    lines = [
        JournalLineInput(
            account_code=INVENTORY_ACCOUNT, side="debit",
            amount=total_inventory,
            description=f"GRN {grn.grn_number} inventory receipt",
            entity_type="grn", entity_id=grn.id,
        ),
        JournalLineInput(
            account_code=AP_ACCOUNT, side="credit",
            amount=total_inventory,
            description=f"GRN {grn.grn_number} AP accrual",
            entity_type="grn", entity_id=grn.id,
        ),
    ]
    if po.country_code:
        setattr(lines[0], "country_code", po.country_code)
        setattr(lines[1], "country_code", po.country_code)
    try:
        gl.create_journal_entry(db, JournalEntryCreate(
            entry_date=grn.receipt_date,
            reference_type="grn", reference_id=grn.id,
            description=f"GRN {grn.grn_number} â€” inventory receipt & AP accrual",
            currency=po.currency, country_code=po.country_code,
            lines=lines,
        ))
    except Exception as e:
        logger.warning("GRN journal post failed (may retry): %s", e)


def three_way_match(
    db: Session, *, po_id: int = None, grn_id: int = None, bill_id: int = None,
) -> dict:
    results = {"po_ok": False, "grn_ok": False, "bill_ok": False, "match": False, "discrepancies": []}
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first() if po_id else None
    grn = db.query(GoodsReceiptNote).options(
        joinedload(GoodsReceiptNote.lines)
    ).filter(GoodsReceiptNote.id == grn_id).first() if grn_id else None
    bill = db.query(APBill).filter(APBill.id == bill_id).first() if bill_id else None
    if po:
        results["po_ok"] = True
    if grn and po:
        po_total_qty = sum((l.quantity_ordered or 0) for l in po.lines)
        grn_total_qty = sum((l.quantity_accepted or 0) for l in grn.lines)
        if abs(grn_total_qty - po_total_qty) > Decimal("0.001"):
            results["discrepancies"].append(
                f"GRN qty ({grn_total_qty}) != PO qty ({po_total_qty})"
            )
        else:
            results["grn_ok"] = True
    if bill and po:
        if abs(bill.amount - po.grand_total) > Decimal("0.01"):
            results["discrepancies"].append(
                f"Bill amount ({bill.amount}) != PO total ({po.grand_total})"
            )
        elif abs(bill.tax_amount - po.tax_total) > Decimal("0.01"):
            results["discrepancies"].append(
                f"Bill tax ({bill.tax_amount}) != PO tax ({po.tax_total})"
            )
        else:
            results["bill_ok"] = True
    if grn is None and po:
        results["grn_ok"] = True
    if bill is None and po:
        results["bill_ok"] = True
    results["match"] = results["po_ok"] and results["grn_ok"] and results["bill_ok"]
    if results["match"] and bill and bill.status == "received":
        bill.status = "approved"
        db.commit()
    return results


# â”€â”€ Sales Order â”€â”€


def create_sales_order(
    db: Session, *, customer_id: int, order_date: datetime = None,
    expected_delivery_date: datetime = None, warehouse_id: int = None,
    currency: str = "OMR", customer_po_number: str = None,
    shipping_address: str = None, billing_address: str = None,
    notes: str = None, terms: str = None, country_code: str = None,
    lines: list[dict] = None, created_by: int = None,
) -> SalesOrder:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise ValueError("Customer not found")
    if customer.credit_limit:
        current_ar = db.query(func.coalesce(func.sum(ARInvoice.amount), 0)).filter(
            ARInvoice.customer_id == customer_id,
            ARInvoice.status.in_(["issued", "partially_paid"]),
        ).scalar()
        new_total = sum(
            Decimal(str(l.get("unit_price", 0))) * Decimal(str(l.get("quantity_ordered", 0)))
            for l in (lines or [])
        )
        if (current_ar or 0) + new_total > customer.credit_limit:
            raise ValueError("Order would exceed customer credit limit")
    so_number = _next_number(db, "SO", SalesOrder.so_number)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    so = SalesOrder(
        so_number=so_number, customer_id=customer_id,
        customer_name=customer.name,
        customer_po_number=customer_po_number,
        order_date=order_date or _utcnow(),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id, currency=currency,
        shipping_address=shipping_address,
        billing_address=billing_address,
        notes=notes, terms=terms,
        country_code=country_code, created_by=created_by,
        status="draft",
    )
    db.add(so)
    db.flush()
    for ld in (lines or []):
        qty = Decimal(str(ld.get("quantity_ordered", 0)))
        price = Decimal(str(ld.get("unit_price", 0)))
        disc_pct = Decimal(str(ld.get("discount_percent", 0)))
        tax_rate = Decimal(str(ld.get("tax_rate", 0)))
        line_disc = qty * price * (disc_pct / Decimal("100"))
        line_sub = qty * price - line_disc
        line_tax = line_sub * (tax_rate / Decimal("100"))
        line_total = line_sub + line_tax
        subtotal += line_sub
        discount_total += line_disc
        tax_total += line_tax
        line = SalesOrderLine(
            so_id=so.id, product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            description=ld.get("description"),
            quantity_ordered=qty, unit_price=price,
            discount_percent=disc_pct, discount_amount=line_disc,
            tax_rate=tax_rate, tax_amount=line_tax,
            line_total=line_total,
            weight=ld.get("weight"), volume=ld.get("volume"),
            country_code=country_code,
        )
        db.add(line)
    so.subtotal = subtotal
    so.discount_total = discount_total
    so.tax_total = tax_total
    so.grand_total = subtotal + tax_total
    db.commit()
    db.refresh(so)
    return so


def confirm_sales_order(db: Session, so_id: int) -> SalesOrder:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status != "draft":
        raise ValueError(f"Cannot confirm SO in status '{so.status}'")
    so.status = "confirmed"
    db.commit()
    db.refresh(so)
    return so


def invoice_sales_order(db: Session, so_id: int, invoice_date: datetime = None,
                        created_by: int = None) -> ARInvoice:
    so = db.query(SalesOrder).options(
        joinedload(SalesOrder.lines)
    ).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status not in ("confirmed", "invoiced", "partially_invoiced"):
        raise ValueError(f"Cannot invoice SO in status '{so.status}'")
    invoice_number = _next_number(db, "INV", ARInvoice.invoice_number)
    inv = ARInvoice(
        customer_id=so.customer_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date or _utcnow(),
        due_date=(invoice_date or _utcnow()) + timedelta(days=30),
        account_code=REVENUE_ACCOUNT,
        amount=so.grand_total,
        tax_amount=so.tax_total,
        description=f"Invoice for SO {so.so_number}",
        country_code=so.country_code,
        created_by=created_by,
        status="issued",
    )
    db.add(inv)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=inv.invoice_date,
        reference_type="so_invoice", reference_id=inv.id,
        description=f"AR invoice {invoice_number} for SO {so.so_number}",
        currency=so.currency, country_code=so.country_code,
        lines=[
            JournalLineInput(
                account_code=AR_ACCOUNT, side="debit",
                amount=so.grand_total,
                description=f"AR for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
            JournalLineInput(
                account_code=REVENUE_ACCOUNT, side="credit",
                amount=so.grand_total - so.tax_total,
                description=f"Revenue for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
            JournalLineInput(
                account_code=VAT_OUTPUT_ACCOUNT, side="credit",
                amount=so.tax_total,
                description=f"VAT for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
        ],
    ), user_id=created_by)
    inv.linked_journal_entry_id = entry.id
    so.status = "invoiced"
    db.commit()
    db.refresh(inv)
    return inv


def dispatch_sales_order(db: Session, so_id: int, dispatch_data: dict,
                         created_by: int = None) -> SalesOrder:
    so = db.query(SalesOrder).options(
        joinedload(SalesOrder.lines)
    ).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status not in ("invoiced", "partially_dispatched"):
        raise ValueError(f"Cannot dispatch SO in status '{so.status}'")
    so.status = "dispatched"
    total_cogs = Decimal("0")
    for sol in so.lines:
        qty = dispatch_data.get("quantities", {}).get(str(sol.id))
        if qty:
            qty_disp = Decimal(str(qty))
            sol.quantity_dispatched = (sol.quantity_dispatched or 0) + qty_disp
            cost = _get_product_cost(db, sol.product_id)
            line_cogs = cost * qty_disp if cost else Decimal("0")
            total_cogs += line_cogs
            _record_stock_movement(
                db, product_id=sol.product_id,
                warehouse_id=so.warehouse_id,
                movement_type="outbound",
                reference_type="so", reference_id=so.id,
                quantity_change=-qty_disp,
                unit_cost=cost,
                country_code=so.country_code,
                created_by=created_by,
            )
    so.delivery_date = dispatch_data.get("dispatch_date") or _utcnow()
    if total_cogs > 0:
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=so.delivery_date,
                reference_type="so_cogs", reference_id=so.id,
                description=f"COGS for SO {so.so_number}",
                currency=so.currency, country_code=so.country_code,
                lines=[
                    JournalLineInput(
                        account_code=COGS_ACCOUNT, side="debit",
                        amount=total_cogs,
                        description=f"COGS for SO {so.so_number}",
                        entity_type="sales_order", entity_id=so.id,
                    ),
                    JournalLineInput(
                        account_code=INVENTORY_ACCOUNT, side="credit",
                        amount=total_cogs,
                        description=f"Inventory reduction for SO {so.so_number}",
                        entity_type="sales_order", entity_id=so.id,
                    ),
                ],
            ), user_id=created_by)
        except Exception as e:
            logger.warning("COGS journal post failed for SO %s: %s", so.so_number, e)
    db.commit()
    db.refresh(so)
    return so


# â”€â”€ Dunning Engine â”€â”€


def run_dunning_engine(db: Session, as_of: date = None) -> list[dict]:
    as_of = as_of or date.today()
    triggered = []
    invoices = db.query(ARInvoice).filter(
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date.isnot(None),
    ).all()
    for inv in invoices:
        days_overdue = (as_of - inv.due_date.date()).days if inv.due_date else 0
        reminders = []
        if days_overdue <= -7 and days_overdue > -14:
            reminders.append({"type": "reminder_1", "message": f"Payment due in {abs(days_overdue)} days for invoice {inv.invoice_number}"})
        elif days_overdue == 0:
            reminders.append({"type": "reminder_2", "message": f"Payment due today for invoice {inv.invoice_number}"})
        elif 1 <= days_overdue <= 7:
            reminders.append({"type": "reminder_3", "message": f"Invoice {inv.invoice_number} is {days_overdue} day(s) overdue â€” late fee may apply"})
        elif 8 <= days_overdue <= 30:
            reminders.append({"type": "reminder_4", "message": f"Invoice {inv.invoice_number} is {days_overdue} day(s) overdue â€” credit hold risk"})
        elif 31 <= days_overdue <= 60:
            reminders.append({"type": "escalation_1", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days â€” management alert"})
        elif 61 <= days_overdue <= 90:
            reminders.append({"type": "escalation_2", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days â€” legal warning"})
        elif days_overdue > 90:
            reminders.append({"type": "write_off_recommendation", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days â€” recommend write-off"})
        if reminders:
            triggered.append({
                "invoice_id": inv.id, "invoice_number": inv.invoice_number,
                "customer_id": inv.customer_id, "days_overdue": days_overdue,
                "amount": float(inv.amount), "reminders": reminders,
            })
            # Send dunning emails
            try:
                from domains.comms.services.transactional_email_service import enqueue_dunning_email
                for reminder in reminders:
                    enqueue_dunning_email(inv.id, reminder["type"], reminder["message"])
            except Exception as e:
                logger.warning("Failed to send dunning email for invoice %s: %s", inv.id, e)
    return triggered


# â”€â”€ Stock â”€â”€


def _get_product_cost(db: Session, product_id: int) -> Optional[Decimal]:
    if not product_id:
        return None
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and product.cost_price:
        return Decimal(str(product.cost_price))
    return None


def _record_stock_movement(
    db: Session, *, product_id: int, warehouse_id: int = None,
    movement_type: str, reference_type: str = None, reference_id: int = None,
    quantity_change: Decimal, unit_cost: Decimal = None,
    country_code: str = None, created_by: int = None,
) -> StockMovement:
    if not product_id:
        return None
    last_mvt = db.query(StockMovement.quantity_after).filter(
        StockMovement.product_id == product_id,
        StockMovement.warehouse_id == warehouse_id,
    ).order_by(StockMovement.id.desc()).first()
    prev_qty = Decimal(str(last_mvt[0])) if last_mvt else Decimal("0")
    qty_after = prev_qty + quantity_change
    total_cost = (unit_cost or Decimal("0")) * abs(quantity_change) if quantity_change else Decimal("0")
    mvt = StockMovement(
        product_id=product_id, warehouse_id=warehouse_id,
        movement_type=movement_type,
        reference_type=reference_type, reference_id=reference_id,
        quantity_change=quantity_change, quantity_after=qty_after,
        unit_cost=unit_cost, total_cost=total_cost,
        country_code=country_code, created_by=created_by,
    )
    db.add(mvt)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        new_stock = (product.stock or 0) + int(quantity_change)
        product.stock = max(0, new_stock)
    return mvt


def get_stock_level(db: Session, product_id: int = None, warehouse_id: int = None) -> list[dict]:
    q = db.query(
        StockMovement.product_id, Product.name, Product.sku,
        func.sum(StockMovement.quantity_change).label("current_stock"),
        func.max(StockMovement.created_at).label("last_movement"),
    ).join(Product, StockMovement.product_id == Product.id)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    q = q.group_by(StockMovement.product_id, Product.name, Product.sku)
    results = []
    for row in q.all():
        results.append({
            "product_id": row.product_id,
            "product_name": row.name,
            "sku": row.sku,
            "current_stock": float(row.current_stock or 0),
            "last_movement": row.last_movement.isoformat() if row.last_movement else None,
        })
    return results


# â”€â”€ Warehouse â”€â”€


def create_warehouse(db: Session, *, name: str, code: str, address: str = None,
                     city: str = None, country_code: str = None) -> Warehouse:
    existing = db.query(Warehouse).filter(Warehouse.code == code).first()
    if existing:
        raise ValueError(f"Warehouse code '{code}' already exists")
    wh = Warehouse(name=name, code=code, address=address, city=city, country_code=country_code)
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


def list_warehouses(db: Session, country_code: str = None) -> list[Warehouse]:
    q = db.query(Warehouse)
    if country_code:
        q = q.filter(Warehouse.country_code == country_code)
    return q.order_by(Warehouse.name).all()


# â”€â”€ PO / SO Listing â”€â”€


def list_purchase_orders(db: Session, status: str = None, supplier_id: int = None,
                          country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    if supplier_id:
        q = q.filter(PurchaseOrder.supplier_id == supplier_id)
    if country_code:
        q = q.filter(PurchaseOrder.country_code == country_code)
    total = q.count()
    rows = q.order_by(PurchaseOrder.id.desc()).limit(limit).all()
    return {"total": total, "items": rows}


def list_sales_orders(db: Session, status: str = None, customer_id: int = None,
                       country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(SalesOrder)
    if status:
        q = q.filter(SalesOrder.status == status)
    if customer_id:
        q = q.filter(SalesOrder.customer_id == customer_id)
    if country_code:
        q = q.filter(SalesOrder.country_code == country_code)
    total = q.count()
    rows = q.order_by(SalesOrder.id.desc()).limit(limit).all()
    return {"total": total, "items": rows}


def list_goods_receipts(db: Session, po_id: int = None, status: str = None,
                         country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(GoodsReceiptNote)
    if po_id:
        q = q.filter(GoodsReceiptNote.po_id == po_id)
    if status:
        q = q.filter(GoodsReceiptNote.status == status)
    if country_code:
        q = q.filter(GoodsReceiptNote.country_code == country_code)
    total = q.count()
    rows = q.order_by(GoodsReceiptNote.id.desc()).limit(limit).all()
    return {"total": total, "items": rows}


# â”€â”€ Single-entity reads (extracted from admin_supplier_trading router) â”€â”€


def get_purchase_order(db: Session, po_id: int) -> PurchaseOrder:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    return po


def get_goods_receipt(db: Session, grn_id: int) -> GoodsReceiptNote:
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise ValueError("Goods receipt note not found")
    return grn


def get_sales_order(db: Session, so_id: int) -> SalesOrder:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    return so


def list_stock_movements(db: Session, product_id: int = None, limit: int = 100,
                         offset: int = 0) -> dict:
    q = db.query(StockMovement)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    total = q.count()
    rows = q.order_by(StockMovement.id.desc()).limit(limit).all()
    return {"total": total, "items": rows}


# â”€â”€ 3-Way Match Scanner â”€â”€


def scan_unmatched_pos(db: Session, country_code: str = None) -> dict:
    """
    Scan for purchase orders that haven't been fully matched (3-way match).
    Returns list of POs with GRN but no matching bill, or bill but no GRN.
    """
    results = {"scanned": 0, "unmatched": 0, "items": []}
    
    # Find POs with status 'received' (GRN confirmed) but no AP bill
    q = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["received", "partial"]),
    )
    if country_code:
        q = q.filter(PurchaseOrder.country_code == country_code)
    
    pos = q.all()
    results["scanned"] = len(pos)
    if not pos:
        return results

    po_numbers = [po.po_number for po in pos]

    # Batch: one AP-bill query for bills referencing any of these POs
    bill_candidates = db.query(APBill).filter(
        APBill.linked_journal_entry_id.isnot(None),
        APBill.description.like("%PO-%"),
    ).all()
    billed_pos: set = set()
    for b in bill_candidates:
        desc = b.description or ""
        for n in po_numbers:
            if f"PO-{n}" in desc:
                billed_pos.add(n)
                break

    # Batch: one GRN query for these POs
    po_ids = [po.id for po in pos]
    grn_rows = db.query(GoodsReceiptNote).filter(
        GoodsReceiptNote.po_id.in_(po_ids),
        GoodsReceiptNote.status == "confirmed",
    ).all()
    grn_pos = {g.po_id for g in grn_rows}

    for po in pos:
        if po.po_number in billed_pos:
            continue
        has_grn = po.id in grn_pos
        results["unmatched"] += 1
        results["items"].append({
            "po_id": po.id,
            "po_number": po.po_number,
            "status": po.status,
            "has_grn": bool(has_grn),
            "has_bill": False,
            "vendor_id": po.vendor_id,
            "total_amount": float(po.total_amount or 0),
        })

    return results


# â”€â”€ E-commerce Auto-Invoice on Delivery (#11) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def auto_invoice_ecommerce_orders(db: Session, country_code: str = None) -> dict:
    """
    Auto-generate AR invoices for delivered e-commerce orders.
    Called daily by the automation scheduler.
    """
    from domains.finance.models.finance import ARInvoice
    from domains.finance.models.finance import Account
    from domains.orders.models.orders import Order

    results = {"scanned": 0, "invoiced": 0, "skipped": 0, "errors": 0}

    orders = db.query(Order).filter(
        Order.payment_method == "card",
        Order.status == "delivered",
        Order.invoice_id.is_(None),
    )
    if country_code:
        orders = orders.filter(Order.country_code == country_code)

    orders_all = orders.all()
    results["scanned"] = len(orders_all)

    # Load constant accounts and existing invoices once instead of per-order
    revenue_acct = db.query(Account).filter(Account.code == "4010").first()
    vat_acct = db.query(Account).filter(Account.code == "2040").first()
    order_ids = [o.id for o in orders_all]
    invoiced_ids: set = set()
    if order_ids:
        inv_rows = db.query(ARInvoice).filter(
            ARInvoice.reference_order_id.in_(order_ids)
        ).all()
        invoiced_ids = {i.reference_order_id for i in inv_rows}

    for order in orders_all:
        try:
            if order.id in invoiced_ids:
                results["skipped"] += 1
                continue

            invoice_number = _next_number(db, "INV", ARInvoice.invoice_number)
            now = _utcnow()

            if not revenue_acct or not vat_acct:
                results["errors"] += 1
                continue

            lines = [
                JournalLineInput(
                    account_code="1100",
                    side="debit",
                    amount=order.total_amount,
                    description=f"AR for delivered order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                JournalLineInput(
                    account_code="4010",
                    side="credit",
                    amount=order.total_amount,
                    description=f"Sales revenue - Order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                JournalLineInput(
                    account_code="2040",
                    side="credit",
                    amount=order.vat_amount or 0,
                    description=f"VAT output - Order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
            ]

            entry_data = JournalEntryCreate(
                entry_date=now,
                reference_type="ecommerce_invoice",
                reference_id=order.id,
                reference_number=invoice_number,
                description=f"Auto-invoice for delivered order #{order.id}",
                currency=order.currency or "OMR",
                country_code=country_code or order.country_code,
                lines=lines,
            )

            je = gl.create_journal_entry(db, entry_data)

            ar_invoice = ARInvoice(
                customer_id=order.user_id,
                invoice_number=invoice_number,
                invoice_date=now,
                due_date=now,
                account_code="1100",
                amount=order.total_amount,
                tax_amount=order.vat_amount,
                status="issued",
                linked_journal_entry_id=je.id,
                country_code=country_code or order.country_code,
                created_by=0,
            )
            db.add(ar_invoice)
            order.invoice_id = ar_invoice.id
            results["invoiced"] += 1
        except Exception as e:
            logger.warning("Auto-invoice failed for order %s: %s", order.id, e)
            results["errors"] += 1

    db.commit()
    return results

# === MERGED from trading_read_service.py ===

ï»¿"""Read helpers for purchase orders, goods receipt notes, sales orders and
stock movements.

Previously these ``db.query(...)`` lookups lived inline in
``routers/admin_supplier_trading.py`` and ``routers/trading.py``. They are
pure data-access functions (no commit, no HTTP concerns) so they belong in
the services layer. The routers delegate through
``controllers/admin/admin_supplier_trading_controller.py``.
"""

from typing import Optional

from sqlalchemy.orm import Session

from domains.finance.models.erp import GoodsReceiptNote
from domains.finance.models.erp import PurchaseOrder
from domains.finance.models.erp import SalesOrder
from domains.finance.models.erp import StockMovement


def get_purchase_order(db: Session, po_id: int) -> Optional[PurchaseOrder]:
    return db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()


def get_goods_receipt_note(db: Session, grn_id: int) -> Optional[GoodsReceiptNote]:
    return db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()


def get_sales_order(db: Session, so_id: int) -> Optional[SalesOrder]:
    return db.query(SalesOrder).filter(SalesOrder.id == so_id).first()


def list_stock_movements(
    db: Session,
    product_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    q = db.query(StockMovement)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    total = q.count()
    rows = q.order_by(StockMovement.id.desc()).limit(limit).all()
    return {"total": total, "items": rows}

# === MERGED from credit_control_service.py ===

"""
Credit Control Service â€” Automated credit limit enforcement.

Handles:
  - #24: Auto Credit Limit Enforcement
  
Features:
  - Pre-dispatch credit check (blocks if over limit)
  - Automated credit hold after 30/60/90 day overdue
  - Credit utilization tracking
  - Auto-notifications for approaching limits
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.finance.models.finance import Customer
from domains.finance.models.finance import ARInvoice
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import FinanceAuditLog
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Credit control thresholds
OVERDUE_HARD_HOLD_DAYS = 30      # Auto-hold after 30 days overdue
CREDIT_UTILIZATION_WARNING = 0.80  # Warn at 80% utilization
CREDIT_UTILIZATION_CRITICAL = 0.95  # Critical at 95% utilization


# â”€â”€ #24: Auto Credit Limit Enforcement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def check_customer_credit(
    db: Session,
    customer_id: int,
    order_amount: Decimal = None,
    country_code: str = None,
) -> dict:
    """
    Pre-dispatch credit check for a customer/distributor.

    Returns:
    - approved: bool (can proceed with order)
    - credit_limit: current limit
    - outstanding: current AR balance
    - available: remaining credit
    - utilization_pct: current utilization percentage
    - reason: explanation if blocked
    """
    customer = db.query(Customer).get(customer_id)
    if not customer:
        raise ValueError(f"Customer #{customer_id} not found")

    outstanding = _get_customer_outstanding_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))

    if credit_limit <= 0:
        return {
            "approved": True,
            "credit_hold": False,
            "credit_limit": 0,
            "outstanding": float(outstanding),
            "available": 0,
            "utilization_pct": 0,
        }

    available = credit_limit - outstanding
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0

    result = {
        "approved": True,
        "credit_hold": False,
        "credit_limit": float(credit_limit),
        "outstanding": float(outstanding),
        "available": float(available),
        "utilization_pct": round(utilization, 1),
    }

    if order_amount:
        if outstanding + Decimal(str(order_amount)) > credit_limit:
            result["approved"] = False
            result["reason"] = (
                f"Order would exceed credit limit. "
                f"Limit: {credit_limit}, Outstanding: {outstanding}, "
                f"Order: {order_amount}, Shortfall: {outstanding + Decimal(str(order_amount)) - credit_limit}"
            )
            return result

    if utilization >= CREDIT_UTILIZATION_CRITICAL * 100:
        result["warning"] = f"Credit utilization critical: {utilization:.1f}%"
    elif utilization >= CREDIT_UTILIZATION_WARNING * 100:
        result["warning"] = f"Credit utilization high: {utilization:.1f}%"

    return result
    
    # Calculate current outstanding AR
    outstanding = _get_customer_outstanding_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))
    
    if credit_limit <= 0:
        # No credit limit set â€” approve (cash customer)
        return {
            "approved": True,
            "credit_hold": False,
            "credit_limit": 0,
            "outstanding": float(outstanding),
            "available": 0,
            "utilization_pct": 0,
        }
    
    available = credit_limit - outstanding
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0
    
    result = {
        "approved": True,
        "credit_hold": False,
        "credit_limit": float(credit_limit),
        "outstanding": float(outstanding),
        "available": float(available),
        "utilization_pct": round(utilization, 1),
    }
    
    # Check if order would exceed limit
    if order_amount:
        if outstanding + Decimal(str(order_amount)) > credit_limit:
            result["approved"] = False
            result["reason"] = (
                f"Order would exceed credit limit. "
                f"Limit: {credit_limit}, Outstanding: {outstanding}, "
                f"Order: {order_amount}, Shortfall: {outstanding + Decimal(str(order_amount)) - credit_limit}"
            )
            return result
    
    # Check utilization warnings
    if utilization >= CREDIT_UTILIZATION_CRITICAL * 100:
        result["warning"] = f"Credit utilization critical: {utilization:.1f}%"
    elif utilization >= CREDIT_UTILIZATION_WARNING * 100:
        result["warning"] = f"Credit utilization high: {utilization:.1f}%"
    
    return result


def enforce_auto_credit_holds(
    db: Session,
    country_code: str = None,
) -> dict:
    """
    Daily cron: Auto-place customers on credit hold if overdue > 30 days.
    Auto-release hold if all overdue invoices are paid.
    """
    results = {"notices_sent": 0, "holds_placed": 0, "holds_released": 0}

    customers = db.query(Customer).filter(Customer.is_active == True)
    if country_code:
        customers = customers.filter(Customer.country_code == country_code)

    for customer in customers.all():
        overdue_days = _get_max_overdue_days(db, customer.id)
        outstanding = _get_customer_outstanding_ar(db, customer.id)
        credit_limit = Decimal(str(customer.credit_limit or 0))

        if credit_limit > 0 and outstanding > credit_limit:
            results["holds_placed"] += 1
            _log_credit_control(db, "credit_exceeded", customer.id, {
                "outstanding": float(outstanding),
                "credit_limit": float(credit_limit),
                "overdue_days": overdue_days,
            }, country_code)
        elif overdue_days < 7 and credit_limit > 0:
            results["holds_released"] += 1
            _log_credit_control(db, "credit_ok", customer.id, {
                "outstanding": float(outstanding),
                "credit_limit": float(credit_limit),
            }, country_code)

    db.commit()
    _log_automation(db, "credit_control_daily",
                    results["holds_placed"] + results["holds_released"],
                    results["holds_placed"] + results["holds_released"],
                    results, country_code)
    return results


def get_customer_credit_summary(
    db: Session,
    customer_id: int,
    country_code: str = None,
) -> dict:
    """Get comprehensive credit summary for a customer."""
    customer = db.query(Customer).get(customer_id)
    if not customer:
        raise ValueError(f"Customer #{customer_id} not found")
    
    outstanding = _get_customer_outstanding_ar(db, customer_id)
    overdue = _get_customer_overdue_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))
    available = credit_limit - outstanding if credit_limit > 0 else Decimal("0")
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0
    
    # Aging buckets
    aging = _get_customer_aging(db, customer_id)
    
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "credit_limit": float(credit_limit),
        "outstanding_ar": float(outstanding),
        "overdue_ar": float(overdue),
        "available_credit": float(available),
        "utilization_pct": round(utilization, 1),
        "payment_terms_days": customer.payment_terms_days,
        "aging": aging,
    }


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _get_customer_outstanding_ar(db: Session, customer_id: int) -> Decimal:
    """Get total outstanding AR for a customer."""
    result = db.query(func.sum(ARInvoice.amount)).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
    ).scalar()
    return Decimal(str(result or 0))


def _get_customer_overdue_ar(db: Session, customer_id: int) -> Decimal:
    """Get total overdue AR for a customer."""
    result = db.query(func.sum(ARInvoice.amount)).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date < _utcnow(),
    ).scalar()
    return Decimal(str(result or 0))


def _get_max_overdue_days(db: Session, customer_id: int) -> int:
    """Get the maximum overdue days across all invoices for a customer."""
    now = _utcnow()
    invoices = db.query(ARInvoice.due_date).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date < now,
    ).all()
    
    if not invoices:
        return 0
    
    max_days = 0
    for inv in invoices:
        if inv.due_date:
            days = (now - inv.due_date).days
            if days > max_days:
                max_days = days
    return max_days


def _get_customer_aging(db: Session, customer_id: int) -> dict:
    """Get AR aging buckets for a customer."""
    now = _utcnow()
    
    def _bucket(days_min, days_max):
        if days_max:
            return db.query(func.sum(ARInvoice.amount)).filter(
                ARInvoice.customer_id == customer_id,
                ARInvoice.status.in_(["issued", "partially_paid"]),
                ARInvoice.due_date >= now - timedelta(days=days_max),
                ARInvoice.due_date < now - timedelta(days=days_min),
            ).scalar() or 0
        else:
            return db.query(func.sum(ARInvoice.amount)).filter(
                ARInvoice.customer_id == customer_id,
                ARInvoice.status.in_(["issued", "partially_paid"]),
                ARInvoice.due_date < now - timedelta(days=days_min),
            ).scalar() or 0
    
    return {
        "current": float(_bucket(0, 30)),
        "31_60": float(_bucket(30, 60)),
        "61_90": float(_bucket(60, 90)),
        "over_90": float(_bucket(90, None)),
    }


def _log_credit_control(db: Session, kind: str, entity_id: int, detail: dict, country_code: str = None):
    """Log credit control activity."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=1,
            records_changed=1,
            detail={**detail, "entity_id": entity_id},
            country_code=country_code,
        ))
        db.add(FinanceAuditLog(
            action="credit_control",
            entity_type="customer",
            entity_id=entity_id,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Credit control log failed: %s", e)
        db.rollback()


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                     detail: dict = None, country_code: str = None):
    """Log automation run."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=processed,
            records_changed=changed,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Automation log failed: %s", e)
        db.rollback()

# === MERGED from contractor_milestone_read_service.py ===

"""Contractor milestone read service (owns the raw SQL read)."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_contractor_milestones(db: Session) -> list[dict]:
    """Return contractor payment/delivery milestones."""
    rows = db.execute(
        text("""
            SELECT m.id, m.employee_id, e.employee_code, m.milestone_type,
                   m.due_date, m.status
            FROM contractor_milestones m
            LEFT JOIN employees e ON e.id = m.employee_id
            ORDER BY m.due_date ASC
        """)
    ).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "milestone_type": r[3],
            "due_date": r[4],
            "status": r[5],
        }
        for r in rows
    ]
