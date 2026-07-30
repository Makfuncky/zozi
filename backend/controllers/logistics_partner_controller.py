"""
Logistics Partner Controller — external logistics partner management.
Partners get limited dashboard access to manage their assigned shipments.
"""
from __future__ import annotations
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any, Optional, cast

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func

from controllers.audit_controller import AuditAction, audit_log
from models import CityDistanceMatrix, LogisticsCategoryPricingRule, LogisticsCODRemittanceReceipt, LogisticsPartner, LogisticsPartnerBankAccount, LogisticsPartnerDocument, LogisticsPartnerPayout, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsSettlement, LogisticsVehicleRule, Notification, Order, OrderLogisticsAllocation, Shipment, ShipmentConfirmation, ShipmentEvent, SupplierProfile, TransactionLedger, User
from services.cash_management_service import apply_shipment_vehicle_selection, create_cod_remittance_receipt, deserialize_pricing_breakdown_json, effective_allocation_delivery_amounts, list_cod_remittance_receipts, serialize_cod_remittance_receipt
from services.finance_transfer_service import build_transfer_reference
from services.logistics_partner_pricing import normalize_city_name, normalize_country_code, partner_can_service_order, partner_is_profile_approved, quote_shipping_for_destination, serialize_category_pricing_rule, serialize_pricing_profile, serialize_service_area, serialize_vehicle_rule
from utils.order_tracking import (
    canonical_scan_code,
    derive_order_financials,
    reconcile_order_status,
    serialize_shipment_confirmation,
    shipment_scan_codes,
    shipment_status_label,
)
from utils.auth import get_password_hash
from utils.realtime import logistics_realtime_hub

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731
ACTIVE_SHIPMENT_STATUSES = ("processing", "picking_up", "shipped", "in_transit")
SLA_ALERT_STATUSES = ("pending", "processing", "picking_up", "shipped", "in_transit")
PARTNER_PICKUP_READY_STATUS = "processing"
PARTNER_HIDDEN_STATUS = "picking_up"
PARTNER_VISIBLE_ASSIGNED_STATUSES = ("picking_up", "shipped", "in_transit", "delivered", "failed", "returned")
CURRENT_LOGISTICS_TERMS_VERSION = "2026-04"
ANALYTICS_LOOKBACK_DAYS = {"7d": 7, "30d": 30, "90d": 90}

_PARTNER_DELETE_BLOCKING_MODELS: list[tuple[Any, Any, str]] = [
    (LogisticsSettlement, LogisticsSettlement.partner_id, "logistics settlement record(s)"),
    (LogisticsPartnerPayout, LogisticsPartnerPayout.partner_id, "partner payout record(s)"),
    (LogisticsCODRemittanceReceipt, LogisticsCODRemittanceReceipt.partner_id, "COD remittance receipt(s)"),
    (TransactionLedger, TransactionLedger.logistics_partner_id, "transaction ledger record(s)"),
    (OrderLogisticsAllocation, OrderLogisticsAllocation.partner_id, "order logistics allocation(s)"),
    (Shipment, Shipment.assigned_partner_id, "shipment assignment(s)"),
    (Order, Order.selected_partner_id, "order quote selection(s)"),
    (LogisticsPartnerBankAccount, LogisticsPartnerBankAccount.partner_id, "partner bank account record(s)"),
]


def _next_partner_code(db: Session, user_id: int) -> str:
    base_code = f"LPAUTO{user_id}"
    candidate = base_code
    suffix = 1
    while db.query(LogisticsPartner).filter(LogisticsPartner.code == candidate).first():
        suffix += 1
        candidate = f"{base_code}_{suffix}"
    return candidate


def _serialize_partner(p: LogisticsPartner, *, include_internal: bool = True) -> dict:
    coverage_regions = cast(Optional[str], getattr(p, "coverage_regions", None))
    service_types = cast(Optional[str], getattr(p, "service_types", None))
    social_links = cast(Optional[str], getattr(p, "social_links", None))
    created_at = cast(Optional[datetime], getattr(p, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(p, "updated_at", None))
    verified_at = cast(Optional[datetime], getattr(p, "verified_at", None))
    terms_accepted_at = cast(Optional[datetime], getattr(p, "terms_accepted_at", None))
    user = cast(Optional[User], getattr(p, "user", None))
    try:
        regions = json.loads(coverage_regions) if coverage_regions else []
    except (ValueError, TypeError):
        regions = []
    try:
        services = json.loads(service_types) if service_types else []
    except (ValueError, TypeError):
        services = []
    try:
        links = json.loads(social_links) if social_links else {}
    except (ValueError, TypeError):
        links = {}
    payload = {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "contact_name": p.contact_name,
        "contact_email": p.contact_email,
        "contact_phone": p.contact_phone,
        "website": p.website,
        "coverage_regions": regions,
        "service_types": services,
        "business_type": p.business_type,
        "country": getattr(p, "country_code", None),
        "region": p.region,
        "city": p.city,
        "address": p.address,
        "postal_code": p.postal_code,
        "tax_id": p.tax_id,
        "bio": p.bio,
        "about_us": p.about_us,
        "logo_url": p.logo_url,
        "banner_url": p.banner_url,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "social_links": links,
        "is_terms_accepted": bool(getattr(p, "is_terms_accepted", False)),
        "terms_version": p.terms_version,
        "terms_accepted_at": terms_accepted_at.isoformat() if terms_accepted_at else None,
        "verification_status": p.verification_status or "pending",
        "verification_note": p.verification_note,
        "verified_at": verified_at.isoformat() if verified_at else None,
        "status": p.status,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }
    if include_internal:
        payload["user_id"] = p.user_id
        payload["linked_username"] = cast(Optional[str], getattr(user, "username", None)) if user else None
        payload["linked_user_email"] = cast(Optional[str], getattr(user, "email", None)) if user else None
        payload["notes"] = p.notes
        payload["verified_by"] = p.verified_by
    return payload


def _sanitize_optional_string(value: Any, *, max_length: int = 500) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_length]


def _build_partner_delete_blocker(partner_id: int, db: Session) -> tuple[int, str] | None:
    for model, column, label in _PARTNER_DELETE_BLOCKING_MODELS:
        related_count = db.query(func.count()).select_from(model).filter(column == partner_id).scalar() or 0
        if related_count > 0:
            return 409, f"Partner has {related_count} {label}. Suspend the partner instead of deleting."
    return None


def _parse_partner_social_links(value: Any) -> str:
    if not value:
        return json.dumps({})
    if isinstance(value, dict):
        normalized = {
            str(key).strip()[:40]: str(link).strip()[:300]
            for key, link in value.items()
            if str(key).strip() and str(link).strip()
        }
        return json.dumps(normalized)
    raise HTTPException(status_code=422, detail="social_links must be an object")


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


def _parse_optional_service_area_id(data: dict[str, Any], *, field_name: str = "service_area_id") -> int | None:
    service_area_id_raw = data.get(field_name)
    if service_area_id_raw in ("", None):
        return None
    try:
        return int(service_area_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be an integer") from exc


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


def _pickup_visible_to_partner(shipment: Shipment, partner: LogisticsPartner, db: Session) -> bool:
    if not _is_pickup_ready(shipment):
        return False
    order = cast(Optional[Order], getattr(shipment, "order", None))
    if order is None:
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order is None:
        return False
    return partner_can_service_order(partner, order, db)


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_partner_for_user(user_id: int, db: Session) -> LogisticsPartner:
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    if not partner:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or cast(str, getattr(user, "role", "")) != "logistics_partner":
            raise HTTPException(status_code=403, detail="No logistics partner profile found")

        partner = LogisticsPartner(
            name=f"{cast(str, getattr(user, 'username', 'Partner'))} Logistics",
            code=_next_partner_code(db, user_id),
            contact_name=cast(Optional[str], getattr(user, "username", None)),
            contact_email=cast(Optional[str], getattr(user, "email", None)),
            contact_phone=cast(Optional[str], getattr(user, "phone", None)),
            status="pending_onboarding",
            user_id=user_id,
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
    return partner


def _partner_is_active(partner: LogisticsPartner) -> bool:
    return cast(str, getattr(partner, "status", "")) == "active"


def _resolve_partner_user_link(
    data: dict,
    db: Session,
    *,
    existing_user_id: int | None = None,
    partner_id: int | None = None,
    allow_existing_link: bool = False,
) -> int | None:
    link_keys = ("user_id", "portal_user_email", "linked_user_email", "user_email")
    if not any(key in data for key in link_keys):
        return existing_user_id

    raw_user_id = data.get("user_id")
    raw_email = str(
        data.get("portal_user_email")
        or data.get("linked_user_email")
        or data.get("user_email")
        or ""
    ).strip()

    if raw_user_id in (None, "") and raw_email == "":
        return None

    user: User | None = None
    if raw_user_id not in (None, ""):
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="user_id must be an integer") from exc
        user = db.query(User).filter(User.id == user_id).first()
    elif raw_email:
        user = db.query(User).filter(func.lower(User.email) == raw_email.lower()).first()

    if not user:
        raise HTTPException(status_code=404, detail="Linked logistics partner user not found")
    if cast(str, getattr(user, "role", "")) != "logistics_partner":
        raise HTTPException(status_code=422, detail="Linked user must have logistics_partner role")

    if not allow_existing_link:
        existing_partner_q = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user.id)
        if partner_id is not None:
            existing_partner_q = existing_partner_q.filter(LogisticsPartner.id != partner_id)
        if existing_partner_q.first():
            raise HTTPException(status_code=409, detail="User is already linked to another logistics partner")

    return cast(int, getattr(user, "id"))


def get_my_partner_profile(current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    return _serialize_partner(_get_partner_for_user(current_user["id"], db))


def update_my_partner_profile(data: dict, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    partner = _get_partner_for_user(current_user["id"], db)
    allowed_fields = {
        "name",
        "contact_name",
        "contact_email",
        "contact_phone",
        "website",
        "business_type",
        "country",
        "region",
        "city",
        "address",
        "postal_code",
        "tax_id",
        "bio",
        "about_us",
        "logo_url",
        "banner_url",
    }
    review_sensitive_fields = {
        "name",
        "contact_name",
        "contact_email",
        "contact_phone",
        "website",
        "business_type",
        "country",
        "region",
        "city",
        "address",
        "postal_code",
        "tax_id",
        "bio",
        "about_us",
        "logo_url",
        "banner_url",
        "latitude",
        "longitude",
        "social_links",
        "coverage_regions",
        "service_types",
    }

    changed = False
    for field in allowed_fields:
        if field not in data:
            continue
        value = _sanitize_optional_string(data.get(field), max_length=5000 if field in {"bio", "about_us", "address"} else 500)
        if field == "website" and value and not value.startswith(("http://", "https://")):
            value = f"https://{value}"
        if getattr(partner, field) != value:
            setattr(partner, field, value)
            changed = True

    if "latitude" in data:
        latitude = data.get("latitude")
        try:
            latitude = float(latitude) if latitude not in (None, "") else None
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="latitude must be a number") from exc
        if getattr(partner, "latitude") != latitude:
            setattr(partner, "latitude", latitude)
            changed = True

    if "longitude" in data:
        longitude = data.get("longitude")
        try:
            longitude = float(longitude) if longitude not in (None, "") else None
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="longitude must be a number") from exc
        if getattr(partner, "longitude") != longitude:
            setattr(partner, "longitude", longitude)
            changed = True

    if "social_links" in data:
        social_links = _parse_partner_social_links(data.get("social_links"))
        if getattr(partner, "social_links") != social_links:
            setattr(partner, "social_links", social_links)
            changed = True

    if "coverage_regions" in data:
        coverage_regions = json.dumps(data.get("coverage_regions", []))
        if getattr(partner, "coverage_regions") != coverage_regions:
            setattr(partner, "coverage_regions", coverage_regions)
            changed = True

    if "service_types" in data:
        service_types = json.dumps(data.get("service_types", []))
        if getattr(partner, "service_types") != service_types:
            setattr(partner, "service_types", service_types)
            changed = True

    if changed and cast(str | None, getattr(partner, "verification_status", None)) == "approved":
        setattr(partner, "verification_status", "under_review")
        setattr(partner, "verification_note", "Profile changes submitted and awaiting admin approval")
        setattr(partner, "verified_at", None)
        setattr(partner, "verified_by", None)

    setattr(partner, "updated_at", _utcnow())
    db.commit()
    db.refresh(partner)
    return _serialize_partner(partner)


