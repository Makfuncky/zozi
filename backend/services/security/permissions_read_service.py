"""
Automatic service for permissions_read_service - DB read operations delegated from controllers.
"""

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from data.models import *
from data.services_write_helpers import add_and_flush, commit_only

def get_logisticspartner_by_condition(db: Session, **filters) -> Optional[LogisticsPartner]:
    query = db.query(LogisticsPartner)
    for key, value in filters.items():
        query = query.filter(getattr(LogisticsPartner, key) == value)
    return query.first()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_user_by_condition(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.first()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def get_userdevice_first(db: Session, **filters) -> Optional[UserDevice]:
    query = db.query(UserDevice)
    for key, value in filters.items():
        query = query.filter(getattr(UserDevice, key) == value)
    return query.limit(1).first()


def get_emailverificationtoken_first(db: Session, **filters) -> Optional[EmailVerificationToken]:
    query = db.query(EmailVerificationToken)
    for key, value in filters.items():
        query = query.filter(getattr(EmailVerificationToken, key) == value)
    return query.limit(1).first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_referralpointevent_first(db: Session, **filters) -> Optional[ReferralPointEvent]:
    query = db.query(ReferralPointEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ReferralPointEvent, key) == value)
    return query.limit(1).first()


def count_referralpointevent(db: Session, **filters) -> int:
    query = db.query(ReferralPointEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ReferralPointEvent, key) == value)
    return query.count()


def get_passwordresettoken_first(db: Session, **filters) -> Optional[PasswordResetToken]:
    query = db.query(PasswordResetToken)
    for key, value in filters.items():
        query = query.filter(getattr(PasswordResetToken, key) == value)
    return query.limit(1).first()


def get_userbrowsinghistory_first(db: Session, **filters) -> Optional[UserBrowsingHistory]:
    query = db.query(UserBrowsingHistory)
    for key, value in filters.items():
        query = query.filter(getattr(UserBrowsingHistory, key) == value)
    return query.limit(1).first()


def get_employee_by_id(db: Session, record_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == record_id).first()


def get_employeebiometric_by_id(db: Session, record_id: int) -> Optional[EmployeeBiometric]:
    return db.query(EmployeeBiometric).filter(EmployeeBiometric.id == record_id).first()


def get_office_by_id(db: Session, record_id: int) -> Optional[Office]:
    return db.query(Office).filter(Office.id == record_id).first()


def get_physicalidcard_by_id(db: Session, record_id: int) -> Optional[PhysicalIDCard]:
    return db.query(PhysicalIDCard).filter(PhysicalIDCard.id == record_id).first()

def _db_logisticspartner_first_0(db: Session, candidate: Any, code: Any) -> Optional[Any]:
    while db.query(LogisticsPartner).filter(LogisticsPartner.code == candidate).first(): suffix += 1
    """Read-only query delegated from controller."""

def _db_user_first_1(db: Session, id: Any, int: Any, subject: Any) -> Optional[Any]:
    return db.query(User).filter(User.id == int(subject)).first()
    """Read-only query delegated from controller."""

def _db_user_first_2(db: Session, str: Any, subject: Any, username: Any) -> Optional[Any]:
    return db.query(User).filter(User.username == str(subject)).first()
    """Read-only query delegated from controller."""

