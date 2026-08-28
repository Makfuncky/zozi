from __future__ import annotations

"""Logistics pricing service — pricing engine for logistics partners."""

from typing import Any, Optional, cast
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.services.partners.partner_service import _get_partner_for_user, _sanitize_optional_string
from domains.logistics.services.partners.pricing_service import (
    normalize_country_code,
    serialize_service_area,
    serialize_pricing_profile,
    serialize_category_pricing_rule,
    serialize_vehicle_rule,
)
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _parse_optional_service_area_id(data: dict[str, Any], *, field_name: str = "service_area_id") -> int | None:
    service_area_id_raw = data.get(field_name)
    if service_area_id_raw in ("", None):
        return None
    try:
        return int(service_area_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be an integer") from exc


def _validate_partner_service_area(db: Session, *, partner_id: int, service_area_id: int | None, detail: str) -> None:
    if service_area_id is None:
        return
    area = (
        db.query(LogisticsPartnerServiceArea)
        .filter(
            LogisticsPartnerServiceArea.id == service_area_id,
            LogisticsPartnerServiceArea.partner_id == partner_id,
        )
        .first()
    )
    if not area:
        raise HTTPException(status_code=404, detail=detail)


def _parse_partner_service_area_payload(data: dict[str, Any]) -> dict[str, Any]:
    country_name = _sanitize_optional_string(data.get("country_name"), max_length=120)
    country_code = _sanitize_optional_string(data.get("country_code"), max_length=10)
    city_name = _sanitize_optional_string(data.get("city_name"), max_length=120) or "Default City"
    origin_city = _sanitize_optional_string(data.get("origin_city"), max_length=120) or city_name
    zone_label = _sanitize_optional_string(data.get("zone_label"), max_length=120)
    currency = _sanitize_optional_string(data.get("currency"), max_length=10) or "AED"
    country_code = normalize_country_code(country_code or country_name)
    if not country_name or not country_code:
        raise HTTPException(status_code=422, detail="country_name or country_code is required")
    try:
        charge_amount = float(data.get("charge_amount", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="charge_amount must be a number") from exc
    if charge_amount < 0:
        raise HTTPException(status_code=422, detail="charge_amount must be non-negative")

    def _parse_optional_non_negative_amount(field_name: str) -> float | None:
        raw_value = data.get(field_name)
        if raw_value in ("", None):
            return None
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field_name} must be a number") from exc
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"{field_name} must be non-negative")
        return parsed

    pickup_charge = _parse_optional_non_negative_amount("pickup_charge")
    dropoff_charge = _parse_optional_non_negative_amount("dropoff_charge")
    minimum_charge = _parse_optional_non_negative_amount("minimum_charge")
    per_kg_rate = _parse_optional_non_negative_amount("per_kg_rate")
    per_km_rate = _parse_optional_non_negative_amount("per_km_rate")
    if pickup_charge is not None and dropoff_charge is not None:
        split_total = round(pickup_charge + dropoff_charge, 2)
        if abs(split_total - round(charge_amount, 2)) > 0.01:
            raise HTTPException(
                status_code=422,
                detail="pickup_charge + dropoff_charge must equal charge_amount",
            )

    raw_fuel_multiplier = data.get("fuel_multiplier")
    if raw_fuel_multiplier in ("", None):
        fuel_multiplier = 1.0
    else:
        try:
            fuel_multiplier = float(raw_fuel_multiplier)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="fuel_multiplier must be a number") from exc
        if fuel_multiplier <= 0:
            raise HTTPException(status_code=422, detail="fuel_multiplier must be greater than 0")

    delivery_days_min = data.get("delivery_days_min")
    delivery_days_max = data.get("delivery_days_max")
    if delivery_days_min in ("", None):
        delivery_days_min = None
    if delivery_days_max in ("", None):
        delivery_days_max = None
    try:
        delivery_days_min = int(delivery_days_min) if delivery_days_min is not None else None
        delivery_days_max = int(delivery_days_max) if delivery_days_max is not None else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="delivery_days_min and delivery_days_max must be integers") from exc

    if delivery_days_min is not None and delivery_days_min < 0:
        raise HTTPException(status_code=422, detail="delivery_days_min must be non-negative")
    if delivery_days_max is not None and delivery_days_max < 0:
        raise HTTPException(status_code=422, detail="delivery_days_max must be non-negative")
    if delivery_days_min is not None and delivery_days_max is not None and delivery_days_min > delivery_days_max:
        raise HTTPException(status_code=422, detail="delivery_days_min cannot exceed delivery_days_max")

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    try:
        latitude = float(latitude) if latitude not in (None, "") else None
        longitude = float(longitude) if longitude not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="latitude and longitude must be numbers") from exc

    return {
        "country_name": country_name,
        "country_code": country_code,
        "city_name": city_name,
        "origin_city": origin_city,
        "zone_label": zone_label,
        "charge_amount": charge_amount,
        "minimum_charge": minimum_charge,
        "per_kg_rate": per_kg_rate,
        "per_km_rate": per_km_rate,
        "fuel_multiplier": fuel_multiplier,
        "pickup_charge": pickup_charge,
        "dropoff_charge": dropoff_charge,
        "currency": currency,
        "latitude": latitude,
        "longitude": longitude,
        "delivery_days_min": delivery_days_min,
        "delivery_days_max": delivery_days_max,
        "is_active": bool(data.get("is_active", True)),
    }


