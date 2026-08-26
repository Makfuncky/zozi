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
        record = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    else:
        record = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()

    if record is None:
        raise HTTPException(status_code=404, detail="Bank account record not found.")

    verification_status = cast(str | None, getattr(record, "verification_status", None))
    db.delete(record)
    db.commit()

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
