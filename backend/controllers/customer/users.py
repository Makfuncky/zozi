"""Admin users controller."""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional, cast

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from data.schemas import CreateStaffAccount, UpdateStaffAccount
from data.models import (
    Address,
    AuditLog,
    BadgeBillingRecord,
    BankTransaction,
    Banner,
    CampaignRecipient,
    CartItem,
    ChatbotQueryEvent,
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    CouponUsage,
    EmailCampaign,
    EmailProviderConfig,
    EmailTemplate,
    EmailVerificationToken,
    FinanceBankAccount,
    Invoice,
    LogisticsCategoryPricingRule,
    LogisticsCODRemittanceReceipt,
    LogisticsPartner,
    LogisticsPartnerBankAccount,
    LogisticsPartnerDocument,
    LogisticsPartnerServiceArea,
    LogisticsPricingProfile,
    LogisticsVehicleRule,
    Notification,
    Order,
    OrderItem,
    OrderLogisticsAllocation,
    PasswordResetToken,
    PaymentGatewayConnection,
    PaymentProviderConfig,
    Payout,
    ProductCommissionOverride,
    ProductVerification,
    PromotionEngineConfig,
    PromotionLedgerEntry,
    PromotionOrderTier,
    PushNotificationToken,
    ReferralPointEvent,
    ReturnRequest,
    Review,
    RevokedToken,
    RolePermissionSetting,
    Shipment,
    ShipmentEvent,
    ShippingCarrier,
    ShippingZone,
    SupplierBankAccount,
    SupplierDocument,
    SupplierProfile,
    SupplierSettlement,
    SupportTicket,
    TicketReply,
    TransactionLedger,
    User,
    VATRemittance,
    Wishlist,
)
from services.db_read import aggregate_rows, all_rows, count, first
from utils.audit import AuditAction, audit_log
from utils.auth import get_password_hash, require_permission
from utils.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE, STAFF_ROLES
from utils.staff_permissions import (
    default_permissions_for_role,
    sanitize_staff_permissions,
)

from utils.admin_shared import (
    ALLOWED_BANK_ACCOUNT_KINDS,
    VALID_USER_ROLES,
    require_admin_role,
)

logger = logging.getLogger(__name__)


def _build_list_page_payload(items: list, total: int, offset: int, page_size: int) -> dict:
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


def _effective_staff_permissions(user: User) -> list[str]:
    assigned_permissions = sanitize_staff_permissions(getattr(user, "staff_permissions", None))
    if assigned_permissions:
        return assigned_permissions
    return default_permissions_for_role(cast(str | None, getattr(user, "role", None)))


def _serialize_staff_user(user: User) -> dict[str, Any]:
    return {
        "id": cast(int, getattr(user, "id")),
        "username": cast(str, getattr(user, "username")),
        "full_name": cast(str | None, getattr(user, "full_name", None)) or cast(str, getattr(user, "username")),
        "email": cast(str, getattr(user, "email")),
        "phone": cast(str | None, getattr(user, "phone", None)),
        "role": cast(str, getattr(user, "role")),
        "is_active": bool(cast(Any, getattr(user, "is_active", False))),
        "staff_role_label": cast(str | None, getattr(user, "staff_role_label", None)),
        "staff_title": cast(str | None, getattr(user, "staff_title", None)),
        "staff_department": cast(str | None, getattr(user, "staff_department", None)),
        "staff_area_of_operation": cast(str | None, getattr(user, "staff_area_of_operation", None)),
        "staff_hire_date": getattr(user, "staff_hire_date", None),
        "staff_experience_level": cast(str | None, getattr(user, "staff_experience_level", None)),
        "staff_performance_summary": cast(str | None, getattr(user, "staff_performance_summary", None)),
        "staff_assigned_tasks": list(getattr(user, "staff_assigned_tasks", None) or []),
        "staff_assigned_projects": list(getattr(user, "staff_assigned_projects", None) or []),
        "permissions": _effective_staff_permissions(user),
        "staff_notes": cast(str | None, getattr(user, "staff_notes", None)),
        "created_at": cast(datetime, getattr(user, "created_at")),
    }


def list_staff_accounts(db: Session) -> list[dict[str, Any]]:
    staff_users = all_rows(
        db,
        User,
        [User.role.in_(tuple(STAFF_ROLES))],
        order_by=[User.created_at.desc()],
        limit=200,
    )
    return [_serialize_staff_user(user) for user in staff_users]


