"""
Cart Shipping Service — handles cart quote calculations and related operations.
"""
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from data.schemas import OrderCreate
from services.logistics.logistics_partner_pricing import normalize_country_code
from data.catalog_product_utils import resolve_product_variant
from utils.audit_log import audit_log
from utils.money import round_money, to_decimal

if TYPE_CHECKING:
    from data.models import Product, ShippingZone, Shipment, LogisticsPartner


def _load_products_for_order(order: OrderCreate, db: Session) -> Tuple[Dict[int, "Product"], Dict[int, int]]:
    if not order.items:
        raise HTTPException(status_code=422, detail="Order must include at least one item")

    from data.models import Product
    from typing import Dict, Tuple, cast, Any

    requested_quantities: Dict[int, int] = {}
    for item in order.items:
        requested_quantities[item.product_id] = requested_quantities.get(item.product_id, 0) + item.quantity

    products = {
        cast(int, cast(Any, product).id): product
        for product in db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id.in_(requested_quantities.keys()),
            Product.is_deleted == False,
        ).with_for_update().all()
    }

    for item in order.items:
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        variant = resolve_product_variant(product, item.selected_size, item.selected_color)
        has_variants = bool(getattr(product, "variants", []) or [])
        if has_variants and ((item.selected_size or "").strip() or (item.selected_color or "").strip()) and variant is None:
            raise HTTPException(status_code=422, detail="Selected variant is not available for '" + str(product.name) + "'")

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


def _group_supplier_totals(
    order: OrderCreate,
    products: Dict[int, "Product"],
    db: Session,
) -> Dict[int, Dict[str, Any]]:
    from decimal import Decimal
    from typing import Dict, Any, cast
    from data.models import SupplierProfile, Product
    from utils.money import round_money, to_decimal

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

        from services.logistics.logistics_partner_pricing import parse_dimensions_to_volume_cm3
        volume_cm3 = parse_dimensions_to_volume_cm3(str(cast(Any, getattr(product, "dimensions", None))))
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


def _resolve_order_level_logistics_fields(shipment_quotes: list[dict[str, Any]]) -> Tuple[int | None, int | None, int | None, int | None]:
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


def _quote_supplier_groups(
    *,
    supplier_totals: dict,
    destination_country: str,
    destination_city: str,
    db: Session,
) -> Tuple[float, list[dict[str, Any]]]:
    from decimal import Decimal
    from typing import Dict, Any, cast

    if not supplier_totals:
        return 0.0, []

    from data.models import ShippingZone, SupplierProfile
    from utils import settings
    from utils.money import round_money, to_decimal

    supplier_ids = list(supplier_totals.keys())
    zones = (
        db.query(ShippingZone)
        .filter(
            ShippingZone.supplier_id.in_(supplier_ids),
            ShippingZone.is_active == True,
        )
        .all()
    )

    zones_by_supplier: Dict[int, list[ShippingZone]] = {}
    for zone in zones:
        countries_json = cast(str | None, getattr(zone, "countries", None))
        try:
            zone_countries = countries_json and __import__("json").loads(countries_json)
        except (ValueError, TypeError):
            zone_countries = []
        if destination_country in zone_countries:
            zones_by_supplier.setdefault(cast(int, zone.supplier_id), []).append(zone)

    shipping_total = 0.0
    shipment_quotes: list[dict[str, Any]] = []
    for supplier_id, metrics in sorted(supplier_totals.items(), key=lambda item: item[0]):
        supplier_subtotal = round_money(cast(Decimal, metrics["subtotal"]))
        supplier_weight_kg = round_money(cast(Decimal, metrics["weight_kg"]))
        supplier_volume_cm3 = round_money(cast(Decimal, metrics["volume_cm3"]))
        supplier_zones = zones_by_supplier.get(supplier_id, [])
        categories = cast(list[str], metrics.get("categories", []))
        supplier_city = cast(str | None, metrics.get("supplier_city"))

        from services.logistics.logistics_partner_pricing import quote_shipping_for_destination
        from utils.money import round_money
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
            shipment_quotes.append({
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
                "currency": getattr(settings, "default_currency", "AED"),
                "pricing_profile": approved_partner_quote.get("pricing_profile"),
                "category_rules": approved_partner_quote.get("category_rules") or [],
                "vehicle_rule": approved_partner_quote.get("vehicle_rule"),
                "pricing_breakdown": approved_partner_quote.get("pricing_breakdown"),
                "categories": categories,
                "total_weight_kg": float(supplier_weight_kg),
                "total_volume_cm3": float(supplier_volume_cm3),
            })
            continue

        if supplier_zones:
            from services.logistics.logistics_partner_pricing import normalize_pricing_breakdown_payload
            zone_costs = []
            for zone in supplier_zones:
                from utils.money import round_money, to_decimal
                from decimal import Decimal
                free_above = to_decimal(zone.free_shipping_above or 0)
                if free_above is not None and supplier_subtotal >= free_above:
                    zone_cost = 0.0
                else:
                    base_price = to_decimal(zone.base_price or 0)
                    price_per_kg = to_decimal(zone.price_per_kg or 0)
                    zone_cost = float(round_money(base_price + (price_per_kg * supplier_weight_kg)))
                zone_costs.append(zone_cost)
            shipping_amount = min(zone_costs)
            selected_zone = supplier_zones[zone_costs.index(shipping_amount)]
            shipping_total += shipping_amount
            shipment_quotes.append({
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
                "currency": getattr(settings, "default_currency", "AED"),
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
            })
        else:
            from services.logistics.logistics_partner_pricing import quote_shipping_for_destination
            from utils.config import settings
            partner_quote = quote_shipping_for_destination(
                db,
                country=destination_country,
                city=destination_city,
                total_weight_kg=float(supplier_weight_kg),
                pickup_count=1,
                dropoff_count=1,
            )
            if partner_quote:
                shipping_amount = float(partner_quote.get("shipping_amount", 0))
            else:
                free_threshold = float(getattr(settings, "free_shipping_threshold", 0) or 0)
                flat_rate = float(getattr(settings, "shipping_flat_rate", 0) or 0)
                shipping_amount = 0.0 if free_threshold > 0 and float(supplier_subtotal) >= free_threshold else flat_rate
            shipping_total += shipping_amount
            shipment_quotes.append({
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
                "currency": getattr(settings, "default_currency", "AED"),
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
            })

    return round_money(shipping_total), shipment_quotes