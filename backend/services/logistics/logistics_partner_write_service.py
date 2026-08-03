"""Logistics partner write service — DB write operations for logistics partner entities."""
import logging
from datetime import datetime, timezone
from typing import Any, Optional, cast

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

from data.models import (
    LogisticsPartner,
    LogisticsPartnerBankAccount,
    LogisticsPartnerDocument,
    LogisticsPartnerPayout,
    LogisticsPartnerServiceArea,
    Shipment,
    ShipmentEvent,
    ShipmentConfirmation,
    CityDistanceMatrix,
    LogisticsCategoryPricingRule,
    LogisticsCODRemittanceReceipt,
    LogisticsPricingProfile,
    LogisticsSettlement,
    LogisticsVehicleRule,
    Order,
    OrderLogisticsAllocation,
    Notification,
    TransactionLedger,
)


def create_logistics_partner(db: Session, **partner_data) -> LogisticsPartner:
    partner = LogisticsPartner(**partner_data)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def update_logistics_partner(db: Session, partner: LogisticsPartner, updates: dict) -> LogisticsPartner:
    for key, value in updates.items():
        setattr(partner, key, value)
    db.commit()
    db.refresh(partner)
    return partner


def delete_logistics_partner(db: Session, partner: LogisticsPartner) -> None:
    db.delete(partner)
    db.commit()