def get_all_users(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    total = count(db, User)
    users = all_rows(
        db,
        User,
        order_by=[User.created_at.desc()],
        limit=resolved_limit,
        offset=offset or None,
    )
    if not users:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    user_ids = [cast(int, getattr(user, "id")) for user in users]
    profiles = {
        cast(int, getattr(profile, "user_id")): profile
        for profile in all_rows(db, SupplierProfile, [SupplierProfile.user_id.in_(user_ids)])
    }

    items = []
    for user in users:
        profile = profiles.get(cast(int, getattr(user, "id")))
        verification_status = cast(str | None, getattr(profile, "verification_status", None)) if profile else None
        if not verification_status:
            if bool(cast(Any, getattr(user, "is_verified", False))):
                verification_status = "verified"
            elif bool(cast(Any, getattr(user, "email_verified", False))):
                verification_status = "email_verified"
            else:
                verification_status = "pending"

        items.append({
            "id": cast(int, getattr(user, "id")),
            "email": getattr(user, "email"),
            "username": getattr(user, "username"),
            "full_name": getattr(user, "full_name", None),
            "phone": getattr(user, "phone", None),
            "role": getattr(user, "role"),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_verified": bool(getattr(user, "is_verified", False)),
            "email_verified": bool(getattr(user, "email_verified", False)),
            "verification_status": verification_status,
            "verified_at": getattr(profile, "verified_at", None) if profile else None,
            "created_at": getattr(user, "created_at"),
            "last_login": getattr(user, "last_login", None),
            "preferred_country": getattr(user, "preferred_country", None),
            "preferred_currency": getattr(user, "preferred_currency", None),
            "country_code": getattr(user, "country_code", None),
        })

    return _build_list_page_payload(items, total, offset=offset, page_size=resolved_limit)


def update_user_role(user_id: int, role: str, acting_user: dict, db: Session) -> dict:
    if role not in VALID_USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_USER_ROLES))}")

    if role in STAFF_ROLES and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign staff roles")

    user = first(db, User, [User.id == user_id])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = cast(str, getattr(user, "role"))
    update_user_role_service(db, user, role)

    audit_log(
        db=db,
        action=AuditAction.ROLE_CHANGED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"old_role": old_role, "new_role": role, "target_user": user.username},
        status="success",
    )
    return {"message": "User role updated", "old_role": old_role, "new_role": role}


def toggle_user_active(user_id: int, acting_user: dict, db: Session) -> dict:
    user = first(db, User, [User.id == user_id])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    toggle_user_active_service(db, user)
    audit_log(
        db=db,
        action="USER_ACTIVE_TOGGLED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"is_active": bool(cast(Any, getattr(user, "is_active")))},
        status="success",
    )
    return {"id": cast(int, getattr(user, "id")), "is_active": cast(Any, getattr(user, "is_active"))}


_PROTECTED_EMAILS: set[str] = {"admin@zozi.com"}

_DELETE_BLOCKING_SUPPLIER_MODELS: list[tuple[Any, Any, str]] = [
    (Shipment, Shipment.supplier_id, "shipment(s) as supplier"),
    (
        OrderLogisticsAllocation,
        getattr(OrderLogisticsAllocation, "supplier_id", OrderLogisticsAllocation.partner_id),
        "logistics allocation record(s)",
    ),
    (Invoice, Invoice.supplier_id, "invoice record(s)"),
    (TransactionLedger, TransactionLedger.supplier_id, "financial ledger record(s)"),
    (SupplierSettlement, SupplierSettlement.supplier_id, "supplier settlement record(s)"),
    (CommissionLedgerEntry, CommissionLedgerEntry.supplier_id, "commission ledger record(s)"),
    (BadgeBillingRecord, BadgeBillingRecord.supplier_id, "badge billing record(s)"),
]

