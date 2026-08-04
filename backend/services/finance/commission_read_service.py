"""Service methods for commission read operations."""
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from data.models import CommissionRecord


def get_all_commission_records(db: Session, skip: int = 0, limit: int = 20) -> list[CommissionRecord]:
    """Get all commission records with pagination."""
    return (
        db.query(CommissionRecord)
        .order_by(CommissionRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_commission_record_by_id(db: Session, record_id: int) -> CommissionRecord | None:
    """Get a commission record by ID."""
    return db.query(CommissionRecord).filter(CommissionRecord.id == record_id).first()


def get_commission_summary(db: Session) -> list[tuple]:
    """Get commission summary grouped by country."""
    return (
        db.query(
            CommissionRecord.country_code,
            sqlfunc.sum(CommissionRecord.amount),
        )
        .group_by(CommissionRecord.country_code)
        .all()
    )


def search_commission_records(
    db: Session,
    agent_id: int | None = None,
    min_amount: float | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[CommissionRecord]:
    """Search commission records with filters."""
    q = db.query(CommissionRecord)
    if agent_id:
        q = q.filter(CommissionRecord.agent_id == agent_id)
    if min_amount:
        q = q.filter(CommissionRecord.amount >= min_amount)
    return q.order_by(CommissionRecord.created_at.desc()).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, record_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == record_id).first()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_commissionagreement_first(db: Session, **filters) -> Optional[CommissionAgreement]:
    query = db.query(CommissionAgreement)
    for key, value in filters.items():
        query = query.filter(getattr(CommissionAgreement, key) == value)
    return query.limit(1).first()


def get_productcommissionoverride_first(db: Session, **filters) -> Optional[ProductCommissionOverride]:
    query = db.query(ProductCommissionOverride)
    for key, value in filters.items():
        query = query.filter(getattr(ProductCommissionOverride, key) == value)
    return query.limit(1).first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def get_commissioncategoryrate_first(db: Session, **filters) -> Optional[CommissionCategoryRate]:
    query = db.query(CommissionCategoryRate)
    for key, value in filters.items():
        query = query.filter(getattr(CommissionCategoryRate, key) == value)
    return query.limit(1).first()


def get_commissionbadgetier_first(db: Session, **filters) -> Optional[CommissionBadgeTier]:
    query = db.query(CommissionBadgeTier)
    for key, value in filters.items():
        query = query.filter(getattr(CommissionBadgeTier, key) == value)
    return query.limit(1).first()


def get_commissionledgerentry_first(db: Session, **filters) -> Optional[CommissionLedgerEntry]:
    query = db.query(CommissionLedgerEntry)
    for key, value in filters.items():
        query = query.filter(getattr(CommissionLedgerEntry, key) == value)
    return query.limit(1).first()


def get_commissionledgerentry_by_id(db: Session, record_id: int) -> Optional[CommissionLedgerEntry]:
    return db.query(CommissionLedgerEntry).filter(CommissionLedgerEntry.id == record_id).first()

def _db_commissionagreement_query_0(db: Session) -> Optional[Any]:
    return db.query(CommissionAgreement)
    """Read-only query delegated from controller."""

def _db_commissionagreement_query_1(db: Session) -> Optional[Any]:
    return db.query(CommissionAgreement)
    """Read-only query delegated from controller."""

def _db_user_first_2(db: Session, id: Any, role: Any, supplier: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == supplier_id, User.role == "supplier").first()
    return result
    """Read-only query delegated from controller."""

def _db_commissionagreement_query_3(db: Session) -> Optional[Any]:
    return db.query(CommissionAgreement)
    """Read-only query delegated from controller."""

def _db_commissionagreement_query_4(db: Session) -> Optional[Any]:
    return db.query(CommissionAgreement)
    """Read-only query delegated from controller."""

def _db_productcommissionoverride_query_5(db: Session) -> Optional[Any]:
    return db.query(ProductCommissionOverride)
    """Read-only query delegated from controller."""

def _db_productcommissionoverride_query_6(db: Session) -> Optional[Any]:
    return db.query(ProductCommissionOverride)
    """Read-only query delegated from controller."""

def _db_productcommissionoverride_query_7(db: Session) -> Optional[Any]:
    return db.query(ProductCommissionOverride)
    """Read-only query delegated from controller."""

def _db_user_query_8(db: Session, true_val: Any, is_active: Any, role: Any, supplier: Any) -> Optional[Any]:
    result = db.query(User).filter(User.role == "supplier", User.is_active == True)  # noqa: E712
    return result
    """Read-only query delegated from controller."""

def _db_commissionagreement_query_9(db: Session) -> Optional[Any]:
    return db.query(CommissionAgreement)
    """Read-only query delegated from controller."""

def _db_commissioncategoryrate_query_10(db: Session) -> Optional[Any]:
    result = db.query(CommissionCategoryRate)
    return result
    """Read-only query delegated from controller."""

def _db_commissioncategoryrate_query_11(db: Session) -> Optional[Any]:
    result = db.query(CommissionCategoryRate)
    return result
    """Read-only query delegated from controller."""

def _db_commissioncategoryrate_first_12(db: Session, category_slug: Any) -> Optional[Any]:
    result = db.query(CommissionCategoryRate).filter( CommissionCategoryRate.category_slug == category_slug ).first()
    return result
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_13(db: Session) -> Optional[Any]:
    result = db.query(CommissionBadgeTier)
    return result
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_14(db: Session) -> Optional[Any]:
    result = db.query(CommissionBadgeTier)
    return result
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_first_15(db: Session, badge_level: Any) -> Optional[Any]:
    result = db.query(CommissionBadgeTier).filter( CommissionBadgeTier.badge_level == badge_level ).first()
    return result
    """Read-only query delegated from controller."""

def _db_commissionledgerentry_query_16(db: Session) -> Optional[Any]:
    result = db.query(CommissionLedgerEntry)
    return result
    """Read-only query delegated from controller."""

def _db_commissionledgerentry_first_17(db: Session, id: Any, ledger_id: Any) -> Optional[Any]:
    result = db.query(CommissionLedgerEntry).filter(CommissionLedgerEntry.id == ledger_id).first()
    return result
    """Read-only query delegated from controller."""
