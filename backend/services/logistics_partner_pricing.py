from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional, cast

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import (
    CityDistanceMatrix,
    CountryConfig,
    LogisticsCategoryPricingRule,
    LogisticsPartner,
    LogisticsPartnerServiceArea,
    LogisticsPricingProfile,
    LogisticsVehicleRule,
    Order,
)
from utils.money import round_money, to_decimal


APPROVED_PROFILE_STATUS = "approved"
APPROVED_AREA_STATUS = "approved"
APPROVED_PRICING_PROFILE_STATUS = "approved"
APPROVED_CATEGORY_RULE_STATUS = "approved"
APPROVED_VEHICLE_RULE_STATUS = "approved"
DEFAULT_VEHICLE_MULTIPLIERS = {
    "bike": Decimal("0.90"),
    "car": Decimal("1.00"),
    "van": Decimal("1.20"),
    "truck": Decimal("1.50"),
}


def lookup_city_distance_km(
    db: Session,
    *,
    origin_country_code: str | None,
    origin_city_name: str | None,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> Decimal:
    """Return the distance in km between an origin/destination city pair.

    Matching is case-insensitive and whitespace-normalised.  Returns ``Decimal(0)``
    when no matching row exists in ``city_distance_matrix``.
    """
    if not (origin_country_code and origin_city_name and destination_country_code and destination_city_name):
        return Decimal("0")

    origin_cc = normalize_country_code(origin_country_code)
    dest_cc = normalize_country_code(destination_country_code)
    origin_key = normalize_city_name(origin_city_name)
    dest_key = normalize_city_name(destination_city_name)

    # SQLite stores text; we normalise both sides at query time.
    row = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    for entry in row:
        if (
            normalize_city_name(cast(str | None, getattr(entry, "origin_city_name", None))) == origin_key
            and normalize_city_name(cast(str | None, getattr(entry, "destination_city_name", None))) == dest_key
        ):
            return to_decimal(getattr(entry, "distance_km", 0) or 0)
    return Decimal("0")


def serialize_pricing_profile(profile: LogisticsPricingProfile) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(profile, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(profile, "created_at", None))
    updated_at = cast(Optional[Any], getattr(profile, "updated_at", None))
    return {
        "id": profile.id,
        "partner_id": profile.partner_id,
        "service_area_id": profile.service_area_id,
        "profile_name": profile.profile_name,
        "base_in_city_fee": float(profile.base_in_city_fee) if getattr(profile, "base_in_city_fee", None) is not None else None,
        "base_inter_city_fee": float(profile.base_inter_city_fee) if getattr(profile, "base_inter_city_fee", None) is not None else None,
        "per_km_rate": float(profile.per_km_rate) if getattr(profile, "per_km_rate", None) is not None else None,
        "per_kg_rate": float(profile.per_kg_rate) if getattr(profile, "per_kg_rate", None) is not None else None,
        "minimum_charge": float(profile.minimum_charge) if getattr(profile, "minimum_charge", None) is not None else None,
        "maximum_charge": float(profile.maximum_charge) if getattr(profile, "maximum_charge", None) is not None else None,
        "fuel_multiplier": float(profile.fuel_multiplier) if getattr(profile, "fuel_multiplier", None) is not None else 1.0,
        "bulk_discount_threshold_kg": float(profile.bulk_discount_threshold_kg) if getattr(profile, "bulk_discount_threshold_kg", None) is not None else None,
        "bulk_discount_percent": float(profile.bulk_discount_percent) if getattr(profile, "bulk_discount_percent", None) is not None else None,
        "currency": profile.currency,
        "is_active": bool(profile.is_active),
        "approval_status": profile.approval_status,
        "review_note": profile.review_note,
        "reviewed_by": profile.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def normalize_category_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_vehicle_type(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def vehicle_baseline_multiplier(vehicle_type: str | None) -> Decimal:
    normalized = normalize_vehicle_type(vehicle_type)
    return DEFAULT_VEHICLE_MULTIPLIERS.get(normalized, Decimal("1.00"))


def normalize_pricing_breakdown_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    data = dict(payload)
    legacy_keys = {
        "applied_category_name",
        "applied_category_rule_id",
        "bulk_discount_amount",
        "bulk_discount_percent",
        "bulk_discount_threshold_kg",
        "category_adjustment_amount",
        "category_extra",
        "category_rule_ids",
        "dropoff_charge",
        "fuel_adjustment_amount",
        "fuel_multiplier",
        "matched_categories",
        "maximum_charge",
        "maximum_charge_applied",
        "minimum_charge",
        "minimum_charge_applied",
        "pickup_charge",
        "pricing_schema_version",
        "special_handling_fee",
        "subtotal_before_fuel",
        "total_category_extra",
        "vehicle_adjustment_amount",
        "vehicle_multiplier",
        "vehicle_rule_id",
        "vehicle_type",
    }
    normalized = {key: value for key, value in data.items() if key not in legacy_keys}

    handling_fee = data.get("handling_fee")
    if handling_fee is None:
        if data.get("total_category_extra") is not None:
            handling_fee = data.get("total_category_extra")
        elif data.get("category_adjustment_amount") is not None:
            handling_fee = data.get("category_adjustment_amount")
        else:
            handling_fee = max(float(data.get("category_extra") or 0), float(data.get("special_handling_fee") or 0))

    pricing_schema_version = str(data.get("pricing_schema_version") or "").strip().lower()
    pricing_model = data.get("pricing_model")
    if not pricing_model:
        pricing_model = "operational_load_fit" if pricing_schema_version == "v1_operational_vehicle_multiplier" else "customer_weight_route"

    load_fit_factor = data.get("load_fit_factor")
    if load_fit_factor is None:
        load_fit_factor = data.get("vehicle_multiplier")
    if load_fit_factor is None:
        load_fit_factor = 1.0

    surcharge_factor = data.get("surcharge_factor")
    if surcharge_factor is None:
        surcharge_factor = data.get("fuel_multiplier")
    if surcharge_factor is None:
        surcharge_factor = 1.0

    normalized.update({
        "base_fee": data.get("base_fee", 0.0),
        "pickup_fee": data.get("pickup_fee", data.get("pickup_charge", 0.0)),
        "dropoff_fee": data.get("dropoff_fee", data.get("dropoff_charge", 0.0)),
        "pickup_count": data.get("pickup_count", 1),
        "dropoff_count": data.get("dropoff_count", 1),
        "extra_pickup_count": data.get("extra_pickup_count", 0),
        "extra_dropoff_count": data.get("extra_dropoff_count", 0),
        "pickup_fee_per_stop": data.get("pickup_fee_per_stop", 0.0),
        "dropoff_fee_per_stop": data.get("dropoff_fee_per_stop", 0.0),
        "route_type": data.get("route_type", "in_city"),
        "is_in_city": bool(data.get("is_in_city", data.get("route_type") == "in_city")),
        "weight_fee": data.get("weight_fee", 0.0),
        "per_kg_rate": data.get("per_kg_rate"),
        "distance_km": data.get("distance_km"),
        "per_km_rate": data.get("per_km_rate"),
        "distance_fee": data.get("distance_fee", 0.0),
        "handling_fee": handling_fee,
        "subtotal_core": data.get("subtotal_core", 0.0),
        "load_fit_factor": load_fit_factor,
        "load_fit_adjustment_amount": data.get("load_fit_adjustment_amount", data.get("vehicle_adjustment_amount", 0.0)),
        "pricing_model": pricing_model,
        "subtotal_before_surcharge": data.get("subtotal_before_surcharge", data.get("subtotal_before_fuel", data.get("subtotal_core", 0.0))),
        "surcharge_factor": surcharge_factor,
        "surcharge_amount": data.get("surcharge_amount", data.get("fuel_adjustment_amount", 0.0)),
        "floor_charge": data.get("floor_charge", data.get("minimum_charge")),
        "floor_applied": bool(data.get("floor_applied", data.get("minimum_charge_applied", False))),
        "ceiling_charge": data.get("ceiling_charge", data.get("maximum_charge")),
        "ceiling_applied": bool(data.get("ceiling_applied", data.get("maximum_charge_applied", False))),
        "weight_discount_threshold_kg": data.get("weight_discount_threshold_kg", data.get("bulk_discount_threshold_kg")),
        "weight_discount_percent": data.get("weight_discount_percent", data.get("bulk_discount_percent")),
        "weight_discount_amount": data.get("weight_discount_amount", data.get("bulk_discount_amount", 0.0)),
        "pricing_profile_id": data.get("pricing_profile_id"),
        "handling_rule_ids": data.get("handling_rule_ids", data.get("category_rule_ids", [])),
        "applied_handling_rule_id": data.get("applied_handling_rule_id", data.get("applied_category_rule_id")),
        "applied_handling_label": data.get("applied_handling_label", data.get("applied_category_name")),
        "matched_handling_labels": data.get("matched_handling_labels", data.get("matched_categories", [])),
        "load_fit_rule_id": data.get("load_fit_rule_id", data.get("vehicle_rule_id")),
        "load_fit_label": data.get("load_fit_label", data.get("vehicle_type")),
        "total_weight_kg": data.get("total_weight_kg", 0.0),
        "total_volume_cm3": data.get("total_volume_cm3", 0.0),
        "shipping_amount": data.get("shipping_amount", 0.0),
    })
    return normalized


def parse_dimensions_to_volume_cm3(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    cleaned = str(value).lower().replace("cm", " ").replace("x", " ").replace("*", " ")
    parts: list[Decimal] = []
    for token in cleaned.split():
        try:
            parts.append(to_decimal(token))
        except Exception:
            continue
        if len(parts) == 3:
            break
    if len(parts) != 3:
        return Decimal("0")
    length, width, height = parts
    if length <= 0 or width <= 0 or height <= 0:
        return Decimal("0")
    return round_money(length * width * height)


def serialize_category_pricing_rule(rule: LogisticsCategoryPricingRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "category_name": rule.category_name,
        "flat_fee_override": float(rule.flat_fee_override) if getattr(rule, "flat_fee_override", None) is not None else None,
        "special_handling_fee": float(rule.special_handling_fee) if getattr(rule, "special_handling_fee", None) is not None else None,
        "currency": rule.currency,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def serialize_vehicle_rule(rule: LogisticsVehicleRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "route_scope": getattr(rule, "route_scope", "any"),
        "vehicle_type": rule.vehicle_type,
        "max_weight_kg": float(rule.max_weight_kg) if getattr(rule, "max_weight_kg", None) is not None else None,
        "max_volume_cm3": float(rule.max_volume_cm3) if getattr(rule, "max_volume_cm3", None) is not None else None,
        "cost_multiplier": float(rule.cost_multiplier),
        "priority_rank": rule.priority_rank,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_category_rules_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    categories: list[str] | None,
) -> list[LogisticsCategoryPricingRule]:
    normalized_categories = [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)]
    if not normalized_categories:
        return []

    rows = (
        db.query(LogisticsCategoryPricingRule)
        .filter(
            LogisticsCategoryPricingRule.partner_id == area.partner_id,
            LogisticsCategoryPricingRule.is_active == True,  # noqa: E712
            LogisticsCategoryPricingRule.approval_status == APPROVED_CATEGORY_RULE_STATUS,
        )
        .order_by(desc(LogisticsCategoryPricingRule.updated_at), desc(LogisticsCategoryPricingRule.id))
        .all()
    )

    resolved: dict[str, LogisticsCategoryPricingRule] = {}
    for category in normalized_categories:
        exact_match = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) == area.id
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if exact_match is not None:
            resolved[category] = exact_match
            continue
        fallback = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) is None
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if fallback is not None:
            resolved[category] = fallback

    return [resolved[category] for category in normalized_categories if category in resolved]


def resolve_vehicle_rule_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    *,
    route_type: str,
    total_weight_kg: Decimal | float | int | None,
    total_volume_cm3: Decimal | float | int | None,
    preferred_vehicle_type: str | None = None,
) -> LogisticsVehicleRule | None:
    weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))
    preferred_vehicle_key = normalize_vehicle_type(preferred_vehicle_type)
    rows = (
        db.query(LogisticsVehicleRule)
        .filter(
            LogisticsVehicleRule.partner_id == area.partner_id,
            LogisticsVehicleRule.is_active == True,  # noqa: E712
            LogisticsVehicleRule.approval_status == APPROVED_VEHICLE_RULE_STATUS,
        )
        .all()
    )
    candidates = []
    for row in rows:
        service_area_id = getattr(row, "service_area_id", None)
        if service_area_id not in (None, area.id):
            continue
        row_route_scope = str(getattr(row, "route_scope", "any") or "any").strip().lower()
        if row_route_scope not in {"any", route_type}:
            continue
        if preferred_vehicle_key and normalize_vehicle_type(cast(str | None, getattr(row, "vehicle_type", None))) != preferred_vehicle_key:
            continue
        max_weight = cast(Decimal | float | int | None, getattr(row, "max_weight_kg", None))
        max_volume = cast(Decimal | float | int | None, getattr(row, "max_volume_cm3", None))
        if max_weight is not None and weight > round_money(to_decimal(max_weight)):
            continue
        if max_volume is not None and volume > round_money(to_decimal(max_volume)):
            continue
        candidates.append(row)

    if not candidates:
        return None

    candidates.sort(
        key=lambda row: (
            0 if getattr(row, "service_area_id", None) == area.id else 1,
            0 if str(getattr(row, "route_scope", "any") or "any").strip().lower() == route_type else 1,
            int(getattr(row, "priority_rank", 100) or 100),
            int(getattr(row, "id", 0) or 0),
        )
    )
    return candidates[0]


