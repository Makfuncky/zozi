"""
Automatic service for logistics_read_service - DB read operations delegated from controllers.
"""

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from data.models import *
from data.services_write_helpers import add_and_flush, commit_only

def get_shipmentevent_by_id(db: Session, record_id: int) -> Optional[ShipmentEvent]:
    return db.query(ShipmentEvent).filter(ShipmentEvent.id == record_id).first()


def get_logisticspartner_by_id(db: Session, record_id: int) -> Optional[LogisticsPartner]:
    return db.query(LogisticsPartner).filter(LogisticsPartner.id == record_id).first()


def get_shippingcarrier_first(db: Session, **filters) -> Optional[ShippingCarrier]:
    query = db.query(ShippingCarrier)
    for key, value in filters.items():
        query = query.filter(getattr(ShippingCarrier, key) == value)
    return query.limit(1).first()


def get_shippingzone_first(db: Session, **filters) -> Optional[ShippingZone]:
    query = db.query(ShippingZone)
    for key, value in filters.items():
        query = query.filter(getattr(ShippingZone, key) == value)
    return query.limit(1).first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def get_order_by_id(db: Session, record_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == record_id).first()


def get_shipment_first(db: Session, **filters) -> Optional[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.limit(1).first()


def get_supplierprofile_by_id(db: Session, record_id: int) -> Optional[SupplierProfile]:
    return db.query(SupplierProfile).filter(SupplierProfile.id == record_id).first()


def get_invoice_first(db: Session, **filters) -> Optional[Invoice]:
    query = db.query(Invoice)
    for key, value in filters.items():
        query = query.filter(getattr(Invoice, key) == value)
    return query.limit(1).first()


def get_shipmentevent_first(db: Session, **filters) -> Optional[ShipmentEvent]:
    query = db.query(ShipmentEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ShipmentEvent, key) == value)
    return query.limit(1).first()


def list_shipment(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.offset(skip).limit(limit).all()


def count_shipment(db: Session, **filters) -> int:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.count()


def get_logisticspartner_by_condition(db: Session, **filters) -> Optional[LogisticsPartner]:
    query = db.query(LogisticsPartner)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartner, key) == value)
    return query.first()


def count_unknown(db: Session, **filters) -> int:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.count()


def get_logisticspartnerservicearea_first(db: Session, **filters) -> Optional[LogisticsPartnerServiceArea]:
    query = db.query(LogisticsPartnerServiceArea)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartnerServiceArea, key) == value)
    return query.limit(1).first()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_user_by_condition(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.first()


def get_logisticspartner_first(db: Session, **filters) -> Optional[LogisticsPartner]:
    query = db.query(LogisticsPartner)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartner, key) == value)
    return query.limit(1).first()


def get_logisticspricingprofile_first(db: Session, **filters) -> Optional[LogisticsPricingProfile]:
    query = db.query(LogisticsPricingProfile)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPricingProfile, key) == value)
    return query.limit(1).first()


def get_logisticscategorypricingrule_first(db: Session, **filters) -> Optional[LogisticsCategoryPricingRule]:
    query = db.query(LogisticsCategoryPricingRule)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsCategoryPricingRule, key) == value)
    return query.limit(1).first()


def get_logisticsvehiclerule_first(db: Session, **filters) -> Optional[LogisticsVehicleRule]:
    query = db.query(LogisticsVehicleRule)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsVehicleRule, key) == value)
    return query.limit(1).first()


def get_logisticspartnerservicearea_by_id(db: Session, record_id: int) -> Optional[LogisticsPartnerServiceArea]:
    return db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == record_id).first()


def get_logisticspricingprofile_by_id(db: Session, record_id: int) -> Optional[LogisticsPricingProfile]:
    return db.query(LogisticsPricingProfile).filter(LogisticsPricingProfile.id == record_id).first()


def get_logisticscategorypricingrule_by_id(db: Session, record_id: int) -> Optional[LogisticsCategoryPricingRule]:
    return db.query(LogisticsCategoryPricingRule).filter(LogisticsCategoryPricingRule.id == record_id).first()


