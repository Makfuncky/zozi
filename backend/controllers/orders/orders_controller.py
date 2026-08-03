"""
Orders Controller — order creation, retrieval, and cancellation business logic.

Totals are computed entirely server-side:
  subtotal     = sum(product.price × qty)
  discount     = coupon reduction (if any)
  vat_amount   = (subtotal − discount) × VAT_RATE  (read from settings)
  shipping     = logistics partner quote → supplier zone fallback → flat-rate fallback
  total_amount = subtotal − discount + vat_amount + shipping_amount

The frontend should NOT compute its own total; it must read order.total_amount
returned from POST /orders/ and pass that order_id to the payment endpoint.
"""
import json
import logging
import random
import string
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Tuple, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from controllers.commerce.coupons_controller import build_coupon_quote
from controllers.commerce.promotion_controller import calculate_order_tier_discount, record_order_tier_ledger
from services.catalog.product_utils import resolve_product_variant
from data.services_orders import (
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    is_checkout_payment_method_allowed,
    normalize_checkout_payment_method,
)
from data.models import (
    LogisticsPartner,
    Notification,
    Order,
    OrderItem,
    Product,
    ReturnRequest,
    Shipment,
    ShipmentConfirmation,
    ShipmentEvent,
    ShippingZone,
    SupplierProfile,
    User,
)
from data.schemas import OrderCreate
from utils.audit_log import audit_log, AuditAction
from data.services_logistics_partner_pricing import normalize_country_code, normalize_pricing_breakdown_payload, parse_dimensions_to_volume_cm3, quote_shipping_for_destination
from services.tax_service import calculate_tax, get_country_config
from utils.config import settings
from utils.constants import STAFF_ROLES
from utils.datetime_utils import utcnow as _utcnow
from utils.money import round_money, to_decimal
from services.orders_write_service import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
)
from utils.order_tracking import build_order_tracking_payload, derive_order_financials, normalize_shipment_event_type, order_status_label, reconcile_order_status, shipment_scan_codes
from utils.redis_client import get_redis
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)


def _generate_order_number() -> str:
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _load_shipments_for_orders(order_ids: list[int], db: Session) -> dict[int, list[Shipment]]:
    if not order_ids:
        return {}

    shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id.in_(order_ids))
        .order_by(Shipment.order_id.asc(), Shipment.created_at.asc(), Shipment.id.asc())
        .all()
    )

    shipments_by_order: dict[int, list[Shipment]] = {}
    for shipment in shipments:
        shipments_by_order.setdefault(cast(int, shipment.order_id), []).append(shipment)
    return shipments_by_order


def _load_events_for_shipments(shipment_ids: list[int], db: Session) -> dict[int, list[ShipmentEvent]]:
    if not shipment_ids:
        return {}

    events = (
        db.query(ShipmentEvent)
        .filter(ShipmentEvent.shipment_id.in_(shipment_ids))
        .order_by(ShipmentEvent.created_at.asc(), ShipmentEvent.id.asc())
        .all()
    )

    events_by_shipment: dict[int, list[ShipmentEvent]] = {}
    for event in events:
        events_by_shipment.setdefault(cast(int, event.shipment_id), []).append(event)
    return events_by_shipment


def _events_for_order(shipments: list[Shipment], events_by_shipment: dict[int, list[ShipmentEvent]]) -> list[ShipmentEvent]:
    events: list[ShipmentEvent] = []
    for shipment in shipments:
        events.extend(events_by_shipment.get(cast(int, shipment.id), []))
    return events


def _build_shipping_address(order: OrderCreate) -> str | None:
    if order.shipping_address:
        if isinstance(order.shipping_address, str):
            return order.shipping_address
        if isinstance(order.shipping_address, dict):
            return json.dumps(order.shipping_address)
        return str(order.shipping_address)
    parts = [order.full_name, order.street, order.city, order.zip, order.country]
    parts = [part.strip() for part in parts if part and part.strip()]
    return ", ".join(parts) if parts else None


def _save_customer_delivery_profile(current_user: dict, order: OrderCreate, db: Session) -> None:
    if not order.save_to_profile:
        return
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        return

    if order.customer_phone is not None:
        cast(Any, user).phone = order.customer_phone.strip() or None

    try:
        current_payload: dict = {}
        if cast(Any, user).address_book:
            try:
                parsed = json.loads(cast(str, cast(Any, user).address_book))
                if isinstance(parsed, dict):
                    current_payload = parsed
            except (TypeError, ValueError):
                current_payload = {}

        current_payload["default_shipping"] = {
            "full_name": (order.full_name or "").strip(),
            "street": (order.street or "").strip(),
            "city": (order.city or "").strip(),
            "zip": (order.zip or "").strip(),
            "country": (order.country or "").strip(),
            "phone": (order.customer_phone or user.phone or "").strip(),
            "delivery_location": (order.delivery_location or "").strip(),
            "delivery_note": (order.delivery_note or "").strip(),
            "shipping_address": _build_shipping_address(order) or "",
        }
        cast(Any, user).address_book = json.dumps(current_payload)
    except AttributeError:
        pass


