"""IAM Router - Zero-Trust Identity, Security & Access."""
from __future__ import annotations


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from rbac import enroll_biometric
from rbac import generate_physical_card
from rbac import generate_qr_token
from rbac import log_geo_fence_event
from rbac import revoke_physical_card
from rbac import validate_geo_fence
from rbac import validate_qr_token
from infrastructure.database.database import get_db

router = APIRouter()


@router.post("/{employee_id}/card")
def create_card(employee_id: int, db: Session = Depends(get_db)):
    return generate_physical_card(employee_id, db)


@router.post("/{employee_id}/biometric")
def enroll_bio(employee_id: int, biometric_type: str = Query(...), data: str = Query(...), db: Session = Depends(get_db)):
    return enroll_biometric(employee_id, biometric_type, data, db)


@router.post("/geo/validate")
def validate_geo(latitude: float = Query(...), longitude: float = Query(...), office_id: int = Query(...), db: Session = Depends(get_db)):
    return validate_geo_fence(latitude, longitude, office_id, db)


@router.post("/{employee_id}/geo-log")
def log_geo(employee_id: int, latitude: float = Query(...), longitude: float = Query(...), is_within: bool = Query(...), db: Session = Depends(get_db)):
    log_geo_fence_event(employee_id, latitude, longitude, is_within, db)
    return {"status": "logged"}


@router.post("/{employee_id}/qr-token")
def get_qr(employee_id: int, db: Session = Depends(get_db)):
    return generate_qr_token(employee_id, db)


@router.post("/qr-login")
def qr_login(qr_token: str = Query(...), db: Session = Depends(get_db)):
    return validate_qr_token(qr_token, db)


@router.post("/{employee_id}/revoke")
def revoke_card(employee_id: int, reason: str = Query(...), db: Session = Depends(get_db)):
    return revoke_physical_card(employee_id, reason, db)
