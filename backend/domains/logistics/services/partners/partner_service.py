from __future__ import annotations

"""Partner service — logistics partner CRUD and profile management."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func

from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsCODRemittanceReceipt, LogisticsPartnerDocument, LogisticsSettlement
from domains.accounts.models.user import User
from domains.logistics.models.logistics import (
    LogisticsPartner,
    LogisticsPartnerServiceArea,
    Shipment,
)
from domains.orders.models.order_entities import Order, OrderLogisticsAllocation
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.finance import TransactionLedger
from domains.logistics.services.partners.pricing_service import (
    normalize_country_code,
    serialize_service_area,
)
from infrastructure.utils.auth import get_password_hash
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

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
        raise HTTPException(status_code=404, detail="Partner not found")
    return _serialize_partner(partner, include_internal=False)