def _load_products_for_order(order: OrderCreate, db: Session) -> Tuple[Dict[int, Product], Dict[int, int]]:
    if not order.items:
        raise HTTPException(status_code=422, detail="Order must include at least one item")

    requested_quantities: Dict[int, int] = {}
    for item in order.items:
        requested_quantities[item.product_id] = requested_quantities.get(item.product_id, 0) + item.quantity

    # Use SELECT FOR UPDATE to lock the rows and prevent overselling under concurrency
    products = {
        cast(int, cast(Any, product).id): product
        for product in db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id.in_(requested_quantities.keys()),
            Product.is_deleted == False,  # noqa: E712
        ).with_for_update().all()
    }

    for item in order.items:
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        variant = resolve_product_variant(product, item.selected_size, item.selected_color)
        has_variants = bool(getattr(product, "variants", []) or [])
        if has_variants and ((item.selected_size or "").strip() or (item.selected_color or "").strip()) and variant is None:
            raise HTTPException(status_code=422, detail=f"Selected variant is not available for '{product.name}'")

    for product_id, requested_quantity in requested_quantities.items():
        product = products.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        matching_variants = [
            resolve_product_variant(product, item.selected_size, item.selected_color)
            for item in order.items
            if item.product_id == product_id
        ]
        if any(variant is not None for variant in matching_variants):
            variant_stock = 0
            for variant in {variant.id: variant for variant in matching_variants if variant is not None}.values():
                variant_stock += int(cast(Any, variant).stock)
            available_quantity = variant_stock
        else:
            available_quantity = cast(int, cast(Any, product).stock)
        if available_quantity < requested_quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for '{product.name}': available {available_quantity}, requested {requested_quantity}",
            )

    return products, requested_quantities


def _resolve_destination_country(order: OrderCreate) -> str:
    if order.country and order.country.strip():
        return normalize_country_code(order.country)

    if order.shipping_address and "," in order.shipping_address:
        suffix = order.shipping_address.split(",")[-1].strip()
        return normalize_country_code(suffix)

    return ""


def _resolve_destination_city(order: OrderCreate) -> str:
    if order.city and order.city.strip():
        return order.city.strip()

    if order.shipping_address and "," in order.shipping_address:
        parts = [part.strip() for part in order.shipping_address.split(",") if part.strip()]
        if len(parts) >= 3:
            return parts[-3]
        if parts:
            return parts[0]

    return ""


def _zone_country_codes(zone: ShippingZone) -> set[str]:
    countries_json = cast(str | None, getattr(zone, "countries"))
    if not countries_json:
        return set()
    try:
        values = json.loads(countries_json)
    except (TypeError, ValueError):
        return set()
    if not isinstance(values, list):
        return set()
    return {normalize_country_code(str(value)) for value in values if value}


def _group_supplier_totals(
    order: OrderCreate,
    products: Dict[int, Product],
    db: Session,
) -> Dict[int, Dict[str, Any]]:
    supplier_totals: Dict[int, Dict[str, Any]] = {}
    for item in order.items:
        product = products[item.product_id]
        supplier_id = cast(int, cast(Any, product).supplier_id or 0)
        if supplier_id <= 0:
            continue

        supplier_bucket = supplier_totals.setdefault(
            supplier_id,
            {
                "subtotal": Decimal("0"),
                "weight_kg": Decimal("0"),
                "volume_cm3": Decimal("0"),
                "categories": set(),
                "items": [],
                "supplier_city": None,
            },
        )

        variant = resolve_product_variant(product, item.selected_size, item.selected_color)
        unit_price = to_decimal(getattr(variant, "price", None) or cast(Any, product).price)
        line_subtotal = unit_price * item.quantity
        supplier_bucket["subtotal"] += line_subtotal

        weight = to_decimal(cast(Any, product).weight or 0)
        if weight > 0:
            supplier_bucket["weight_kg"] += weight * item.quantity

        volume_cm3 = parse_dimensions_to_volume_cm3(cast(str | None, getattr(product, "dimensions", None)))
        if volume_cm3 > 0:
            supplier_bucket["volume_cm3"] += volume_cm3 * item.quantity

        category = str(getattr(product, "category", "") or "").strip()
        if category:
            cast(set[str], supplier_bucket["categories"]).add(category)

        cast(list[dict[str, Any]], supplier_bucket["items"]).append(
            {
                "product_id": cast(int, getattr(product, "id")),
                "quantity": int(item.quantity),
                "category": category or None,
                "weight_kg": float(round_money(weight * item.quantity)) if weight > 0 else 0.0,
                "volume_cm3": float(round_money(volume_cm3 * item.quantity)) if volume_cm3 > 0 else 0.0,
            }
        )

    if supplier_totals:
        supplier_profiles = {
            cast(int, profile.user_id): profile
            for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_totals.keys())).all()
        }
        for supplier_id, metrics in supplier_totals.items():
            profile = supplier_profiles.get(supplier_id)
            metrics["supplier_city"] = str(getattr(profile, "city", "") or "").strip() or None
            metrics["categories"] = sorted(cast(set[str], metrics["categories"]))

    return supplier_totals


def _calculate_supplier_zone_shipping(
    zone: ShippingZone,
    supplier_subtotal: Decimal,
    supplier_weight_kg: Decimal,
) -> Decimal:
    free_above = to_decimal(zone.free_shipping_above or 0)
    if zone.free_shipping_above is not None and supplier_subtotal >= free_above:
        return round_money(0)

    base_price = to_decimal(zone.base_price or 0)
    price_per_kg = to_decimal(zone.price_per_kg or 0)
    return round_money(base_price + (price_per_kg * supplier_weight_kg))


def _calculate_fallback_shipping(subtotal_after_discount: Decimal) -> Decimal:
    threshold = to_decimal(settings.free_shipping_threshold)
    if threshold > 0 and subtotal_after_discount >= threshold:
        return round_money(0)
    return round_money(settings.shipping_flat_rate)