def accept_partner_terms(current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    setattr(partner, "is_terms_accepted", True)
    setattr(partner, "terms_version", CURRENT_LOGISTICS_TERMS_VERSION)
    setattr(partner, "terms_accepted_at", _utcnow())
    setattr(partner, "updated_at", _utcnow())
    db.commit()
    return {"detail": "Terms accepted", "terms_version": CURRENT_LOGISTICS_TERMS_VERSION}


def submit_partner_profile_for_review(current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    required_fields = {
        "name": partner.name,
        "country": partner.country,
        "city": partner.city,
        "address": partner.address,
        "contact_phone": partner.contact_phone,
    }
    missing = [label for label, value in required_fields.items() if not str(value or "").strip()]
    if missing:
        raise HTTPException(status_code=422, detail=f"Complete required profile fields before review: {', '.join(missing)}")
    if not bool(getattr(partner, "is_terms_accepted", False)):
        raise HTTPException(status_code=422, detail="Accept terms before requesting admin approval")
    setattr(partner, "verification_status", "under_review")
    setattr(partner, "verification_note", "Awaiting admin review")
    setattr(partner, "verified_at", None)
    setattr(partner, "verified_by", None)
    setattr(partner, "updated_at", _utcnow())
    db.commit()
    db.refresh(partner)
    return _serialize_partner(partner)


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


def review_partner_profile(partner_id: int, data: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "under_review", "pending"}:
        raise HTTPException(status_code=422, detail="status must be one of: pending, under_review, approved, rejected")
    note = _sanitize_optional_string(data.get("note"), max_length=2000)
    setattr(partner, "verification_status", decision)
    setattr(partner, "verification_note", note or ("Approved" if decision == "approved" else "Rejected" if decision == "rejected" else "Awaiting review"))
    setattr(partner, "verified_by", current_user["id"] if decision == "approved" else None)
    setattr(partner, "verified_at", _utcnow() if decision == "approved" else None)
    if decision == "approved" and cast(str | None, getattr(partner, "status", None)) == "pending_onboarding":
        setattr(partner, "status", "active")
    db.commit()
    db.refresh(partner)
    return _serialize_partner(partner)


def review_partner_service_area(area_id: int, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    area = db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Service area not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=422, detail="status must be one of: pending, approved, rejected")
    note = _sanitize_optional_string(data.get("note"), max_length=2000)
    setattr(area, "approval_status", decision)
    setattr(area, "review_note", note or ("Approved" if decision == "approved" else "Rejected" if decision == "rejected" else "Awaiting review"))
    setattr(area, "reviewed_by", current_user["id"] if decision in {"approved", "rejected"} else None)
    setattr(area, "reviewed_at", _utcnow() if decision in {"approved", "rejected"} else None)
    setattr(area, "updated_at", _utcnow())
    db.commit()
    db.refresh(area)
    return serialize_service_area(area)


def review_partner_pricing_profile(profile_id: int, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    profile = db.query(LogisticsPricingProfile).filter(LogisticsPricingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Pricing profile not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=422, detail="status must be one of: pending, approved, rejected")
    note = _sanitize_optional_string(data.get("note"), max_length=2000)
    setattr(profile, "approval_status", decision)
    setattr(profile, "review_note", note or ("Approved" if decision == "approved" else "Rejected" if decision == "rejected" else "Awaiting review"))
    setattr(profile, "reviewed_by", current_user["id"] if decision in {"approved", "rejected"} else None)
    setattr(profile, "reviewed_at", _utcnow() if decision in {"approved", "rejected"} else None)
    setattr(profile, "updated_at", _utcnow())
    db.commit()
    db.refresh(profile)
    return serialize_pricing_profile(profile)


def review_partner_category_rule(rule_id: int, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    rule = db.query(LogisticsCategoryPricingRule).filter(LogisticsCategoryPricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Category pricing rule not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=422, detail="status must be one of: pending, approved, rejected")
    note = _sanitize_optional_string(data.get("note"), max_length=2000)
    setattr(rule, "approval_status", decision)
    setattr(rule, "review_note", note or ("Approved" if decision == "approved" else "Rejected" if decision == "rejected" else "Awaiting review"))
    setattr(rule, "reviewed_by", current_user["id"] if decision in {"approved", "rejected"} else None)
    setattr(rule, "reviewed_at", _utcnow() if decision in {"approved", "rejected"} else None)
    setattr(rule, "updated_at", _utcnow())
    db.commit()
    db.refresh(rule)
    return serialize_category_pricing_rule(rule)


def review_partner_vehicle_rule(rule_id: int, data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    rule = db.query(LogisticsVehicleRule).filter(LogisticsVehicleRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Vehicle rule not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=422, detail="status must be one of: pending, approved, rejected")
    note = _sanitize_optional_string(data.get("note"), max_length=2000)
    setattr(rule, "approval_status", decision)
    setattr(rule, "review_note", note or ("Approved" if decision == "approved" else "Rejected" if decision == "rejected" else "Awaiting review"))
    setattr(rule, "reviewed_by", current_user["id"] if decision in {"approved", "rejected"} else None)
    setattr(rule, "reviewed_at", _utcnow() if decision in {"approved", "rejected"} else None)
    setattr(rule, "updated_at", _utcnow())
    db.commit()
    db.refresh(rule)
    return serialize_vehicle_rule(rule)


def shipping_quote_for_customer(data: dict, db: Session) -> dict[str, Any]:
    country = str(data.get("country", "")).strip()
    city = str(data.get("city", "")).strip()
    try:
        total_weight_kg = float(data.get("total_weight_kg", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="total_weight_kg must be a number") from exc

    def _parse_optional_count(field_name: str) -> int | None:
        raw = data.get(field_name)
        if raw is None:
            return None
        try:
            parsed = int(raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"{field_name} must be an integer") from exc
        if parsed < 0:
            raise HTTPException(status_code=422, detail=f"{field_name} must be greater than or equal to 0")
        return parsed

    pickup_count = _parse_optional_count("pickup_count")
    dropoff_count = _parse_optional_count("dropoff_count")

    if not country:
        raise HTTPException(status_code=422, detail="country is required")
    quote = quote_shipping_for_destination(
        db,
        country=country,
        city=city,
        total_weight_kg=max(total_weight_kg, 0.0),
        pickup_count=pickup_count,
        dropoff_count=dropoff_count,
    )
    if quote is None:
        return {
            "shipping_amount": 0.0,
            "currency": "AED",
            "partner_id": None,
            "partner_name": None,
            "partner_code": None,
            "service_area": None,
            "destination": {"country": country, "country_code": normalize_country_code(country), "city": city or None, "city_key": None},
            "pricing_breakdown": None,
            "source": "none",
        }
    return {**quote, "source": "approved_logistics_partner"}


def list_public_partners(
    db: Session,
    q: str | None = None,
    country: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    region_code = normalize_country_code(country)
    query = db.query(LogisticsPartner).filter(
        LogisticsPartner.status == "active",
        LogisticsPartner.verification_status == "approved",
    )
    search = (q or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            LogisticsPartner.name.ilike(pattern)
            | LogisticsPartner.code.ilike(pattern)
            | LogisticsPartner.city.ilike(pattern)
            | LogisticsPartner.country_code.ilike(pattern)
            | LogisticsPartner.bio.ilike(pattern)
        )
    partners = query.order_by(LogisticsPartner.name.asc()).limit(min(limit, 100)).all()
    if region_code:
        partner_ids = [cast(int, getattr(partner, "id")) for partner in partners]
        if partner_ids:
            matching_ids = {
                cast(int, partner_id)
                for (partner_id,) in (
                    db.query(LogisticsPartnerServiceArea.partner_id)
                    .filter(
                        LogisticsPartnerServiceArea.partner_id.in_(partner_ids),
                        LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
                        LogisticsPartnerServiceArea.approval_status == "approved",
                        LogisticsPartnerServiceArea.country_code == region_code,
                    )
                    .all()
                )
            }
            partners = [
                partner
                for partner in partners
                if cast(int, getattr(partner, "id")) in matching_ids
            ]
        else:
            partners = []
    total = len(partners)
    partners = partners[: max(1, min(limit, 50))]
    return {
        "total": total,
        "items": [_serialize_partner(partner, include_internal=False) for partner in partners],
    }


def get_public_partner(partner_id: int, db: Session) -> dict[str, Any]:
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.id == partner_id,
        LogisticsPartner.status == "active",
        LogisticsPartner.verification_status == "approved",
    ).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    approved_areas = (
        db.query(LogisticsPartnerServiceArea)
        .filter(
            LogisticsPartnerServiceArea.partner_id == partner.id,
            LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
            LogisticsPartnerServiceArea.approval_status == "approved",
        )
        .order_by(LogisticsPartnerServiceArea.country_name.asc(), LogisticsPartnerServiceArea.city_name.asc(), LogisticsPartnerServiceArea.charge_amount.asc())
        .all()
    )
    payload = _serialize_partner(partner, include_internal=False)
    payload["service_areas"] = [serialize_service_area(area) for area in approved_areas]
    return payload


def _scoped_shipments_query(current_user: dict, db: Session) -> tuple:
    role = current_user.get("role")
    if role in ("admin", "sub_admin", "moderator"):
        return db.query(Shipment), None
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        return db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id), partner
    raise HTTPException(status_code=403, detail="Logistics partner access required")


def _partner_visible_shipments_query(current_user: dict, db: Session) -> tuple:
    role = current_user.get("role")
    if role in ("admin", "sub_admin", "moderator"):
        return db.query(Shipment), None
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        if not _partner_is_active(partner):
            return db.query(Shipment).filter(Shipment.id == -1), partner
        pickup_ready_event_exists = db.query(ShipmentEvent.id).filter(
            ShipmentEvent.shipment_id == Shipment.id,
            ShipmentEvent.event_type.in_(["supplier_prepared", "pickup_cancelled", "picked_from_supplier"]),
        ).exists()
        pickup_ready_clause = (
            (Shipment.status == PARTNER_PICKUP_READY_STATUS)
            & pickup_ready_event_exists
        )
        assigned_clause = (
            (Shipment.assigned_partner_id == partner.id)
            & (Shipment.status.in_(PARTNER_VISIBLE_ASSIGNED_STATUSES))
        )
        return db.query(Shipment).filter(pickup_ready_clause | assigned_clause), partner
    raise HTTPException(status_code=403, detail="Logistics partner access required")


def _is_shipment_visible_to_partner(shipment: Shipment, partner: LogisticsPartner, db: Session) -> bool:
    partner_id = cast(int, getattr(partner, "id"))
    assigned_to_partner = cast(Optional[int], getattr(shipment, "assigned_partner_id", None)) == partner_id
    visible_pickup = _pickup_visible_to_partner(shipment, partner, db)
    return assigned_to_partner or visible_pickup


def _is_pickup_ready(shipment: Shipment) -> bool:
    status = cast(str, getattr(shipment, "status", "pending"))
    if status != PARTNER_PICKUP_READY_STATUS:
        return False
    return shipment_status_label(status, shipment=shipment) == "Prepared"


def _partner_api_status(shipment: Shipment) -> str:
    if _is_pickup_ready(shipment):
        return "prepared"
    return cast(str, getattr(shipment, "status", "pending"))


def _status_display(shipment: Shipment) -> str:
    status = cast(str, getattr(shipment, "status", "pending"))
    return shipment_status_label(status, shipment=shipment)


def _apply_delivery_signature(shipment: Shipment, data: dict[str, Any]) -> None:
    signature_name = str(data.get("delivery_signature_name", "")).strip()
    signature_data_url = str(data.get("delivery_signature_data_url", "")).strip()
    if not signature_name or not signature_data_url:
        raise HTTPException(
            status_code=422,
            detail="delivery_signature_name and delivery_signature_data_url are required to confirm delivery",
        )
    setattr(shipment, "delivery_signature_name", signature_name)
    setattr(shipment, "delivery_signature_data_url", signature_data_url)
    setattr(shipment, "delivery_signature_captured_at", _utcnow())


def _extract_delivery_signature(data: dict[str, Any]) -> tuple[str, str]:
    signature_name = str(data.get("delivery_signature_name", "")).strip()
    signature_data_url = str(data.get("delivery_signature_data_url", "")).strip()
    if not signature_name or not signature_data_url:
        raise HTTPException(
            status_code=422,
            detail="delivery_signature_name and delivery_signature_data_url are required to confirm delivery",
        )
    return signature_name, signature_data_url


def _active_confirmation_map(shipment_ids: list[int], db: Session) -> dict[int, ShipmentConfirmation]:
    if not shipment_ids:
        return {}
    confirmations = (
        db.query(ShipmentConfirmation)
        .filter(
            ShipmentConfirmation.shipment_id.in_(shipment_ids),
            ShipmentConfirmation.status == "pending",
        )
        .order_by(ShipmentConfirmation.created_at.desc(), ShipmentConfirmation.id.desc())
        .all()
    )
    latest_by_shipment: dict[int, ShipmentConfirmation] = {}
    for confirmation in confirmations:
        shipment_id = cast(int, getattr(confirmation, "shipment_id"))
        if shipment_id not in latest_by_shipment:
            latest_by_shipment[shipment_id] = confirmation
    return latest_by_shipment


def _notify_partner_transition(shipment: Shipment, new_status: str, db: Session) -> None:
    order = cast(Optional[Order], getattr(shipment, "order", None))
    if order is None:
        return
    if new_status == "picking_up":
        db.add(
            Notification(
                user_id=shipment.supplier_id,
                type="shipment_update",
                title="Pickup In Progress",
                message=f"Logistics partner is collecting Order #{shipment.order_id}.",
                link="/supplier/orders",
            )
        )
    elif new_status == "shipped":
        db.add(
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Order Shipped",
                message=f"Order #{shipment.order_id} has been received by logistics and is now shipped.",
                link=f"/orders/{shipment.order_id}",
            )
        )
    elif new_status == "delivered":
        db.add(
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Delivery Confirmed",
                message=f"Order #{shipment.order_id} has been delivered with signature confirmation.",
                link=f"/orders/{shipment.order_id}",
            )
        )


def _calculate_partner_analytics(shipments_q, db: Session) -> dict:
    total_shipments = shipments_q.count()
    status_breakdown = {
        "pending": 0,
        "processing": 0,
        "picking_up": 0,
        "shipped": 0,
        "in_transit": 0,
        "delivered": 0,
        "failed": 0,
        "returned": 0,
    }

    for shipment_status, count in (
        shipments_q.with_entities(Shipment.status, func.count(Shipment.id))
        .group_by(Shipment.status)
        .all()
    ):
        if shipment_status in status_breakdown:
            status_breakdown[cast(str, shipment_status)] = count
    shipment_ids_subquery = shipments_q.with_entities(Shipment.id).subquery()
    shipments_with_events = (
        db.query(func.count(func.distinct(ShipmentEvent.shipment_id)))
        .filter(ShipmentEvent.shipment_id.in_(db.query(shipment_ids_subquery.c.id)))
        .scalar()
        or 0
    )

    delivered_shipments = (
        shipments_q.filter(Shipment.status == "delivered")
        .with_entities(Shipment.shipped_at, Shipment.actual_delivery, Shipment.estimated_delivery)
        .all()
    )

    transit_hours: list[float] = []
    on_time_deliveries = 0
    sla_eligible_shipments = 0
    for shipped_at, actual_delivery, estimated_delivery in delivered_shipments:
        if shipped_at and actual_delivery and actual_delivery >= shipped_at:
            transit_hours.append((actual_delivery - shipped_at).total_seconds() / 3600)
        if estimated_delivery and actual_delivery:
            sla_eligible_shipments += 1
            if actual_delivery <= estimated_delivery:
                on_time_deliveries += 1

    average_transit_hours = round(sum(transit_hours) / len(transit_hours), 1) if transit_hours else 0.0
    delivery_rate = round((status_breakdown["delivered"] / total_shipments) * 100, 1) if total_shipments else 0.0
    scan_compliance_rate = round((shipments_with_events / total_shipments) * 100, 1) if total_shipments else 0.0
    sla_on_time_rate = round((on_time_deliveries / sla_eligible_shipments) * 100, 1) if sla_eligible_shipments else 0.0

    return {
        "delivery_rate": delivery_rate,
        "average_transit_hours": average_transit_hours,
        "scan_compliance_rate": scan_compliance_rate,
        "sla_on_time_rate": sla_on_time_rate,
        "shipments_with_events": shipments_with_events,
        "sla_eligible_shipments": sla_eligible_shipments,
        "status_breakdown": status_breakdown,
    }


def _partner_dashboard_shipments_query(current_user: dict, db: Session) -> tuple:
    role = current_user.get("role")
    if role in ("admin", "sub_admin", "moderator"):
        return db.query(Shipment), None
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        return (
            db.query(Shipment).filter(
                Shipment.assigned_partner_id == partner.id,
                Shipment.status.in_((PARTNER_PICKUP_READY_STATUS, *PARTNER_VISIBLE_ASSIGNED_STATUSES)),
            ),
            partner,
        )
    raise HTTPException(status_code=403, detail="Logistics partner access required")


def _filter_partner_analytics_period(shipments_q, period: str):
    normalized_period = str(period or "30d").strip().lower()
    lookback_days = ANALYTICS_LOOKBACK_DAYS.get(normalized_period)
    if lookback_days is None:
        raise HTTPException(status_code=422, detail="Invalid analytics period")

    cutoff = _utcnow() - timedelta(days=lookback_days)
    activity_timestamp = func.coalesce(
        Shipment.actual_delivery,
        Shipment.shipped_at,
        Shipment.updated_at,
        Shipment.created_at,
    )
    return shipments_q.filter(activity_timestamp >= cutoff)


def _serialize_partner_analytics_payload(analytics: dict[str, Any]) -> dict[str, Any]:
    status_breakdown = cast(dict[str, int], analytics.get("status_breakdown", {}))
    delivered = int(status_breakdown.get("delivered", 0) or 0)
    failed = int(status_breakdown.get("failed", 0) or 0) + int(status_breakdown.get("returned", 0) or 0)
    in_transit = sum(
        int(status_breakdown.get(status, 0) or 0)
        for status in ("processing", "picking_up", "shipped", "in_transit")
    )
    total_shipments = sum(int(count or 0) for count in status_breakdown.values())

    return {
        "delivery_rate": round(float(analytics.get("delivery_rate", 0) or 0) / 100, 4),
        "average_transit_hours": float(analytics.get("average_transit_hours", 0) or 0),
        "sla_on_time_rate": round(float(analytics.get("sla_on_time_rate", 0) or 0) / 100, 4),
        "scan_compliance_rate": round(float(analytics.get("scan_compliance_rate", 0) or 0) / 100, 4),
        "total_shipments": total_shipments,
        "delivered": delivered,
        "failed": failed,
        "in_transit": in_transit,
    }


def _serialize_partner_payout(payout: LogisticsPartnerPayout) -> dict:
    created_at = cast(Optional[datetime], getattr(payout, "created_at", None))
    processed_at = cast(Optional[datetime], getattr(payout, "processed_at", None))
    partner = cast(Optional[LogisticsPartner], getattr(payout, "partner", None))
    return {
        "id": payout.id,
        "partner_id": payout.partner_id,
        "partner_name": partner.name if partner else None,
        "partner_code": partner.code if partner else None,
        "amount": float(getattr(payout, "amount", 0) or 0),
        "status": payout.status,
        "method": payout.method,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "created_at": created_at.isoformat() if created_at else None,
        "processed_at": processed_at.isoformat() if processed_at else None,
    }


def _order_shipment_counts(order_ids: list[int], db: Session) -> dict[int, int]:
    if not order_ids:
        return {}
    rows = (
        db.query(Shipment.order_id, func.count(Shipment.id))
        .filter(Shipment.order_id.in_(order_ids))
        .group_by(Shipment.order_id)
        .all()
    )
    return {int(order_id): int(count) for order_id, count in rows}


def _format_compound_location(*values: Optional[str]) -> Optional[str]:
    parts = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not parts:
        return None
    # Preserve order but avoid repeated city/region strings in the final label.
    unique_parts = list(dict.fromkeys(parts))
    return ", ".join(unique_parts)


def _shipment_pickup_details(
    shipment: Shipment,
    supplier_profile: SupplierProfile | None,
) -> tuple[Optional[str], Optional[str]]:
    fallback_hub = cast(Optional[str], getattr(shipment, "current_hub", None))
    if supplier_profile is None:
        return fallback_hub, fallback_hub

    pickup_address = cast(Optional[str], getattr(supplier_profile, "address", None))
    pickup_location = _format_compound_location(
        cast(Optional[str], getattr(supplier_profile, "city", None)),
        cast(Optional[str], getattr(supplier_profile, "region", None)),
        cast(Optional[str], getattr(supplier_profile, "country", None)),
    )

    if not pickup_address:
        pickup_address = fallback_hub
    if not pickup_location:
        pickup_location = fallback_hub
    return pickup_address, pickup_location


def _shipment_logistics_allocation(shipment: Shipment) -> OrderLogisticsAllocation | None:
    order = cast(Optional[Order], getattr(shipment, "order", None))
    if order is None:
        return None
    allocations = cast(list[OrderLogisticsAllocation] | None, getattr(order, "logistics_allocations", None)) or []
    shipment_id = cast(int | None, getattr(shipment, "id", None))
    if shipment_id is not None:
        exact = next((allocation for allocation in allocations if getattr(allocation, "shipment_id", None) == shipment_id), None)
        if exact is not None:
            return exact
    supplier_id = cast(int | None, getattr(shipment, "supplier_id", None))
    if supplier_id is None:
        return None
    return next((allocation for allocation in allocations if getattr(allocation, "supplier_id", None) == supplier_id), None)


def _shipment_effective_pricing_breakdown(shipment: Shipment) -> dict[str, Any]:
    allocation = _shipment_logistics_allocation(shipment)
    if allocation is None:
        return {}
    accepted_breakdown_json = cast(str | None, getattr(allocation, "accepted_pricing_breakdown_json", None))
    if accepted_breakdown_json:
        return deserialize_pricing_breakdown_json(accepted_breakdown_json)
    return deserialize_pricing_breakdown_json(cast(str | None, getattr(allocation, "pricing_breakdown_json", None)))


def _shipment_partner_revenue(shipment: Shipment, order_counts: dict[int, int]) -> float:
    allocation = _shipment_logistics_allocation(shipment)
    if allocation is not None:
        amounts = effective_allocation_delivery_amounts(allocation)
        allocation_shipping_amount = float(amounts["shipping_amount"])
        if allocation_shipping_amount > 0:
            return round(allocation_shipping_amount, 2)
    order = cast(Optional[Order], getattr(shipment, "order", None))
    if not order:
        return 0.0
    shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)
    if shipping_amount <= 0:
        # Some legacy orders were saved before shipping values were backfilled.
        shipping_amount = float(derive_order_financials(order).get("shipping", 0) or 0)
    shipment_order_id = cast(int, getattr(shipment, "order_id"))
    divisor = max(1, order_counts.get(shipment_order_id, 1))
    return round(shipping_amount / divisor, 2)


def _calculate_partner_payout_summary(shipments_q, partner: LogisticsPartner | None, db: Session) -> dict:
    empty = {
        "total_earned": 0.0,
        "available_balance": 0.0,
        "pending_amount": 0.0,
        "completed_amount": 0.0,
        "payout_count": 0,
        "recent_payouts": [],
        "recent_earnings": [],
    }
    if partner is None:
        return empty

    delivered_shipments = shipments_q.filter(Shipment.status == "delivered").all()
    order_counts = _order_shipment_counts([int(shipment.order_id) for shipment in delivered_shipments], db)
    total_earned = round(sum(_shipment_partner_revenue(shipment, order_counts) for shipment in delivered_shipments), 2)

    # Build per-shipment earnings sorted by most recently delivered
    def _delivery_ts(s: Shipment) -> datetime:
        return cast(Optional[datetime], getattr(s, "actual_delivery", None)) or cast(Optional[datetime], getattr(s, "updated_at", None)) or datetime.min

    recent_earnings: list[dict] = []
    for shipment in sorted(delivered_shipments, key=_delivery_ts, reverse=True)[:10]:
        revenue = _shipment_partner_revenue(shipment, order_counts)
        actual_delivery = cast(Optional[datetime], getattr(shipment, "actual_delivery", None))
        recent_earnings.append({
            "shipment_id": int(cast(int, getattr(shipment, "id"))),
            "order_id": int(cast(int, getattr(shipment, "order_id"))),
            "tracking_number": cast(Optional[str], getattr(shipment, "tracking_number", None)),
            "amount": revenue,
            "delivered_at": actual_delivery.isoformat() if actual_delivery else None,
        })

    payouts = (
        db.query(LogisticsPartnerPayout)
        .filter(LogisticsPartnerPayout.partner_id == partner.id)
        .order_by(desc(LogisticsPartnerPayout.created_at))
        .all()
    )
    pending_amount = round(
        sum(
            float(getattr(payout, "amount", 0) or 0)
            for payout in payouts
            if cast(str, getattr(payout, "status", "")) in {"pending", "processing"}
        ),
        2,
    )
    completed_amount = round(
        sum(
            float(getattr(payout, "amount", 0) or 0)
            for payout in payouts
            if cast(str, getattr(payout, "status", "")) == "completed"
        ),
        2,
    )
    available_balance = round(max(0.0, total_earned - pending_amount - completed_amount), 2)
    return {
        "total_earned": total_earned,
        "available_balance": available_balance,
        "pending_amount": pending_amount,
        "completed_amount": completed_amount,
        "payout_count": len(payouts),
        "recent_payouts": [_serialize_partner_payout(payout) for payout in payouts[:5]],
        "recent_earnings": recent_earnings,
    }


def _latest_geo_events_for_shipments(shipments: list[Shipment], db: Session) -> dict[int, ShipmentEvent]:
    shipment_ids = [cast(int, getattr(shipment, "id")) for shipment in shipments]
    if not shipment_ids:
        return {}
    events = (
        db.query(ShipmentEvent)
        .filter(
            ShipmentEvent.shipment_id.in_(shipment_ids),
            ShipmentEvent.latitude.isnot(None),
            ShipmentEvent.longitude.isnot(None),
        )
        .order_by(ShipmentEvent.shipment_id.asc(), ShipmentEvent.created_at.desc())
        .all()
    )
    latest: dict[int, ShipmentEvent] = {}
    for event in events:
        shipment_id = cast(int, getattr(event, "shipment_id"))
        if shipment_id not in latest:
            latest[shipment_id] = event
    return latest


def _build_live_locations(shipments: list[Shipment], db: Session) -> list[dict]:
    latest_events = _latest_geo_events_for_shipments(shipments, db)
    locations: list[dict] = []
    for shipment in shipments:
        event = latest_events.get(cast(int, getattr(shipment, "id")))
        if event is None:
            continue
        created_at = cast(Optional[datetime], getattr(event, "created_at", None))
        locations.append(
            {
                "shipment_id": shipment.id,
                "order_id": shipment.order_id,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "current_hub": shipment.current_hub,
                "location": event.location,
                "latitude": float(cast(float, getattr(event, "latitude"))),
                "longitude": float(cast(float, getattr(event, "longitude"))),
                "recorded_at": created_at.isoformat() if created_at else None,
            }
        )
    return locations


def _haversine_km(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat_b - lat_a)
    d_lng = radians(lng_b - lng_a)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(d_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _build_route_plan(points: list[dict]) -> dict:
    if not points:
        return {
            "generated_at": None,
            "total_stops": 0,
            "estimated_distance_km": 0.0,
            "estimated_duration_hours": 0.0,
            "stops": [],
        }

    remaining = [dict(point) for point in points]
    ordered: list[dict] = []
    total_distance = 0.0

    current = remaining.pop(0)
    ordered.append({**current, "stop_number": 1, "distance_from_previous_km": 0.0})

    while remaining:
        next_index = 0
        next_distance = _haversine_km(
            float(current["latitude"]),
            float(current["longitude"]),
            float(remaining[0]["latitude"]),
            float(remaining[0]["longitude"]),
        )
        for index, candidate in enumerate(remaining[1:], start=1):
            candidate_distance = _haversine_km(
                float(current["latitude"]),
                float(current["longitude"]),
                float(candidate["latitude"]),
                float(candidate["longitude"]),
            )
            if candidate_distance < next_distance:
                next_index = index
                next_distance = candidate_distance
        current = remaining.pop(next_index)
        total_distance += next_distance
        ordered.append(
            {
                **current,
                "stop_number": len(ordered) + 1,
                "distance_from_previous_km": round(next_distance, 1),
            }
        )

    return {
        "generated_at": _utcnow().isoformat(),
        "total_stops": len(ordered),
        "estimated_distance_km": round(total_distance, 1),
        "estimated_duration_hours": round((total_distance / 40.0) + max(0, len(ordered) - 1) * 0.15, 1),
        "stops": ordered,
    }


def _collect_sla_alerts(shipments_q) -> list[dict]:
    now = _utcnow()
    overdue_shipments = (
        shipments_q.filter(
            Shipment.estimated_delivery.isnot(None),
            Shipment.actual_delivery.is_(None),
            Shipment.status.in_(SLA_ALERT_STATUSES),
            Shipment.estimated_delivery < now,
        )
        .order_by(Shipment.estimated_delivery.asc())
        .limit(20)
        .all()
    )
    alerts: list[dict] = []
    for shipment in overdue_shipments:
        estimated_delivery = cast(Optional[datetime], getattr(shipment, "estimated_delivery", None))
        if estimated_delivery is None:
            continue
        alerts.append(
            {
                "shipment_id": shipment.id,
                "order_id": shipment.order_id,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "current_hub": shipment.current_hub,
                "estimated_delivery": estimated_delivery.isoformat(),
                "overdue_hours": round((now - estimated_delivery).total_seconds() / 3600, 1),
            }
        )
    return alerts


def _ensure_sla_notifications(alerts: list[dict], partner: LogisticsPartner, db: Session) -> None:
    partner_user_id = cast(Optional[int], getattr(partner, "user_id", None))
    if not partner_user_id or not alerts:
        return

    existing_links = {
        cast(str, link)
        for (link,) in db.query(Notification.link)
        .filter(Notification.user_id == partner_user_id, Notification.title == "SLA Breach Alert")
        .all()
        if link
    }

    created = False
    for alert in alerts:
        link = f"/logistics-partner/shipments?shipment_id={alert['shipment_id']}"
        if link in existing_links:
            continue
        db.add(
            Notification(
                user_id=partner_user_id,
                type="order_update",
                title="SLA Breach Alert",
                message=f"Shipment #{alert['shipment_id']} is overdue by {alert['overdue_hours']} hours.",
                link=link,
            )
        )
        created = True
    if created:
        db.commit()


def _publish_shipment_update(shipment: Shipment, event: ShipmentEvent | None, kind: str = "shipment.updated") -> None:
    payload = {
        "type": kind,
        "shipment_id": shipment.id,
        "order_id": shipment.order_id,
        "assigned_partner_id": shipment.assigned_partner_id,
        "status": _partner_api_status(shipment),
        "tracking_number": shipment.tracking_number,
        "current_hub": shipment.current_hub,
        "scan_code": canonical_scan_code(shipment),
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "status_after": event.status_after,
            "location": event.location,
            "latitude": getattr(event, "latitude", None),
            "longitude": getattr(event, "longitude", None),
            "created_at": event.created_at.isoformat() if getattr(event, "created_at", None) else None,
        }
        if event is not None
        else None,
    }
    logistics_realtime_hub.publish(
        partner_id=cast(Optional[int], getattr(shipment, "assigned_partner_id", None)),
        order_id=cast(int, getattr(shipment, "order_id")),
        payload=payload,
        broadcast_all_partners=_partner_api_status(shipment) in {"prepared", "picking_up"},
    )


# ── Admin: manage partners ────────────────────────────────────────────────────

def list_partners(current_user: dict, db: Session) -> list:
    role = current_user.get("role")
    if role in ("admin", "sub_admin"):
        partners = db.query(LogisticsPartner).order_by(desc(LogisticsPartner.created_at)).limit(200).all()
        return [_serialize_partner(p) for p in partners]
    elif role == "supplier":
        partners = (
            db.query(LogisticsPartner)
            .filter(LogisticsPartner.status == "active", LogisticsPartner.verification_status == "approved")
            .order_by(LogisticsPartner.name.asc())
            .limit(200)
            .all()
        )
        return [_serialize_partner(p, include_internal=False) for p in partners]
    elif role == "logistics_partner":
        partners = [_get_partner_for_user(current_user["id"], db)]
        return [_serialize_partner(p, include_internal=False) for p in partners]
    else:
        raise HTTPException(status_code=403, detail="Access denied")


def create_partner(data: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    code = data.get("code", "").strip().upper()
    if not code or not data.get("name"):
        raise HTTPException(status_code=422, detail="name and code are required")

    requested_status = str(data.get("status", "pending_onboarding") or "pending_onboarding").strip()
    verification_status = str(data.get("verification_status", "") or "").strip() or (
        "approved" if requested_status == "active" else "pending"
    )

    linked_user_id = _resolve_partner_user_link(data, db, allow_existing_link=True)

    if linked_user_id is not None:
        existing_placeholder = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == linked_user_id).first()
        if existing_placeholder:
            code_conflict = db.query(LogisticsPartner).filter(
                LogisticsPartner.code == code,
                LogisticsPartner.id != existing_placeholder.id,
            ).first()
            if code_conflict:
                raise HTTPException(status_code=409, detail="Partner code already exists")
            setattr(existing_placeholder, "name", data["name"])
            setattr(existing_placeholder, "code", code)
            setattr(existing_placeholder, "contact_name", data.get("contact_name"))
            setattr(existing_placeholder, "contact_email", data.get("contact_email"))
            setattr(existing_placeholder, "contact_phone", data.get("contact_phone"))
            setattr(existing_placeholder, "website", data.get("website"))
            setattr(existing_placeholder, "coverage_regions", json.dumps(data.get("coverage_regions", [])))
            setattr(existing_placeholder, "service_types", json.dumps(data.get("service_types", [])))
            setattr(existing_placeholder, "status", requested_status)
            setattr(existing_placeholder, "verification_status", verification_status)
            setattr(existing_placeholder, "verification_note", data.get("verification_note"))
            setattr(existing_placeholder, "country_code", data.get("country_code") or data.get("country"))
            setattr(existing_placeholder, "region", data.get("region"))
            setattr(existing_placeholder, "city", data.get("city"))
            setattr(existing_placeholder, "address", data.get("address"))
            setattr(existing_placeholder, "postal_code", data.get("postal_code"))
            setattr(existing_placeholder, "bio", data.get("bio"))
            setattr(existing_placeholder, "logo_url", data.get("logo_url"))
            setattr(existing_placeholder, "notes", data.get("notes"))
            setattr(existing_placeholder, "updated_at", _utcnow())
            db.commit()
            db.refresh(existing_placeholder)
            return _serialize_partner(existing_placeholder)

    existing = db.query(LogisticsPartner).filter(LogisticsPartner.code == code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Partner code already exists")

    partner = LogisticsPartner(
        name=data["name"],
        code=code,
        contact_name=data.get("contact_name"),
        contact_email=data.get("contact_email"),
        contact_phone=data.get("contact_phone"),
        website=data.get("website"),
        coverage_regions=json.dumps(data.get("coverage_regions", [])),
        service_types=json.dumps(data.get("service_types", [])),
        country_code=data.get("country_code") or data.get("country"),
        region=data.get("region"),
        city=data.get("city"),
        address=data.get("address"),
        postal_code=data.get("postal_code"),
        bio=data.get("bio"),
        logo_url=data.get("logo_url"),
        status=requested_status,
        verification_status=verification_status,
        verification_note=data.get("verification_note"),
        verified_by=current_user["id"] if verification_status == "approved" else None,
        verified_at=_utcnow() if verification_status == "approved" else None,
        user_id=linked_user_id,
        notes=data.get("notes"),
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return _serialize_partner(partner)


def update_partner(partner_id: int, data: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    if "code" in data:
        code = str(data.get("code", "")).strip().upper()
        if not code:
            raise HTTPException(status_code=422, detail="code cannot be empty")
        code_conflict = db.query(LogisticsPartner).filter(
            LogisticsPartner.code == code,
            LogisticsPartner.id != partner_id,
        ).first()
        if code_conflict:
            raise HTTPException(status_code=409, detail="Partner code already exists")
        setattr(partner, "code", code)

    for field in (
        "name", "contact_name", "contact_email", "contact_phone", "website", "status", "notes",
        "business_type", "country_code", "region", "city", "address", "postal_code", "tax_id",
        "bio", "about_us", "logo_url", "banner_url", "verification_status", "verification_note",
    ):
        if field in data:
            setattr(partner, field, data[field])
    if "coverage_regions" in data:
        setattr(partner, "coverage_regions", json.dumps(data["coverage_regions"]))
    if "service_types" in data:
        setattr(partner, "service_types", json.dumps(data["service_types"]))
    if "social_links" in data:
        setattr(partner, "social_links", _parse_partner_social_links(data.get("social_links")))
    setattr(
        partner,
        "user_id",
        _resolve_partner_user_link(
            data,
            db,
            existing_user_id=cast(Optional[int], getattr(partner, "user_id", None)),
            partner_id=partner_id,
        ),
    )

    setattr(partner, "updated_at", _utcnow())
    if str(getattr(partner, "verification_status", "")).strip() == "approved":
        setattr(partner, "verified_by", current_user["id"])
        setattr(partner, "verified_at", _utcnow())
    db.commit()
    db.refresh(partner)
    return _serialize_partner(partner)


def delete_partner(partner_id: int, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin-only")
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    blocker = _build_partner_delete_blocker(partner_id, db)
    if blocker is not None:
        raise HTTPException(status_code=blocker[0], detail=blocker[1])
    try:
        db.delete(partner)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Partner has related records that must be archived or removed before deletion.",
        )
    return {"detail": "Partner deleted"}


def bulk_manage_partners(
    partner_ids: list[int],
    action: str,
    note: str | None,
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    """Bulk review, activate/suspend, or delete logistics partners for admins."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin-only")
    if not partner_ids:
        raise HTTPException(status_code=400, detail="No partner IDs provided")

    normalized_action = str(action or "").strip().lower()
    if normalized_action not in {"approve", "reject", "activate", "suspend", "delete"}:
        raise HTTPException(
            status_code=400,
            detail="action must be one of: approve, reject, activate, suspend, delete",
        )

    normalized_note = _sanitize_optional_string(note, max_length=2000)
    ordered_ids = list(dict.fromkeys(partner_ids))
    partners = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.id.in_(ordered_ids))
        .all()
    )
    partner_by_id = {cast(int, getattr(partner, "id")): partner for partner in partners}
    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for partner_id in ordered_ids:
        partner = partner_by_id.get(partner_id)
        if partner is None:
            skipped.append({"id": partner_id, "reason": "Partner not found"})
            continue

        if normalized_action == "delete":
            blocker = _build_partner_delete_blocker(partner_id, db)
            if blocker is not None:
                skipped.append({"id": partner_id, "reason": blocker[1]})
                continue

        if normalized_action == "approve":
            setattr(partner, "verification_status", "approved")
            setattr(partner, "verification_note", normalized_note or "Approved")
            setattr(partner, "verified_by", current_user["id"])
            setattr(partner, "verified_at", _utcnow())
            if cast(str | None, getattr(partner, "status", None)) == "pending_onboarding":
                setattr(partner, "status", "active")
        elif normalized_action == "reject":
            setattr(partner, "verification_status", "rejected")
            setattr(partner, "verification_note", normalized_note or "Rejected")
            setattr(partner, "verified_by", None)
            setattr(partner, "verified_at", None)
        elif normalized_action == "activate":
            setattr(partner, "status", "active")
        elif normalized_action == "suspend":
            setattr(partner, "status", "suspended")
        else:
            try:
                with db.begin_nested():
                    db.delete(partner)
                    db.flush()
            except IntegrityError:
                skipped.append(
                    {
                        "id": partner_id,
                        "reason": "Partner has related records that must be archived or removed before deletion.",
                    }
                )
                continue

        if normalized_action != "delete":
            setattr(partner, "updated_at", _utcnow())
            processed.append(
                {
                    "id": partner_id,
                    "status": getattr(partner, "status", None),
                    "verification_status": getattr(partner, "verification_status", None),
                }
            )
        else:
            processed.append({"id": partner_id, "deleted": True})

    db.commit()
    return {
        "action": normalized_action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


# ── Partner Dashboard ─────────────────────────────────────────────────────────

def get_partner_dashboard(current_user: dict, db: Session) -> dict:
    """
    The logistics partner views their assigned shipments, active deliveries,
    and distribution channel metrics.
    Partners must have a linked user with role 'logistics_partner'.
    Admins can also access this for any partner.
    """
    shipments_q, partner = _partner_dashboard_shipments_query(current_user, db)

    total_shipments = shipments_q.count()
    active = shipments_q.filter(Shipment.status.in_(["shipped", "in_transit", "processing"])).count()
    delivered = shipments_q.filter(Shipment.status == "delivered").count()
    pending = shipments_q.filter(Shipment.status == "pending").count()
    failed = shipments_q.filter(Shipment.status.in_(["failed", "returned"])).count()

    # Distribution channel breakdown
    channel_stats = (
        shipments_q.filter(Shipment.distribution_channel.isnot(None))
        .with_entities(Shipment.distribution_channel, func.count(Shipment.id))
        .group_by(Shipment.distribution_channel)
        .all()
    )

    # Recent active shipments
    recent_shipments = (
        shipments_q.filter(Shipment.status.in_(ACTIVE_SHIPMENT_STATUSES))
        .order_by(desc(Shipment.updated_at))
        .limit(20)
        .all()
    )
    analytics = _calculate_partner_analytics(shipments_q, db)
    live_locations = _build_live_locations(recent_shipments, db)
    route_plan = _build_route_plan(live_locations)
    sla_alerts = _collect_sla_alerts(shipments_q)
    if partner is not None:
        _ensure_sla_notifications(sla_alerts, partner, db)
    payout_summary = _calculate_partner_payout_summary(shipments_q, partner, db)

    def _ser_shipment(s: Shipment) -> dict:
        estimated_delivery = cast(Optional[datetime], getattr(s, "estimated_delivery", None))
        shipped_at = cast(Optional[datetime], getattr(s, "shipped_at", None))
        return {
            "id": s.id,
            "order_id": s.order_id,
            "tracking_number": s.tracking_number,
            "carrier_name": s.carrier_name,
            "assigned_partner_id": s.assigned_partner_id,
            "assigned_partner_name": s.assigned_partner.name if s.assigned_partner else None,
            "assigned_partner_code": s.assigned_partner.code if s.assigned_partner else None,
            "status": _partner_api_status(s),
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "estimated_delivery": estimated_delivery.isoformat() if estimated_delivery else None,
            "shipped_at": shipped_at.isoformat() if shipped_at else None,
        }

    return {
        "stats": {
            "total": total_shipments,
            "active": active,
            "delivered": delivered,
            "pending": pending,
            "failed": failed,
        },
        "analytics": analytics,
        "channel_breakdown": {ch: cnt for ch, cnt in channel_stats},
        "active_shipments": [_ser_shipment(s) for s in recent_shipments],
        "live_locations": live_locations,
        "route_plan": route_plan,
        "sla_alerts": sla_alerts,
        "payout_summary": payout_summary,
    }


def get_partner_analytics(current_user: dict, db: Session, period: str = "30d") -> dict[str, Any]:
    shipments_q, _partner = _partner_dashboard_shipments_query(current_user, db)
    filtered_shipments_q = _filter_partner_analytics_period(shipments_q, period)
    analytics = _calculate_partner_analytics(filtered_shipments_q, db)
    return _serialize_partner_analytics_payload(analytics)


def get_partner_payouts(current_user: dict, db: Session) -> list:
    role = current_user.get("role")
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        payouts = (
            db.query(LogisticsPartnerPayout)
            .filter(LogisticsPartnerPayout.partner_id == partner.id)
            .order_by(desc(LogisticsPartnerPayout.created_at))
            .all()
        )
        return [_serialize_partner_payout(payout) for payout in payouts]
    if role in ("admin", "sub_admin"):
        payouts = db.query(LogisticsPartnerPayout).order_by(desc(LogisticsPartnerPayout.created_at)).all()
        return [_serialize_partner_payout(payout) for payout in payouts]
    raise HTTPException(status_code=403, detail="Access denied")


def request_partner_payout(data: dict, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")

    partner = _get_partner_for_user(current_user["id"], db)
    shipments_q, _ = _scoped_shipments_query(current_user, db)
    payout_summary = _calculate_partner_payout_summary(shipments_q, partner, db)

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Amount must be numeric") from exc

    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be positive")
    if amount > payout_summary["available_balance"] + 0.01:
        raise HTTPException(status_code=422, detail="Requested amount exceeds available logistics balance")

    payout = LogisticsPartnerPayout(
        partner_id=partner.id,
        amount=round(amount, 2),
        method=str(data.get("method", "bank") or "bank"),
        notes=str(data.get("notes", "")).strip() or None,
    )
    db.add(payout)
    db.flush()
    payout.reference_id = build_transfer_reference(
        db,
        kind="logistics_payout",
        entity_id=int(partner.id),
        record_id=int(payout.id),
    )
    partner_user_id = cast(Optional[int], getattr(partner, "user_id", None))
    if partner_user_id is not None:
        db.add(
            Notification(
                user_id=partner_user_id,
                type="payout",
                title="Payout Request Received",
                message=f"Your logistics payout request of {payout.amount:.2f} AED has been submitted.",
                link="/logistics-partner/payouts",
            )
        )
    db.commit()
    db.refresh(payout)
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_REQUESTED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="logistics_payout",
        resource_id=cast(int, getattr(payout, "id")),
        details={"amount": payout.amount, "partner_id": partner.id, "method": payout.method},
    )
    return _serialize_partner_payout(payout)


def list_pending_partner_payouts(current_user: dict, db: Session) -> list:
    _require_admin(current_user)
    payouts = (
        db.query(LogisticsPartnerPayout)
        .filter(LogisticsPartnerPayout.status.in_(["pending", "processing"]))
        .order_by(LogisticsPartnerPayout.created_at.desc(), LogisticsPartnerPayout.id.desc())
        .all()
    )
    return [_serialize_partner_payout(payout) for payout in payouts]


def verify_partner_payout(payout_id: int, data: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    payout = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id == payout_id).first()
    if payout is None:
        raise HTTPException(status_code=404, detail="Logistics payout not found")

    new_status = str(data.get("status", "")).strip().lower()
    if new_status not in {"processing", "completed", "rejected"}:
        raise HTTPException(status_code=422, detail="status must be one of: processing, completed, rejected")

    setattr(payout, "status", new_status)
    setattr(
        payout,
        "reference_id",
        str(data.get("reference", "")).strip()
        or cast(Optional[str], getattr(payout, "reference_id", None))
        or build_transfer_reference(
            db,
            kind="logistics_payout",
            entity_id=int(payout.partner_id),
            record_id=int(payout.id),
        ),
    )
    setattr(
        payout,
        "notes",
        str(data.get("notes", "")).strip() or cast(Optional[str], getattr(payout, "notes", None)),
    )
    if new_status in {"completed", "rejected"}:
        setattr(payout, "processed_at", _utcnow())

    partner = cast(Optional[LogisticsPartner], getattr(payout, "partner", None))
    partner_user_id = cast(Optional[int], getattr(partner, "user_id", None)) if partner else None
    if partner_user_id is not None:
        db.add(
            Notification(
                user_id=partner_user_id,
                type="payout",
                title="Payout Update",
                message=(
                    f"Your logistics payout request #{payout.id} has been completed."
                    if new_status == "completed"
                    else f"Your logistics payout request #{payout.id} is now {new_status}."
                ),
                link="/logistics-partner/payouts",
            )
        )
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="logistics_payout",
        resource_id=cast(int, getattr(payout, "id")),
        details={"status": new_status, "reference": payout.reference_id},
        status="success",
    )
    return _serialize_partner_payout(payout)


def scan_lookup_shipment_partner(code: str, current_user: dict, db: Session) -> dict:
    """Look up a shipment by scan_code or tracking_number. Accessible by logistics partners and admins."""
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    trimmed = (code or "").strip()
    if not trimmed:
        raise HTTPException(status_code=422, detail="code is required")

    partner = _get_partner_for_user(current_user["id"], db) if role == "logistics_partner" else None
    partner_has_approved_service_areas = False
    if partner is not None:
        partner_has_approved_service_areas = (
            db.query(LogisticsPartnerServiceArea)
            .filter(
                LogisticsPartnerServiceArea.partner_id == cast(int, getattr(partner, "id")),
                LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
                LogisticsPartnerServiceArea.approval_status == "approved",
            )
            .first()
            is not None
        )

    def _is_visible_to_partner(candidate: Shipment) -> bool:
        if partner is None:
            return True
        partner_id = cast(int, getattr(partner, "id"))
        assigned_partner_id = cast(Optional[int], getattr(candidate, "assigned_partner_id", None))
        visible_pickup = _pickup_visible_to_partner(candidate, partner, db)
        assigned_to_partner = assigned_partner_id == partner_id
        return visible_pickup or assigned_to_partner

    shipment = (
        db.query(Shipment)
        .filter(
            (Shipment.scan_code == trimmed) | (Shipment.tracking_number == trimmed)
        )
        .order_by(desc(Shipment.created_at))
        .first()
    )

    if shipment and not _is_visible_to_partner(shipment):
        # Keep the pickup board approval-gated, but allow an explicit QR/tracking lookup
        # when the partner already has the exact shipment code in hand.
        assigned_partner_id = cast(Optional[int], getattr(shipment, "assigned_partner_id", None))
        direct_unassigned_lookup = (
            assigned_partner_id is None
            and not partner_has_approved_service_areas
            and trimmed in shipment_scan_codes(shipment)
        )
        if partner is None or not direct_unassigned_lookup:
            shipment = None

    if not shipment:
        fallback_candidates: list[Shipment] = []
        upper_trimmed = trimmed.upper()
        if upper_trimmed.startswith("SHIP-"):
            shipment_id_text = trimmed.split("-", 1)[1]
            if shipment_id_text.isdigit():
                candidate = db.query(Shipment).filter(Shipment.id == int(shipment_id_text)).first()
                if candidate is not None:
                    fallback_candidates = [candidate]
        elif upper_trimmed.startswith("ORDER-"):
            order_id_text = trimmed.split("-", 1)[1]
            if order_id_text.isdigit():
                fallback_candidates = (
                    db.query(Shipment)
                    .filter(Shipment.order_id == int(order_id_text))
                    .order_by(desc(Shipment.created_at))
                    .all()
                )

        matching_candidates = [
            candidate
            for candidate in fallback_candidates
            if trimmed in shipment_scan_codes(candidate) and _is_visible_to_partner(candidate)
        ]
        if len(matching_candidates) == 1:
            shipment = matching_candidates[0]
        elif len(matching_candidates) > 1:
            raise HTTPException(
                status_code=409,
                detail="Multiple shipments match this order QR. Use the shipment scan code or tracking number.",
            )

    if not shipment:
        raise HTTPException(status_code=404, detail=f"No shipment found for code: {trimmed!r}")

    shipped_at = cast(Optional[datetime], getattr(shipment, "shipped_at", None))
    estimated_delivery = cast(Optional[datetime], getattr(shipment, "estimated_delivery", None))
    actual_delivery = cast(Optional[datetime], getattr(shipment, "actual_delivery", None))
    packaged_at = cast(Optional[datetime], getattr(shipment, "packaged_at", None))
    created_at = cast(Optional[datetime], getattr(shipment, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(shipment, "updated_at", None))
    shipment_id = cast(int, getattr(shipment, "id"))
    delivery_signature_captured_at = cast(Optional[datetime], getattr(shipment, "delivery_signature_captured_at", None))
    order = cast(Optional[Order], getattr(shipment, "order", None))
    customer = cast(Optional[User], getattr(order, "user", None)) if order else None
    supplier = cast(Optional[User], getattr(shipment, "supplier", None))
    supplier_profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == cast(int, getattr(shipment, "supplier_id")))
        .first()
    )
    supplier_pickup_address, supplier_pickup_location = _shipment_pickup_details(shipment, supplier_profile)
    order_counts = _order_shipment_counts([cast(int, getattr(shipment, "order_id"))], db)
    estimated_partner_payout = _shipment_partner_revenue(shipment, order_counts)
    active_confirmation = _active_confirmation_map([shipment_id], db).get(shipment_id)
    allocation = _shipment_logistics_allocation(shipment)
    allocation_amounts = effective_allocation_delivery_amounts(allocation)
    accepted_vehicle_selected_at = cast(Optional[datetime], getattr(shipment, "accepted_vehicle_selected_at", None))

    return {
        "id": shipment_id,
        "order_id": shipment.order_id,
        "supplier_id": shipment.supplier_id,
        "supplier_name": cast(Optional[str], getattr(supplier, "username", None)) if supplier else None,
        "supplier_phone": cast(Optional[str], getattr(supplier, "phone", None)) if supplier else None,
        "supplier_pickup_address": supplier_pickup_address,
        "supplier_pickup_location": supplier_pickup_location,
        "assigned_partner_id": shipment.assigned_partner_id,
        "assigned_partner_name": shipment.assigned_partner.name if shipment.assigned_partner else None,
        "assigned_partner_code": shipment.assigned_partner.code if shipment.assigned_partner else None,
        "customer_name": cast(Optional[str], getattr(customer, "username", None)) if customer else None,
        "customer_phone": cast(Optional[str], getattr(order, "customer_phone", None)) if order else None,
        "customer_dropoff_address": cast(Optional[str], getattr(order, "shipping_address", None)) if order else None,
        "customer_dropoff_location": cast(Optional[str], getattr(order, "delivery_location", None)) if order else None,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "status": _partner_api_status(shipment),
        "status_label": _status_display(shipment),
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
        "scan_code": canonical_scan_code(shipment),
        "estimated_partner_payout": estimated_partner_payout,
        "accepted_load_fit_label": cast(Optional[str], getattr(shipment, "accepted_vehicle_type", None)),
        "accepted_load_fit_factor": float(getattr(shipment, "accepted_vehicle_multiplier", 0) or 0) if getattr(shipment, "accepted_vehicle_multiplier", None) is not None else None,
        "accepted_vehicle_type": cast(Optional[str], getattr(shipment, "accepted_vehicle_type", None)),
        "accepted_vehicle_multiplier": float(getattr(shipment, "accepted_vehicle_multiplier", 0) or 0) if getattr(shipment, "accepted_vehicle_multiplier", None) is not None else None,
        "accepted_shipping_amount": float(allocation_amounts["shipping_amount"]) if allocation is not None and getattr(allocation, "accepted_shipping_amount", None) is not None else None,
        "accepted_vehicle_selected_at": accepted_vehicle_selected_at.isoformat() if accepted_vehicle_selected_at else None,
        "pricing_breakdown": _shipment_effective_pricing_breakdown(shipment) or None,
        "shipping_address": cast(Optional[str], getattr(order, "shipping_address", None)) if order else None,
        "delivery_location": cast(Optional[str], getattr(order, "delivery_location", None)) if order else None,
        "package_count": shipment.package_count,
        "package_weight_kg": shipment.package_weight_kg,
        "package_dimensions": shipment.package_dimensions,
        "packaged_at": packaged_at.isoformat() if packaged_at else None,
        "packaging_notes": shipment.packaging_notes,
        "shipped_at": shipped_at.isoformat() if shipped_at else None,
        "estimated_delivery": estimated_delivery.isoformat() if estimated_delivery else None,
        "actual_delivery": actual_delivery.isoformat() if actual_delivery else None,
        "delivery_signature_name": cast(Optional[str], getattr(shipment, "delivery_signature_name", None)),
        "delivery_signature_data_url": cast(Optional[str], getattr(shipment, "delivery_signature_data_url", None)),
        "delivery_signature_captured_at": delivery_signature_captured_at.isoformat() if delivery_signature_captured_at else None,
        "active_confirmation_request": serialize_shipment_confirmation(active_confirmation) if active_confirmation else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def get_partner_shipments(
    current_user: dict,
    db: Session,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 30,
) -> dict:
    role = current_user.get("role")
    q, partner = _partner_visible_shipments_query(current_user, db)
    all_candidates = q.order_by(desc(Shipment.created_at)).all()
    filtered_shipments: list[Shipment] = []
    for shipment in all_candidates:
        external_status = _partner_api_status(shipment)
        if status and external_status != status:
            continue
        if role == "logistics_partner" and partner is not None and not _is_shipment_visible_to_partner(shipment, partner, db):
            continue
        filtered_shipments.append(shipment)

    total = len(filtered_shipments)
    start = (page - 1) * page_size
    shipments = filtered_shipments[start:start + page_size]
    active_confirmations = _active_confirmation_map([cast(int, shipment.id) for shipment in shipments], db)
    order_counts = _order_shipment_counts([cast(int, shipment.order_id) for shipment in shipments], db)
    supplier_ids = sorted({cast(int, shipment.supplier_id) for shipment in shipments})
    supplier_profiles = {
        cast(int, getattr(profile, "user_id")): profile
        for profile in (
            db.query(SupplierProfile)
            .filter(SupplierProfile.user_id.in_(supplier_ids))
            .all()
            if supplier_ids
            else []
        )
    }

    # Batch-load logistics settlements for enriching payment/settlement status
    visible_order_ids = [cast(int, s.order_id) for s in shipments if s.order_id is not None]
    partner_obj = partner  # may be None for admin
    if partner_obj is not None and visible_order_ids:
        _lp_settlements: dict[int, LogisticsSettlement] = {
            cast(int, ls.order_id): ls
            for ls in db.query(LogisticsSettlement).filter(
                LogisticsSettlement.partner_id == cast(int, partner_obj.id),
                LogisticsSettlement.order_id.in_(visible_order_ids),
            ).all()
        }
    else:
        _lp_settlements = {}

    def _ser(s: Shipment) -> dict:
        shipment_id = cast(int, getattr(s, "id"))
        shipped_at = cast(Optional[datetime], getattr(s, "shipped_at", None))
        estimated_delivery = cast(Optional[datetime], getattr(s, "estimated_delivery", None))
        actual_delivery = cast(Optional[datetime], getattr(s, "actual_delivery", None))
        packaged_at = cast(Optional[datetime], getattr(s, "packaged_at", None))
        created_at = cast(Optional[datetime], getattr(s, "created_at", None))
        delivery_signature_captured_at = cast(Optional[datetime], getattr(s, "delivery_signature_captured_at", None))
        order = cast(Optional[Order], getattr(s, "order", None))
        customer = cast(Optional[User], getattr(order, "user", None)) if order else None
        supplier = cast(Optional[User], getattr(s, "supplier", None))
        supplier_profile = supplier_profiles.get(cast(int, getattr(s, "supplier_id")))
        supplier_pickup_address, supplier_pickup_location = _shipment_pickup_details(s, supplier_profile)
        estimated_partner_payout = _shipment_partner_revenue(s, order_counts)
        allocation = _shipment_logistics_allocation(s)
        allocation_amounts = effective_allocation_delivery_amounts(allocation)
        accepted_vehicle_selected_at = cast(Optional[datetime], getattr(s, "accepted_vehicle_selected_at", None))
        return {
            "id": shipment_id,
            "order_id": s.order_id,
            "supplier_id": s.supplier_id,
            "supplier_name": cast(Optional[str], getattr(supplier, "username", None)) if supplier else None,
            "supplier_phone": cast(Optional[str], getattr(supplier, "phone", None)) if supplier else None,
            "supplier_pickup_address": supplier_pickup_address,
            "supplier_pickup_location": supplier_pickup_location,
            "assigned_partner_id": s.assigned_partner_id,
            "assigned_partner_name": s.assigned_partner.name if s.assigned_partner else None,
            "assigned_partner_code": s.assigned_partner.code if s.assigned_partner else None,
            "customer_name": cast(Optional[str], getattr(customer, "username", None)) if customer else None,
            "customer_phone": cast(Optional[str], getattr(order, "customer_phone", None)) if order else None,
            "customer_dropoff_address": cast(Optional[str], getattr(order, "shipping_address", None)) if order else None,
            "customer_dropoff_location": cast(Optional[str], getattr(order, "delivery_location", None)) if order else None,
            "carrier_name": s.carrier_name,
            "tracking_number": s.tracking_number,
            "status": _partner_api_status(s),
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": canonical_scan_code(s),
            "estimated_partner_payout": estimated_partner_payout,
            "accepted_load_fit_label": cast(Optional[str], getattr(s, "accepted_vehicle_type", None)),
            "accepted_load_fit_factor": float(getattr(s, "accepted_vehicle_multiplier", 0) or 0) if getattr(s, "accepted_vehicle_multiplier", None) is not None else None,
            "accepted_vehicle_type": cast(Optional[str], getattr(s, "accepted_vehicle_type", None)),
            "accepted_vehicle_multiplier": float(getattr(s, "accepted_vehicle_multiplier", 0) or 0) if getattr(s, "accepted_vehicle_multiplier", None) is not None else None,
            "accepted_shipping_amount": float(allocation_amounts["shipping_amount"]) if allocation is not None and getattr(allocation, "accepted_shipping_amount", None) is not None else None,
            "accepted_vehicle_selected_at": accepted_vehicle_selected_at.isoformat() if accepted_vehicle_selected_at else None,
            "pricing_breakdown": _shipment_effective_pricing_breakdown(s) or None,
            "package_count": s.package_count,
            "package_weight_kg": s.package_weight_kg,
            "package_dimensions": s.package_dimensions,
            "packaged_at": packaged_at.isoformat() if packaged_at else None,
            "packaging_notes": s.packaging_notes,
            "shipping_address": cast(Optional[str], getattr(order, "shipping_address", None)) if order else None,
            "shipped_at": shipped_at.isoformat() if shipped_at else None,
            "estimated_delivery": estimated_delivery.isoformat() if estimated_delivery else None,
            "actual_delivery": actual_delivery.isoformat() if actual_delivery else None,
            "status_label": _status_display(s),
            "delivery_signature_name": cast(Optional[str], getattr(s, "delivery_signature_name", None)),
            "delivery_signature_captured_at": delivery_signature_captured_at.isoformat() if delivery_signature_captured_at else None,
            "active_confirmation_request": (
                serialize_shipment_confirmation(active_confirmations[shipment_id])
                if shipment_id in active_confirmations
                else None
            ),
            "settlement_status": cast(str, getattr(_lp_settlements.get(cast(int, s.order_id)), "status", None)) if s.order_id else None,
            "order_payment_status": "paid" if order and getattr(order, "paid_at", None) else "unpaid",
            "created_at": created_at.isoformat() if created_at else None,
        }

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [_ser(s) for s in shipments],
    }


def create_shipment_confirmation_request_partner(
    shipment_id: int,
    data: dict,
    current_user: dict,
    db: Session,
) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    partner: LogisticsPartner | None = None
    old_status = cast(str, getattr(shipment, "status"))
    external_old_status = _partner_api_status(shipment)
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        partner_id = cast(int, getattr(partner, "id"))
        assigned_partner_id = cast(Optional[int], getattr(shipment, "assigned_partner_id", None))
        visible_pickup = _pickup_visible_to_partner(shipment, partner, db)
        assigned_to_partner = assigned_partner_id == partner_id
        if not visible_pickup and not assigned_to_partner:
            raise HTTPException(status_code=404, detail="Shipment not found")
        if visible_pickup and assigned_partner_id is None:
            setattr(shipment, "assigned_partner_id", partner_id)

    requested_status = str(data.get("requested_status", "")).strip()
    if requested_status not in {"shipped", "delivered"}:
        raise HTTPException(status_code=422, detail="requested_status must be one of: shipped, delivered")

    confirmation_type: str
    target_user_id: int | None
    target_role: str
    order = cast(Optional[Order], getattr(shipment, "order", None))
    if order is None:
        order = db.query(Order).filter(Order.id == shipment.order_id).first()

    signature_name: str | None = None
    signature_data_url: str | None = None
    if requested_status == "shipped":
        if old_status != "picking_up":
            raise HTTPException(status_code=409, detail="Shipment is not awaiting supplier pickup confirmation")
        confirmation_type = "pickup"
        target_user_id = cast(Optional[int], getattr(shipment, "supplier_id", None))
        target_role = "supplier"
    else:
        if old_status not in {"shipped", "in_transit"}:
            raise HTTPException(status_code=409, detail="Shipment is not awaiting customer delivery confirmation")
        confirmation_type = "delivery"
        target_user_id = cast(Optional[int], getattr(order, "user_id", None)) if order else None
        target_role = "customer"
        signature_name, signature_data_url = _extract_delivery_signature(cast(dict[str, Any], data))

    if target_user_id is None:
        raise HTTPException(status_code=409, detail="No target user found for this confirmation request")

    existing_pending = (
        db.query(ShipmentConfirmation)
        .filter(
            ShipmentConfirmation.shipment_id == shipment.id,
            ShipmentConfirmation.confirmation_type == confirmation_type,
            ShipmentConfirmation.status == "pending",
        )
        .order_by(ShipmentConfirmation.created_at.desc(), ShipmentConfirmation.id.desc())
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=409, detail="A pending confirmation request already exists for this shipment")

    submitted_scan_code = str(data.get("scan_code", "")).strip()
    if submitted_scan_code and submitted_scan_code not in shipment_scan_codes(shipment):
        raise HTTPException(status_code=409, detail="scan_code does not match this shipment")
    if not cast(Optional[str], getattr(shipment, "scan_code", None)):
        setattr(shipment, "scan_code", canonical_scan_code(shipment))

    requested_event_type = str(data.get("event_type", "")).strip() or (
        "picked_from_supplier" if requested_status == "shipped" else "customer_received"
    )

    confirmation = ShipmentConfirmation(
        shipment_id=shipment.id,
        order_id=shipment.order_id,
        supplier_id=shipment.supplier_id,
        requester_user_id=current_user["id"],
        requester_role=role,
        target_user_id=target_user_id,
        target_role=target_role,
        confirmation_type=confirmation_type,
        status="pending",
        requested_status=requested_status,
        requested_event_type=requested_event_type,
        current_hub=str(data.get("current_hub", "")).strip() or None,
        tracking_number=str(data.get("tracking_number", "")).strip() or None,
        delivery_signature_name=signature_name if requested_status == "delivered" else None,
        delivery_signature_data_url=signature_data_url if requested_status == "delivered" else None,
        notes=str(data.get("notes", "")).strip() or None,
    )
    db.add(confirmation)
    db.add(
        Notification(
            user_id=target_user_id,
            type="shipment_update",
            title=(
                "Pickup Confirmation Requested"
                if confirmation_type == "pickup"
                else "Delivery Confirmation Requested"
            ),
            message=(
                f"Please confirm pickup for Order #{shipment.order_id}."
                if confirmation_type == "pickup"
                else f"Please confirm delivery for Order #{shipment.order_id}."
            ),
            link=f"/tracking/{shipment.order_id}",
        )
    )
    setattr(shipment, "updated_at", _utcnow())
    db.commit()
    db.refresh(confirmation)

    return {
        "shipment_id": shipment.id,
        "order_id": shipment.order_id,
        "status": _partner_api_status(shipment),
        "status_label": _status_display(shipment),
        "request": serialize_shipment_confirmation(confirmation),
    }


def get_partner_pricing_insights(
    current_user: dict,
    db: Session,
    *,
    partner_id: int | None = None,
    service_area_id: int | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    resolved_partner_id = partner_id
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        resolved_partner_id = cast(int, getattr(partner, "id"))
    if resolved_partner_id is None:
        raise HTTPException(status_code=422, detail="partner_id is required")

    allocations_q = db.query(OrderLogisticsAllocation).filter(OrderLogisticsAllocation.partner_id == resolved_partner_id)
    if service_area_id is not None:
        allocations_q = allocations_q.filter(OrderLogisticsAllocation.service_area_id == service_area_id)
    allocations = allocations_q.order_by(desc(OrderLogisticsAllocation.updated_at), desc(OrderLogisticsAllocation.id)).all()

    minimum_hits = 0
    maximum_hits = 0
    near_cap_count = 0
    accepted_vehicle_count = 0
    total_effective_shipping = 0.0
    accepted_shipping_total = 0.0
    accepted_shipping_rows = 0

    for allocation in allocations:
        effective_breakdown = deserialize_pricing_breakdown_json(
            cast(str | None, getattr(allocation, "accepted_pricing_breakdown_json", None))
            or cast(str | None, getattr(allocation, "pricing_breakdown_json", None))
        )
        effective_amounts = effective_allocation_delivery_amounts(allocation)
        shipping_amount = float(effective_amounts["shipping_amount"])
        total_effective_shipping += shipping_amount

        if getattr(allocation, "accepted_vehicle_type", None):
            accepted_vehicle_count += 1
        if getattr(allocation, "accepted_shipping_amount", None) is not None:
            accepted_shipping_total += float(getattr(allocation, "accepted_shipping_amount", 0) or 0)
            accepted_shipping_rows += 1

        ceiling_charge = float(effective_breakdown.get("ceiling_charge") or 0)
        if bool(effective_breakdown.get("floor_applied")):
            minimum_hits += 1
        if bool(effective_breakdown.get("ceiling_applied")):
            maximum_hits += 1
        elif ceiling_charge > 0 and shipping_amount >= ceiling_charge * 0.9:
            near_cap_count += 1

    historical_orders: list[dict[str, Any]] = []
    for allocation in allocations[: max(limit, 1)]:
        effective_breakdown = deserialize_pricing_breakdown_json(
            cast(str | None, getattr(allocation, "accepted_pricing_breakdown_json", None))
            or cast(str | None, getattr(allocation, "pricing_breakdown_json", None))
        )
        effective_amounts = effective_allocation_delivery_amounts(allocation)
        activity_timestamp = (
            cast(Optional[datetime], getattr(allocation, "accepted_at", None))
            or cast(Optional[datetime], getattr(allocation, "updated_at", None))
            or cast(Optional[datetime], getattr(allocation, "created_at", None))
        )
        historical_orders.append(
            {
                "id": f"allocation-{allocation.id}",
                "source": "accepted_load_fit" if getattr(allocation, "accepted_vehicle_type", None) else "order_quote",
                "label": f"Order #{allocation.order_id} · {allocation.destination_city or allocation.destination_country or 'Route'}",
                "order_id": allocation.order_id,
                "shipment_id": allocation.shipment_id,
                "service_area_id": allocation.service_area_id,
                "route_type": effective_breakdown.get("route_type") or "in_city",
                "distance_km": effective_breakdown.get("distance_km"),
                "weight_kg": effective_breakdown.get("total_weight_kg"),
                "pickup_count": effective_breakdown.get("pickup_count") or 1,
                "dropoff_count": effective_breakdown.get("dropoff_count") or 1,
                "handling_labels": effective_breakdown.get("matched_handling_labels") or [],
                "load_fit_label": getattr(allocation, "accepted_vehicle_type", None) or effective_breakdown.get("load_fit_label"),
                "load_fit_factor": float(getattr(allocation, "accepted_vehicle_multiplier", 0) or effective_breakdown.get("load_fit_factor") or 0) or None,
                "shipping_amount": float(effective_amounts["shipping_amount"]),
                "destination_city": allocation.destination_city,
                "destination_country": allocation.destination_country,
                "created_at": activity_timestamp.isoformat() if activity_timestamp else None,
            }
        )

    route_presets: list[dict[str, Any]] = []
    areas_q = db.query(LogisticsPartnerServiceArea).options(selectinload(LogisticsPartnerServiceArea.partner)).filter(
        LogisticsPartnerServiceArea.partner_id == resolved_partner_id,
        LogisticsPartnerServiceArea.approval_status == "approved",
        LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
    )
    if service_area_id is not None:
        areas_q = areas_q.filter(LogisticsPartnerServiceArea.id == service_area_id)
    for area in areas_q.order_by(desc(LogisticsPartnerServiceArea.updated_at), desc(LogisticsPartnerServiceArea.id)).all():
        origin_city = normalize_city_name(cast(Optional[str], getattr(area, "origin_city", None)) or cast(Optional[str], getattr(area, "city_name", None)))
        area_city = normalize_city_name(cast(Optional[str], getattr(area, "city_name", None)))
        updated_at = cast(Optional[datetime], getattr(area, "updated_at", None))
        route_presets.append(
            {
                "id": f"service-area-{area.id}",
                "source": "route_preset",
                "label": area.zone_label or area.city_name or area.country_name,
                "service_area_id": area.id,
                "route_type": "in_city" if origin_city and origin_city == area_city else "inter_city",
                "distance_km": None,
                "weight_kg": 8,
                "pickup_count": 1,
                "dropoff_count": 1,
                "handling_labels": [],
                "load_fit_label": None,
                "load_fit_factor": None,
                "shipping_amount": float(getattr(area, "charge_amount", 0) or 0),
                "destination_city": area.city_name,
                "destination_country": area.country_name,
                "created_at": updated_at.isoformat() if updated_at else None,
            }
        )

    alerts: list[dict[str, Any]] = []
    if minimum_hits:
        alerts.append({
            "kind": "minimum_hit",
            "severity": "warning",
            "count": minimum_hits,
            "title": "Minimum floor is still rescuing live quotes",
            "body": f"{minimum_hits} historical lane(s) landed below the configured floor and were lifted to the minimum charge.",
        })
    if maximum_hits:
        alerts.append({
            "kind": "maximum_hit",
            "severity": "danger",
            "count": maximum_hits,
            "title": "Maximum cap is actively clamping quotes",
            "body": f"{maximum_hits} historical lane(s) exceeded the ceiling and were reduced to the configured maximum charge.",
        })
    if near_cap_count:
        alerts.append({
            "kind": "near_cap",
            "severity": "info",
            "count": near_cap_count,
            "title": "Some lanes are close to the cap",
            "body": f"{near_cap_count} historical lane(s) finished within 90% of the configured maximum charge.",
        })

    return {
        "partner_id": resolved_partner_id,
        "service_area_id": service_area_id,
        "health_summary": {
            "total_allocations": len(allocations),
            "minimum_hits": minimum_hits,
            "maximum_hits": maximum_hits,
            "near_cap_count": near_cap_count,
            "accepted_vehicle_count": accepted_vehicle_count,
            "average_effective_charge": round(total_effective_shipping / len(allocations), 2) if allocations else 0.0,
            "average_accepted_charge": round(accepted_shipping_total / accepted_shipping_rows, 2) if accepted_shipping_rows else None,
        },
        "alerts": alerts,
        "historical_orders": historical_orders,
        "route_presets": route_presets,
    }


def update_shipment_status_partner(
    shipment_id: int,
    data: dict,
    current_user: dict,
    db: Session,
) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    partner: LogisticsPartner | None = None
    partner_has_approved_service_areas = False
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        partner_has_approved_service_areas = (
            db.query(LogisticsPartnerServiceArea)
            .filter(
                LogisticsPartnerServiceArea.partner_id == cast(int, getattr(partner, "id")),
                LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
                LogisticsPartnerServiceArea.approval_status == "approved",
            )
            .first()
            is not None
        )

    allowed_statuses = ("processing", "prepared", "picking_up", "shipped", "in_transit", "delivered", "failed", "returned")
    requested_status = str(data.get("status", "")).strip()
    if requested_status not in allowed_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {allowed_statuses}")

    new_status = "processing" if requested_status == "prepared" else requested_status
    old_status = cast(str, getattr(shipment, "status"))
    external_old_status = _partner_api_status(shipment)
    vehicle_selection_note: str | None = None

    if role == "logistics_partner" and partner is not None:
        partner_id = cast(int, getattr(partner, "id"))
        assigned_partner_id = cast(Optional[int], getattr(shipment, "assigned_partner_id", None))
        visible_pickup = _pickup_visible_to_partner(shipment, partner, db)
        assigned_to_partner = assigned_partner_id == partner_id
        explicit_pickup_claim = (
            external_old_status == "prepared"
            and requested_status == "picking_up"
            and assigned_partner_id is None
            and not partner_has_approved_service_areas
        )
        if not visible_pickup and not assigned_to_partner and not explicit_pickup_claim:
            raise HTTPException(status_code=404, detail="Shipment not found")

        allowed_transitions = {
            "prepared": {"picking_up"},
            "picking_up": {"prepared", "shipped"},
            "shipped": {"in_transit", "delivered", "failed", "returned"},
            "in_transit": {"delivered", "failed", "returned"},
            "delivered": set(),
            "failed": set(),
            "returned": set(),
        }
        if requested_status not in allowed_transitions.get(external_old_status, set()) and requested_status != external_old_status:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot change shipment status from '{external_old_status}' to '{requested_status}'",
            )

        if external_old_status == "prepared" and requested_status == "picking_up":
            setattr(shipment, "assigned_partner_id", partner_id)
            requested_vehicle_type = str(data.get("load_fit_label") or data.get("vehicle_type") or "").strip()
            if requested_vehicle_type:
                accepted_breakdown = apply_shipment_vehicle_selection(
                    shipment,
                    db,
                    vehicle_type=requested_vehicle_type,
                )
                if accepted_breakdown is not None:
                    vehicle_selection_note = (
                        f"Load-fit locked: {accepted_breakdown.get('load_fit_label') or requested_vehicle_type} "
                        f"x{float(accepted_breakdown.get('load_fit_factor') or 1):.2f} · "
                        f"payout {float(accepted_breakdown.get('shipping_amount') or 0):.2f}"
                    )

        if external_old_status == "picking_up" and requested_status == "prepared" and bool(data.get("release_assignment", True)):
            setattr(shipment, "assigned_partner_id", None)
            apply_shipment_vehicle_selection(shipment, db, vehicle_type=None)
            vehicle_selection_note = "Load-fit override cleared"

        if new_status == "delivered":
            _apply_delivery_signature(shipment, cast(dict[str, Any], data))

    setattr(shipment, "status", new_status)
    if data.get("current_hub"):
        setattr(shipment, "current_hub", data["current_hub"])
    if data.get("tracking_number"):
        setattr(shipment, "tracking_number", data["tracking_number"])
    submitted_scan_code = str(data.get("scan_code", "")).strip()
    if submitted_scan_code and submitted_scan_code not in shipment_scan_codes(shipment):
        raise HTTPException(status_code=409, detail="scan_code does not match this shipment")
    if not cast(Optional[str], getattr(shipment, "scan_code", None)):
        setattr(shipment, "scan_code", canonical_scan_code(shipment))
    if new_status == "shipped" and not cast(Optional[datetime], getattr(shipment, "shipped_at", None)):
        setattr(shipment, "shipped_at", _utcnow())
    if new_status == "delivered" and not cast(Optional[datetime], getattr(shipment, "actual_delivery", None)):
        setattr(shipment, "actual_delivery", _utcnow())
    setattr(shipment, "updated_at", _utcnow())

    distribution_channel = cast(Optional[str], getattr(shipment, "distribution_channel", None))
    event_type_raw = str(data.get("event_type", "")).strip()
    valid_event_types = {
        "picked_from_supplier", "pickup_confirmed", "pickup_cancelled", "logistics_received", "distribution_checkpoint",
        "out_for_delivery", "customer_received", "shipment_failed", "shipment_returned", "shipment_delayed",
        "shipment_rescheduled", "shipment_cancelled",
    }
    if event_type_raw in valid_event_types:
        event_type = event_type_raw
    else:
        event_type = {
            ("processing", "picking_up"): "pickup_confirmed",
            ("picking_up", "processing"): "pickup_cancelled",
            ("picking_up", "shipped"): "picked_from_supplier",
            ("shipped", "in_transit"): "distribution_checkpoint",
            ("shipped", "delivered"): "customer_received",
            ("in_transit", "delivered"): "customer_received",
            ("shipped", "failed"): "shipment_failed",
            ("in_transit", "failed"): "shipment_failed",
            ("shipped", "returned"): "shipment_returned",
            ("in_transit", "returned"): "shipment_returned",
        }.get((old_status, new_status), f"status_updated_to_{new_status}")

    event_notes = " · ".join(
        part for part in [str(data.get("notes", "")).strip() or None, vehicle_selection_note] if part
    ) or None
    event = ShipmentEvent(
        shipment_id=shipment.id,
        order_id=shipment.order_id,
        supplier_id=shipment.supplier_id,
        actor_user_id=current_user["id"],
        actor_role=role,
        event_type=event_type,
        status_after=new_status,
        distribution_channel=distribution_channel,
        location=data.get("current_hub") or data.get("location"),
        scan_code=submitted_scan_code or canonical_scan_code(shipment),
        notes=event_notes,
    )
    db.add(event)

    order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order is not None:
        order_shipments = db.query(Shipment).filter(Shipment.order_id == order.id).all()
        new_order_status = reconcile_order_status(order, order_shipments)
        setattr(order, "status", new_order_status)
        if new_order_status == "delivered":
            try:
                from services.cash_management_service import create_settlements_on_delivery

                create_settlements_on_delivery(order, db)
            except Exception:
                logger.exception("Failed to create settlements for delivered order %s", order.id)

    _notify_partner_transition(shipment, new_status, db)
    db.commit()
    db.refresh(shipment)
    db.refresh(event)
    _publish_shipment_update(shipment, event)
    try:
        from services.transactional_email_service import enqueue_shipment_status_email

        enqueue_shipment_status_email(cast(int, shipment.id), event_type=cast(str, event.event_type))
    except Exception:
        logger.exception("Failed to enqueue shipment-status email for shipment %s", shipment.id)

    return {
        "id": shipment.id,
        "status": _partner_api_status(shipment),
        "status_label": _status_display(shipment),
        "old_status": external_old_status,
        "assigned_partner_id": shipment.assigned_partner_id,
        "current_hub": shipment.current_hub,
        "tracking_number": shipment.tracking_number,
        "accepted_load_fit_label": cast(Optional[str], getattr(shipment, "accepted_vehicle_type", None)),
        "accepted_load_fit_factor": float(getattr(shipment, "accepted_vehicle_multiplier", 0) or 0) if getattr(shipment, "accepted_vehicle_multiplier", None) is not None else None,
        "accepted_vehicle_type": cast(Optional[str], getattr(shipment, "accepted_vehicle_type", None)),
        "accepted_vehicle_multiplier": float(getattr(shipment, "accepted_vehicle_multiplier", 0) or 0) if getattr(shipment, "accepted_vehicle_multiplier", None) is not None else None,
    }


def bulk_update_shipment_status_partner(
    shipment_ids: list,
    status: str,
    notes: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """
    Bulk-update shipment status for logistics partners and admins.
    Partners can only update their own assigned / pickup-ready shipments.
    Admins can update any shipment.
    """
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    if not shipment_ids:
        raise HTTPException(status_code=400, detail="No shipment IDs provided")
    if len(shipment_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot update more than 100 shipments at once")

    # Resolve partner early for role == logistics_partner
    partner: LogisticsPartner | None = None
    if role == "logistics_partner":
        partner = _get_partner_for_user(current_user["id"], db)
        if not _partner_is_active(partner):
            raise HTTPException(status_code=403, detail="Logistics partner account is not active")

    allowed_statuses = ("picking_up", "shipped", "in_transit", "delivered", "failed", "returned")
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed for bulk update: {allowed_statuses}",
        )

    # partner-role transition map (same table as single update)
    allowed_transitions = {
        "prepared": {"picking_up"},
        "picking_up": {"shipped"},
        "shipped": {"in_transit", "delivered", "failed", "returned"},
        "in_transit": {"delivered", "failed", "returned"},
    }

    updated: list[dict] = []
    skipped: list[dict] = []

    for sid in shipment_ids:
        shipment = db.query(Shipment).filter(Shipment.id == sid).first()
        if not shipment:
            skipped.append({"id": sid, "reason": "Not found"})
            continue

        external_old_status = _partner_api_status(shipment)
        old_status = cast(str, getattr(shipment, "status"))

        if role == "logistics_partner" and partner is not None:
            partner_id = cast(int, getattr(partner, "id"))
            assigned_partner_id = cast(Optional[int], getattr(shipment, "assigned_partner_id", None))
            visible_pickup = _pickup_visible_to_partner(shipment, partner, db)
            assigned_to_partner = assigned_partner_id == partner_id

            if not visible_pickup and not assigned_to_partner:
                skipped.append({"id": sid, "reason": "Not assigned to this partner"})
                continue

            if status not in allowed_transitions.get(external_old_status, set()):
                skipped.append({
                    "id": sid,
                    "reason": f"Invalid transition from '{external_old_status}' to '{status}'",
                })
                continue

            # Auto-assign partner on first pickup
            if external_old_status == "prepared" and status == "picking_up":
                setattr(shipment, "assigned_partner_id", partner_id)

        new_internal_status = shipment.status if status == "prepared" else status

        # delivered requires signature — skip for bulk (no per-shipment signature input)
        if status == "delivered":
            skipped.append({
                "id": sid,
                "reason": "Delivery requires signature confirmation; use the single-shipment endpoint",
            })
            continue

        setattr(shipment, "status", new_internal_status)
        if status == "shipped" and not cast(Optional[datetime], getattr(shipment, "shipped_at", None)):
            setattr(shipment, "shipped_at", _utcnow())
        setattr(shipment, "updated_at", _utcnow())

        event_type = {
            "picking_up": "pickup_confirmed",
            "shipped": "picked_from_supplier",
            "in_transit": "distribution_checkpoint",
            "failed": "shipment_failed",
            "returned": "shipment_returned",
        }.get(status, f"status_updated_to_{status}")

        distribution_channel = cast(Optional[str], getattr(shipment, "distribution_channel", None))
        event = ShipmentEvent(
            shipment_id=shipment.id,
            order_id=shipment.order_id,
            supplier_id=shipment.supplier_id,
            actor_user_id=current_user["id"],
            actor_role=role,
            event_type=event_type,
            status_after=new_internal_status,
            distribution_channel=distribution_channel,
            notes=notes,
        )
        db.add(event)

        # Reconcile parent order status
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order is not None:
            order_shipments = db.query(Shipment).filter(Shipment.order_id == order.id).all()
            setattr(order, "status", reconcile_order_status(order, order_shipments))

        updated.append({"id": sid, "new_status": status, "old_status": external_old_status})

    if updated:
        db.commit()
        audit_log(
            db=db,
            action=AuditAction.SHIPMENT_STATUS_UPDATED,
            user_id=current_user["id"],
            username=current_user.get("username"),
            user_role=role,
            resource_type="shipment",
            resource_id=0,
            details={
                "bulk": True,
                "count": len(updated),
                "status": status,
                "ids": [u["id"] for u in updated],
            },
            status="success",
        )

    return {
        "status": status,
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


# ── Logistics Partner Bank Account (Payout Beneficiary) ─────────────────────

def _get_partner_for_user(current_user: dict | int, db: Session) -> LogisticsPartner:
    user_id = int(current_user["id"]) if isinstance(current_user, dict) else int(current_user)
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    if partner is None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or cast(str, getattr(user, "role", "")) != "logistics_partner":
            raise HTTPException(status_code=403, detail="No logistics partner profile found")

        partner = LogisticsPartner(
            name=f"{cast(str, getattr(user, 'username', 'Partner'))} Logistics",
            code=_next_partner_code(db, user_id),
            contact_name=cast(Optional[str], getattr(user, "username", None)),
            contact_email=cast(Optional[str], getattr(user, "email", None)),
            contact_phone=cast(Optional[str], getattr(user, "phone", None)),
            status="pending_onboarding",
            user_id=user_id,
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
    return partner


def get_partner_bank_account(current_user: dict, db: Session) -> dict:
    """Return the logistics partner's own bank account details."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required.")
    partner = _get_partner_for_user(current_user, db)
    partner_id = int(cast(int, partner.id))
    record = db.query(LogisticsPartnerBankAccount).filter(
        LogisticsPartnerBankAccount.partner_id == partner_id
    ).first()
    if record is None:
        return {"configured": False}
    return {
        "configured": True,
        "id": record.id,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": record.account_number,
        "iban": record.iban,
        "swift_code": record.swift_code,
        "routing_number": record.routing_number,
        "currency": record.currency,
        "bank_country": record.bank_country,
        "verification_status": record.verification_status,
        "verification_note": record.verification_note,
        "provider": record.provider,
        "provider_recipient_id": record.provider_recipient_id,
        "provider_status": record.provider_status,
        "provider_last_synced_at": record.provider_last_synced_at.isoformat() if record.provider_last_synced_at else None,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def upsert_partner_bank_account(body: dict, current_user: dict, db: Session) -> dict:
    """Logistics partner submits or updates their payout bank account. Triggers re-verification."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required.")
    partner = _get_partner_for_user(current_user, db)
    partner_id = int(cast(int, partner.id))

    record = db.query(LogisticsPartnerBankAccount).filter(
        LogisticsPartnerBankAccount.partner_id == partner_id
    ).first()
    is_new = record is None
    if is_new:
        record = LogisticsPartnerBankAccount(partner_id=partner_id)
        db.add(record)

    for field in ("beneficiary_name", "bank_name", "branch_name", "account_number",
                  "iban", "swift_code", "routing_number", "currency", "bank_country"):
        value = body.get(field)
        if value is not None:
            setattr(record, field, value)

    if not is_new and getattr(record, "verification_status", "pending") != "pending":
        setattr(record, "verification_status", "pending")
        setattr(record, "verification_note", "Resubmitted by partner — awaiting re-verification.")
        setattr(record, "provider", None)
        setattr(record, "provider_recipient_id", None)
        setattr(record, "provider_status", None)
        setattr(record, "provider_last_synced_at", None)
        setattr(record, "verified_at", None)
        setattr(record, "verified_by", None)

    db.commit()
    db.refresh(record)
    return {
        "ok": True,
        "id": record.id,
        "verification_status": record.verification_status,
        "message": "Bank account saved. Awaiting admin verification." if is_new else "Bank account updated. Awaiting re-verification.",
    }


# ── Logistics Partner Documents ───────────────────────────────────────────────

ALLOWED_LP_DOC_TYPES = (
    "business_license", "trade_license", "tax_certificate",
    "national_id", "bank_statement", "insurance", "other",
)


def _serialize_lp_doc(doc: LogisticsPartnerDocument) -> dict:
    expires_at = cast(Optional[datetime], getattr(doc, "expires_at", None))
    reviewed_at = cast(Optional[datetime], getattr(doc, "reviewed_at", None))
    created_at = cast(Optional[datetime], getattr(doc, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(doc, "updated_at", None))
    return {
        "id": doc.id,
        "partner_id": doc.partner_id,
        "document_type": doc.document_type,
        "document_name": doc.document_name,
        "file_url": doc.file_url,
        "status": doc.status,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "review_note": doc.review_note,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def list_partner_documents(current_user: dict, db: Session) -> list:
    """List all documents submitted by the authenticated logistics partner."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user, db)
    docs = (
        db.query(LogisticsPartnerDocument)
        .filter(LogisticsPartnerDocument.partner_id == cast(int, partner.id))
        .order_by(LogisticsPartnerDocument.created_at.desc())
        .all()
    )
    return [_serialize_lp_doc(d) for d in docs]


def list_partner_cod_remittance_receipts(
    current_user: dict,
    db: Session,
    *,
    status: str | None = None,
    settlement_id: int | None = None,
) -> list[dict[str, Any]]:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user, db)
    receipts = list_cod_remittance_receipts(
        db,
        partner_id=cast(int, partner.id),
        status=(status or None),
        settlement_id=settlement_id,
        limit=100,
    )
    return [serialize_cod_remittance_receipt(receipt, db) for receipt in receipts]


async def upload_partner_cod_remittance_receipt(
    settlement_id: int,
    amount: float,
    file: UploadFile,
    bank_reference: Optional[str],
    notes: Optional[str],
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Receipt amount must be positive")

    from services.storage import storage as _storage
    from utils.file_validation import validate_upload_document
    from utils.constants import MAX_UPLOAD_SIZE_BYTES

    safe_name = os.path.basename(file.filename or "cod-receipt.pdf")
    ext = os.path.splitext(safe_name)[1].lower() or ".pdf"
    filename = f"cod_receipt_{uuid.uuid4().hex}{ext}"
    key = f"logistics_cod_receipts/{filename}"

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    validate_upload_document(contents, safe_name)
    url = _storage.save(key, contents, content_type=file.content_type)

    partner = _get_partner_for_user(current_user, db)
    try:
        receipt = create_cod_remittance_receipt(
            settlement_id=settlement_id,
            partner_id=cast(int, partner.id),
            amount=cast(Any, amount),
            receipt_file_url=url,
            db=db,
            bank_reference=bank_reference,
            notes=notes,
        )
        db.commit()
        db.refresh(receipt)
        return serialize_cod_remittance_receipt(receipt, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


async def upload_partner_document(
    file: UploadFile,
    document_type: str,
    document_name: str,
    expires_at_str: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """Upload a KYC/compliance document for the authenticated logistics partner."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    if document_type not in ALLOWED_LP_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid document type. Allowed: {ALLOWED_LP_DOC_TYPES}")

    from services.storage import storage as _storage
    from utils.file_validation import validate_upload_document
    from utils.constants import MAX_UPLOAD_SIZE_BYTES

    safe_name = os.path.basename(file.filename or "document.pdf")
    ext = os.path.splitext(safe_name)[1].lower() or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"lp_documents/{filename}"

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    validate_upload_document(contents, safe_name)
    url = _storage.save(key, contents, content_type=file.content_type)

    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    partner = _get_partner_for_user(current_user, db)
    doc = LogisticsPartnerDocument(
        partner_id=cast(int, partner.id),
        document_type=document_type,
        document_name=document_name or safe_name,
        file_url=url,
        status="pending",
        expires_at=expires_at,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _serialize_lp_doc(doc)


def delete_partner_document(doc_id: int, current_user: dict, db: Session) -> dict:
    """Delete a document — only allowed when status is pending or rejected."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user, db)
    doc = db.query(LogisticsPartnerDocument).filter(
        LogisticsPartnerDocument.id == doc_id,
        LogisticsPartnerDocument.partner_id == cast(int, partner.id),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status in ("under_review", "approved"):
        raise HTTPException(status_code=409, detail="Cannot delete a document that is under review or approved")
    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}


def admin_review_lp_document(doc_id: int, data: dict, current_user: dict, db: Session) -> dict:
    """Admin reviews a logistics partner document — approve/reject with optional note."""
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Admin access required")

    doc = db.query(LogisticsPartnerDocument).filter(LogisticsPartnerDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    allowed_statuses = ("pending", "under_review", "approved", "rejected", "expired")
    new_status = data.get("status")
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {allowed_statuses}")

    setattr(doc, "status", new_status)
    setattr(doc, "review_note", data.get("review_note"))
    setattr(doc, "reviewed_by", current_user["id"])
    setattr(doc, "reviewed_at", _utcnow())
    setattr(doc, "updated_at", _utcnow())
    db.commit()
    db.refresh(doc)
    return _serialize_lp_doc(doc)


# ── City Distance Matrix CRUD (admin only) ────────────────────────────────────

def _serialize_city_distance(entry: CityDistanceMatrix) -> dict[str, Any]:
    created_at = cast(Optional[datetime], getattr(entry, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(entry, "updated_at", None))
    return {
        "id": entry.id,
        "origin_country_code": entry.origin_country_code,
        "origin_city_name": entry.origin_city_name,
        "destination_country_code": entry.destination_country_code,
        "destination_city_name": entry.destination_city_name,
        "distance_km": float(entry.distance_km),
        "notes": entry.notes,
        "created_by": entry.created_by,
        "updated_by": entry.updated_by,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def list_city_distances(
    current_user: dict,
    db: Session,
    *,
    origin_country_code: str | None = None,
    destination_country_code: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    _require_admin(current_user)
    query = db.query(CityDistanceMatrix)
    if origin_country_code:
        query = query.filter(CityDistanceMatrix.origin_country_code == origin_country_code.upper())
    if destination_country_code:
        query = query.filter(CityDistanceMatrix.destination_country_code == destination_country_code.upper())
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            func.lower(CityDistanceMatrix.origin_city_name).like(like)
            | func.lower(CityDistanceMatrix.destination_city_name).like(like)
        )
    total = query.count()
    items = (
        query.order_by(CityDistanceMatrix.origin_country_code, CityDistanceMatrix.origin_city_name, CityDistanceMatrix.destination_city_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": [_serialize_city_distance(e) for e in items]}


def create_city_distance(data: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    origin_cc = normalize_country_code(str(data.get("origin_country_code") or ""))
    dest_cc = normalize_country_code(str(data.get("destination_country_code") or ""))
    origin_city = _sanitize_optional_string(data.get("origin_city_name"), max_length=120)
    dest_city = _sanitize_optional_string(data.get("destination_city_name"), max_length=120)
    if not origin_cc or not dest_cc or not origin_city or not dest_city:
        raise HTTPException(status_code=422, detail="origin_country_code, origin_city_name, destination_country_code, destination_city_name are all required")
    try:
        distance_km = float(data.get("distance_km") or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="distance_km must be a positive number") from exc
    if distance_km <= 0:
        raise HTTPException(status_code=422, detail="distance_km must be greater than 0")
    existing = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    origin_key = normalize_city_name(origin_city)
    dest_key = normalize_city_name(dest_city)
    for row in existing:
        if (
            normalize_city_name(cast(str | None, getattr(row, "origin_city_name", None))) == origin_key
            and normalize_city_name(cast(str | None, getattr(row, "destination_city_name", None))) == dest_key
        ):
            raise HTTPException(status_code=409, detail="A distance entry for this route already exists. Use PUT to update it.")
    entry = CityDistanceMatrix(
        origin_country_code=origin_cc,
        origin_city_name=origin_city,
        destination_country_code=dest_cc,
        destination_city_name=dest_city,
        distance_km=distance_km,
        notes=_sanitize_optional_string(data.get("notes"), max_length=1000),
        created_by=current_user["id"],
        updated_by=current_user["id"],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _serialize_city_distance(entry)


def update_city_distance(matrix_id: int, data: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    entry = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="City distance entry not found")
    try:
        distance_km = float(data.get("distance_km") or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="distance_km must be a positive number") from exc
    if distance_km <= 0:
        raise HTTPException(status_code=422, detail="distance_km must be greater than 0")
    setattr(entry, "distance_km", distance_km)
    if "notes" in data:
        setattr(entry, "notes", _sanitize_optional_string(data.get("notes"), max_length=1000))
    setattr(entry, "updated_by", current_user["id"])
    setattr(entry, "updated_at", _utcnow())
    db.commit()
    db.refresh(entry)
    return _serialize_city_distance(entry)


def delete_city_distance(matrix_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    entry = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="City distance entry not found")
    db.delete(entry)
    db.commit()
    return {"detail": "City distance entry deleted"}



