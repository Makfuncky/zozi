"""
Automatic service for country_read_service - DB read operations delegated from controllers.
"""
from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from data.models import *
from data.services_write_helpers import add_and_flush, commit_only

def get_countryconfig_by_condition(db: Session, **filters) -> Optional[CountryConfig]:
    query = db.query(CountryConfig)
    for key, value in filters.items():
        query = query.filter(getattr(CountryConfig, key) == value)
    return query.first()


def get_countryconfigversion_first(db: Session, **filters) -> Optional[CountryConfigVersion]:
    query = db.query(CountryConfigVersion)
    for key, value in filters.items():
        query = query.filter(getattr(CountryConfigVersion, key) == value)
    return query.limit(1).first()


def get_countrycity_first(db: Session, **filters) -> Optional[CountryCity]:
    query = db.query(CountryCity)
    for key, value in filters.items():
        query = query.filter(getattr(CountryCity, key) == value)
    return query.limit(1).first()


def get_countryconfig_first(db: Session, **filters) -> Optional[CountryConfig]:
    query = db.query(CountryConfig)
    for key, value in filters.items():
        query = query.filter(getattr(CountryConfig, key) == value)
    return query.limit(1).first()


def list_omandeliveryzone(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[OmanDeliveryZone]:
    query = db.query(OmanDeliveryZone)
    for key, value in filters.items():
        query = query.filter(getattr(OmanDeliveryZone, key) == value)
    return query.offset(skip).limit(limit).all()


def get_suppliercountrycommission_first(db: Session, **filters) -> Optional[SupplierCountryCommission]:
    query = db.query(SupplierCountryCommission)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierCountryCommission, key) == value)
    return query.limit(1).first()


def get_countryfeatureflag_first(db: Session, **filters) -> Optional[CountryFeatureFlag]:
    query = db.query(CountryFeatureFlag)
    for key, value in filters.items():
        query = query.filter(getattr(CountryFeatureFlag, key) == value)
    return query.limit(1).first()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_countrystaffassignment_first(db: Session, **filters) -> Optional[CountryStaffAssignment]:
    query = db.query(CountryStaffAssignment)
    for key, value in filters.items():
        query = query.filter(getattr(CountryStaffAssignment, key) == value)
    return query.limit(1).first()


