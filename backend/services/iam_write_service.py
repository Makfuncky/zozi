"""IAM write service — DB write operations for IAM entities."""
from datetime import datetime

from sqlalchemy.orm import Session

from models.employee_models import (
    EmployeeBiometric,
    GeoFenceLog,
    PhysicalIDCard,
)
from utils.datetime_utils import utcnow as _utcnow


def create_physical_id_card(
    db: Session, employee_id: int, card_number: str
) -> PhysicalIDCard:
    card = PhysicalIDCard(employee_id=employee_id, card_number=card_number)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_physical_id_card(
    db: Session, card: PhysicalIDCard, is_revoked: bool = True, reason: str = None
) -> PhysicalIDCard:
    card.is_revoked = is_revoked
    card.revoked_at = _utcnow() if is_revoked else None
    db.commit()
    db.refresh(card)
    return card


def create_employee_biometric(
    db: Session,
    employee_id: int,
    biometric_type: str,
    fingerprint_hash: str = None,
    face_encoding: str = None,
) -> EmployeeBiometric:
    bio = EmployeeBiometric(
        employee_id=employee_id,
        fingerprint_hash=fingerprint_hash,
        face_encoding=face_encoding,
        biometric_type=biometric_type,
    )
    db.add(bio)
    db.commit()
    db.refresh(bio)
    return bio


def update_employee_biometric(
    db: Session,
    biometric: EmployeeBiometric,
    biometric_type: str = None,
    fingerprint_hash: str = None,
    face_encoding: str = None,
    is_active: bool = True,
) -> EmployeeBiometric:
    if fingerprint_hash is not None:
        biometric.fingerprint_hash = fingerprint_hash
    if face_encoding is not None:
        biometric.face_encoding = face_encoding
    if biometric_type is not None:
        biometric.biometric_type = biometric_type
    biometric.is_active = is_active
    db.commit()
    db.refresh(biometric)
    return biometric


def create_geo_fence_log(
    db: Session,
    employee_id: int,
    latitude: float,
    longitude: float,
    is_within_fence: bool = False,
    accuracy_meters: int = None,
    country_code: str = None,
) -> GeoFenceLog:
    log = GeoFenceLog(
        employee_id=employee_id,
        latitude=latitude,
        longitude=longitude,
        is_within_fence=is_within_fence,
        accuracy_meters=accuracy_meters,
        country_code=country_code,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log