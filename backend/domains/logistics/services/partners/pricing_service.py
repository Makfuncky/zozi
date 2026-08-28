from __future__ import annotations

"""Logistics partner pricing service — pricing profiles, category rules, vehicle rules."""

from decimal import Decimal
from typing import Any, Optional, cast
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from domains.governance.models.core import CityDistanceMatrix
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.orders.models.order_entities import Order
from kernel.money import round_money, to_decimal


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

_COUNTRY_CODE_ALIASES: dict[str, str] = {
    "AE": "AE", "UAE": "AE", "UNITEDARABEMIRATES": "AE", "EMIRATES": "AE",
    "PK": "PK", "PAKISTAN": "PK",
    "OM": "OM", "OMAN": "OM",
    "SA": "SA", "SAUDIARABIA": "SA", "KSA": "SA",
    "IN": "IN", "INDIA": "IN",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US",
    "GB": "GB", "UK": "GB", "UNITEDKINGDOM": "GB",
    "KW": "KW", "KUWAIT": "KW",
    "QA": "QA", "QATAR": "QA",
    "BH": "BH", "BAHRAIN": "BH",
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
    return letters[:2]


def normalize_city_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


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


def lookup_city_distance_km(
    db: Session,
    *,
    origin_country_code: str | None,
    origin_city_name: str | None,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> Decimal:
    """Return the distance in km between an origin/destination city pair."""
    if not (origin_country_code and origin_city_name and destination_country_code and destination_city_name):
        return Decimal("0")

    origin_cc = normalize_country_code(origin_country_code)
    dest_cc = normalize_country_code(destination_country_code)
    origin_key = normalize_city_name(origin_city_name)
    dest_key = normalize_city_name(destination_city_name)

    row = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
            func.lower(func.trim(CityDistanceMatrix.origin_city_name)) == origin_key,
            func.lower(func.trim(CityDistanceMatrix.destination_city_name)) == dest_key,
        )
        .first()
    )
    if row is not None:
        return to_decimal(getattr(row, "distance_km", 0) or 0)
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


def partner_is_profile_approved(partner: LogisticsPartner | None) -> bool:
    if partner is None:
        return False
    return (
        cast(str | None, getattr(partner, "status", None)) == "active"
        and cast(str | None, getattr(partner, "verification_status", None)) == APPROVED_PROFILE_STATUS
    )


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
            LogisticsCategoryPricingRule.is_active == True,
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
            LogisticsVehicleRule.is_active == True,
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
            LogisticsPricingProfile.is_active == True,
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