def list_user(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.offset(skip).limit(limit).all()


def get_countrycommunication_first(db: Session, **filters) -> Optional[CountryCommunication]:
    query = db.query(CountryCommunication)
    for key, value in filters.items():
        query = query.filter(getattr(CountryCommunication, key) == value)
    return query.limit(1).first()


def get_countrycommunication_by_id(db: Session, record_id: int) -> Optional[CountryCommunication]:
    return db.query(CountryCommunication).filter(CountryCommunication.id == record_id).first()


def get_crosscountrycustomersession_first(db: Session, **filters) -> Optional[CrossCountryCustomerSession]:
    query = db.query(CrossCountryCustomerSession)
    for key, value in filters.items():
        query = query.filter(getattr(CrossCountryCustomerSession, key) == value)
    return query.limit(1).first()


def list_countrycity(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[CountryCity]:
    query = db.query(CountryCity)
    for key, value in filters.items():
        query = query.filter(getattr(CountryCity, key) == value)
    return query.offset(skip).limit(limit).all()

def _db_countryconfig_first_0(db: Session, code: Any, normalized: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfigversion_query_1(db: Session) -> Optional[Any]:
    return db.query(CountryConfigVersion)
    """Read-only query delegated from controller."""

def _db_countrycity_count_2(db: Session, True: Any, code: Any, country: Any, country_code: Any, is_active: Any) -> Optional[Any]:
    result = db.query(CountryCity).filter( CountryCity.country_code == country.code, CountryCity.is_active == True, ).count()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_query_3(db: Session) -> Optional[Any]:
    return db.query(CountryConfig)
    """Read-only query delegated from controller."""

def _db_countryconfig_first_4(db: Session, True: Any, cc: Any, code: Any, is_active: Any, noqa: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter( CountryConfig.code == cc, CountryConfig.is_active == True,  # noqa: E712 ).first()
    return result
    """Read-only query delegated from controller."""

def _db_countrycity_query_5(db: Session) -> Optional[Any]:
    return db.query(CountryCity)
    """Read-only query delegated from controller."""

def _db_countryconfig_query_6(db: Session) -> Optional[Any]:
    result = db.query(CountryConfig)
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_7(db: Session, code: Any, normalized_code: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfigversion_query_8(db: Session, country_code: Any, normalized_code: Any) -> Optional[Any]:
    result = db.query(CountryConfigVersion).filter(CountryConfigVersion.country_code == normalized_code)
    return result
    """Read-only query delegated from controller."""

def _db_countryconfigversion_query_9(db: Session) -> Optional[Any]:
    return db.query(CountryConfigVersion)
    """Read-only query delegated from controller."""

def _db_omandeliveryzone_all_10(db: Session) -> Optional[Any]:
    result = {zone.zone_code: zone for zone in db.query(OmanDeliveryZone).all()}
    return result
    """Read-only query delegated from controller."""

def _db_suppliercountrycommission_query_11(db: Session) -> Optional[Any]:
    return for entry in db.query(SupplierCountryCommission)
    """Read-only query delegated from controller."""

def _db_countryfeatureflag_query_12(db: Session) -> Optional[Any]:
    return for flag in db.query(CountryFeatureFlag)
    """Read-only query delegated from controller."""

def _db_countryconfigversion_query_13(db: Session) -> Optional[Any]:
    return db.query(CountryConfigVersion)
    """Read-only query delegated from controller."""

def _db_countryconfigversion_query_14(db: Session) -> Optional[Any]:
    return db.query(CountryConfigVersion)
    """Read-only query delegated from controller."""

def _db_suppliercountrycommission_query_15(db: Session) -> Optional[Any]:
    return db.query(SupplierCountryCommission)
    """Read-only query delegated from controller."""

def _db_countryfeatureflag_query_16(db: Session) -> Optional[Any]:
    return db.query(CountryFeatureFlag)
    """Read-only query delegated from controller."""

def _db_omandeliveryzone_all_17(db: Session) -> Optional[Any]:
    result = db.query(OmanDeliveryZone).order_by(OmanDeliveryZone.sort_order.asc(), OmanDeliveryZone.zone_code.asc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_countrycity_query_18(db: Session, cc: Any, country_code: Any) -> Optional[Any]:
    result = db.query(CountryCity).filter(CountryCity.country_code == cc)
    return result
    """Read-only query delegated from controller."""

def _db_countrystaffassignment_first_19(db: Session, country_code: Any, upper: Any, user_id: Any) -> Optional[Any]:
    result = db.query(CountryStaffAssignment).filter( CountryStaffAssignment.user_id == user_id, CountryStaffAssignment.country_code == country_code.upper(), ).first()
    return result
    """Read-only query delegated from controller."""

def _db_countrystaffassignment_all_20(db: Session, True: Any, country_code: Any, upper: Any) -> Optional[Any]:
    result = db.query(CountryStaffAssignment).filter( CountryStaffAssignment.country_code == country_code.upper(), CountryStaffAssignment.is_active == True, ).order_by(CountryStaffAssignment.created_at.desc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_user_all_21(db: Session, id: Any, in_: Any, user_ids: Any) -> Optional[Any]:
    result = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return result
    """Read-only query delegated from controller."""

def _db_countrystaffassignment_first_22(db: Session, country_code: Any, upper: Any, user_id: Any) -> Optional[Any]:
    result = db.query(CountryStaffAssignment).filter( CountryStaffAssignment.user_id == user_id, CountryStaffAssignment.country_code == country_code.upper(), ).first()
    return result
    """Read-only query delegated from controller."""

def _db_countrycommunication_query_23(db: Session, country_code: Any, upper: Any) -> Optional[Any]:
    result = db.query(CountryCommunication).filter(CountryCommunication.country_code == country_code.upper())
    return result
    """Read-only query delegated from controller."""

def _db_countrycommunication_first_24(db: Session, comm_id: Any, id: Any) -> Optional[Any]:
    result = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_crosscountrycustomersession_all_25(db: Session, country_code: Any, target_country_code: Any, upper: Any) -> Optional[Any]:
    result = db.query(CrossCountryCustomerSession).filter( CrossCountryCustomerSession.target_country_code == country_code.upper(), ).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_26(db: Session, True: Any, code: Any, is_active: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter( CountryConfig.code == code, CountryConfig.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_27(db: Session, code: Any, normalized_code: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    return result
    """Read-only query delegated from controller."""

def _db_countrycity_all_28(db: Session, cc: Any, country_code: Any) -> Optional[Any]:
    result = db.query(CountryCity).filter(CountryCity.country_code == cc).order_by(CountryCity.sort_order.asc(), CountryCity.name.asc()).all()
    return result
    """Read-only query delegated from controller."""