def create_logistics_partner_bank_account(db: Session, partner_id: int, **account_data) -> LogisticsPartnerBankAccount:
    account = LogisticsPartnerBankAccount(partner_id=partner_id, **account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_logistics_partner_bank_account(db: Session, account: LogisticsPartnerBankAccount, updates: dict) -> LogisticsPartnerBankAccount:
    for key, value in updates.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


def delete_logistics_partner_bank_account(db: Session, account: LogisticsPartnerBankAccount) -> None:
    db.delete(account)
    db.commit()


def create_logistics_partner_document(db: Session, partner_id: int, **doc_data) -> LogisticsPartnerDocument:
    doc = LogisticsPartnerDocument(partner_id=partner_id, **doc_data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_logistics_partner_document(db: Session, doc: LogisticsPartnerDocument, updates: dict) -> LogisticsPartnerDocument:
    for key, value in updates.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc


def delete_logistics_partner_document(db: Session, doc: LogisticsPartnerDocument) -> None:
    db.delete(doc)
    db.commit()


def create_logistics_partner_payout(db: Session, partner_id: int, **payout_data) -> LogisticsPartnerPayout:
    payout = LogisticsPartnerPayout(partner_id=partner_id, **payout_data)
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


def update_logistics_partner_payout(db: Session, payout: LogisticsPartnerPayout, updates: dict) -> LogisticsPartnerPayout:
    for key, value in updates.items():
        setattr(payout, key, value)
    db.commit()
    db.refresh(payout)
    return payout


def delete_logistics_partner_payout(db: Session, payout: LogisticsPartnerPayout) -> None:
    db.delete(payout)
    db.commit()


def create_logistics_partner_service_area(db: Session, partner_id: int, **area_data) -> LogisticsPartnerServiceArea:
    area = LogisticsPartnerServiceArea(partner_id=partner_id, **area_data)
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def update_logistics_partner_service_area(db: Session, area: LogisticsPartnerServiceArea, updates: dict) -> LogisticsPartnerServiceArea:
    for key, value in updates.items():
        setattr(area, key, value)
    db.commit()
    db.refresh(area)
    return area


def delete_logistics_partner_service_area(db: Session, area: LogisticsPartnerServiceArea) -> None:
    db.delete(area)
    db.commit()


def create_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_transaction_ledger_entry(db: Session, **ledger_data) -> TransactionLedger:
    entry = TransactionLedger(**ledger_data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_transaction_ledger(db: Session, entry: TransactionLedger, updates: dict) -> TransactionLedger:
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def create_shipment(db: Session, **shipment_data) -> Shipment:
    shipment = Shipment(**shipment_data)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def update_shipment(db: Session, shipment: Shipment, updates: dict) -> Shipment:
    for key, value in updates.items():
        setattr(shipment, key, value)
    db.commit()
    db.refresh(shipment)
    return shipment


def delete_shipment(db: Session, shipment: Shipment) -> None:
    db.delete(shipment)
    db.commit()


def create_shipment_event(db: Session, shipment_id: int, **event_data) -> ShipmentEvent:
    event = ShipmentEvent(shipment_id=shipment_id, **event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_shipment_confirmation(db: Session, **confirmation_data) -> ShipmentConfirmation:
    confirmation = ShipmentConfirmation(**confirmation_data)
    db.add(confirmation)
    db.commit()
    db.refresh(confirmation)
    return confirmation


def update_order(db: Session, order: Order, updates: dict) -> Order:
    for key, value in updates.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


def create_order_logistics_allocation(db: Session, **allocation_data) -> OrderLogisticsAllocation:
    allocation = OrderLogisticsAllocation(**allocation_data)
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def update_order_logistics_allocation(db: Session, allocation: OrderLogisticsAllocation, updates: dict) -> OrderLogisticsAllocation:
    for key, value in updates.items():
        setattr(allocation, key, value)
    db.commit()
    db.refresh(allocation)
    return allocation


def create_city_distance_matrix(db: Session, **matrix_data) -> CityDistanceMatrix:
    matrix = CityDistanceMatrix(**matrix_data)
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    return matrix


def update_city_distance_matrix(db: Session, matrix: CityDistanceMatrix, updates: dict) -> CityDistanceMatrix:
    for key, value in updates.items():
        setattr(matrix, key, value)
    db.commit()
    db.refresh(matrix)
    return matrix


def create_pricing_rule(db: Session, **rule_data) -> LogisticsCategoryPricingRule:
    rule = LogisticsCategoryPricingRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_pricing_rule(db: Session, rule: LogisticsCategoryPricingRule, updates: dict) -> LogisticsCategoryPricingRule:
    for key, value in updates.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete_pricing_rule(db: Session, rule: LogisticsCategoryPricingRule) -> None:
    db.delete(rule)
    db.commit()


def create_coding_remittance_receipt(db: Session, **receipt_data) -> LogisticsCODRemittanceReceipt:
    receipt = LogisticsCODRemittanceReceipt(**receipt_data)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def create_pricing_profile(db: Session, **profile_data) -> LogisticsPricingProfile:
    profile = LogisticsPricingProfile(**profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_pricing_profile(db: Session, profile: LogisticsPricingProfile, updates: dict) -> LogisticsPricingProfile:
    for key, value in updates.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def create_settlement(db: Session, **settlement_data) -> LogisticsSettlement:
    settlement = LogisticsSettlement(**settlement_data)
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def update_settlement(db: Session, settlement: LogisticsSettlement, updates: dict) -> LogisticsSettlement:
    for key, value in updates.items():
        setattr(settlement, key, value)
    db.commit()
    db.refresh(settlement)
    return settlement


def create_vehicle_rule(db: Session, **rule_data) -> LogisticsVehicleRule:
    rule = LogisticsVehicleRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_vehicle_rule(db: Session, rule: LogisticsVehicleRule, updates: dict) -> LogisticsVehicleRule:
    for key, value in updates.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete_vehicle_rule(db: Session, rule: LogisticsVehicleRule) -> None:
    db.delete(rule)
    db.commit()


def delete_pricing_profile(db: Session, profile: LogisticsPricingProfile) -> None:
    db.delete(profile)
    db.commit()


def delete_category_pricing_rule(db: Session, rule: LogisticsCategoryPricingRule) -> None:
    db.delete(rule)
    db.commit()


def delete_city_distance_matrix(db: Session, matrix: CityDistanceMatrix) -> None:
    db.delete(matrix)
    db.commit()


def update_notification(db: Session, notification: Notification, updates: dict) -> Notification:
    for key, value in updates.items():
        setattr(notification, key, value)
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, notification: Notification) -> None:
    db.delete(notification)
    db.commit()


# ── Composite transaction helpers ─────────────────────────────────────────────
# These encapsulate multi-entity writes that the logistics-partner controller
# used to perform inline (W1 audit: move DB writes out of controllers).


def stage_notification(db: Session, **notification_data) -> Notification:
    """Queue a Notification in the session WITHOUT committing (caller owns the transaction)."""
    notification = Notification(**notification_data)
    db.add(notification)
    return notification


def stage_shipment_event(db: Session, **event_data) -> ShipmentEvent:
    """Queue a ShipmentEvent in the session WITHOUT committing (caller owns the transaction)."""
    event = ShipmentEvent(**event_data)
    db.add(event)
    return event


def commit_session(db: Session) -> None:
    """Commit the current session (bulk flows that batch many staged writes)."""
    db.commit()


def commit_and_refresh(db: Session, *objects) -> None:
    """Commit then refresh each provided ORM object in one call."""
    db.commit()
    for obj in objects:
        db.refresh(obj)


def try_delete_logistics_partner(db: Session, partner: LogisticsPartner) -> bool:
    """Delete a partner inside a savepoint; returns False when related records block it."""
    try:
        with db.begin_nested():
            db.delete(partner)
            db.flush()
        return True
    except IntegrityError:
        return False


def stage_logistics_partner_service_area(db: Session, partner_id: int) -> LogisticsPartnerServiceArea:
    """Create an (empty) service-area object and queue it — caller sets fields, then commits once."""
    area = LogisticsPartnerServiceArea(partner_id=partner_id)
    db.add(area)
    return area


def stage_logistics_partner_pricing_profile(db: Session, partner_id: int) -> LogisticsPricingProfile:
    """Create an (empty) pricing-profile object and queue it — caller sets fields, then commits once."""
    profile = LogisticsPricingProfile(partner_id=partner_id)
    db.add(profile)
    return profile


def stage_logistics_partner_category_rule(db: Session, partner_id: int) -> LogisticsCategoryPricingRule:
    """Create an (empty) category-rule object and queue it — caller sets fields, then commits once."""
    rule = LogisticsCategoryPricingRule(partner_id=partner_id)
    db.add(rule)
    return rule


def stage_logistics_partner_vehicle_rule(db: Session, partner_id: int) -> LogisticsVehicleRule:
    """Create an (empty) vehicle-rule object and queue it — caller sets fields, then commits once."""
    rule = LogisticsVehicleRule(partner_id=partner_id)
    db.add(rule)
    return rule


def create_logistics_payout_request(
    db: Session,
    partner: LogisticsPartner,
    *,
    amount: float,
    method: str,
    notes: Optional[str],
) -> LogisticsPartnerPayout:
    """Create a logistics-partner payout with a generated transfer reference and a
    partner notification, all in one transaction."""
    from services.finance_transfer_service import build_transfer_reference

    payout = LogisticsPartnerPayout(
        partner_id=cast(int, partner.id),
        amount=round(amount, 2),
        method=method,
        notes=notes,
    )
    db.add(payout)
    db.flush()
    payout.reference_id = build_transfer_reference(
        db,
        kind="logistics_payout",
        entity_id=int(cast(int, partner.id)),
        record_id=int(cast(int, payout.id)),
    )
    partner_user_id = cast(Optional[int], getattr(partner, "user_id", None))
    if partner_user_id is not None:
        stage_notification(
            db,
            user_id=partner_user_id,
            type="payout",
            title="Payout Request Received",
            message=f"Your logistics payout request of {payout.amount:.2f} AED has been submitted.",
            link="/logistics-partner/payouts",
        )
    db.commit()
    db.refresh(payout)
    return payout


def update_logistics_payout_status(
    db: Session,
    payout: LogisticsPartnerPayout,
    *,
    status: str,
    reference_id: str,
    notes: Optional[str],
    partner_user_id: Optional[int],
) -> LogisticsPartnerPayout:
    """Update a logistics payout's status and notify the partner in one transaction."""
    setattr(payout, "status", status)
    setattr(payout, "reference_id", reference_id)
    setattr(payout, "notes", notes)
    if status in {"completed", "rejected"}:
        setattr(payout, "processed_at", _utcnow())
    if partner_user_id is not None:
        stage_notification(
            db,
            user_id=partner_user_id,
            type="payout",
            title="Payout Update",
            message=(
                f"Your logistics payout request #{payout.id} has been completed."
                if status == "completed"
                else f"Your logistics payout request #{payout.id} is now {status}."
            ),
            link="/logistics-partner/payouts",
        )
    db.commit()
    return payout


def stage_partner_transition_notifications(
    db: Session,
    shipment: Shipment,
    new_status: str,
    order: Optional[Order],
) -> None:
    """Queue partner-transition notifications (pickup/shipped/delivered) without committing."""
    if order is None:
        return
    if new_status == "picking_up":
        stage_notification(
            db,
            user_id=shipment.supplier_id,
            type="shipment_update",
            title="Pickup In Progress",
            message=f"Logistics partner is collecting Order #{shipment.order_id}.",
            link="/supplier/orders",
        )
    elif new_status == "shipped":
        stage_notification(
            db,
            user_id=order.user_id,
            type="order_update",
            title="Order Shipped",
            message=f"Order #{shipment.order_id} has been received by logistics and is now shipped.",
            link=f"/orders/{shipment.order_id}",
        )
    elif new_status == "delivered":
        stage_notification(
            db,
            user_id=order.user_id,
            type="order_update",
            title="Delivery Confirmed",
            message=f"Order #{shipment.order_id} has been delivered with signature confirmation.",
            link=f"/orders/{shipment.order_id}",
        )


def persist_shipment_status_update(
    db: Session,
    shipment: Shipment,
    *,
    new_status: str,
    event_fields: dict[str, Any],
) -> tuple[Shipment, ShipmentEvent]:
    """Persist a shipment status transition atomically: queue the event, reconcile the
    parent order (creating settlements on delivery), stage transition notifications,
    then commit and refresh both objects."""
    from utils.order_tracking import reconcile_order_status

    event = stage_shipment_event(db, **event_fields)
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
        stage_partner_transition_notifications(db, shipment, new_status, order)
    db.commit()
    db.refresh(shipment)
    db.refresh(event)
    return shipment, event


def create_shipment_confirmation_request(
    db: Session,
    *,
    confirmation_fields: dict[str, Any],
    notification_fields: dict[str, Any],
    shipment: Shipment,
) -> ShipmentConfirmation:
    """Create a shipment confirmation request plus the target-user notification atomically."""
    confirmation = ShipmentConfirmation(**confirmation_fields)
    db.add(confirmation)
    stage_notification(db, **notification_fields)
    setattr(shipment, "updated_at", _utcnow())
    db.commit()
    db.refresh(confirmation)
    return confirmation


def create_sla_breach_notifications(
    db: Session,
    *,
    partner_user_id: int,
    alerts: list[dict[str, Any]],
    existing_links: set[str],
) -> int:
    """Queue (and commit) SLA-breach notifications, skipping links that already exist."""
    created = 0
    for alert in alerts:
        link = f"/logistics-partner/shipments?shipment_id={alert['shipment_id']}"
        if link in existing_links:
            continue
        stage_notification(
            db,
            user_id=partner_user_id,
            type="order_update",
            title="SLA Breach Alert",
            message=f"Shipment #{alert['shipment_id']} is overdue by {alert['overdue_hours']} hours.",
            link=link,
        )
        created += 1
    if created:
        db.commit()
    return created