def resolve_pricing_profile_for_area(db: Session, area: LogisticsPartnerServiceArea) -> LogisticsPricingProfile | None:
    rows = (
        db.query(LogisticsPricingProfile)
        .filter(
            LogisticsPricingProfile.partner_id == area.partner_id,
            LogisticsPricingProfile.is_active == True,  # noqa: E712
            LogisticsPricingProfile.approval_status == APPROVED_PRICING_PROFILE_STATUS,
        )
        .order_by(desc(LogisticsPricingProfile.updated_at), desc(LogisticsPricingProfile.id))
        .all()
    )
    exact = [row for row in rows if getattr(row, "service_area_id", None) == area.id]
    if exact:
        return exact[0]
    fallback = [row for row in rows if getattr(row, "service_area_id", None) is None]
    return fallback[0] if fallback else None


def _resolve_route_context(
    area: LogisticsPartnerServiceArea,
    *,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> dict[str, Any]:
    origin_country_code = normalize_country_code(cast(str | None, getattr(area, "country_code", None)))
    origin_city_name = cast(str | None, getattr(area, "origin_city", None))
    destination_country = normalize_country_code(destination_country_code)
    origin_city_key = normalize_city_name(origin_city_name)
    destination_city_key = normalize_city_name(destination_city_name)
    is_in_city = bool(
        origin_country_code
        and destination_country
        and origin_country_code == destination_country
        and origin_city_key
        and destination_city_key
        and origin_city_key == destination_city_key
    )
    return {
        "origin_country_code": origin_country_code or None,
        "origin_city_name": origin_city_name,
        "destination_country_code": destination_country or None,
        "destination_city_name": destination_city_name,
        "is_in_city": is_in_city,
        "route_type": "in_city" if is_in_city else "inter_city",
    }


def _build_service_area_pricing_breakdown(
    area: LogisticsPartnerServiceArea,
    *,
    pricing_profile: LogisticsPricingProfile | None = None,
    category_rules: list[LogisticsCategoryPricingRule] | None = None,
    vehicle_rule: LogisticsVehicleRule | None = None,
    vehicle_type_override: str | None = None,
    vehicle_multiplier_override: Decimal | float | int | None = None,
    vehicle_rule_id_override: int | None = None,
    apply_vehicle_multiplier: bool = True,
    categories: list[str] | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
    distance_km: Decimal | float | int | None = None,
    destination_country_code: str | None = None,
    destination_city_name: str | None = None,
) -> dict[str, Any]:
    route_context = _resolve_route_context(
        area,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    raw_minimum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "minimum_charge", None) if getattr(pricing_profile, "minimum_charge", None) is not None else getattr(area, "minimum_charge", None),
    )
    raw_per_kg_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_kg_rate", None) if getattr(pricing_profile, "per_kg_rate", None) is not None else getattr(area, "per_kg_rate", None),
    )
    raw_per_km_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None),
    )
    raw_fuel_multiplier = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "fuel_multiplier", None) if getattr(pricing_profile, "fuel_multiplier", None) is not None else getattr(area, "fuel_multiplier", None),
    )
    raw_bulk_discount_threshold = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_threshold_kg", None))
    raw_bulk_discount_percent = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_percent", None))

    profile_base = None
    if pricing_profile is not None:
        profile_base = getattr(pricing_profile, "base_in_city_fee", None) if route_context["is_in_city"] else getattr(pricing_profile, "base_inter_city_fee", None)
    pickup_fee_per_stop = round_money(to_decimal(getattr(area, "pickup_charge", None) or 0))
    dropoff_fee_per_stop = round_money(to_decimal(getattr(area, "dropoff_charge", None) or 0))
    resolved_pickup_count = max(int(pickup_count if pickup_count is not None else 1), 0)
    resolved_dropoff_count = max(int(dropoff_count if dropoff_count is not None else 1), 0)
    # First pickup and first dropoff are included in the base fee; only extra stops are charged.
    extra_pickups = max(resolved_pickup_count - 1, 0)
    extra_dropoffs = max(resolved_dropoff_count - 1, 0)
    pickup_fee = round_money(pickup_fee_per_stop * to_decimal(extra_pickups))
    dropoff_fee = round_money(dropoff_fee_per_stop * to_decimal(extra_dropoffs))
    resolved_base_fee = round_money(to_decimal(profile_base if profile_base is not None else getattr(area, "charge_amount", None) or 0))
    total_weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    total_volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))

    category_rules = category_rules or []

    # Category handling is intentionally simplified for the business-facing rate card.
    # Legacy rules may still store two numbers (flat fee + handling fee), but the
    # customer-facing quote collapses them into one handling amount per rule by taking
    # the stronger configured charge. Across multiple matched rules, only the single
    # highest collapsed handling amount is applied.
    category_extra = Decimal("0")
    special_handling_fee = Decimal("0")
    applied_category_rule = None
    highest_category_total = Decimal("0")
    for rule in category_rules:
        rule_category_extra = round_money(to_decimal(getattr(rule, "flat_fee_override", None) or 0))
        rule_special_handling = round_money(to_decimal(getattr(rule, "special_handling_fee", None) or 0))
        rule_total = round_money(max(rule_category_extra, rule_special_handling))
        if rule_total > highest_category_total:
            highest_category_total = rule_total
            category_extra = Decimal("0")
            special_handling_fee = rule_total
            applied_category_rule = rule

    total_category_extra = round_money(category_extra + special_handling_fee)

    # STEP 1 — Base fee (in-city) or STEP 2 — Distance cost (inter-city).
    # resolved_base_fee is already set to base_in_city_fee (in-city) or base_inter_city_fee (inter-city)
    # by the profile_base lookup above. These two are mutually exclusive by route_type.
    base_fee = resolved_base_fee

    # STEP 3 — Weight cost. Calculated once from global per_kg_rate. Never overridden by category rules.
    per_kg_rate = round_money(to_decimal(raw_per_kg_rate or 0))
    weight_fee = round_money(total_weight * per_kg_rate) if total_weight > 0 and per_kg_rate > 0 else Decimal("0")

    # STEP 2 (distance component) — inter-city only.
    # When base_inter_city_fee is set and per_km_rate is null, distance_fee stays 0 (flat-rate mode).
    # When per_km_rate is set, distance_fee = distance_km x per_km_rate (per-km mode).
    resolved_distance = max(round_money(to_decimal(distance_km or 0)), Decimal("0"))
    per_km_rate = to_decimal(raw_per_km_rate or 0)
    distance_fee = round_money(resolved_distance * per_km_rate) if resolved_distance > 0 and per_km_rate > 0 else Decimal("0")

    # Core additive subtotal: (base OR distance) + weight + category.
    # base_fee and distance_fee are mutually exclusive by route_type — only one is non-zero at a time.
    subtotal_core = round_money(base_fee + distance_fee + weight_fee + total_category_extra)

    # Pickup / drop-off surcharges: additive exceptional access charges.
    # These are 0 for standard routes and non-zero only for explicitly configured exceptional areas.
    subtotal_before_multipliers = round_money(subtotal_core + pickup_fee + dropoff_fee)

    # STEP 5 — Vehicle multiplier is optional.
    # Customer-facing quotes keep the formula weight-first and route-first.
    # Operational acceptance flows can still opt in to multiplier-based snapshots.
    resolved_vehicle_multiplier = to_decimal(
        vehicle_multiplier_override
        if vehicle_multiplier_override is not None
        else getattr(vehicle_rule, "cost_multiplier", None) or 1
    )
    vehicle_multiplier = resolved_vehicle_multiplier if apply_vehicle_multiplier else Decimal("1")
    subtotal_after_vehicle = round_money(subtotal_before_multipliers * vehicle_multiplier)

    # STEP 6 — Fuel multiplier.
    fuel_multiplier = to_decimal(raw_fuel_multiplier or 1)
    fuel_adjusted_total = round_money(subtotal_after_vehicle * fuel_multiplier)

    # STEP 7 — Minimum charge floor.
    minimum_charge = round_money(to_decimal(raw_minimum_charge or 0))
    total_after_minimum = round_money(max(fuel_adjusted_total, minimum_charge))

    # Maximum charge ceiling (guardrail) — clamps the total from above when set.
    raw_maximum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "maximum_charge", None) if pricing_profile is not None else None,
    )
    maximum_charge_limit = round_money(to_decimal(raw_maximum_charge)) if raw_maximum_charge is not None else None
    maximum_charge_applied = False
    if maximum_charge_limit is not None and maximum_charge_limit > 0 and total_after_minimum > maximum_charge_limit:
        total_after_minimum = maximum_charge_limit
        maximum_charge_applied = True

    # Bulk discount (optional, applied after floor/ceiling guardrails).
    # The discount is restricted to the weight fee so route and stop charges stay stable.
    bulk_discount_threshold = round_money(to_decimal(raw_bulk_discount_threshold or 0))
    bulk_discount_percent = round_money(to_decimal(raw_bulk_discount_percent or 0))
    bulk_discount_amount = Decimal("0")
    if bulk_discount_threshold > 0 and bulk_discount_percent > 0 and total_weight >= bulk_discount_threshold:
        bulk_discount_amount = round_money(weight_fee * (bulk_discount_percent / Decimal("100")))
    final_charge = round_money(max(total_after_minimum - bulk_discount_amount, Decimal("0")))

    return normalize_pricing_breakdown_payload({
        "base_fee": float(base_fee),
        "pickup_count": resolved_pickup_count,
        "dropoff_count": resolved_dropoff_count,
        "extra_pickup_count": extra_pickups,
        "extra_dropoff_count": extra_dropoffs,
        "pickup_fee_per_stop": float(pickup_fee_per_stop),
        "dropoff_fee_per_stop": float(dropoff_fee_per_stop),
        "pickup_fee": float(pickup_fee),
        "dropoff_fee": float(dropoff_fee),
        "route_type": route_context["route_type"],
        "is_in_city": route_context["is_in_city"],
        "currency": getattr(pricing_profile, "currency", None) or getattr(area, "currency", None),
        "weight_fee": float(weight_fee),
        "per_kg_rate": float(per_kg_rate) if raw_per_kg_rate is not None else None,
        "distance_km": float(resolved_distance) if distance_km is not None else None,
        "per_km_rate": float(per_km_rate) if raw_per_km_rate is not None else None,
        "distance_fee": float(distance_fee),
        "category_extra": float(category_extra),
        "special_handling_fee": float(special_handling_fee),
        "total_category_extra": float(total_category_extra),
        "subtotal_core": float(subtotal_core),
        "vehicle_multiplier": float(vehicle_multiplier),
        "vehicle_adjustment_amount": float(round_money(subtotal_after_vehicle - subtotal_before_multipliers)),
        "pricing_schema_version": "v1_operational_vehicle_multiplier" if apply_vehicle_multiplier else "v2_weight_first_customer_charge",
        "subtotal_before_fuel": float(subtotal_after_vehicle),
        "fuel_multiplier": float(fuel_multiplier),
        "fuel_adjustment_amount": float(round_money(fuel_adjusted_total - subtotal_after_vehicle)),
        "minimum_charge": float(minimum_charge) if raw_minimum_charge is not None else None,
        "minimum_charge_applied": raw_minimum_charge is not None and total_after_minimum == minimum_charge and minimum_charge > fuel_adjusted_total,
        "maximum_charge": float(maximum_charge_limit) if maximum_charge_limit is not None else None,
        "maximum_charge_applied": maximum_charge_applied,
        "bulk_discount_threshold_kg": float(bulk_discount_threshold) if raw_bulk_discount_threshold is not None else None,
        "bulk_discount_percent": float(bulk_discount_percent) if raw_bulk_discount_percent is not None else None,
        "bulk_discount_amount": float(bulk_discount_amount),
        "pricing_profile_id": getattr(pricing_profile, "id", None),
        "category_rule_ids": [getattr(applied_category_rule, "id", None)] if applied_category_rule is not None else [],
        "applied_category_rule_id": getattr(applied_category_rule, "id", None) if applied_category_rule is not None else None,
        "applied_category_name": getattr(applied_category_rule, "category_name", None) if applied_category_rule is not None else None,
        "matched_categories": [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)],
        "vehicle_rule_id": vehicle_rule_id_override if vehicle_rule_id_override is not None else getattr(vehicle_rule, "id", None),
        "vehicle_type": vehicle_type_override if vehicle_type_override is not None else getattr(vehicle_rule, "vehicle_type", None),
        "total_weight_kg": float(total_weight),
        "total_volume_cm3": float(total_volume),
        "shipping_amount": float(final_charge),
    })