def _quote_supplier_groups(
    *,
    supplier_totals: Dict[int, Dict[str, Any]],
    destination_country: str,
    destination_city: str,
    db: Session,
) -> Tuple[Decimal, list[dict[str, Any]]]:
    if not supplier_totals:
        return Decimal("0"), []

    supplier_ids = list(supplier_totals.keys())
    zones = (
        db.query(ShippingZone)
        .filter(
            ShippingZone.supplier_id.in_(supplier_ids),
            ShippingZone.is_active == True,  # noqa: E712
        )
        .all()
    )

    zones_by_supplier: Dict[int, List[ShippingZone]] = {}
    for zone in zones:
        if destination_country in _zone_country_codes(zone):
            zones_by_supplier.setdefault(cast(int, zone.supplier_id), []).append(zone)

    shipping_total = Decimal("0")
    shipment_quotes: list[dict[str, Any]] = []
    for supplier_id, metrics in sorted(supplier_totals.items(), key=lambda item: item[0]):
        supplier_subtotal = round_money(metrics["subtotal"])
        supplier_weight_kg = round_money(metrics["weight_kg"])
        supplier_volume_cm3 = round_money(cast(Decimal, metrics["volume_cm3"]))
        supplier_zones = zones_by_supplier.get(supplier_id, [])
        categories = cast(list[str], metrics["categories"])
        supplier_city = cast(str | None, metrics["supplier_city"])

        approved_partner_quote = quote_shipping_for_destination(
            db,
            country=destination_country,
            city=destination_city,
            supplier_city=supplier_city,
            total_weight_kg=supplier_weight_kg,
            categories=categories,
            total_volume_cm3=supplier_volume_cm3,
            pickup_count=1,
            dropoff_count=1,
        )
        if approved_partner_quote is not None:
            shipping_amount = round_money(approved_partner_quote["shipping_amount"])
            shipping_total += shipping_amount
            service_area = approved_partner_quote.get("service_area") or {}
            shipment_quotes.append(
                {
                    "supplier_id": supplier_id,
                    "source": "approved_logistics_partner",
                    "supplier_city": supplier_city,
                    "partner_id": approved_partner_quote.get("partner_id"),
                    "partner_name": approved_partner_quote.get("partner_name"),
                    "partner_code": approved_partner_quote.get("partner_code"),
                    "service_area_id": service_area.get("id"),
                    "service_area": service_area,
                    "estimated_delivery_min": service_area.get("delivery_days_min"),
                    "estimated_delivery_max": service_area.get("delivery_days_max"),
                    "shipping_amount": float(shipping_amount),
                    "currency": approved_partner_quote.get("currency") or settings.default_currency,
                    "pricing_profile": approved_partner_quote.get("pricing_profile"),
                    "category_rules": approved_partner_quote.get("category_rules") or [],
                    "vehicle_rule": approved_partner_quote.get("vehicle_rule"),
                    "pricing_breakdown": approved_partner_quote.get("pricing_breakdown"),
                    "categories": categories,
                    "total_weight_kg": float(supplier_weight_kg),
                    "total_volume_cm3": float(supplier_volume_cm3),
                }
            )
            continue

        if supplier_zones:
            zone_costs = [
                _calculate_supplier_zone_shipping(zone, supplier_subtotal, supplier_weight_kg)
                for zone in supplier_zones
            ]
            shipping_amount = min(zone_costs)
            selected_zone = supplier_zones[zone_costs.index(shipping_amount)]
            shipping_total += shipping_amount
            shipment_quotes.append(
                {
                    "supplier_id": supplier_id,
                    "source": "supplier_shipping_zone",
                    "supplier_city": supplier_city,
                    "partner_id": None,
                    "partner_name": None,
                    "partner_code": None,
                    "service_area_id": None,
                    "service_area": None,
                    "estimated_delivery_min": None,
                    "estimated_delivery_max": None,
                    "shipping_amount": float(shipping_amount),
                    "currency": settings.default_currency,
                    "pricing_profile": None,
                    "category_rules": [],
                    "vehicle_rule": None,
                    "pricing_breakdown": normalize_pricing_breakdown_payload({
                        "source": "supplier_shipping_zone",
                        "zone_id": cast(int, getattr(selected_zone, "id")),
                        "base_fee": float(round_money(to_decimal(getattr(selected_zone, "base_price", 0) or 0))),
                        "pickup_fee": 0.0,
                        "dropoff_fee": 0.0,
                        "weight_fee": float(round_money(to_decimal(getattr(selected_zone, "price_per_kg", 0) or 0) * supplier_weight_kg)),
                        "distance_fee": 0.0,
                        "handling_fee": 0.0,
                        "load_fit_factor": 1.0,
                        "load_fit_adjustment_amount": 0.0,
                        "surcharge_factor": 1.0,
                        "surcharge_amount": 0.0,
                        "weight_discount_amount": 0.0,
                        "shipping_amount": float(shipping_amount),
                    }),
                    "categories": categories,
                    "total_weight_kg": float(supplier_weight_kg),
                    "total_volume_cm3": float(supplier_volume_cm3),
                }
            )
        else:
            shipping_amount = _calculate_fallback_shipping(supplier_subtotal)
            shipping_total += shipping_amount
            shipment_quotes.append(
                {
                    "supplier_id": supplier_id,
                    "source": "fallback_flat_rate",
                    "supplier_city": supplier_city,
                    "partner_id": None,
                    "partner_name": None,
                    "partner_code": None,
                    "service_area_id": None,
                    "service_area": None,
                    "estimated_delivery_min": None,
                    "estimated_delivery_max": None,
                    "shipping_amount": float(shipping_amount),
                    "currency": settings.default_currency,
                    "pricing_profile": None,
                    "category_rules": [],
                    "vehicle_rule": None,
                    "pricing_breakdown": normalize_pricing_breakdown_payload({
                        "source": "fallback_flat_rate",
                        "base_fee": float(shipping_amount),
                        "pickup_fee": 0.0,
                        "dropoff_fee": 0.0,
                        "weight_fee": 0.0,
                        "distance_fee": 0.0,
                        "handling_fee": 0.0,
                        "load_fit_factor": 1.0,
                        "load_fit_adjustment_amount": 0.0,
                        "surcharge_factor": 1.0,
                        "surcharge_amount": 0.0,
                        "weight_discount_amount": 0.0,
                        "shipping_amount": float(shipping_amount),
                    }),
                    "categories": categories,
                    "total_weight_kg": float(supplier_weight_kg),
                    "total_volume_cm3": float(supplier_volume_cm3),
                }
            )

    return round_money(shipping_total), shipment_quotes


