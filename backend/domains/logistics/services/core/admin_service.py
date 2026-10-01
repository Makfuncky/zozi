from __future__ import annotations

"""Admin service — admin-only operations for logistics partners."""

import json
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from domains.governance.models.admin import LogisticsPartnerDocument, LogisticsSettlement
from domains.accounts.models.user import User
from domains.logistics.models.logistics import (
    LogisticsCategoryPricingRule,
    LogisticsPartner,
    LogisticsPartnerServiceArea,
    LogisticsPricingProfile,
    LogisticsVehicleRule,
)
from domains.orders.models.order_entities import Order, OrderLogisticsAllocation
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.finance import TransactionLedger
from domains.logistics.services.partners.partner_service import (
    _serialize_partner,
    _get_partner_for_user,
    _resolve_partner_user_link,
    _build_partner_delete_blocker,
    _parse_partner_social_links,
    _sanitize_optional_string,
    _next_partner_code,
)
from domains.logistics.services.partners.pricing_service import (
    serialize_service_area,
    serialize_pricing_profile,
    serialize_category_pricing_rule,
    serialize_vehicle_rule,
)
from infrastructure.utils.datetime_utils import utcnow as _utcnow

_PARTNER_DELETE_BLOCKING_MODELS: list[tuple[Any, Any, str]] = [
    (LogisticsSettlement, LogisticsSettlement.partner_id, "logistics settlement record(s)"),
    (LogisticsPartnerPayout, LogisticsPartnerPayout.partner_id, "partner payout record(s)"),
    (TransactionLedger, TransactionLedger.logistics_partner_id, "transaction ledger record(s)"),
    (OrderLogisticsAllocation, OrderLogisticsAllocation.partner_id, "order logistics allocation(s)"),
    (Order, Order.selected_partner_id, "order quote selection(s)"),
]


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


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


def _serialize_lp_doc(doc: LogisticsPartnerDocument) -> dict:
    created_at = cast(Optional[datetime], getattr(doc, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(doc, "updated_at", None))
    expires_at = cast(Optional[datetime], getattr(doc, "expires_at", None))
    reviewed_at = cast(Optional[datetime], getattr(doc, "reviewed_at", None))
    return {
        "id": doc.id,
        "partner_id": doc.partner_id,
        "document_type": doc.document_type,
        "document_name": doc.document_name,
        "file_url": doc.file_url,
        "status": doc.status,
        "review_note": doc.review_note,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }
