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
from infrastructure.utils.admin_shared import VALID_USER_ROLES

from infrastructure.database.schemas import CreateStaffAccount, UpdateStaffAccount


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

        user = db.query(User).filter(User.id == uid).first()
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
        db.commit()
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