def _calculate_shipping(
    subtotal_after_discount: Decimal,
    order: OrderCreate,
    products: Dict[int, Product],
    db: Session,
) -> Tuple[Decimal, list[dict[str, Any]]]:
    """
    Flat-rate shipping model:
    - Free when subtotal_after_discount >= settings.free_shipping_threshold
    - settings.shipping_flat_rate otherwise

    Zone-aware model:
    - If destination country and supplier shipping zones are configured, sum per-supplier
      shipping based on zone base price + weight.
    - Fall back to flat-rate logic per supplier when no zone match exists.

    Returns (shipping_amount, shipment_quotes).
    """
    if settings.app_env == "test":
        return round_money(0), []

    destination_country = _resolve_destination_country(order)
    destination_city = _resolve_destination_city(order)
    supplier_totals = _group_supplier_totals(order, products, db)
    if not supplier_totals:
        return _calculate_fallback_shipping(subtotal_after_discount), []
    return _quote_supplier_groups(
        supplier_totals=supplier_totals,
        destination_country=destination_country,
        destination_city=destination_city,
        db=db,
    )


def _resolve_order_level_logistics_fields(shipment_quotes: list[dict[str, Any]]) -> tuple[int | None, int | None, int | None, int | None]:
    partner_ids = {int(quote["partner_id"]) for quote in shipment_quotes if quote.get("partner_id") is not None}
    service_area_ids = {int(quote["service_area_id"]) for quote in shipment_quotes if quote.get("service_area_id") is not None}
    delivery_mins = [int(quote["estimated_delivery_min"]) for quote in shipment_quotes if quote.get("estimated_delivery_min") is not None]
    delivery_maxes = [int(quote["estimated_delivery_max"]) for quote in shipment_quotes if quote.get("estimated_delivery_max") is not None]
    return (
        next(iter(partner_ids)) if len(partner_ids) == 1 else None,
        next(iter(service_area_ids)) if len(service_area_ids) == 1 else None,
        min(delivery_mins) if delivery_mins else None,
        max(delivery_maxes) if delivery_maxes else None,
    )


def _calculate_order_amounts(
    order: OrderCreate,
    current_user: dict,
    db: Session,
) -> Tuple[
    Dict[int, Product],
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    str,
    str,
    str | None,
    list[dict[str, Any]],
    Any | None,
    Decimal,
]:
    """
        Returns: (
            products,
            subtotal,
            discount_amount,
            tax_amount,
            vat_amount,
            shipping_amount,
            total_amount,
            country_code,
            currency,
            tax_type,
            coupon_code,
            shipment_quotes,
            applied_tier,
            tier_discount,
        )

    Tax is computed server-side using country configuration when available.
    Falls back to legacy VAT settings when country config is unavailable.
    Shipping uses a flat-rate model: free above settings.free_shipping_threshold.
    shipment_quotes contains per-supplier logistics resolution details.
    """
    products, _ = _load_products_for_order(order, db)

    subtotal = round_money(
        sum(
            (
                to_decimal(getattr(resolve_product_variant(products[item.product_id], item.selected_size, item.selected_color), "price", None) or cast(Any, products[item.product_id]).price)
                * item.quantity
                for item in order.items
            ),
            Decimal("0"),
        )
    )

    discount_amount = Decimal("0.00")
    tier_discount = Decimal("0.00")
    applied_tier = None
    coupon_code = None
    if order.coupon_code and order.coupon_code.strip():
        coupon_quote = build_coupon_quote(order.coupon_code, subtotal, db)
        discount_amount = round_money(coupon_quote["discount_amount"])
        coupon_code = coupon_quote["code"]

    coupon_adjusted_subtotal = round_money(subtotal - discount_amount)
    try:
        tier_discount, applied_tier = calculate_order_tier_discount(coupon_adjusted_subtotal, db)
    except Exception:
        logger.exception("Failed to evaluate tier discount, proceeding without tier promotion")
        tier_discount = Decimal("0.00")
        applied_tier = None

    discount_amount = round_money(discount_amount + tier_discount)
    after_discount = round_money(subtotal - discount_amount)

    country_code = normalize_country_code(order.country or current_user.get("preferred_country") or "OM") or "OM"
    currency = str(current_user.get("preferred_currency") or settings.default_currency)

    try:
        from services.cross_border_detection import CrossBorderDetectionMiddleware
        cb = CrossBorderDetectionMiddleware(db)
        user_id = current_user.get("id")
        home_country = current_user.get("country_code") or country_code
        result = cb.detect_cross_border_session(user_id, home_country, country_code)
        if result:
            logger.info(
                f"Cross-border checkout: user {user_id} from {home_country} -> {country_code}"
            )
            # Persist cross-country session
            try:
                from data.models_country_enhancements import CrossCountryCustomerSession
                session = CrossCountryCustomerSession(
                    user_id=user_id,
                    source_country_code=home_country,
                    target_country_code=country_code,
                    ip_address=current_user.get("ip_address", ""),
                    conversion=True,
                )
                add_and_flush(db, session)
            except Exception as persist_err:
                logger.debug("Cross-country session persist skipped: %s", persist_err)
    except Exception as exc:
        logger.debug("Cross-border detection skipped: %s", exc)

    tax_type = "VAT"
    tax_amount = Decimal("0.00")
    vat_amount = Decimal("0.00")
    primary_category: str | None = None
    categories = {
        str(getattr(products[item.product_id], "category", "") or "").strip().lower()
        for item in order.items
    }
    categories.discard("")
    if len(categories) == 1:
        primary_category = next(iter(categories))

    try:
        tax_preview = calculate_tax(after_discount, country_code, db, category=primary_category)
        tax_type = str(tax_preview.get("tax_type") or "VAT").upper()
        currency = str(tax_preview.get("currency") or currency)
        tax_amount = round_money(to_decimal(tax_preview.get("tax_amount") or 0))
        vat_amount = tax_amount if tax_type == "VAT" else Decimal("0.00")
    except Exception:
        # Backward compatibility for environments without country config rows.
        vat_rate = to_decimal(settings.vat_rate if settings.app_env != "test" else 0)
        vat_amount = round_money(after_discount * vat_rate)
        tax_amount = vat_amount
        tax_type = "VAT"

    shipping_amount, shipment_quotes = _calculate_shipping(after_discount, order, products, db)
    total_amount = round_money(after_discount + tax_amount + shipping_amount)

    return (
        products,
        subtotal,
        discount_amount,
        tax_amount,
        vat_amount,
        shipping_amount,
        total_amount,
        country_code,
        currency,
        tax_type,
        coupon_code,
        shipment_quotes,
        applied_tier,
        tier_discount,
    )