def _parse_pricing_profile_payload(data: dict[str, Any]) -> dict[str, Any]:
    profile_name = _sanitize_optional_string(data.get("profile_name"), max_length=120)
    currency = _sanitize_optional_string(data.get("currency"), max_length=10) or "AED"

    def _parse_optional_non_negative_amount(field_name: str) -> float | None:
        raw_value = data.get(field_name)
        if raw_value in ("", None):
            return None
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field_name} must be a number") from exc
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"{field_name} must be non-negative")
        return parsed

    service_area_id_raw = data.get("service_area_id")
    if service_area_id_raw in ("", None):
        service_area_id = None
    else:
        try:
            service_area_id = int(service_area_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="service_area_id must be an integer") from exc

    raw_fuel_multiplier = data.get("fuel_multiplier")
    if raw_fuel_multiplier in ("", None):
        fuel_multiplier = None
    else:
        try:
            fuel_multiplier = float(raw_fuel_multiplier)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="fuel_multiplier must be a number") from exc
        if fuel_multiplier <= 0:
            raise HTTPException(status_code=422, detail="fuel_multiplier must be greater than 0")

    bulk_discount_threshold_kg = _parse_optional_non_negative_amount("bulk_discount_threshold_kg")
    bulk_discount_percent = _parse_optional_non_negative_amount("bulk_discount_percent")
    if (bulk_discount_threshold_kg is None) != (bulk_discount_percent is None):
        raise HTTPException(status_code=422, detail="bulk_discount_threshold_kg and bulk_discount_percent must be provided together")
    if bulk_discount_percent is not None and bulk_discount_percent > 100:
        raise HTTPException(status_code=422, detail="bulk_discount_percent cannot exceed 100")

    minimum_charge = _parse_optional_non_negative_amount("minimum_charge")
    maximum_charge = _parse_optional_non_negative_amount("maximum_charge")
    if minimum_charge is not None and maximum_charge is not None and maximum_charge < minimum_charge:
        raise HTTPException(status_code=422, detail="maximum_charge cannot be less than minimum_charge")

    payload = {
        "service_area_id": service_area_id,
        "profile_name": profile_name,
        "base_in_city_fee": _parse_optional_non_negative_amount("base_in_city_fee"),
        "base_inter_city_fee": _parse_optional_non_negative_amount("base_inter_city_fee"),
        "per_km_rate": _parse_optional_non_negative_amount("per_km_rate"),
        "per_kg_rate": _parse_optional_non_negative_amount("per_kg_rate"),
        "minimum_charge": minimum_charge,
        "maximum_charge": maximum_charge,
        "fuel_multiplier": fuel_multiplier,
        "bulk_discount_threshold_kg": bulk_discount_threshold_kg,
        "bulk_discount_percent": bulk_discount_percent,
        "currency": currency,
        "is_active": bool(data.get("is_active", True)),
    }
    has_pricing_value = any(
        payload[key] is not None
        for key in (
            "base_in_city_fee",
            "base_inter_city_fee",
            "per_km_rate",
            "per_kg_rate",
            "minimum_charge",
            "maximum_charge",
            "fuel_multiplier",
            "bulk_discount_threshold_kg",
            "bulk_discount_percent",
        )
    )
    if not has_pricing_value:
        raise HTTPException(status_code=422, detail="At least one pricing profile field is required")
    return payload