def get_logisticsvehiclerule_by_id(db: Session, record_id: int) -> Optional[LogisticsVehicleRule]:
    return db.query(LogisticsVehicleRule).filter(LogisticsVehicleRule.id == record_id).first()


def get_shipmentconfirmation_first(db: Session, **filters) -> Optional[ShipmentConfirmation]:
    query = db.query(ShipmentConfirmation)
    for key, value in filters.items():
        query = query.filter(getattr(ShipmentConfirmation, key) == value)
    return query.limit(1).first()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()


def get_logisticspartnerpayout_first(db: Session, **filters) -> Optional[LogisticsPartnerPayout]:
    query = db.query(LogisticsPartnerPayout)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartnerPayout, key) == value)
    return query.limit(1).first()


def list_logisticspartner(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[LogisticsPartner]:
    query = db.query(LogisticsPartner)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartner, key) == value)
    return query.offset(skip).limit(limit).all()


def list_logisticspartnerpayout(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[LogisticsPartnerPayout]:
    query = db.query(LogisticsPartnerPayout)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartnerPayout, key) == value)
    return query.offset(skip).limit(limit).all()


def get_logisticspartnerpayout_by_id(db: Session, record_id: int) -> Optional[LogisticsPartnerPayout]:
    return db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id == record_id).first()


def get_shipment_by_id(db: Session, record_id: int) -> Optional[Shipment]:
    return db.query(Shipment).filter(Shipment.id == record_id).first()


def get_supplierprofile_first(db: Session, **filters) -> Optional[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.limit(1).first()


def get_logisticssettlement_first(db: Session, **filters) -> Optional[LogisticsSettlement]:
    query = db.query(LogisticsSettlement)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsSettlement, key) == value)
    return query.limit(1).first()


def get_orderlogisticsallocation_first(db: Session, **filters) -> Optional[OrderLogisticsAllocation]:
    query = db.query(OrderLogisticsAllocation)
    for key, value in filters.items():
        query = query.filter(getattr(OrderLogisticsAllocation, key) == value)
    return query.limit(1).first()


def get_logisticspartnerbankaccount_first(db: Session, **filters) -> Optional[LogisticsPartnerBankAccount]:
    query = db.query(LogisticsPartnerBankAccount)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartnerBankAccount, key) == value)
    return query.limit(1).first()


def get_logisticspartnerdocument_first(db: Session, **filters) -> Optional[LogisticsPartnerDocument]:
    query = db.query(LogisticsPartnerDocument)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartnerDocument, key) == value)
    return query.limit(1).first()


def get_logisticspartnerdocument_by_id(db: Session, record_id: int) -> Optional[LogisticsPartnerDocument]:
    return db.query(LogisticsPartnerDocument).filter(LogisticsPartnerDocument.id == record_id).first()


def get_citydistancematrix_first(db: Session, **filters) -> Optional[CityDistanceMatrix]:
    query = db.query(CityDistanceMatrix)
    for key, value in filters.items():
        query = query.filter(getattr(CityDistanceMatrix, key) == value)
    return query.limit(1).first()


def get_citydistancematrix_by_id(db: Session, record_id: int) -> Optional[CityDistanceMatrix]:
    return db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == record_id).first()

def _db_logisticspartner_first_0(db: Session, current_user: Any, get: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.get("id")).first()
    return result
    """Read-only query delegated from controller."""