def create_order(order: OrderCreate, current_user: dict, db: Session, request: Any = None) -> Order:
    products, subtotal, discount_amount, tax_amount, vat_amount, shipping_amount, total_amount, country_code, currency, tax_type, coupon_code, shipment_quotes, applied_tier, tier_discount = (
        _calculate_order_amounts(order, current_user, db)
    )
    payment_method = normalize_checkout_payment_method(order.payment_method)
    if not is_checkout_payment_method_allowed(payment_method, db, country_code):
        raise HTTPException(status_code=422, detail="payment_method must be one of: cod, card, tap, paytabs, or a configured gateway")

    fraud_score = 0
    fraud_action = "allow"
    if total_amount and float(total_amount) > 500:
        try:
            redis_client = get_redis()
            fraud_engine = FraudScoringEngine(db, redis_client)
            device_hash = getattr(request.state, "device_fingerprint", None) if request else None
            score_result = fraud_engine.calculate_score(
                user_id=current_user["id"],
                ip_address=get_request_ip(request),
                device_hash=device_hash,
                event_type="checkout",
                amount=float(total_amount),
                additional_signals={
                    "is_cod": payment_method == "cod",
                    "is_new_account": current_user.get("created_at", "").startswith("2025") or current_user.get("created_at", "").startswith("2026"),
                }
            )
            fraud_score = score_result.get("score", 0)
            fraud_action = score_result.get("action", "allow")
            
            if score_result.get("is_blocked"):
                raise HTTPException(status_code=403, detail="Order blocked by fraud detection system")
        except Exception as e:
            logger.warning(f"Fraud scoring error: {e}")

    payment_snapshot = build_order_payment_snapshot(payment_method, total_amount, db, country_code)

    initial_status = "confirmed" if payment_method == "cod" else "pending"

    selected_partner_id, selected_service_area_id, estimated_delivery_min, estimated_delivery_max = _resolve_order_level_logistics_fields(shipment_quotes)

    db_order = Order(
        user_id=current_user["id"],
        customer_id=current_user["id"],
        order_number=_generate_order_number(),
        currency=currency,
        subtotal_amount=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        vat_amount=vat_amount,
        shipping_amount=shipping_amount,
        total_amount=total_amount,
        coupon_code=coupon_code,
        payment_method=payment_method,
        payment_gateway_code=payment_snapshot["payment_gateway_code"],
        payment_gateway_fee_amount=payment_snapshot["payment_gateway_fee_amount"],
        payment_customer_total_amount=payment_snapshot["payment_customer_total_amount"],
        payment_gateway_fee_passed_to_customer=payment_snapshot["payment_gateway_fee_passed_to_customer"],
        status=initial_status,
        shipping_address=_build_shipping_address(order),
        shipping_city=(order.city or "").strip() or None,
        shipping_country=(order.country or country_code or "").strip() or None,
        shipping_postal_code=(order.zip or "").strip() or None,
        customer_phone=(order.customer_phone or "").strip() or None,
        delivery_location=(order.delivery_location or "").strip() or None,
        delivery_note=(order.delivery_note or "").strip() or None,
        selected_partner_id=selected_partner_id,
        selected_service_area_id=selected_service_area_id,
        estimated_delivery_min=estimated_delivery_min,
        estimated_delivery_max=estimated_delivery_max,
        fraud_score=fraud_score,
        fraud_action=fraud_action,
        country_code=country_code,
    )
    add_and_flush(db, db_order)

    for item in order.items:
        product = products[item.product_id]
        variant = resolve_product_variant(product, item.selected_size, item.selected_color)
        unit_price = round_money(getattr(variant, "price", None) or cast(Any, product).price)
        # Stock is decremented later during payment confirmation
        # (via _finalize_inventory_for_paid_order), not at order creation time.
        # For COD orders this happens immediately via confirm_cash_on_delivery_order.
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            variant_id=cast(int | None, getattr(variant, "id", None)) if variant is not None else None,
            supplier_id=cast(Any, product).supplier_id,
            product_name=cast(Any, product).name,
            product_image=cast(Any, getattr(product, "image_url", None)),
            quantity=item.quantity,
            unit_price=unit_price,
            total_price=round_money(unit_price * item.quantity),
            price=unit_price,
            selected_size=(item.selected_size or "").strip(),
            selected_color=(item.selected_color or "").strip(),
        )
        add_and_flush(db, db_item)

    if applied_tier is not None and tier_discount > 0:
        record_order_tier_ledger(
            order_id=cast(int, cast(Any, db_order).id),
            user_id=current_user.get("id"),
            tier=applied_tier,
            discount_amount=tier_discount,
            db=db,
        )

    _save_customer_delivery_profile(current_user, order, db)

    if payment_method == "cod":
        confirm_cash_on_delivery_order(db_order, db)

    commit_and_refresh(db, db_order)
    _ = list(db_order.items)
    audit_log(
        db=db,
        action=AuditAction.ORDER_CREATED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="order",
        resource_id=cast(int, cast(Any, db_order).id),
        details={
            "subtotal": db_order.subtotal_amount,
            "discount": db_order.discount_amount,
            "tax": db_order.tax_amount,
            "vat": db_order.vat_amount,
            "shipping": db_order.shipping_amount,
            "total": db_order.total_amount,
            "country_code": country_code,
            "currency": currency,
            "tax_type": tax_type,
            "coupon_code": db_order.coupon_code,
            "tier_discount": float(tier_discount),
            "tier_name": getattr(applied_tier, "tier_name", None) if applied_tier is not None else None,
            "payment_method": db_order.payment_method,
            "payment_gateway_code": db_order.payment_gateway_code,
            "payment_gateway_fee_amount": db_order.payment_gateway_fee_amount,
            "payment_customer_total_amount": db_order.payment_customer_total_amount,
            "payment_gateway_fee_passed_to_customer": db_order.payment_gateway_fee_passed_to_customer,
            "status": db_order.status,
        },
        status="success",
    )
    try:
        from services.transactional_email_service import enqueue_order_created_email

        enqueue_order_created_email(cast(int, cast(Any, db_order).id))
    except Exception:
        logger.exception("Failed to enqueue order-created email for order %s", cast(Any, db_order).id)
    return db_order