_COUNTRY_CODE_ALIASES: dict[str, str] = {
    "AE": "AE",
    "UAE": "AE",
    "UNITEDARABEMIRATES": "AE",
    "EMIRATES": "AE",
    "PK": "PK",
    "PAKISTAN": "PK",
    "OM": "OM",
    "OMAN": "OM",
    "SA": "SA",
    "SAUDIARABIA": "SA",
    "KSA": "SA",
    "IN": "IN",
    "INDIA": "IN",
    "US": "US",
    "USA": "US",
    "UNITEDSTATES": "US",
    "UNITEDSTATESOFAMERICA": "US",
    "GB": "GB",
    "UK": "GB",
    "UNITEDKINGDOM": "GB",
    "KW": "KW",
    "KUWAIT": "KW",
    "QA": "QA",
    "QATAR": "QA",
    "BH": "BH",
    "BAHRAIN": "BH",
}


def normalize_country_code(value: str | None) -> str:
    if not value:
        return ""

    letters = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if not letters:
        return ""

    aliased = _COUNTRY_CODE_ALIASES.get(letters)
    if aliased:
        return aliased

    if len(letters) == 2:
        return letters

    # Preserve backward compatibility for unknown country names/codes.
    return letters[:2]


def calculate_per_km_delivery(
    *,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str,
    vehicle_config: dict[str, dict[str, Decimal]],
    base_rate: Decimal,
    minimum_charge: Decimal,
    weight_surcharge_rate: Decimal,
    weight_surcharge_threshold_kg: Decimal,
    currency: str,
    country_code: str,
) -> dict[str, Any]:
    """Generic per-km delivery formula for any country configuration.

    total = max(base_rate + (distance_km * vehicle_rate) + weight_surcharge, minimum_charge)
    """
    vehicle_key = normalize_vehicle_type(vehicle_type) or "bike"
    vehicle = vehicle_config.get(vehicle_key)
    if vehicle is None:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")

    route_distance = round_money(to_decimal(distance_km))
    total_weight = round_money(to_decimal(weight_kg))
    max_weight = round_money(to_decimal(vehicle.get("max_weight_kg", 0) or 0))
    if max_weight > 0 and total_weight > max_weight:
        raise ValueError(f"{total_weight}kg exceeds vehicle capacity {max_weight}kg")

    per_km_rate = round_money(to_decimal(vehicle.get("per_km_rate", 0) or 0))
    surcharge_threshold = round_money(to_decimal(weight_surcharge_threshold_kg or 0))
    surcharge_rate = round_money(to_decimal(weight_surcharge_rate or 0))
    surcharge_weight = max(Decimal("0"), total_weight - surcharge_threshold)
    weight_surcharge = round_money(surcharge_weight * surcharge_rate)
    subtotal = round_money(round_money(to_decimal(base_rate or 0)) + (route_distance * per_km_rate) + weight_surcharge)
    resolved_minimum_charge = round_money(to_decimal(minimum_charge or 0))
    total = round_money(max(subtotal, resolved_minimum_charge))

    return {
        "country_code": normalize_country_code(country_code),
        "vehicle_type": vehicle_key,
        "distance_km": route_distance,
        "weight_kg": total_weight,
        "base_rate": round_money(to_decimal(base_rate or 0)),
        "per_km_rate": per_km_rate,
        "weight_surcharge": weight_surcharge,
        "minimum_charge": resolved_minimum_charge,
        "total": total,
        "currency": str(currency or ""),
    }