def _db_user_first_3(db: Session, lower: Any, referral_code: Any) -> Optional[Any]:
    result = db.query(User).filter(func.lower(User.referral_code) == candidate.lower()).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_query_4(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_userdevice_query_5(db: Session) -> Optional[Any]:
    return db.query(UserDevice)
    """Read-only query delegated from controller."""

def _db_userdevice_query_6(db: Session, fingerprint_hash: Any, fp: Any, user_id: Any) -> Optional[Any]:
    return db.query(UserDevice).filter( UserDevice.user_id == user_id, UserDevice.fingerprint_hash != fp, ).update({"is_current": False})
    """Read-only query delegated from controller."""

def _db_user_first_7(db: Session, lower: Any, username: Any) -> Optional[Any]:
    if not db.query(User).filter(func.lower(User.username) == username.lower()).first(): return username
    """Read-only query delegated from controller."""

def _db_user_first_8(db: Session, lower: Any, username: Any) -> Optional[Any]:
    if not db.query(User).filter(func.lower(User.username) == next_candidate.lower()).first(): return next_candidate
    """Read-only query delegated from controller."""

def _db_user_first_9(db: Session, email: Any, lower: Any) -> Optional[Any]:
    result = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_10(db: Session, email: Any, user: Any) -> Optional[Any]:
    if db.query(User).filter(User.email == user.email).first(): raise HTTPException(status_code=400, detail="Email already registered")
    """Read-only query delegated from controller."""

def _db_user_first_11(db: Session, user: Any, username: Any) -> Optional[Any]:
    if db.query(User).filter(User.username == user.username).first(): raise HTTPException(status_code=400, detail="Username already taken")
    """Read-only query delegated from controller."""

def _db_user_query_12(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_emailverificationtoken_query_13(db: Session) -> Optional[Any]:
    return db.query(EmailVerificationToken)
    """Read-only query delegated from controller."""

def _db_user_first_14(db: Session, ev: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == ev.user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_emailverificationtoken_query_15(db: Session, current_user: Any, id: Any, is_: Any, used: Any, user_id: Any) -> Optional[Any]:
    return db.query(EmailVerificationToken).filter( EmailVerificationToken.user_id == current_user["id"], EmailVerificationToken.used.is_(False), ).update({"used": True})
    """Read-only query delegated from controller."""

def _db_emailverificationtoken_query_16(db: Session, _user_id: Any, user: Any, user_id: Any) -> Optional[Any]:
    return db.query(EmailVerificationToken).filter( EmailVerificationToken.user_id == _user_id(user), EmailVerificationToken.used.is_(False), ).update({"used": True})
    """Read-only query delegated from controller."""

def _db_user_first_17(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_referralpointevent_query_18(db: Session) -> Optional[Any]:
    return db.query(ReferralPointEvent)
    """Read-only query delegated from controller."""

def _db_user_first_19(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_referralpointevent_query_20(db: Session, _user_id: Any, user: Any, user_id: Any) -> Optional[Any]:
    result = db.query(ReferralPointEvent).filter(ReferralPointEvent.user_id == _user_id(user))
    return result
    """Read-only query delegated from controller."""

def _db_user_first_21(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_referralpointevent_query_22(db: Session) -> Optional[Any]:
    return db.query(ReferralPointEvent)
    """Read-only query delegated from controller."""

def _db_user_first_23(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_24(db: Session, username: Any) -> Optional[Any]:
    if db.query(User).filter(User.username == username).first(): raise HTTPException(status_code=409, detail="Username already taken")
    """Read-only query delegated from controller."""

def _db_user_first_25(db: Session, email: Any) -> Optional[Any]:
    if db.query(User).filter(User.email == email).first(): raise HTTPException(status_code=409, detail="Email already in use")
    """Read-only query delegated from controller."""

def _db_user_first_26(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_27(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_28(db: Session, body: Any, email: Any) -> Optional[Any]:
    result = db.query(User).filter(User.email == body.email).first()
    return result
    """Read-only query delegated from controller."""

def _db_passwordresettoken_query_29(db: Session, id: Any, is_: Any, used: Any, user: Any, user_id: Any) -> Optional[Any]:
    return db.query(PasswordResetToken).filter( PasswordResetToken.user_id == user.id, PasswordResetToken.used.is_(False), ).update({"used": True})
    """Read-only query delegated from controller."""

def _db_passwordresettoken_query_30(db: Session) -> Optional[Any]:
    return db.query(PasswordResetToken)
    """Read-only query delegated from controller."""

def _db_user_first_31(db: Session, db_token: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == db_token.user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_32(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_userbrowsinghistory_all_33(db: Session, id: Any, user: Any, user_id: Any) -> Optional[Any]:
    result = db.query(UserBrowsingHistory).filter( UserBrowsingHistory.user_id == user.id ).order_by(UserBrowsingHistory.viewed_at.desc()).limit(20).all()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_34(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_35(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_36(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_37(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_38(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_39(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_employeebiometric_first_0(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeBiometric).filter(EmployeeBiometric.employee_id == employee_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_office_first_1(db: Session, id: Any, office_id: Any) -> Optional[Any]:
    result = db.query(Office).filter(Office.id == office_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_employee_first_2(db: Session, employee_id: Any, id: Any, token_data: Any) -> Optional[Any]:
    result = db.query(Employee).filter(Employee.id == token_data["employee_id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_physicalidcard_first_4(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(PhysicalIDCard).filter(PhysicalIDCard.employee_id == employee_id).first()
    return result
    """Read-only query delegated from controller."""