def preview_order(order: OrderCreate, current_user: dict, db: Session) -> dict[str, Any]:
    (
        _products,
        subtotal,
        discount_amount,
        tax_amount,
        vat_amount,
        shipping_amount,
        total_amount,
        country_code,
        currency,
        tax_type,
        coupon_code,
        shipment_quotes,
        _applied_tier,
        _tier_discount,
    ) = _calculate_order_amounts(order, current_user, db)

    payment_method = normalize_checkout_payment_method(order.payment_method)
    if not is_checkout_payment_method_allowed(payment_method, db, country_code):
        raise HTTPException(status_code=422, detail="payment_method must be one of: cod, card, tap, paytabs, thawani, or a configured gateway")

    payment_snapshot = build_order_payment_snapshot(payment_method, total_amount, db, country_code)
    amount_after_discount = round_money(subtotal - discount_amount)
    country_id: int | None = None
    country_name: str | None = None
    tax_name = tax_type
    tax_rate = Decimal("0.00")
    is_inclusive = False

    try:
        tax_preview = calculate_tax(amount_after_discount, country_code, db)
        tax_name = str(tax_preview.get("tax_name") or tax_type)
        tax_rate = to_decimal(tax_preview.get("tax_rate") or 0)
        is_inclusive = bool(tax_preview.get("is_inclusive") or False)
        currency = str(tax_preview.get("currency") or currency)
    except Exception:
        tax_rate = to_decimal(settings.vat_rate if settings.app_env != "test" else 0)

    try:
        country_config = get_country_config(db, country_code)
        country_id = cast(int | None, getattr(country_config, "id", None))
        country_name = cast(str | None, getattr(country_config, "name", None))
    except Exception:
        country_id = None
        country_name = None

    return {
        "subtotal_amount": float(subtotal),
        "discount_amount": float(discount_amount),
        "tax_amount": float(tax_amount),
        "vat_amount": float(vat_amount),
        "shipping_amount": float(shipping_amount),
        "total_amount": float(total_amount),
        "currency": currency,
        "coupon_code": coupon_code,
        "payment_method": payment_method,
        "payment_gateway_code": payment_snapshot["payment_gateway_code"],
        "payment_gateway_fee_amount": float(payment_snapshot["payment_gateway_fee_amount"]),
        "payment_customer_total_amount": float(payment_snapshot["payment_customer_total_amount"]),
        "payment_gateway_fee_passed_to_customer": bool(payment_snapshot["payment_gateway_fee_passed_to_customer"]),
        "country_id": country_id,
        "country_code": country_code,
        "country_name": country_name,
        "shipment_groups": [normalize_pricing_breakdown_payload(quote) for quote in shipment_quotes],
        "tax_breakdown": {
            "country_id": country_id,
            "country_code": country_code,
            "country_name": country_name,
            "tax_type": tax_type,
            "tax_name": tax_name,
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amount),
            "vat_amount": float(vat_amount),
            "is_inclusive": is_inclusive,
            "currency": currency,
        },
    }