def _country_vehicle_config(config: CountryConfig) -> dict[str, dict[str, Decimal]]:
    base_per_km = round_money(to_decimal(getattr(config, "per_km_rate", 0) or 0))
    default_vehicle = normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"

    # Build a sensible multi-vehicle map for any country from a single country-level per_km_rate.
    config_map: dict[str, dict[str, Decimal]] = {}
    for vehicle_name, multiplier in DEFAULT_VEHICLE_MULTIPLIERS.items():
        max_weight = {
            "bike": Decimal("10"),
            "car": Decimal("30"),
            "van": Decimal("100"),
            "truck": Decimal("500"),
        }.get(vehicle_name, Decimal("100"))
        config_map[vehicle_name] = {
            "per_km_rate": round_money(base_per_km * multiplier),
            "max_weight_kg": max_weight,
        }

    # Keep configured default vehicle at exactly country per_km_rate.
    if default_vehicle in config_map:
        config_map[default_vehicle]["per_km_rate"] = base_per_km
    return config_map


def calculate_country_per_km_delivery(
    db: Session,
    *,
    country_code: str,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str | None = None,
) -> dict[str, Any]:
    """Resolve country delivery values from CountryConfig and compute per-km quote."""
    normalized_code = normalize_country_code(country_code)
    if not normalized_code:
        raise ValueError("Unknown country: empty code")

    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == normalized_code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )
    if config is None:
        raise ValueError(f"Unknown country: {normalized_code}")

    model = str(getattr(config, "logistics_model", "") or "").strip().lower()
    if model not in {"per_km", "per-km", "distance", "distance_based"}:
        raise ValueError(f"Country {normalized_code} is not configured for per-km logistics")

    resolved_vehicle = normalize_vehicle_type(vehicle_type) or normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"
    vehicle_config = _country_vehicle_config(config)
    return calculate_per_km_delivery(
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=resolved_vehicle,
        vehicle_config=vehicle_config,
        base_rate=round_money(to_decimal(getattr(config, "base_rate", 0) or 0)),
        minimum_charge=round_money(to_decimal(getattr(config, "minimum_charge", 0) or 0)),
        weight_surcharge_rate=round_money(to_decimal(getattr(config, "weight_surcharge_rate", 0) or 0)),
        weight_surcharge_threshold_kg=round_money(to_decimal(getattr(config, "weight_surcharge_threshold_kg", 0) or 0)),
        currency=str(getattr(config, "currency", "") or ""),
        country_code=normalized_code,
    )


