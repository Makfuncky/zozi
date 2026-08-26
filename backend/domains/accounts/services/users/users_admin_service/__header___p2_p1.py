"""Admin users controller."""
from __future__ import annotations

from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.core import AuditLog
from domains.governance.models.core import SupportTicket
from domains.governance.models.core import Address
from domains.governance.models.core import CartItem
from domains.governance.models.user import User
from domains.governance.models.user import ReferralPointEvent
from domains.governance.models.user import PasswordResetToken
from domains.governance.models.user import EmailVerificationToken
from domains.governance.models.user import RevokedToken
from domains.catalog.models.products import Wishlist
from domains.catalog.models.products import Review
from domains.comms.models.communication import Notification
from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailTemplate
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.suppliers import SupplierDocument
from domains.comms.models.suppliers import SupplierProfile
from domains.finance.models.commission import CommissionLedgerEntry
from domains.finance.models.commission import CommissionAgreement
from domains.finance.models.commission import ProductCommissionOverride
from domains.finance.models.commission import CommissionCategoryRate
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import TransactionLedger
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import BankTransaction
from domains.finance.models.finance import VATRemittance
from domains.governance.models.admin import BadgeBillingRecord
from domains.governance.models.admin import ChatbotQueryEvent
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ProductVerification
from domains.governance.models.admin import LogisticsPartnerDocument
from domains.governance.models.admin import PromotionEngineConfig
from domains.governance.models.admin import PromotionOrderTier
from domains.governance.models.admin import PromotionLedgerEntry
from domains.governance.models.admin import PaymentProviderConfig
from domains.governance.models.admin import EmailProviderConfig
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.governance.models.admin import SupplierBankAccount
from domains.governance.models.admin import LogisticsPartnerBankAccount
from domains.governance.models.admin import FinanceBankAccount
from domains.governance.models.admin import RolePermissionSetting
from domains.governance.models.admin import TicketReply
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import CommissionBadgeTier
from domains.governance.models.admin import CouponUsage
from domains.governance.models.admin import PushNotificationToken
from domains.governance.models.admin import ShippingZone
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.orders.models.orders import ReturnRequest
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.catalog.models.promotions import Banner
from domains.finance.models.payments import PaymentGatewayConnection
from domains.finance.models.payments import Payout
from infrastructure.utils.auth import get_password_hash, require_permission
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.constants import STAFF_ROLES, _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE
from infrastructure.utils.staff_permissions import default_permissions_for_role, sanitize_staff_permissions
from infrastructure.utils.admin_shared import VALID_USER_ROLES, ALLOWED_BANK_ACCOUNT_KINDS as _ALLOWED_BANK_ACCOUNT_KINDS

from infrastructure.database.schemas import CreateStaffAccount, UpdateStaffAccount


def _require_admin(current_user: dict) -> None:
    role = current_user["role"]
    if role not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required.")


