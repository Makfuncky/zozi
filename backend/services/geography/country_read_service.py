"""Country read service.

Read-only data access for country configuration, cities, communications,
feature flags, staff assignments, delivery zones, config versions and
cross-country sessions. Functions are intentionally thin query helpers so the
country controller stays free of raw SQLAlchemy.

NOTE: this module was missing from the codebase; the symbols below were
reverse-engineered from the controller's import list and call sites so the
``controllers.country.country_controller`` (and the routers that pull it in)
import cleanly.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    CountryCommunication,
    CountryConfig,
    CountryConfigVersion,
    CountryFeatureFlag,
    CountryStaffAssignment,
    CrossCountryCustomerSession,
    OmanDeliveryZone,
    SupplierCountryCommission,
    User,
)
import structlog
logger = structlog.get_logger(__name__)


def get_country_by_code(db: Session, code: str) -> Optional[CountryConfig]:
    return db.query(CountryConfig).filter(CountryConfig.code == code).first()


def get_active_country_by_code(db: Session, code: str) -> Optional[CountryConfig]:
    return (
        db.query(CountryConfig)
        .filter(CountryConfig.code == code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )


def list_active_countries(db: Session) -> List[CountryConfig]:
    return (
        db.query(CountryConfig)
        .filter(CountryConfig.is_active == True)  # noqa: E712
        .order_by(CountryConfig.code)
        .all()
    )


def list_country_configs(db: Session, assigned=None) -> List[CountryConfig]:
    q = db.query(CountryConfig)
    if assigned:
        q = q.filter(CountryConfig.is_active == True)  # noqa: E712
    return q.order_by(CountryConfig.code).all()


def list_active_cities_for_country(db: Session, country_code: str) -> List[CountryCity]:
    return (
        db.query(CountryCity)
        .filter(CountryCity.country_code == country_code, CountryCity.is_active == True)  # noqa: E712
        .order_by(CountryCity.sort_order, CountryCity.name)
        .all()
    )


def count_active_cities_for_country(db: Session, country_code: str) -> int:
    return (
        db.query(CountryCity)
        .filter(CountryCity.country_code == country_code, CountryCity.is_active == True)  # noqa: E712
        .count()
    )


def list_cities_for_country_ordered(
    db: Session, country_code: str, include_inactive: bool = False
) -> List[CountryCity]:
    q = db.query(CountryCity).filter(CountryCity.country_code == country_code)
    if not include_inactive:
        q = q.filter(CountryCity.is_active == True)  # noqa: E712
    return q.order_by(CountryCity.sort_order, CountryCity.name).all()


def search_cities_for_country(
    db: Session,
    country_code: str,
    include_inactive: bool = False,
    query: Optional[str] = None,
    limit: int = 50,
) -> List[CountryCity]:
    q = db.query(CountryCity).filter(CountryCity.country_code == country_code)
    if not include_inactive:
        q = q.filter(CountryCity.is_active == True)  # noqa: E712
    if query:
        q = q.filter(CountryCity.name.ilike(f"%{query}%"))
    return q.order_by(CountryCity.sort_order, CountryCity.name).limit(limit).all()


def get_communication_by_id(db: Session, comm_id: int) -> Optional[CountryCommunication]:
    return db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()


def list_country_communications(
    db: Session, country_code: str, category: Optional[str] = None
) -> List[CountryCommunication]:
    q = db.query(CountryCommunication).filter(CountryCommunication.country_code == country_code)
    if category:
        q = q.filter(CountryCommunication.category == category)
    return q.order_by(CountryCommunication.created_at.desc()).all()


def list_country_versions(
    db: Session, country_code: str, config_type: Optional[str] = None
) -> List[CountryConfigVersion]:
    q = db.query(CountryConfigVersion).filter(CountryConfigVersion.country_code == country_code)
    if config_type:
        q = q.filter(CountryConfigVersion.config_type == config_type)
    return q.order_by(CountryConfigVersion.version.desc()).all()


def get_country_version(
    db: Session, version_id: int, country_code: str
) -> Optional[CountryConfigVersion]:
    return (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == country_code)
        .first()
    )


def get_latest_version_number(db: Session, country_code: str, config_type: str) -> int:
    res = (
        db.query(func.max(CountryConfigVersion.version))
        .filter(
            CountryConfigVersion.country_code == country_code,
            CountryConfigVersion.config_type == config_type,
        )
        .scalar()
    )
    return res or 0


def get_published_country_version(
    db: Session, version_id: int, country_code: str
) -> Optional[CountryConfigVersion]:
    return (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == country_code,
            CountryConfigVersion.status == "published",
        )
        .first()
    )


def list_country_feature_flags(db: Session, country_code: str) -> List[CountryFeatureFlag]:
    return (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == country_code)
        .order_by(CountryFeatureFlag.feature_key)
        .all()
    )


def list_country_feature_flags_ordered(db: Session, country_code: str) -> List[CountryFeatureFlag]:
    return list_country_feature_flags(db, country_code)


def get_country_staff_assignment(
    db: Session, user_id: int, country_code: str
) -> Optional[CountryStaffAssignment]:
    return (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == country_code,
        )
        .first()
    )


def list_country_staff_assignments(db: Session, country_code: str) -> List[CountryStaffAssignment]:
    return (
        db.query(CountryStaffAssignment)
        .filter(CountryStaffAssignment.country_code == country_code)
        .all()
    )


def list_all_oman_delivery_zones(db: Session) -> List[OmanDeliveryZone]:
    return (
        db.query(OmanDeliveryZone)
        .filter(OmanDeliveryZone.is_active == True)  # noqa: E712
        .order_by(OmanDeliveryZone.sort_order)
        .all()
    )


def list_oman_delivery_zones_ordered(db: Session) -> List[OmanDeliveryZone]:
    return list_all_oman_delivery_zones(db)


def list_country_commissions(db: Session, country_code: str) -> List[SupplierCountryCommission]:
    return (
        db.query(SupplierCountryCommission)
        .filter(SupplierCountryCommission.country_code == country_code)
        .order_by(SupplierCountryCommission.id)
        .all()
    )


def list_country_commissions_ordered(db: Session, country_code: str) -> List[SupplierCountryCommission]:
    return list_country_commissions(db, country_code)


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_users_by_ids(db: Session, user_ids: List[int]) -> List[User]:
    if not user_ids:
        return []
    return db.query(User).filter(User.id.in_(user_ids)).all()


def list_recent_cross_country_sessions(
    db: Session, country_code: str
) -> List[CrossCountryCustomerSession]:
    return (
        db.query(CrossCountryCustomerSession)
        .filter(CrossCountryCustomerSession.target_country_code == country_code)
        .order_by(CrossCountryCustomerSession.created_at.desc())
        .limit(50)
        .all()
    )