def calculate_pk_delivery(
    *,
    db: Session,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Pakistan-specific helper — reads per-km pricing from CountryConfig for PK."""
    return calculate_country_per_km_delivery(
        db=db,
        country_code="PK",
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=vehicle_type,
    )


def calculate_pk_delivery_for_cities(
    db: Session,
    *,
    origin_country_code: str,
    origin_city_name: str,
    destination_country_code: str,
    destination_city_name: str,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Backward-compatible city-distance helper for Pakistan delivery quotes."""
    distance_km = lookup_city_distance_km(
        db,
        origin_country_code=origin_country_code,
        origin_city_name=origin_city_name,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    return calculate_pk_delivery(db=db, distance_km=distance_km, weight_kg=weight_kg, vehicle_type=vehicle_type)


def normalize_city_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def partner_is_profile_approved(partner: LogisticsPartner | None) -> bool:
    if partner is None:
        return False
    return (
        cast(str | None, getattr(partner, "status", None)) == "active"
        and cast(str | None, getattr(partner, "verification_status", None)) == APPROVED_PROFILE_STATUS
    )


def serialize_service_area(area: LogisticsPartnerServiceArea) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(area, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(area, "created_at", None))
    updated_at = cast(Optional[Any], getattr(area, "updated_at", None))
    charge_amount = cast(Decimal | float | int | None, getattr(area, "charge_amount", None))
    minimum_charge = cast(Decimal | float | int | None, getattr(area, "minimum_charge", None))
    per_kg_rate = cast(Decimal | float | int | None, getattr(area, "per_kg_rate", None))
    per_km_rate = cast(Decimal | float | int | None, getattr(area, "per_km_rate", None))
    fuel_multiplier = cast(Decimal | float | int | None, getattr(area, "fuel_multiplier", None))
    pickup_charge = cast(Decimal | float | int | None, getattr(area, "pickup_charge", None))
    dropoff_charge = cast(Decimal | float | int | None, getattr(area, "dropoff_charge", None))
    return {
        "id": area.id,
        "partner_id": area.partner_id,
        "country_code": area.country_code,
        "country_name": area.country_name,
        "city_name": area.city_name,
        "origin_city": getattr(area, "origin_city", None),
        "zone_label": area.zone_label,
        "charge_amount": float(charge_amount or 0),
        "minimum_charge": float(minimum_charge) if minimum_charge is not None else None,
        "per_kg_rate": float(per_kg_rate) if per_kg_rate is not None else None,
        "per_km_rate": float(per_km_rate) if per_km_rate is not None else None,
        "fuel_multiplier": float(fuel_multiplier) if fuel_multiplier is not None else 1.0,
        "pickup_charge": float(pickup_charge) if pickup_charge is not None else None,
        "dropoff_charge": float(dropoff_charge) if dropoff_charge is not None else None,
        "currency": area.currency,
        "latitude": getattr(area, "latitude", None),
        "longitude": getattr(area, "longitude", None),
        "delivery_days_min": area.delivery_days_min,
        "delivery_days_max": area.delivery_days_max,
        "is_active": bool(area.is_active),
        "approval_status": area.approval_status,
        "review_note": area.review_note,
        "reviewed_by": area.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_destination(*, country: str | None = None, city: str | None = None, shipping_address: str | None = None, order: Order | None = None) -> dict[str, str | None]:
    resolved_country = (country or "").strip()
    resolved_city = (city or "").strip()
    shipping_text = (shipping_address or "").strip()

    if order is not None:
        resolved_country = resolved_country or str(getattr(order, "shipping_country", "") or "").strip()
        resolved_city = resolved_city or str(getattr(order, "shipping_city", "") or "").strip()
        shipping_text = shipping_text or str(getattr(order, "shipping_address", "") or "").strip()

    if shipping_text:
        parts = [part.strip() for part in shipping_text.split(",") if part.strip()]
        if not resolved_country and parts:
            resolved_country = parts[-1]
        if not resolved_city:
            if len(parts) >= 3:
                resolved_city = parts[-3]
            elif parts:
                resolved_city = parts[0]

    return {
        "country": resolved_country or None,
        "country_code": normalize_country_code(resolved_country),
        "city": resolved_city or None,
        "city_key": normalize_city_name(resolved_city),
    }


def approved_service_areas_query(db: Session):
    return (
        db.query(LogisticsPartnerServiceArea)
        .join(LogisticsPartner, LogisticsPartner.id == LogisticsPartnerServiceArea.partner_id)
        .filter(
            LogisticsPartner.status == "active",
            LogisticsPartner.verification_status == APPROVED_PROFILE_STATUS,
            LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
            LogisticsPartnerServiceArea.approval_status == APPROVED_AREA_STATUS,
        )
    )


def find_matching_service_areas(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
) -> list[LogisticsPartnerServiceArea]:
    destination = resolve_destination(country=country, city=city)
    if not destination["country_code"]:
        return []

    query = approved_service_areas_query(db).filter(
        LogisticsPartnerServiceArea.country_code == destination["country_code"],
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerServiceArea.partner_id == partner_id)

    rows = query.order_by(LogisticsPartnerServiceArea.updated_at.desc(), LogisticsPartnerServiceArea.id.desc()).all()
    if not rows:
        return []

    city_key = cast(str, destination["city_key"] or "")
    if not city_key:
        country_rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]
        rows = country_rows or rows
    else:
        exact_rows = [
            row
            for row in rows
            if normalize_city_name(cast(str | None, getattr(row, "city_name", None))) == city_key
        ]
        if exact_rows:
            rows = exact_rows
        else:
            rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]

    # Filter by origin_city (pickup city): NULL origin means any pickup city is accepted
    if supplier_city:
        normalized_supplier = normalize_city_name(supplier_city)
        rows = [
            row for row in rows
            if not getattr(row, "origin_city", None)
            or normalize_city_name(cast(str | None, getattr(row, "origin_city", None))) == normalized_supplier
        ]

    return rows


def quote_shipping_for_destination(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    categories: list[str] | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
) -> dict[str, Any] | None:
    matches = find_matching_service_areas(db, country=country, city=city, partner_id=partner_id, supplier_city=supplier_city)
    if not matches:
        return None

    destination = resolve_destination(country=country, city=city)
    dest_city = cast(str | None, destination.get("city"))
    dest_cc = cast(str | None, destination.get("country_code"))

    ranked = sorted(
        (
            (
                area,
                resolve_pricing_profile_for_area(db, area),
                _resolve_route_context(area, destination_country_code=dest_cc, destination_city_name=dest_city),
            )
            for area in matches
        ),
        key=lambda item: item[0].id,
    )

    resolved_quotes: list[tuple[LogisticsPartnerServiceArea, LogisticsPricingProfile | None, dict[str, Any]]] = []
    for area, pricing_profile, route_context in ranked:
        effective_per_km_rate = getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None)
        category_rules = resolve_category_rules_for_area(db, area, categories)
        distance_km = None
        if effective_per_km_rate and not route_context["is_in_city"]:
            distance_km = lookup_city_distance_km(
                db,
                origin_country_code=cast(str | None, route_context["origin_country_code"]),
                origin_city_name=cast(str | None, route_context["origin_city_name"]),
                destination_country_code=dest_cc,
                destination_city_name=dest_city,
            )
        vehicle_rule = resolve_vehicle_rule_for_area(
            db,
            area,
            route_type=cast(str, route_context["route_type"]),
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
        )
        pricing_breakdown = _build_service_area_pricing_breakdown(
            area,
            pricing_profile=pricing_profile,
            category_rules=category_rules,
            vehicle_rule=vehicle_rule,
            apply_vehicle_multiplier=False,
            categories=categories,
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
            pickup_count=pickup_count,
            dropoff_count=dropoff_count,
            distance_km=distance_km,
            destination_country_code=dest_cc,
            destination_city_name=dest_city,
        )
        resolved_quotes.append((area, pricing_profile, pricing_breakdown))

    selected, pricing_profile, pricing_breakdown = sorted(
        resolved_quotes,
        key=lambda item: (item[2]["shipping_amount"], item[0].id),
    )[0]
    partner = cast(LogisticsPartner | None, getattr(selected, "partner", None))
    return {
        "shipping_amount": pricing_breakdown["shipping_amount"],
        "currency": selected.currency,
        "partner_id": selected.partner_id,
        "partner_name": getattr(partner, "name", None) if partner else None,
        "partner_code": getattr(partner, "code", None) if partner else None,
        "service_area": serialize_service_area(selected),
        "pricing_profile": serialize_pricing_profile(pricing_profile) if pricing_profile is not None else None,
        "category_rules": [serialize_category_pricing_rule(rule) for rule in resolve_category_rules_for_area(db, selected, categories)],
        "vehicle_rule": serialize_vehicle_rule(resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3)) if resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3) is not None else None,
        "pricing_breakdown": pricing_breakdown,
        "destination": resolve_destination(country=country, city=city),
    }


def partner_can_service_order(partner: LogisticsPartner, order: Order, db: Session) -> bool:
    if not partner_is_profile_approved(partner):
        return False
    destination = resolve_destination(order=order)
    if not destination["country_code"]:
        return False
    quote = quote_shipping_for_destination(
        db,
        country=cast(str | None, destination["country"]),
        city=cast(str | None, destination["city"]),
        partner_id=cast(int, getattr(partner, "id")),
    )
    return quote is not None