_NULLABLE_USER_REFERENCE_UPDATES: list[tuple[Any, Any, str]] = [
    (User, User.referred_by_user_id, "referred_by_user_id"),
    (AuditLog, AuditLog.user_id, "user_id"),
    (ReferralPointEvent, ReferralPointEvent.referred_user_id, "referred_user_id"),
    (ChatbotQueryEvent, ChatbotQueryEvent.user_id, "user_id"),
    (CampaignRecipient, CampaignRecipient.user_id, "user_id"),
    (EmailTemplate, EmailTemplate.created_by, "created_by"),
    (EmailCampaign, EmailCampaign.created_by, "created_by"),
    (ShippingCarrier, ShippingCarrier.supplier_id, "supplier_id"),
    (Shipment, Shipment.packaged_by_user_id, "packaged_by_user_id"),
    (ShipmentEvent, ShipmentEvent.actor_user_id, "actor_user_id"),
    (Banner, Banner.created_by, "created_by"),
    (SupplierDocument, SupplierDocument.verified_by, "verified_by"),
    (ProductVerification, ProductVerification.verified_by, "verified_by"),
    (LogisticsPartner, LogisticsPartner.user_id, "user_id"),
    (LogisticsPartner, LogisticsPartner.verified_by, "verified_by"),
    (LogisticsPartnerDocument, LogisticsPartnerDocument.reviewed_by, "reviewed_by"),
    (LogisticsPartnerServiceArea, LogisticsPartnerServiceArea.reviewed_by, "reviewed_by"),
    (LogisticsPricingProfile, LogisticsPricingProfile.reviewed_by, "reviewed_by"),
    (LogisticsCategoryPricingRule, LogisticsCategoryPricingRule.reviewed_by, "reviewed_by"),
    (LogisticsVehicleRule, LogisticsVehicleRule.reviewed_by, "reviewed_by"),
    (PromotionEngineConfig, PromotionEngineConfig.updated_by, "updated_by"),
    (PromotionOrderTier, PromotionOrderTier.updated_by, "updated_by"),
    (PromotionLedgerEntry, PromotionLedgerEntry.user_id, "user_id"),
    (PaymentGatewayConnection, PaymentGatewayConnection.gateway_name, "gateway_name"),
    (PaymentProviderConfig, PaymentProviderConfig.updated_by, "updated_by"),
    (EmailProviderConfig, EmailProviderConfig.updated_by, "updated_by"),
    (LogisticsCODRemittanceReceipt, LogisticsCODRemittanceReceipt.reviewed_by, "reviewed_by"),
    (BankTransaction, BankTransaction.linked_supplier_id, "linked_supplier_id"),
    (BankTransaction, BankTransaction.reconciled_by, "reconciled_by"),
    (VATRemittance, VATRemittance.remitted_by, "remitted_by"),
    (SupplierBankAccount, SupplierBankAccount.verified_by, "verified_by"),
    (LogisticsPartnerBankAccount, LogisticsPartnerBankAccount.verified_by, "verified_by"),
    (FinanceBankAccount, FinanceBankAccount.created_by, "created_by"),
    (FinanceBankAccount, FinanceBankAccount.updated_by, "updated_by"),
    (RolePermissionSetting, RolePermissionSetting.role, "role"),
    (TicketReply, TicketReply.sender_id, "sender_id"),
    (SupportTicket, SupportTicket.user_id, "user_id"),
    (CommissionAgreement, CommissionAgreement.set_by_admin_id, "set_by_admin_id"),
    (ProductCommissionOverride, ProductCommissionOverride.set_by_admin_id, "set_by_admin_id"),
    (CommissionGlobalConfig, CommissionGlobalConfig.updated_by, "updated_by"),
    (CommissionCategoryRate, CommissionCategoryRate.category_id, "category_id"),
    (CommissionBadgeTier, CommissionBadgeTier.name, "name"),
    (CommissionLedgerEntry, CommissionLedgerEntry.adjusted_by, "adjusted_by"),
    (BadgeBillingRecord, BadgeBillingRecord.user_id, "user_id"),
]

_DELETABLE_USER_OWNED_MODELS: list[tuple[Any, Any]] = [
    (ReferralPointEvent, ReferralPointEvent.user_id),
    (Wishlist, Wishlist.user_id),
    (Address, Address.user_id),
    (Review, Review.user_id),
    (Notification, Notification.user_id),
    (CouponUsage, CouponUsage.user_id),
    (PasswordResetToken, PasswordResetToken.user_id),
    (EmailVerificationToken, EmailVerificationToken.user_id),
    (ReturnRequest, ReturnRequest.customer_id),
    (Payout, Payout.supplier_id),
    (CartItem, CartItem.user_id),
    (PushNotificationToken, PushNotificationToken.user_id),
    (RevokedToken, RevokedToken.user_id),
    (ShippingZone, ShippingZone.supplier_id),
    (SupplierDocument, SupplierDocument.supplier_id),
    (SupplierProfile, SupplierProfile.user_id),
    (SupplierBankAccount, SupplierBankAccount.supplier_id),
    (CommissionAgreement, CommissionAgreement.supplier_id),
    (ProductCommissionOverride, ProductCommissionOverride.supplier_id),
]


