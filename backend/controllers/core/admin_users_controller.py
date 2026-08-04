"""Admin users controller."""
from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Shipment, User, OrderLogisticsAllocation, Invoice, TransactionLedger, SupplierSettlement, CommissionLedgerEntry, BadgeBillingRecord, AuditLog, ReferralPointEvent, ChatbotQueryEvent, CampaignRecipient, EmailTemplate, EmailCampaign, ShippingCarrier, ShipmentEvent, Banner, SupplierDocument, ProductVerification, LogisticsPartner, LogisticsPartnerDocument, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsCategoryPricingRule, LogisticsVehicleRule, PromotionEngineConfig, PromotionOrderTier, PromotionLedgerEntry, PaymentGatewayConnection, PaymentProviderConfig, EmailProviderConfig, LogisticsCODRemittanceReceipt, BankTransaction, VATRemittance, SupplierBankAccount, LogisticsPartnerBankAccount, FinanceBankAccount, RolePermissionSetting, TicketReply, SupportTicket, CommissionAgreement, ProductCommissionOverride, CommissionGlobalConfig, CommissionCategoryRate, CommissionBadgeTier, Wishlist, Address, Review, Notification, CouponUsage, PasswordResetToken, EmailVerificationToken, ReturnRequest, Payout, CartItem, PushNotificationToken, RevokedToken, ShippingZone, SupplierProfile, Order, OrderItem
from utils.auth import get_password_hash, require_permission
from utils.audit import audit_log, AuditAction
from utils.constants import STAFF_ROLES, _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE
from utils.staff_permissions import default_permissions_for_role, sanitize_staff_permissions

from data.schemas import CreateStaffAccount, UpdateStaffAccount

from data.services_write_helpers import add_and_flush, commit_and_refresh, commit_only, delete_only, rollback_only
from services.core.admin_operations_service import get_user_by_id

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
    staff_users = (
        _db_user_query_0(db)
        .filter(User.role.in_(tuple(STAFF_ROLES)))
        .order_by(User.created_at.desc())
        .limit(200)
        .all()
    )
    return [_serialize_staff_user(user) for user in staff_users]