def _parse_category_pricing_rule_payload(data: dict[str, Any]) -> dict[str, Any]:
    category_name = _sanitize_optional_string(data.get("category_name"), max_length=120)
    if not category_name:
        raise HTTPException(status_code=422, detail="category_name is required")
    currency = _sanitize_optional_string(data.get("currency"), max_length=10) or "AED"

    def _parse_optional_non_negative_amount(field_name: str) -> float | None:
        raw_value = data.get(field_name)
        if raw_value in ("", None):
            return None
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field_name} must be a number") from exc
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"{field_name} must be non-negative")
        return parsed

    payload = {
        "service_area_id": _parse_optional_service_area_id(data),
        "category_name": category_name,
        "flat_fee_override": _parse_optional_non_negative_amount("flat_fee_override"),
        "special_handling_fee": _parse_optional_non_negative_amount("special_handling_fee"),
        "currency": currency,
        "is_active": bool(data.get("is_active", True)),
    }
    has_adjustment = any(
        payload[key] is not None
        for key in ("flat_fee_override", "special_handling_fee")
    )
    if not has_adjustment:
        raise HTTPException(status_code=422, detail="At least one category pricing adjustment is required (flat_fee_override or special_handling_fee)")
    return payload


def _parse_vehicle_rule_payload(data: dict[str, Any]) -> dict[str, Any]:
    vehicle_type = _sanitize_optional_string(data.get("vehicle_type"), max_length=50)
    if not vehicle_type:
        raise HTTPException(status_code=422, detail="vehicle_type is required")

    route_scope = _sanitize_optional_string(data.get("route_scope"), max_length=20) or "any"
    route_scope = route_scope.lower()
    if route_scope not in {"any", "in_city", "inter_city"}:
        raise HTTPException(status_code=422, detail="route_scope must be one of: any, in_city, inter_city")

    def _parse_optional_non_negative_amount(field_name: str) -> float | None:
        raw_value = data.get(field_name)
        if raw_value in ("", None):
            return None
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field_name} must be a number") from exc
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"{field_name} must be non-negative")
        return parsed

    raw_cost_multiplier = data.get("cost_multiplier")
    if raw_cost_multiplier in ("", None):
        cost_multiplier = 1.0
    else:
        try:
            cost_multiplier = float(raw_cost_multiplier)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="cost_multiplier must be a number") from exc
        if cost_multiplier <= 0:
            raise HTTPException(status_code=422, detail="cost_multiplier must be greater than 0")

    raw_priority_rank = data.get("priority_rank")
    if raw_priority_rank in ("", None):
        priority_rank = 100
    else:
        try:
            priority_rank = int(raw_priority_rank)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="priority_rank must be an integer") from exc

    return {
        "service_area_id": _parse_optional_service_area_id(data),
        "route_scope": route_scope,
        "vehicle_type": vehicle_type,
        "max_weight_kg": _parse_optional_non_negative_amount("max_weight_kg"),
        "max_volume_cm3": _parse_optional_non_negative_amount("max_volume_cm3"),
        "cost_multiplier": cost_multiplier,
        "priority_rank": priority_rank,
        "is_active": bool(data.get("is_active", True)),
    }