def _db_shippingcarrier_all_1(db: Session, is_: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(ShippingCarrier).filter( (ShippingCarrier.supplier_id.is_(None)) | (ShippingCarrier.supplier_id == supplier_id), ShippingCarrier.is_active.is_(True), ).order_by(ShippingCarrier.supplier_id.nullsfirst(), ShippingCarrier.name).limit(100).all()
    return result
    """Read-only query delegated from controller."""

def _db_shippingcarrier_first_2(db: Session, carrier_id: Any, id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(ShippingCarrier).filter( ShippingCarrier.id == carrier_id, ShippingCarrier.supplier_id == supplier_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_shippingzone_all_3(db: Session, supplier_id: Any) -> Optional[Any]:
    result = db.query(ShippingZone).filter( ShippingZone.supplier_id == supplier_id, ).order_by(ShippingZone.name).limit(100).all()
    return result
    """Read-only query delegated from controller."""

def _db_shippingzone_first_4(db: Session, id: Any, supplier_id: Any, zone_id: Any) -> Optional[Any]:
    result = db.query(ShippingZone).filter( ShippingZone.id == zone_id, ShippingZone.supplier_id == supplier_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_shippingzone_first_5(db: Session, id: Any, supplier_id: Any, zone_id: Any) -> Optional[Any]:
    result = db.query(ShippingZone).filter( ShippingZone.id == zone_id, ShippingZone.supplier_id == supplier_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_query_6(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_shipment_first_7(db: Session, failed: Any, notin_: Any, order_id: Any, returned: Any, status: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter( Shipment.order_id == order_id, Shipment.supplier_id == supplier_id, Shipment.status.notin_(["failed", "returned"]), ).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_8(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_invoice_first_9(db: Session, invoice_type: Any, order_id: Any, sale: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Invoice).filter( Invoice.order_id == order_id, Invoice.supplier_id == supplier_id, Invoice.invoice_type == "sale", ).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_10(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_query_11(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_query_12(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipmentevent_all_13(db: Session, shipment_id: Any) -> Optional[Any]:
    result = db.query(ShipmentEvent).filter( ShipmentEvent.shipment_id == shipment_id ).order_by(ShipmentEvent.created_at.asc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_14(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_all_15(db: Session, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == shipment.order_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_16(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_all_17(db: Session, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == shipment.order_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_count_18(db: Session, in_: Any, in_transit: Any, shipped: Any, status: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter( Shipment.supplier_id == supplier_id, Shipment.status.in_(["shipped", "in_transit"]), ).count()
    return result
    """Read-only query delegated from controller."""

def _db_order_count_19(db: Session, id: Any, in_: Any, order_ids_with_items: Any) -> Optional[Any]:
    result = db.query(Order).filter( Order.id.in_(order_ids_with_items), Order.id.notin_(shipped_order_ids), Order.status.in_(["confirmed", "paid", "processing"]), ).count()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_1(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerServiceArea)
    """Read-only query delegated from controller."""

def _db_order_first_2(db: Session, id: Any, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == shipment.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_3(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_4(db: Session, email: Any, lower: Any) -> Optional[Any]:
    result = db.query(User).filter(func.lower(User.email) == raw_email.lower()).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_query_5(db: Session, id: Any, user: Any, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user.id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_6(db: Session) -> Optional[Any]:
    result = db.query(LogisticsPartnerServiceArea)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspricingprofile_query_7(db: Session) -> Optional[Any]:
    result = db.query(LogisticsPricingProfile)
    return result
    """Read-only query delegated from controller."""

def _db_logisticscategorypricingrule_query_8(db: Session) -> Optional[Any]:
    result = db.query(LogisticsCategoryPricingRule)
    return result
    """Read-only query delegated from controller."""

def _db_logisticsvehiclerule_query_9(db: Session) -> Optional[Any]:
    result = db.query(LogisticsVehicleRule)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_10(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerServiceArea)
    """Read-only query delegated from controller."""

def _db_logisticspricingprofile_query_11(db: Session) -> Optional[Any]:
    return db.query(LogisticsPricingProfile)
    """Read-only query delegated from controller."""

def _db_logisticscategorypricingrule_query_12(db: Session) -> Optional[Any]:
    return db.query(LogisticsCategoryPricingRule)
    """Read-only query delegated from controller."""

def _db_logisticsvehiclerule_query_13(db: Session) -> Optional[Any]:
    return db.query(LogisticsVehicleRule)
    """Read-only query delegated from controller."""

def _db_logisticspricingprofile_query_14(db: Session, id: Any, profile_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPricingProfile).filter(LogisticsPricingProfile.id == profile_id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticscategorypricingrule_query_15(db: Session, id: Any, rule_id: Any) -> Optional[Any]:
    result = db.query(LogisticsCategoryPricingRule).filter(LogisticsCategoryPricingRule.id == rule_id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticsvehiclerule_query_16(db: Session, id: Any, rule_id: Any) -> Optional[Any]:
    result = db.query(LogisticsVehicleRule).filter(LogisticsVehicleRule.id == rule_id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_17(db: Session, area_id: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == area_id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_first_18(db: Session, area_id: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerServiceArea).filter(LogisticsPartnerServiceArea.id == area_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspricingprofile_first_19(db: Session, id: Any, profile_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPricingProfile).filter(LogisticsPricingProfile.id == profile_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticscategorypricingrule_first_20(db: Session, id: Any, rule_id: Any) -> Optional[Any]:
    result = db.query(LogisticsCategoryPricingRule).filter(LogisticsCategoryPricingRule.id == rule_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticsvehiclerule_first_21(db: Session, id: Any, rule_id: Any) -> Optional[Any]:
    result = db.query(LogisticsVehicleRule).filter(LogisticsVehicleRule.id == rule_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_query_22(db: Session, active: Any, approved: Any, status: Any, verification_status: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter( LogisticsPartner.status == "active", LogisticsPartner.verification_status == "approved", )
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_23(db: Session, active: Any, approved: Any, id: Any, partner_id: Any, status: Any, verification_status: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter( LogisticsPartner.id == partner_id, LogisticsPartner.status == "active", LogisticsPartner.verification_status == "approved", ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_24(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerServiceArea)
    """Read-only query delegated from controller."""

def _db_shipment_query_25(db: Session) -> Optional[Any]:
    return db.query(Shipment), None
    """Read-only query delegated from controller."""

def _db_shipment_query_26(db: Session, assigned_partner_id: Any, id: Any, partner: Any) -> Optional[Any]:
    return db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id), partner
    """Read-only query delegated from controller."""

def _db_shipment_query_27(db: Session) -> Optional[Any]:
    return db.query(Shipment), None
    """Read-only query delegated from controller."""

def _db_shipment_query_28(db: Session, id: Any) -> Optional[Any]:
    return db.query(Shipment).filter(Shipment.id == -1), partner
    """Read-only query delegated from controller."""

def _db_shipment_query_29(db: Session, assigned_clause: Any, pickup_ready_clause: Any) -> Optional[Any]:
    return db.query(Shipment).filter(pickup_ready_clause | assigned_clause), partner
    """Read-only query delegated from controller."""

def _db_shipmentconfirmation_query_30(db: Session) -> Optional[Any]:
    return db.query(ShipmentConfirmation)
    """Read-only query delegated from controller."""

def _db_shipment_query_31(db: Session) -> Optional[Any]:
    return db.query(Shipment), None
    """Read-only query delegated from controller."""

def _db_shipment_query_32(db: Session, assigned_partner_id: Any, id: Any, in_: Any, partner: Any, status: Any) -> Optional[Any]:
    return db.query(Shipment).filter( Shipment.assigned_partner_id == partner.id, Shipment.status.in_((PARTNER_PICKUP_READY_STATUS, *PARTNER_VISIBLE_ASSIGNED_STATUSES)) ), partner
    """Read-only query delegated from controller."""

def _db_logisticspartnerpayout_query_33(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerPayout)
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_34(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_logisticspartner_all_35(db: Session) -> Optional[Any]:
    result = db.query(LogisticsPartner).order_by(desc(LogisticsPartner.created_at)).limit(200).all()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_query_36(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartner)
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_37(db: Session, linked_user_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == linked_user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_38(db: Session, code: Any, existing_placeholder: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter( LogisticsPartner.code == code, LogisticsPartner.id != existing_placeholder.id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_39(db: Session, code: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.code == code).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_40(db: Session, code: Any, id: Any, partner_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter( LogisticsPartner.code == code, LogisticsPartner.id != partner_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_query_41(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartner)
    """Read-only query delegated from controller."""

def _db_logisticspartnerpayout_query_42(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerPayout)
    """Read-only query delegated from controller."""

def _db_logisticspartnerpayout_all_43(db: Session) -> Optional[Any]:
    result = db.query(LogisticsPartnerPayout).order_by(desc(LogisticsPartnerPayout.created_at)).all()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerpayout_query_44(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerPayout)
    """Read-only query delegated from controller."""

def _db_logisticspartnerpayout_first_45(db: Session, id: Any, payout_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id == payout_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_46(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerServiceArea)
    """Read-only query delegated from controller."""

def _db_shipment_query_47(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_first_48(db: Session, id: Any, int: Any, shipment_id_text: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.id == int(shipment_id_text)).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_49(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_supplierprofile_query_50(db: Session) -> Optional[Any]:
    return db.query(SupplierProfile)
    """Read-only query delegated from controller."""

def _db_supplierprofile_query_51(db: Session) -> Optional[Any]:
    return db.query(SupplierProfile)
    """Read-only query delegated from controller."""

def _db_logisticssettlement_all_52(db: Session, cast: Any, id: Any, int: Any, partner_id: Any, partner_obj: Any, visible_order_ids: Any) -> list[Any]:
    result = db.query(LogisticsSettlement).filter( LogisticsSettlement.partner_id == cast(int, partner_obj.id), LogisticsSettlement.order_id.in_(visible_order_ids), ).all().all()
    return result
    """Read-only query delegated from controller."""

def _db_order_first_53(db: Session, id: Any, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == shipment.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipmentconfirmation_query_54(db: Session) -> Optional[Any]:
    return db.query(ShipmentConfirmation)
    """Read-only query delegated from controller."""

def _db_orderlogisticsallocation_query_55(db: Session, partner_id: Any, resolved_partner_id: Any) -> Optional[Any]:
    result = db.query(OrderLogisticsAllocation).filter(OrderLogisticsAllocation.partner_id == resolved_partner_id)
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_56(db: Session, true_val: Any, approval_status: Any, approved: Any, is_active: Any, noqa: Any, partner_id: Any, resolved_partner_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerServiceArea).options(selectinload(LogisticsPartnerServiceArea.partner)).filter( LogisticsPartnerServiceArea.partner_id == resolved_partner_id, LogisticsPartnerServiceArea.approval_status == "approved", LogisticsPartnerServiceArea.is_active == True, )
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerservicearea_query_57(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerServiceArea)
    """Read-only query delegated from controller."""

def _db_order_first_58(db: Session, id: Any, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == shipment.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_all_59(db: Session, id: Any, order: Any, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order.id).all()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_60(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerbankaccount_first_61(db: Session, partner_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerBankAccount).filter( LogisticsPartnerBankAccount.partner_id == partner_id ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerbankaccount_first_62(db: Session, partner_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerBankAccount).filter( LogisticsPartnerBankAccount.partner_id == partner_id ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerdocument_query_63(db: Session) -> Optional[Any]:
    return db.query(LogisticsPartnerDocument)
    """Read-only query delegated from controller."""

def _db_logisticspartnerdocument_first_64(db: Session, cast: Any, doc_id: Any, id: Any, int: Any, partner: Any, partner_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerDocument).filter( LogisticsPartnerDocument.id == doc_id, LogisticsPartnerDocument.partner_id == cast(int, partner.id), ).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerdocument_first_65(db: Session, doc_id: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerDocument).filter(LogisticsPartnerDocument.id == doc_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_citydistancematrix_query_66(db: Session) -> Optional[Any]:
    result = db.query(CityDistanceMatrix)
    return result
    """Read-only query delegated from controller."""

def _db_citydistancematrix_query_67(db: Session) -> Optional[Any]:
    return db.query(CityDistanceMatrix)
    """Read-only query delegated from controller."""

def _db_citydistancematrix_first_68(db: Session, id: Any, matrix_id: Any) -> Optional[Any]:
    result = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_citydistancematrix_first_69(db: Session, id: Any, matrix_id: Any) -> Optional[Any]:
    result = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    return result
    """Read-only query delegated from controller."""