def get_all_users(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = _db_user_query_1(db)
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    users = query.all()
    if not users:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    user_ids = [cast(int, getattr(user, "id")) for user in users]
    profiles = {
        cast(int, getattr(profile, "user_id")): profile
        _db_supplierprofile_all_2(db, in_, user_id, user_ids)
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

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = cast(str, getattr(user, "role"))
    setattr(user, "role", role)
    commit_only(db)

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
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_active = bool(cast(Any, getattr(user, "is_active")))
    setattr(user, "is_active", 0 if current_active else 1)
    commit_only(db)
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


# Protected demo accounts that cannot be deleted
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
    (SupplierDocument, SupplierDocument.reviewed_by, "reviewed_by"),
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


def delete_user_admin(user_id: int, acting_user: dict, db: Session, delete_orders: bool = False) -> dict:
    """Hard-delete a user and their non-order data. Blocked if user has orders."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_orders = _db_order_all_3(db, user_id)
    blocker = _build_user_delete_blocker(
        user,
        acting_user,
        db,
        delete_orders=delete_orders,
        order_count=len(user_orders),
    )
    if blocker is not None:
        raise HTTPException(status_code=blocker[0], detail=blocker[1])

    deleted_orders: list[dict] = []
    if delete_orders:
        for order in user_orders:
            deleted_orders.append(_delete_order_records(order, db))

    username = cast(str, getattr(user, "username"))
    email = cast(str, getattr(user, "email"))

    try:
        _hard_delete_user_record(user, db)
        commit_only(db)
    except IntegrityError as e:
        rollback_only(db)
        logger.warning("admin delete blocked by remaining related records", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(
            status_code=409,
            detail="User has related records that must be archived or removed before deletion.",
        )
    except Exception as e:
        rollback_only(db)
        logger.exception("admin delete user failed", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to delete user: " + str(e))

    audit_log(
        db=db,
        action=AuditAction.USER_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={
            "deleted_username": username,
            "deleted_email": email,
            "deleted_order_count": len(deleted_orders),
            "deleted_orders": deleted_orders,
        },
        status="success",
    )
    return {"message": f"User '{username}' deleted successfully"}


def bulk_delete_users_admin(user_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk hard-delete multiple users. Admin-only. Skips protected/order-holding accounts."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 users at once")

    deleted: List[dict] = []
    skipped: List[dict] = []

    for uid in user_ids:
        if uid == acting_user["id"]:
            skipped.append({"id": uid, "reason": "Cannot delete own account"})
            continue

        user = get_user_by_id(db, uid)
        if not user:
            skipped.append({"id": uid, "reason": "Not found"})
            continue

        blocker = _build_user_delete_blocker(user, acting_user, db, delete_orders=False)
        if blocker is not None:
            skipped.append({"id": uid, "reason": blocker[1]})
            continue

        username = cast(str, getattr(user, "username"))
        try:
            with db.begin_nested():
                _hard_delete_user_record(user, db)
            deleted.append({"id": uid, "username": username})
        except IntegrityError:
            rollback_only(db)
            skipped.append(
                {
                    "id": uid,
                    "reason": "Has related records that must be archived or removed before deletion",
                }
            )

    if deleted:
        commit_only(db)
        audit_log(
            db=db,
            action=AuditAction.USER_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "deleted_users": deleted},
            status="success",
        )
    else:
        rollback_only(db)

    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


def force_reset_password_admin(user_id: int, new_password: str, acting_user: dict, db: Session) -> dict:
    """Force-set any user's password without requiring the old one (admin only)."""
    if acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can force-reset passwords")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent resetting another admin's password
    if cast(str, getattr(user, "role")) == "admin" and user_id != acting_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot reset another admin's password")

    setattr(user, "hashed_password", get_password_hash(new_password))
    commit_only(db)

    audit_log(
        db=db,
        action=AuditAction.PASSWORD_FORCE_RESET,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"target_username": cast(str, getattr(user, "username"))},
        status="success",
    )
    return {"message": f"Password reset for user '{cast(str, getattr(user, 'username'))}'"}


# â”€â”€ Bulk Order Operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

        user = get_user_by_id(db, uid)
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

        setattr(user, "role", normalized_role)
        updated.append(
            {
                "id": uid,
                "username": getattr(user, "username", f"user-{uid}"),
                "old_role": old_role,
                "new_role": normalized_role,
            }
        )

    if updated:
        commit_only(db)
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


# â”€â”€ Bulk User Toggle Active â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        user = get_user_by_id(db, uid)
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
        commit_only(db)
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

    _db_user_first_4(db, email, payload)

    _db_user_first_5(db, payload, username)


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
    add_and_flush(db, new_user)
    commit_and_refresh(db, new_user)

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

    user = _db_user_first_6(db, id, in_, role, tuple, user_id)
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
        existing = _db_user_first_7(db, email, id, next_email, user_id)
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

    commit_and_refresh(db, user)

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
    staff_user = _db_user_first_8(db, id, in_, role, tuple, user_id)
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
        _db_user_query_9(db)
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
        existing = _db_user_first_10(db, email, id, next_email, not_in_, user_ids)
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

    commit_only(db)

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
        "message": "Successfully updated " + str(len(user_ids)) + " staff account(s)",
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


def verify_bank_account(
    kind: str,
    account_id: int,
    action: str,
    note: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """Approve or reject a supplier or logistics partner bank account."""
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    if kind == "supplier":
        record = _db_supplierbankaccount_first_11(db, account_id, id)
    else:
        record = _db_logisticspartnerbankaccount_first_12(db, account_id, id)

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    new_status = "verified" if action == "approve" else "rejected"
    setattr(record, "verification_status", new_status)
    setattr(record, "verification_note", note or ("Approved." if action == "approve" else "Rejected by admin."))
    if action == "reject":
        setattr(record, "provider", None)
        setattr(record, "provider_recipient_id", None)
        setattr(record, "provider_status", None)
        setattr(record, "provider_last_synced_at", None)
    setattr(record, "verified_at", datetime.now(timezone.utc))
    setattr(record, "verified_by", int(current_user["id"]))
    commit_only(db)

    audit_log(
        db,
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
    _require_admin(current_user)
    if kind not in _ALLOWED_BANK_ACCOUNT_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_ALLOWED_BANK_ACCOUNT_KINDS)}")

    if kind == "supplier":
        record = _db_supplierbankaccount_first_13(db, account_id, id)
    else:
        record = _db_logisticspartnerbankaccount_first_14(db, account_id, id)

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    verification_status = cast(str | None, getattr(record, "verification_status", None))
    delete_only(db, record)
    commit_only(db)

    audit_log(
        db,
        user_id=int(current_user["id"]),
        username=current_user["username"],
        user_role=current_user["role"],
        action="BANK_ACCOUNT_DELETE",
        resource_type=f"{kind}_bank_account",
        resource_id=account_id,
        details={"status": verification_status},
    )
    return {"ok": True, "id": account_id, "deleted": True}