def list_my_partner_service_areas(
    current_user: dict,
    db: Session,
    *,
    partner_id: int | None = None,
    approval_status: str | None = None,
) -> list[dict[str, Any]]:
    role = current_user.get("role")
    query = db.query(LogisticsPartnerServiceArea)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsPartnerServiceArea.partner_id == partner.id)
    elif role in ("admin", "sub_admin"):
        if partner_id is not None:
            query = query.filter(LogisticsPartnerServiceArea.partner_id == partner_id)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    normalized_status = str(approval_status or "").strip().lower()
    if normalized_status:
        query = query.filter(LogisticsPartnerServiceArea.approval_status == normalized_status)

    rows = (
        query.order_by(desc(LogisticsPartnerServiceArea.updated_at), desc(LogisticsPartnerServiceArea.id)).all()
    )
    return [serialize_service_area(row) for row in rows]


def list_my_partner_pricing_profiles(
    current_user: dict,
    db: Session,
    *,
    partner_id: int | None = None,
    approval_status: str | None = None,
    service_area_id: int | None = None,
) -> list[dict[str, Any]]:
    role = current_user.get("role")
    query = db.query(LogisticsPricingProfile)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsPricingProfile.partner_id == partner.id)
    elif role in ("admin", "sub_admin"):
        if partner_id is not None:
            query = query.filter(LogisticsPricingProfile.partner_id == partner_id)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    normalized_status = str(approval_status or "").strip().lower()
    if normalized_status:
        query = query.filter(LogisticsPricingProfile.approval_status == normalized_status)
    if service_area_id is not None:
        query = query.filter(LogisticsPricingProfile.service_area_id == service_area_id)

    rows = query.order_by(desc(LogisticsPricingProfile.updated_at), desc(LogisticsPricingProfile.id)).all()
    return [serialize_pricing_profile(row) for row in rows]


def list_my_partner_category_rules(
    current_user: dict,
    db: Session,
    *,
    partner_id: int | None = None,
    approval_status: str | None = None,
    service_area_id: int | None = None,
) -> list[dict[str, Any]]:
    role = current_user.get("role")
    query = db.query(LogisticsCategoryPricingRule)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsCategoryPricingRule.partner_id == partner.id)
    elif role in ("admin", "sub_admin"):
        if partner_id is not None:
            query = query.filter(LogisticsCategoryPricingRule.partner_id == partner_id)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    normalized_status = str(approval_status or "").strip().lower()
    if normalized_status:
        query = query.filter(LogisticsCategoryPricingRule.approval_status == normalized_status)
    if service_area_id is not None:
        query = query.filter(LogisticsCategoryPricingRule.service_area_id == service_area_id)

    rows = query.order_by(desc(LogisticsCategoryPricingRule.updated_at), desc(LogisticsCategoryPricingRule.id)).all()
    return [serialize_category_pricing_rule(row) for row in rows]


def list_my_partner_vehicle_rules(
    current_user: dict,
    db: Session,
    *,
    partner_id: int | None = None,
    approval_status: str | None = None,
    service_area_id: int | None = None,
) -> list[dict[str, Any]]:
    role = current_user.get("role")
    query = db.query(LogisticsVehicleRule)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsVehicleRule.partner_id == partner.id)
    elif role in ("admin", "sub_admin"):
        if partner_id is not None:
            query = query.filter(LogisticsVehicleRule.partner_id == partner_id)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    normalized_status = str(approval_status or "").strip().lower()
    if normalized_status:
        query = query.filter(LogisticsVehicleRule.approval_status == normalized_status)
    if service_area_id is not None:
        query = query.filter(LogisticsVehicleRule.service_area_id == service_area_id)

    rows = query.order_by(desc(LogisticsVehicleRule.updated_at), desc(LogisticsVehicleRule.id)).all()
    return [serialize_vehicle_rule(row) for row in rows]