def bulk_toggle_users_active(
    user_ids: List[int], is_active: bool, acting_user: dict, db: Session
) -> dict:
    """Bulk enable or disable multiple user accounts (admin / sub_admin)."""
    require_permission("users.toggle_active", acting_user)
    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 users at once")

    updated: List[dict] = []
    skipped: List[dict] = []

    for uid in user_ids:
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot change own account status"})
            continue
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue
        if cast(str, getattr(user, "email", "")) in _PROTECTED_EMAILS:
            skipped.append({"id": uid, "reason": "Protected account"})
            continue
        current_active = bool(cast(Any, getattr(user, "is_active")))
        if current_active == is_active:
            skipped.append({"id": uid, "reason": "Status unchanged"})
            continue
        setattr(user, "is_active", int(is_active))
        updated.append({"id": uid, "username": user.username, "is_active": is_active})

    if updated:
        db.commit()
        audit_log(
            db=db,
            action="USER_BULK_TOGGLE_ACTIVE",
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "is_active": is_active, "count": len(updated), "users": updated},
            status="success",
        )
    return {
        "is_active": is_active,
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def create_staff_account(payload: CreateStaffAccount, acting_user: dict, db: Session) -> dict:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create staff accounts")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    assigned_permissions = sanitize_staff_permissions(payload.permissions)
    if not assigned_permissions:
        assigned_permissions = default_permissions_for_role(payload.role)

    new_user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        country_code=acting_user.get("country_code") or "OM",
        is_active=1,
        phone=payload.phone,
        email_verified=True,
        staff_role_label=payload.staff_role_label,
        staff_title=payload.staff_title,
        staff_department=payload.staff_department,
        staff_area_of_operation=payload.staff_area_of_operation,
        staff_hire_date=payload.staff_hire_date,
        staff_experience_level=payload.staff_experience_level,
        staff_performance_summary=payload.staff_performance_summary,
        staff_assigned_tasks=payload.staff_assigned_tasks,
        staff_assigned_projects=payload.staff_assigned_projects,
        staff_permissions=assigned_permissions,
        staff_notes=payload.staff_notes,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_log(
        db=db,
        action=AuditAction.STAFF_CREATED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=cast(int, getattr(new_user, "id")),
        details={
            "created_username": new_user.username,
            "role": new_user.role,
            "staff_role_label": new_user.staff_role_label,
            "staff_title": new_user.staff_title,
            "staff_area_of_operation": new_user.staff_area_of_operation,
            "staff_hire_date": getattr(new_user, "staff_hire_date", None),
            "permissions": assigned_permissions,
        },
        status="success",
    )
    return _serialize_staff_user(new_user)


def update_staff_account(user_id: int, payload: UpdateStaffAccount, acting_user: dict, db: Session) -> dict[str, Any]:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update staff accounts")

    user = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    updates = payload.model_dump(exclude_unset=True)
    next_role = cast(str, updates.get("role", getattr(user, "role")))
    explicit_permissions = updates.get("permissions")

    if user_id == acting_user["id"]:
        if "role" in updates or "permissions" in updates or updates.get("is_active") is False:
            raise HTTPException(status_code=400, detail="Cannot change your own role, permissions, or active status")

    next_email = cast(str | None, updates.get("email"))
    if next_email and next_email != getattr(user, "email"):
        existing = db.query(User).filter(User.email == next_email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    if "full_name" in updates:
        setattr(user, "full_name", updates["full_name"])
    if "email" in updates:
        setattr(user, "email", updates["email"])
    if "phone" in updates:
        setattr(user, "phone", updates["phone"])
    if "role" in updates:
        setattr(user, "role", next_role)
    if "staff_role_label" in updates:
        setattr(user, "staff_role_label", updates["staff_role_label"])
    if "staff_title" in updates:
        setattr(user, "staff_title", updates["staff_title"])
    if "staff_department" in updates:
        setattr(user, "staff_department", updates["staff_department"])
    if "staff_area_of_operation" in updates:
        setattr(user, "staff_area_of_operation", updates["staff_area_of_operation"])
    if "staff_hire_date" in updates:
        setattr(user, "staff_hire_date", updates["staff_hire_date"])
    if "staff_experience_level" in updates:
        setattr(user, "staff_experience_level", updates["staff_experience_level"])
    if "staff_performance_summary" in updates:
        setattr(user, "staff_performance_summary", updates["staff_performance_summary"])
    if "staff_assigned_tasks" in updates:
        setattr(user, "staff_assigned_tasks", updates["staff_assigned_tasks"])
    if "staff_assigned_projects" in updates:
        setattr(user, "staff_assigned_projects", updates["staff_assigned_projects"])
    if "staff_notes" in updates:
        setattr(user, "staff_notes", updates["staff_notes"])
    if "is_active" in updates:
        setattr(user, "is_active", int(bool(updates["is_active"])))

    if explicit_permissions is not None:
        sanitized_permissions = sanitize_staff_permissions(cast(list[str], explicit_permissions))
        if not sanitized_permissions:
            raise HTTPException(status_code=400, detail="Assign at least one valid permission")
        setattr(user, "staff_permissions", sanitized_permissions)
    elif "role" in updates:
        setattr(user, "staff_permissions", default_permissions_for_role(next_role))

    db.commit()
    db.refresh(user)

    audit_log(
        db=db,
        action="STAFF_UPDATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={
            "updated_fields": sorted(updates.keys()),
            "role": getattr(user, "role"),
            "permissions": _effective_staff_permissions(user),
        },
        status="success",
    )
    return _serialize_staff_user(user)


def delete_staff_account(user_id: int, acting_user: dict, db: Session) -> dict[str, Any]:
    staff_user = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    if not staff_user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    username = cast(str, getattr(staff_user, "username", ""))
    role = cast(str, getattr(staff_user, "role", ""))
    result = delete_user_admin(user_id, acting_user, db)
    audit_log(
        db=db,
        action="STAFF_DELETED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"deleted_username": username, "deleted_role": role},
        status="success",
    )
    return result


def bulk_update_staff_accounts(user_ids: List[int], updates: UpdateStaffAccount, acting_user: dict, db: Session) -> dict[str, Any]:
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can bulk update staff accounts")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")

    # Fetch all staff users at once
    staff_users = (
        db.query(User)
        .filter(User.id.in_(user_ids), User.role.in_(tuple(STAFF_ROLES)))
        .all()
    )

    found_ids = {cast(int, getattr(u, "id")) for u in staff_users}
    missing_ids = set(user_ids) - found_ids
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Staff users not found: {sorted(missing_ids)}")

    # Prevent self-update of sensitive fields
    acting_user_id = acting_user["id"]
    if acting_user_id in user_ids:
        sensitive_fields = {"role", "permissions", "is_active"}
        update_fields = updates.model_dump(exclude_unset=True).keys()
        if any(field in sensitive_fields for field in update_fields):
            raise HTTPException(status_code=400, detail="Cannot bulk update your own role, permissions, or active status")

    update_data = updates.model_dump(exclude_unset=True)
    next_role = cast(str | None, update_data.get("role"))
    explicit_permissions = update_data.get("permissions")

    # Validate role if provided
    if next_role and next_role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(STAFF_ROLES))}")

    # Validate email uniqueness if provided
    next_email = cast(str | None, update_data.get("email"))
    if next_email:
        existing = db.query(User).filter(User.email == next_email, User.id.not_in_(user_ids)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    updated_users = []
    for user in staff_users:
        user_id = cast(int, getattr(user, "id"))

        # Apply updates
        if "full_name" in update_data:
            setattr(user, "full_name", update_data["full_name"])
        if "email" in update_data:
            setattr(user, "email", update_data["email"])
        if "phone" in update_data:
            setattr(user, "phone", update_data["phone"])
        if "role" in update_data:
            setattr(user, "role", next_role)
        if "staff_role_label" in update_data:
            setattr(user, "staff_role_label", update_data["staff_role_label"])
        if "staff_title" in update_data:
            setattr(user, "staff_title", update_data["staff_title"])
        if "staff_department" in update_data:
            setattr(user, "staff_department", update_data["staff_department"])
        if "staff_area_of_operation" in update_data:
            setattr(user, "staff_area_of_operation", update_data["staff_area_of_operation"])
        if "staff_experience_level" in update_data:
            setattr(user, "staff_experience_level", update_data["staff_experience_level"])
        if "staff_performance_summary" in update_data:
            setattr(user, "staff_performance_summary", update_data["staff_performance_summary"])
        if "staff_assigned_tasks" in update_data:
            setattr(user, "staff_assigned_tasks", update_data["staff_assigned_tasks"])
        if "staff_assigned_projects" in update_data:
            setattr(user, "staff_assigned_projects", update_data["staff_assigned_projects"])
        if "staff_notes" in update_data:
            setattr(user, "staff_notes", update_data["staff_notes"])
        if "is_active" in update_data:
            setattr(user, "is_active", int(bool(update_data["is_active"])))

        # Handle permissions
        if explicit_permissions is not None:
            sanitized_permissions = sanitize_staff_permissions(cast(list[str], explicit_permissions))
            if not sanitized_permissions:
                raise HTTPException(status_code=400, detail="Assign at least one valid permission")
            setattr(user, "staff_permissions", sanitized_permissions)
        elif next_role:
            setattr(user, "staff_permissions", default_permissions_for_role(next_role))

        updated_users.append(_serialize_staff_user(user))

    db.commit()

    audit_log(
        db=db,
        action="STAFF_BULK_UPDATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=None,  # Bulk operation
        details={
            "user_ids": user_ids,
            "updated_fields": sorted(update_data.keys()),
            "count": len(user_ids),
        },
        status="success",
    )

    return {
        "message": f"Successfully updated {len(user_ids)} staff account(s)",
        "updated_users": updated_users,
        "updated_fields": sorted(update_data.keys()),
    }


def list_pending_bank_accounts(kind: str, db: Session, current_user: dict, limit: int = 200, offset: int = 0) -> list[dict]:
    """List bank accounts awaiting verification for a given kind (supplier|logistics_partner)."""
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")

    safe_limit = min(max(1, limit), 200)
    safe_offset = max(0, offset)

    if kind == "supplier":
        rows = (
            db.query(SupplierBankAccount, User.username, SupplierProfile.business_name)
            .join(User, SupplierBankAccount.supplier_id == User.id)
            .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
            .filter(SupplierBankAccount.verification_status == "pending")
            .order_by(SupplierBankAccount.created_at.asc())
            .offset(safe_offset)
            .limit(safe_limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "supplier_id": r.supplier_id,
                "entity_name": business_name or username or str(r.supplier_id),
                "beneficiary_name": r.beneficiary_name,
                "bank_name": r.bank_name,
                "branch_name": r.branch_name,
                "account_number": r.account_number,
                "iban": r.iban,
                "swift_code": r.swift_code,
                "routing_number": r.routing_number,
                "currency": r.currency,
                "bank_country": r.bank_country,
                "verification_status": r.verification_status,
                "provider": r.provider,
                "provider_recipient_id": r.provider_recipient_id,
                "provider_status": r.provider_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, username, business_name in rows
        ]
    else:
        rows = (
            db.query(LogisticsPartnerBankAccount, LogisticsPartner.name)
            .join(LogisticsPartner, LogisticsPartnerBankAccount.partner_id == LogisticsPartner.id)
            .filter(LogisticsPartnerBankAccount.verification_status == "pending")
            .order_by(LogisticsPartnerBankAccount.created_at.asc())
            .offset(safe_offset)
            .limit(safe_limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "partner_id": r.partner_id,
                "entity_name": partner_name or str(r.partner_id),
                "beneficiary_name": r.beneficiary_name,
                "bank_name": r.bank_name,
                "branch_name": r.branch_name,
                "account_number": r.account_number,
                "iban": r.iban,
                "swift_code": r.swift_code,
                "routing_number": r.routing_number,
                "currency": r.currency,
                "bank_country": r.bank_country,
                "verification_status": r.verification_status,
                "provider": r.provider,
                "provider_recipient_id": r.provider_recipient_id,
                "provider_status": r.provider_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, partner_name in rows
        ]