def bulk_update_users_role(
    user_ids: List[int], role: str, acting_user: dict, db: Session
) -> dict:
    """Bulk assign the same role to multiple users (admin-only for staff roles)."""
    require_permission("users.role.update", acting_user)

    normalized_role = str(role or "").strip()
    if normalized_role not in VALID_USER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_USER_ROLES))}",
        )

    if normalized_role in STAFF_ROLES and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign staff roles")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot update more than 200 users at once")

    updated: List[dict] = []
    skipped: List[dict] = []

    for uid in list(dict.fromkeys(user_ids)):
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot change own account role in bulk"})
            continue

        user = first(db, User, [User.id == uid])
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue

        old_role = cast(str, getattr(user, "role"))
        if old_role == normalized_role:
            skipped.append({"id": uid, "reason": "Role unchanged"})
            continue

        if old_role == "admin" and acting_user.get("role") != "admin":
            skipped.append({"id": uid, "reason": "Only admins can change admin roles"})
            continue

        update_user_role_service(db, user, normalized_role)
        updated.append(
            {
                "id": uid,
                "username": getattr(user, "username", f"user-{uid}"),
                "old_role": old_role,
                "new_role": normalized_role,
            }
        )

    if updated:
        audit_log(
            db=db,
            action=AuditAction.ROLE_CHANGED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "new_role": normalized_role, "count": len(updated), "users": updated},
            status="success",
        )

    return {
        "role": normalized_role,
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


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
        user = first(db, User, [User.id == uid])
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
        update_staff_user(db, user, {"is_active": int(is_active)})
        updated.append({"id": uid, "username": user.username, "is_active": is_active})

    if updated:
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

    if first(db, User, [User.email == payload.email]):
        raise HTTPException(status_code=400, detail="Email already registered")
    if first(db, User, [User.username == payload.username]):
        raise HTTPException(status_code=400, detail="Username already taken")

    assigned_permissions = sanitize_staff_permissions(payload.permissions)
    if not assigned_permissions:
        assigned_permissions = default_permissions_for_role(payload.role)

    new_user = create_staff_user(
        db=db,
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

    user = first(db, User, [User.id == user_id, User.role.in_(tuple(STAFF_ROLES))])
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")

    updates = payload.model_dump(exclude_unset=True)

    if user_id == acting_user["id"]:
        if "role" in updates or "permissions" in updates or updates.get("is_active") is False:
            raise HTTPException(status_code=400, detail="Cannot change your own role, permissions, or active status")

    next_email = cast(str | None, updates.get("email"))
    if next_email and next_email != getattr(user, "email"):
        existing = first(db, User, [User.email == next_email, User.id != user_id])
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_staff_user(db, user, updates)

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
    from controllers.security.admin_users import delete_user_admin

    staff_user = first(db, User, [User.id == user_id, User.role.in_(tuple(STAFF_ROLES))])
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

    staff_users = all_rows(
        db,
        User,
        [User.id.in_(user_ids), User.role.in_(tuple(STAFF_ROLES))],
    )

    found_ids = {cast(int, getattr(u, "id")) for u in staff_users}
    missing_ids = set(user_ids) - found_ids
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Staff users not found: {sorted(missing_ids)}")

    acting_user_id = acting_user["id"]
    if acting_user_id in user_ids:
        sensitive_fields = {"role", "permissions", "is_active"}
        update_fields = updates.model_dump(exclude_unset=True).keys()
        if any(field in sensitive_fields for field in update_fields):
            raise HTTPException(status_code=400, detail="Cannot bulk update your own role, permissions, or active status")

    update_data = updates.model_dump(exclude_unset=True)
    next_role = update_data.get("role")

    if next_role and next_role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(STAFF_ROLES))}")

    next_email = cast(str | None, update_data.get("email"))
    if next_email:
        existing = first(db, User, [User.email == next_email, User.id.not_in_(user_ids)])
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    updated_users = []
    for user in staff_users:
        update_staff_user(db, user, update_data)
        updated_users.append(_serialize_staff_user(user))

    audit_log(
        db=db,
        action="STAFF_BULK_UPDATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=None,
        details={
            "user_ids": user_ids,
            "updated_fields": sorted(update_data.keys()),
            "count": len(user_ids),
        },
        status="success",
    )

    return {
        "message": f"Successfully saved {len(user_ids)} staff account(s)",
        "updated_users": updated_users,
        "updated_fields": sorted(update_data.keys()),
    }


