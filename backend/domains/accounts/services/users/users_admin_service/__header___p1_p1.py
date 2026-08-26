"""Admin users controller."""
from __future__ import annotations

from datetime import datetime
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
from infrastructure.utils.admin_shared import VALID_USER_ROLES

from infrastructure.database.schemas import CreateStaffAccount, UpdateStaffAccount


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
        db.query(User)
        .filter(User.role.in_(tuple(STAFF_ROLES)))
        .order_by(User.created_at.desc())
        .limit(200)
        .all()
    )
    return [_serialize_staff_user(user) for user in staff_users]


def get_all_users(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(User).order_by(User.created_at.desc())
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
        for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(user_ids)).all()
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

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = cast(str, getattr(user, "role"))
    setattr(user, "role", role)
    db.commit()

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_active = bool(cast(Any, getattr(user, "is_active")))
    setattr(user, "is_active", 0 if current_active else 1)
    db.commit()
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

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_orders = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.shipments)).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
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
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.warning("admin delete blocked by remaining related records", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(
            status_code=409,
            detail="User has related records that must be archived or removed before deletion.",
        )
    except Exception as e:
        db.rollback()
        logger.exception("admin delete user failed", extra={"user_id": user_id, "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

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

        user = db.query(User).filter(User.id == uid).first()
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
            db.rollback()
            skipped.append(
                {
                    "id": uid,
                    "reason": "Has related records that must be archived or removed before deletion",
                }
            )

    if deleted:
        db.commit()
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
        db.rollback()

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

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent resetting another admin's password
    if cast(str, getattr(user, "role")) == "admin" and user_id != acting_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot reset another admin's password")

    setattr(user, "hashed_password", get_password_hash(new_password))
    db.commit()

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

