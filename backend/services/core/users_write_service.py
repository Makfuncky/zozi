"""Users write service — DB write operations for User and staff account entities."""

from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from models import (
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


def create_staff_user(db: Session, **user_data) -> User:
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_staff_user(db: Session, user: User, updates: dict) -> User:
    for key, value in updates.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def update_user_role(db: Session, user: User, role: str) -> None:
    user.role = role
    db.commit()


def toggle_user_active(db: Session, user: User) -> None:
    user.is_active = 0 if user.is_active else 1
    db.commit()


def force_reset_password(db: Session, user: User, hashed_password: str) -> None:
    user.hashed_password = hashed_password
    db.commit()


def update_bank_account_verification(
    db: Session,
    record,
    verification_status: str,
    verification_note: str,
    verified_at: datetime,
    verified_by: int,
    action: str,
) -> None:
    record.verification_status = verification_status
    record.verification_note = verification_note
    if action == "reject":
        record.provider = None
        record.provider_recipient_id = None
        record.provider_status = None
        record.provider_last_synced_at = None
    record.verified_at = verified_at
    record.verified_by = verified_by
    db.commit()


def delete_bank_account_record(db: Session, record) -> None:
    db.delete(record)
    db.commit()


_DELETE_BLOCKING_SUPPLIER_MODELS = [
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

_NULLABLE_USER_REFERENCE_UPDATES = [
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

_DELETABLE_USER_OWNED_MODELS = [
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

_PROTECTED_EMAILS = {"admin@zozi.com"}


def _delete_order_records(order: Order, db: Session) -> dict:
    order_id = order.id
    items = order.items
    shipments = order.shipments

    for item in items:
        db.delete(item)

    for shipment in shipments:
        for event in shipment.events:
            db.delete(event)
        db.delete(shipment)

    db.delete(order)
    db.commit()

    return {"order_id": order_id, "deleted_items": len(items or []), "deleted_shipments": len(shipments or [])}


def _nullify_user_references(db: Session, user_id: int) -> None:
    for model, fk_column, _ in _NULLABLE_USER_REFERENCE_UPDATES:
        db.query(model).filter(fk_column == user_id).update({fk_column: None})


def _delete_user_owned_records(db: Session, user_id: int) -> None:
    for model, fk_column in _DELETABLE_USER_OWNED_MODELS:
        for record in db.query(model).filter(fk_column == user_id).all():
            db.delete(record)


def _hard_delete_user_record(user: User, db: Session) -> None:
    _nullify_user_references(db, user.id)
    _delete_user_owned_records(db, user.id)
    db.delete(user)
    db.commit()


def _build_user_delete_blocker(
    user: User,
    acting_user: dict,
    db: Session,
    delete_orders: bool = False,
    order_count: int = 0,
) -> tuple[int, str] | None:
    user_orders = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product),
        selectinload(Order.shipments)
    ).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()

    if user_orders and not delete_orders:
        return (409, f"User has {len(user_orders)} order(s). Set delete_orders=true to delete orders along with user.")

    if user.id == acting_user.get("id"):
        return (403, "Cannot delete your own account")

    if str(user.email) in _PROTECTED_EMAILS:
        return (403, "Cannot delete protected admin account")

    return None


def create_chatbot_query_event(
    db: Session,
    *,
    session_id: str,
    event_type: str,
    user_id: int | None = None,
    message: str | None = None,
    normalized_query: str | None = None,
    intent: str | None = None,
    filters_json: str | None = None,
    result_count: int = 0,
    product_ids_json: str | None = None,
    clicked_product_id: int | None = None,
) -> ChatbotQueryEvent:
    event = ChatbotQueryEvent(
        user_id=user_id,
        session_id=session_id,
        event_type=event_type,
        message=message,
        normalized_query=normalized_query,
        intent=intent,
        filters_json=filters_json,
        result_count=max(result_count, 0),
        product_ids_json=product_ids_json,
        clicked_product_id=clicked_product_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_user_browsing_history(
    db: Session,
    user: User,
    product_id: int,
    max_items: int = 50,
) -> None:
    import json
    from typing import Any, cast

    history: list[int] = []
    browsing_json = cast(str | None, getattr(user, "browsing_history_json", None))
    if browsing_json:
        try:
            loaded = json.loads(browsing_json)
            if isinstance(loaded, list):
                history = [int(item) for item in loaded if str(item).isdigit()]
        except (TypeError, ValueError, json.JSONDecodeError):
            history = []

    history = [pid for pid in history if pid != product_id]
    history.insert(0, product_id)
    history = history[:max_items]
    setattr(user, "browsing_history_json", json.dumps(history))
    db.commit()