def get_orders(current_user: dict, db: Session, *, skip: int = 0, limit: int = 50) -> List[Order]:
    orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.user_id == current_user["id"])
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
        .all()
    )
    order_ids = [cast(int, order.id) for order in orders]
    shipments_by_order = _load_shipments_for_orders(order_ids, db)
    shipment_ids = [cast(int, shipment.id) for shipments in shipments_by_order.values() for shipment in shipments]
    events_by_shipment = _load_events_for_shipments(shipment_ids, db)
    updated = False
    for order in orders:
        shipments = shipments_by_order.get(cast(int, order.id), [])
        events = _events_for_order(shipments, events_by_shipment)
        reconciled_status = reconcile_order_status(order, shipments)
        if order.status != reconciled_status:
            order.status = reconciled_status
            updated = True
        setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
    if updated:
        commit_only(db)
    return orders


def get_order(order_id: int, current_user: dict, db: Session) -> Order:
    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(
            Order.id == order_id,
            Order.user_id == current_user["id"],
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    shipments_by_order = _load_shipments_for_orders([cast(int, order.id)], db)
    shipments = shipments_by_order.get(cast(int, order.id), [])
    shipment_ids = [cast(int, shipment.id) for shipment in shipments]
    events_by_shipment = _load_events_for_shipments(shipment_ids, db)
    events = _events_for_order(shipments, events_by_shipment)
    reconciled_status = reconcile_order_status(order, shipments)
    if order.status != reconciled_status:
        order.status = reconciled_status
        commit_and_refresh(db, order)
    setattr(order, "status_label", order_status_label(reconciled_status, shipments, events))
    return order


def _supplier_can_access_order(order: Order, supplier_id: int) -> bool:
    for item in order.items:
        if item.product and item.product.supplier_id == supplier_id:
            return True
    return False


def _get_logistics_partner_for_user(user_id: int | None, db: Session) -> LogisticsPartner:
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    if not partner:
        raise HTTPException(status_code=403, detail="No logistics partner profile found")
    return partner


def _build_supply_chain_timeline(shipments: list[Shipment], events: list[ShipmentEvent], order_status: str) -> list[dict]:
    stage_order = ["supplier", "warehouse", "in_transit", "delivered"]
    stage_labels = {
        "supplier": "Prepared for Pickup",
        "warehouse": "Picked From Supplier",
        "in_transit": "Out for Delivery",
        "delivered": "Customer Receiving Confirmed",
    }
    event_to_stage = {
        "supplier_prepared": "supplier",
        "pickup_confirmed": "supplier",
        "pickup_cancelled": "supplier",
        "picked_from_supplier": "warehouse",
        "logistics_received": "warehouse",
        "distribution_checkpoint": "in_transit",
        "out_for_delivery": "in_transit",
        "customer_received": "delivered",
        "status_manual_update": None,
    }

    timeline: dict[str, dict] = {
        stage: {
            "stage": stage,
            "label": stage_labels[stage],
            "timestamp": None,
            "notes": None,
            "completed": False,
        }
        for stage in stage_order
    }

    # Build from immutable events first.
    for event in events:
        event_type = normalize_shipment_event_type(event)
        event_status_after = cast(str | None, getattr(event, "status_after"))
        event_created_at = cast(datetime | None, getattr(event, "created_at"))
        event_location = cast(str | None, getattr(event, "location"))
        event_notes = cast(str | None, getattr(event, "notes"))
        mapped = event_to_stage.get(event_type)
        if not mapped and event_status_after in {"shipped", "in_transit"}:
            mapped = "in_transit"
        if not mapped and event_status_after == "delivered":
            mapped = "delivered"
        if not mapped:
            continue
        entry = timeline[mapped]
        entry["completed"] = True
        if not entry["timestamp"]:
            entry["timestamp"] = event_created_at.isoformat() if event_created_at else None
        if event_location:
            entry["notes"] = f"{event_location}" if not entry["notes"] else f"{entry['notes']} · {event_location}"
        elif event_notes and not entry["notes"]:
            entry["notes"] = event_notes

    # Fill from shipment status if events missing.
    for shipment in shipments:
        shipment_status = cast(str, getattr(shipment, "status"))
        shipped_at = cast(datetime | None, getattr(shipment, "shipped_at"))
        current_hub = cast(str | None, getattr(shipment, "current_hub"))
        updated_at = cast(datetime | None, getattr(shipment, "updated_at"))
        distribution_channel = cast(str | None, getattr(shipment, "distribution_channel"))
        actual_delivery = cast(datetime | None, getattr(shipment, "actual_delivery"))
        if shipment_status in {"processing", "picking_up", "shipped", "in_transit", "delivered"}:
            timeline["supplier"]["completed"] = True
            if shipped_at and not timeline["supplier"]["timestamp"]:
                timeline["supplier"]["timestamp"] = shipped_at.isoformat()

        if current_hub:
            timeline["warehouse"]["completed"] = True
            timeline["warehouse"]["notes"] = current_hub
            if updated_at and not timeline["warehouse"]["timestamp"]:
                timeline["warehouse"]["timestamp"] = updated_at.isoformat()

        if shipment_status in {"shipped", "in_transit", "delivered"}:
            timeline["in_transit"]["completed"] = True
            if shipped_at and not timeline["in_transit"]["timestamp"]:
                timeline["in_transit"]["timestamp"] = shipped_at.isoformat()
            if distribution_channel:
                timeline["in_transit"]["notes"] = distribution_channel

        if shipment_status == "delivered":
            timeline["delivered"]["completed"] = True
            if actual_delivery and not timeline["delivered"]["timestamp"]:
                timeline["delivered"]["timestamp"] = actual_delivery.isoformat()

    # Fallback by order status.
    if order_status == "delivered":
        timeline["delivered"]["completed"] = True

    return [timeline[stage] for stage in stage_order]


def get_order_invoice(order_id: int, current_user: dict, db: Session) -> dict:
    order = (
        db.query(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.shipments).selectinload(Shipment.carrier),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    role = current_user.get("role")
    user_id = current_user.get("id")
    if role in STAFF_ROLES:
        pass
    elif role == "supplier":
        if not _supplier_can_access_order(order, user_id):
            raise HTTPException(status_code=403, detail="You do not have access to this order invoice")
    elif order.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this order invoice")

    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).order_by(Shipment.created_at.asc()).all()
    shipment_ids = [shipment.id for shipment in shipments]
    events = (
        db.query(ShipmentEvent)
        .filter(ShipmentEvent.shipment_id.in_(shipment_ids))
        .order_by(ShipmentEvent.created_at.asc())
        .all()
        if shipment_ids
        else []
    )

    supplier_ids = sorted({item.product.supplier_id for item in order.items if item.product and item.product.supplier_id})
    suppliers = (
        db.query(User).filter(User.id.in_(supplier_ids)).all()
        if supplier_ids
        else []
    )
    supplier_map = {supplier.id: supplier for supplier in suppliers}

    if len(suppliers) == 1:
        supplier_name = suppliers[0].username
        supplier_email = suppliers[0].email
    elif len(suppliers) > 1:
        supplier_name = "Multiple Suppliers"
        supplier_email = None
    else:
        supplier_name = "Unknown Supplier"
        supplier_email = None

    customer = order.user
    customer_name = customer.username if customer else f"Customer #{order.user_id}"
    customer_email = customer.email if customer else ""

    items_payload = []
    for item in order.items:
        supplier_user = supplier_map.get(item.product.supplier_id) if item.product else None
        unit_price = float(to_decimal(item.price))
        qty = int(item.quantity or 0)
        items_payload.append(
            {
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else f"Product #{item.product_id}",
                "quantity": qty,
                "unit_price": unit_price,
                "total": float(round_money(to_decimal(item.price) * qty)),
                "supplier_id": item.product.supplier_id if item.product else None,
                "supplier_name": supplier_user.username if supplier_user else None,
            }
        )

    primary_shipment = shipments[0] if shipments else None
    timeline = _build_supply_chain_timeline(shipments, events, order.status)
    order_created_at = cast(datetime | None, getattr(order, "created_at"))
    financials = derive_order_financials(order)

    return {
        "id": order.id,
        "invoice_number": f"INV-{order.id}",
        "order_id": order.id,
        "created_at": order_created_at.isoformat() if order_created_at else None,
        "status": order.status,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_address": order.shipping_address,
        "supplier_name": supplier_name,
        "supplier_email": supplier_email,
        "items": items_payload,
        "subtotal": financials["subtotal"],
        "vat": financials["vat"],
        "shipping": financials["shipping"],
        "total": financials["total"],
        "logistics": timeline,
        "tracking_number": primary_shipment.tracking_number if primary_shipment else order.tracking_number,
        "carrier": (
            primary_shipment.carrier_name
            or (primary_shipment.carrier.name if primary_shipment and primary_shipment.carrier else None)
            if primary_shipment
            else None
        ),
        "distribution_channels": [
            channel
            for channel in {
                cast(str | None, getattr(shipment, "distribution_channel"))
                for shipment in shipments
                if cast(str | None, getattr(shipment, "distribution_channel"))
            }
        ],
        "scan_codes": [shipment.scan_code or f"SHIP-{shipment.id}" for shipment in shipments],
    }


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
    add_and_flush(db, event)

    reconciled_status = reconcile_order_status(order, shipments)
    order.status = reconciled_status
    if reconciled_status == "delivered" and not getattr(order, "delivered_at", None):
        order.delivered_at = now

    commit_and_refresh(db, order)

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
        commit_and_refresh(db, order)

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
        add_and_flush(db, 
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
                    from services.cash_management_service import create_settlements_on_delivery
                    create_settlements_on_delivery(order, db)
                except Exception:
                    logger.exception("Failed to create settlements for delivered order %s", order.id)

        if confirmation.requester_user_id is not None:
            add_and_flush(db, 
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
            add_and_flush(db, 
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

    commit_and_refresh(db, confirmation)
    if decision == "accepted":
        try:
            from services.transactional_email_service import enqueue_shipment_status_email

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

    add_and_flush(db, 
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
    add_and_flush(db, 
        Notification(
            user_id=order.user_id,
            type="order_update",
            title="Delivery Confirmed",
            message=f"Order #{order.id} has been confirmed as received.",
            link=f"/orders/{order.id}",
        )
    )

    commit_only(db)
    return {
        "message": "Receipt confirmed",
        "order_id": order.id,
        "shipment_id": matched.id,
        "status": order.status,
    }


def cancel_order(order_id: int, current_user: dict, db: Session) -> Order:
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel order in '{order.status}' status. Only pending or confirmed orders can be cancelled.",
        )
    apply_order_status_change(order, "cancelled", db)
    add_and_flush(db, 
        Notification(
            user_id=order.user_id,
            type="order_update",
            title="Order Cancelled",
            message=f"Order #{order.id} has been cancelled.",
            link=f"/orders/{order.id}",
        )
    )
    commit_and_refresh(db, order)
    setattr(order, "status_label", order_status_label(order.status, [], []))
    return order

