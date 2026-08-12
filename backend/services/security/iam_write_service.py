"""Write operations for IAM / employee identity & access primitives.

Implements the previously-stubbed biometric, geo-fence and physical ID-card
handlers following the shared ``services`` convention (create/update helpers,
ORM-object OR id based updates, ``None``-skipping change application).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from utils.datetime_utils import utcnow as _utcnow
from models import EmployeeBiometric, GeoFenceLog, PhysicalIDCard
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    return isinstance(obj, Model)


def _apply_changes(record, changes):
    for field, value in (changes or {}).items():
        if value is None:
            continue
        if hasattr(record, field):
            setattr(record, field, value)
    return record


def create_employee_biometric(
    db: Session,
    *,
    employee_id: int,
    biometric_type: str = "fingerprint",
    fingerprint_hash: Optional[str] = None,
    face_encoding: Optional[bytes] = None,
    is_active: bool = True,
    **data,
) -> EmployeeBiometric:
    record = EmployeeBiometric(
        employee_id=employee_id,
        biometric_type=biometric_type,
        fingerprint_hash=fingerprint_hash,
        face_encoding=face_encoding,
        is_active=is_active,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_employee_biometric(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, EmployeeBiometric):
        record = record_or_id
    else:
        record = db.get(EmployeeBiometric, int(record_or_id))
        if record is None:
            raise ValueError(f"EmployeeBiometric {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def create_geo_fence_log(
    db: Session,
    *,
    employee_id: int,
    latitude: float,
    longitude: float,
    accuracy_meters: Optional[float] = None,
    scanned_at: Optional[datetime] = None,
    is_within_fence: Optional[bool] = None,
    **data,
) -> GeoFenceLog:
    record = GeoFenceLog(
        employee_id=employee_id,
        latitude=latitude,
        longitude=longitude,
        accuracy_meters=accuracy_meters,
        scanned_at=scanned_at or _utcnow(),
        is_within_fence=is_within_fence,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_physical_id_card(
    db: Session,
    *,
    employee_id: int,
    card_number: str,
    issued_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    is_revoked: bool = False,
    **data,
) -> PhysicalIDCard:
    record = PhysicalIDCard(
        employee_id=employee_id,
        card_number=card_number,
        issued_at=issued_at or _utcnow(),
        expires_at=expires_at,
        is_revoked=is_revoked,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_physical_id_card(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, PhysicalIDCard):
        record = record_or_id
    else:
        record = db.get(PhysicalIDCard, int(record_or_id))
        if record is None:
            raise ValueError(f"PhysicalIDCard {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record