def upsert_my_partner_service_area(area_id: int | None, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    if role in ("admin", "sub_admin"):
        partner_id_raw = data.get("partner_id")
        if not partner_id_raw:
            raise HTTPException(status_code=422, detail="partner_id is required when admin manages a service area")
        try:
            target_partner_id = int(partner_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="partner_id must be an integer") from exc
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == target_partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Logistics partner not found")
    elif role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    payload = _parse_partner_service_area_payload(cast(dict[str, Any], data))

    if area_id is None:
        area = LogisticsPartnerServiceArea(partner_id=partner.id)
        db.add(area)
    else:
        area = (
            db.query(LogisticsPartnerServiceArea)
            .filter(
                LogisticsPartnerServiceArea.id == area_id,
                LogisticsPartnerServiceArea.partner_id == partner.id,
            )
            .first()
        )
        if not area:
            raise HTTPException(status_code=404, detail="Service area not found")

    for key, value in payload.items():
        setattr(area, key, value)

    if role in ("admin", "sub_admin"):
        setattr(area, "approval_status", "approved")
        setattr(area, "review_note", "Set directly by admin")
        setattr(area, "reviewed_by", current_user["id"])
        setattr(area, "reviewed_at", _utcnow())
    else:
        setattr(area, "approval_status", "pending")
        setattr(area, "review_note", "Awaiting admin approval")
        setattr(area, "reviewed_by", None)
        setattr(area, "reviewed_at", None)
    setattr(area, "updated_at", _utcnow())
    db.commit()
    db.refresh(area)
    return serialize_service_area(area)


def upsert_my_partner_pricing_profile(profile_id: int | None, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    if role in ("admin", "sub_admin"):
        partner_id_raw = data.get("partner_id")
        if not partner_id_raw:
            raise HTTPException(status_code=422, detail="partner_id is required when admin manages a pricing profile")
        try:
            target_partner_id = int(partner_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="partner_id must be an integer") from exc
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == target_partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Logistics partner not found")
    elif role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    payload = _parse_pricing_profile_payload(cast(dict[str, Any], data))

    service_area_id = cast(int | None, payload.get("service_area_id"))
    _validate_partner_service_area(
        db,
        partner_id=partner.id,
        service_area_id=service_area_id,
        detail="Service area not found for pricing profile",
    )

    if profile_id is None:
        profile = LogisticsPricingProfile(partner_id=partner.id)
        db.add(profile)
    else:
        profile = (
            db.query(LogisticsPricingProfile)
            .filter(
                LogisticsPricingProfile.id == profile_id,
                LogisticsPricingProfile.partner_id == partner.id,
            )
            .first()
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Pricing profile not found")

    for key, value in payload.items():
        setattr(profile, key, value)

    if role in ("admin", "sub_admin"):
        setattr(profile, "approval_status", "approved")
        setattr(profile, "review_note", "Set directly by admin")
        setattr(profile, "reviewed_by", current_user["id"])
        setattr(profile, "reviewed_at", _utcnow())
    else:
        setattr(profile, "approval_status", "pending")
        setattr(profile, "review_note", "Awaiting admin approval")
        setattr(profile, "reviewed_by", None)
        setattr(profile, "reviewed_at", None)
    setattr(profile, "updated_at", _utcnow())
    db.commit()
    db.refresh(profile)
    return serialize_pricing_profile(profile)


def upsert_my_partner_category_rule(rule_id: int | None, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    if role in ("admin", "sub_admin"):
        partner_id_raw = data.get("partner_id")
        if not partner_id_raw:
            raise HTTPException(status_code=422, detail="partner_id is required when admin manages a category rule")
        try:
            target_partner_id = int(partner_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="partner_id must be an integer") from exc
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == target_partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Logistics partner not found")
    elif role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    payload = _parse_category_pricing_rule_payload(cast(dict[str, Any], data))

    service_area_id = cast(int | None, payload.get("service_area_id"))
    _validate_partner_service_area(
        db,
        partner_id=partner.id,
        service_area_id=service_area_id,
        detail="Service area not found for category rule",
    )

    if rule_id is None:
        rule = LogisticsCategoryPricingRule(partner_id=partner.id)
        db.add(rule)
    else:
        rule = (
            db.query(LogisticsCategoryPricingRule)
            .filter(
                LogisticsCategoryPricingRule.id == rule_id,
                LogisticsCategoryPricingRule.partner_id == partner.id,
            )
            .first()
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Category pricing rule not found")

    for key, value in payload.items():
        setattr(rule, key, value)

    if role in ("admin", "sub_admin"):
        setattr(rule, "approval_status", "approved")
        setattr(rule, "review_note", "Set directly by admin")
        setattr(rule, "reviewed_by", current_user["id"])
        setattr(rule, "reviewed_at", _utcnow())
    else:
        setattr(rule, "approval_status", "pending")
        setattr(rule, "review_note", "Awaiting admin approval")
        setattr(rule, "reviewed_by", None)
        setattr(rule, "reviewed_at", None)
    setattr(rule, "updated_at", _utcnow())
    db.commit()
    db.refresh(rule)
    return serialize_category_pricing_rule(rule)


def upsert_my_partner_vehicle_rule(rule_id: int | None, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    if role in ("admin", "sub_admin"):
        partner_id_raw = data.get("partner_id")
        if not partner_id_raw:
            raise HTTPException(status_code=422, detail="partner_id is required when admin manages a vehicle rule")
        try:
            target_partner_id = int(partner_id_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="partner_id must be an integer") from exc
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == target_partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Logistics partner not found")
    elif role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
    else:
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    payload = _parse_vehicle_rule_payload(cast(dict[str, Any], data))

    service_area_id = cast(int | None, payload.get("service_area_id"))
    _validate_partner_service_area(
        db,
        partner_id=partner.id,
        service_area_id=service_area_id,
        detail="Service area not found for vehicle rule",
    )

    if rule_id is None:
        rule = LogisticsVehicleRule(partner_id=partner.id)
        db.add(rule)
    else:
        rule = (
            db.query(LogisticsVehicleRule)
            .filter(
                LogisticsVehicleRule.id == rule_id,
                LogisticsVehicleRule.partner_id == partner.id,
            )
            .first()
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Vehicle rule not found")

    for key, value in payload.items():
        setattr(rule, key, value)

    if role in ("admin", "sub_admin"):
        setattr(rule, "approval_status", "approved")
        setattr(rule, "review_note", "Set directly by admin")
        setattr(rule, "reviewed_by", current_user["id"])
        setattr(rule, "reviewed_at", _utcnow())
    else:
        setattr(rule, "approval_status", "pending")
        setattr(rule, "review_note", "Awaiting admin approval")
        setattr(rule, "reviewed_by", None)
        setattr(rule, "reviewed_at", None)
    setattr(rule, "updated_at", _utcnow())
    db.commit()
    db.refresh(rule)
    return serialize_vehicle_rule(rule)


def delete_my_partner_pricing_profile(profile_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    query = db.query(LogisticsPricingProfile).filter(LogisticsPricingProfile.id == profile_id)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsPricingProfile.partner_id == partner.id)
    elif role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    profile = query.first()
    if not profile:
        raise HTTPException(status_code=404, detail="Pricing profile not found")
    db.delete(profile)
    db.commit()
    return {"detail": "Pricing profile deleted"}


def delete_my_partner_category_rule(rule_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    query = db.query(LogisticsCategoryPricingRule).filter(LogisticsCategoryPricingRule.id == rule_id)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsCategoryPricingRule.partner_id == partner.id)
    elif role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    rule = query.first()
    if not rule:
        raise HTTPException(status_code=404, detail="Category pricing rule not found")
    db.delete(rule)
    db.commit()
    return {"detail": "Category pricing rule deleted"}


def delete_my_partner_vehicle_rule(rule_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    query = db.query(LogisticsVehicleRule).filter(LogisticsVehicleRule.id == rule_id)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsVehicleRule.partner_id == partner.id)
    elif role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    rule = query.first()
    if not rule:
        raise HTTPException(status_code=404, detail="Vehicle rule not found")
    db.delete(rule)
    db.commit()
    return {"detail": "Vehicle rule deleted"}


def delete_my_partner_service_area(area_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    role = current_user.get("role")
    query = db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == area_id)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        query = query.filter(LogisticsPartnerServiceArea.partner_id == partner.id)
    elif role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    area = query.first()
    if not area:
        raise HTTPException(status_code=404, detail="Service area not found")
    db.delete(area)
    db.commit()
    return {"detail": "Service area deleted"}
