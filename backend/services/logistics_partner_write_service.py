"""Logistics partner write service — DB write operations for logistics partner entities."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models import (
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