def list_pending_bank_accounts(kind: str, db: Session, current_user: dict, limit: int = 200, offset: int = 0) -> list[dict]:
    """List bank accounts awaiting verification for a given kind (supplier|logistics_partner)."""
    require_admin_role(current_user)
    if kind not in ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(ALLOWED_BANK_ACCOUNT_KINDS)}")

    safe_limit = min(max(1, limit), 200)
    safe_offset = max(0, offset)

    if kind == "supplier":
        rows = aggregate_rows(
            db,
            [SupplierBankAccount, User.username, SupplierProfile.business_name],
            [SupplierBankAccount.verification_status == "pending"],
            joins=[(User, SupplierBankAccount.supplier_id == User.id)],
            outerjoins=[(SupplierProfile, SupplierProfile.user_id == User.id)],
            order_by=[SupplierBankAccount.created_at.asc()],
            offset=safe_offset,
            limit=safe_limit,
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
        rows = aggregate_rows(
            db,
            [LogisticsPartnerBankAccount, LogisticsPartner.name],
            [LogisticsPartnerBankAccount.verification_status == "pending"],
            joins=[(LogisticsPartner, LogisticsPartnerBankAccount.partner_id == LogisticsPartner.id)],
            order_by=[LogisticsPartnerBankAccount.created_at.asc()],
            offset=safe_offset,
            limit=safe_limit,
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


def verify_bank_account(
    kind: str,
    account_id: int,
    action: str,
    note: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """Approve or reject a supplier or logistics partner bank account."""
    require_admin_role(current_user)
    if kind not in ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(ALLOWED_BANK_ACCOUNT_KINDS)}")
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    if kind == "supplier":
        record = first(db, SupplierBankAccount, [SupplierBankAccount.id == account_id])
    else:
        record = first(db, LogisticsPartnerBankAccount, [LogisticsPartnerBankAccount.id == account_id])

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    new_status = "verified" if action == "approve" else "rejected"
    update_bank_account_verification(
        db=db,
        record=record,
        verification_status=new_status,
        verification_note=note or ("Approved." if action == "approve" else "Rejected by admin."),
        verified_at=datetime.now(timezone.utc),
        verified_by=int(current_user["id"]),
        action=action,
    )

    audit_log(
        db=db,
        user_id=int(current_user["id"]),
        username=current_user["username"],
        user_role=current_user["role"],
        action=f"BANK_ACCOUNT_{action.upper()}",
        resource_type=f"{kind}_bank_account",
        resource_id=account_id,
        details={"status": new_status, "note": note},
    )
    return {
        "ok": True,
        "id": account_id,
        "verification_status": new_status,
        "verification_note": note or ("Approved." if action == "approve" else "Rejected by admin."),
    }


def delete_bank_account_record(
    kind: str,
    account_id: int,
    current_user: dict,
    db: Session,
) -> dict:
    """Delete a supplier or logistics partner bank account record."""
    require_admin_role(current_user)
    if kind not in ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(ALLOWED_BANK_ACCOUNT_KINDS)}")

    if kind == "supplier":
        record = first(db, SupplierBankAccount, [SupplierBankAccount.id == account_id])
    else:
        record = first(db, LogisticsPartnerBankAccount, [LogisticsPartnerBankAccount.id == account_id])

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    verification_status = cast(str | None, getattr(record, "verification_status", None))
    delete_bank_account_record_service(db, record)

    audit_log(
        db=db,
        user_id=int(current_user["id"]),
        username=current_user["username"],
        user_role=current_user["role"],
        action="BANK_ACCOUNT_DELETE",
        resource_type=f"{kind}_bank_account",
        resource_id=account_id,
        details={"status": verification_status},
    )
    return {"ok": True, "id": account_id, "deleted": True}
# ── Deferred re-export bridge ─────────────────────────────────────────────────
# Imported at the BOTTOM (not the top) of this module: `services.users_write_service`
# re-exports handlers defined *in this very module*, so a top-level import would
# be self-referential and trigger an import-time circular-import failure.
from services.users_write_service import (  # noqa: E402
    _build_user_delete_blocker,
    _delete_order_records,
    _hard_delete_user_record,
    delete_bank_account_record as delete_bank_account_record_service,
    force_reset_password as force_reset_password_service,
    toggle_user_active as toggle_user_active_service,
    update_bank_account_verification,
    update_staff_user,
    update_user_role as update_user_role_service,
    create_staff_user,
)