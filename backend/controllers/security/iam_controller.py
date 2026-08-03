"""Zero-Trust IAM Controller with QR, Biometric, and Geo-fence."""
from __future__ import annotations
import os
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timezone, date
from typing import Optional
from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models_employee_models import Employee, Office, PhysicalIDCard, DynamicQRSession, EmployeeBiometric, GeoFenceLog
from data.models import User
from utils.datetime_utils import utcnow as _utcnow
from services.write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
)



_QR_SECRET_KEY = os.getenv("EMPLOYEE_QR_SECRET_KEY", "")


def generate_physical_card(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    card_number = f"ZOZI-{secrets.token_hex(8).upper()}"
    card = PhysicalIDCard(employee_id=employee_id, card_number=card_number)
    add_and_flush(db, card)
    commit_and_refresh(db, card)
    return {"card_id": card.id, "card_number": card.card_number, "employee_id": employee_id}


def enroll_biometric(employee_id: int, biometric_type: str, data: str, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    existing = db.query(EmployeeBiometric).filter(EmployeeBiometric.employee_id == employee_id).first()
    if existing:
        existing.fingerprint_hash = data if biometric_type == "fingerprint" else existing.fingerprint_hash
        existing.face_encoding = data if biometric_type == "face" else existing.face_encoding
        existing.biometric_type = biometric_type
        existing.is_active = True
        commit_and_refresh(db, existing)
        return {"biometric_id": existing.id, "type": biometric_type, "active": True}
    bio = EmployeeBiometric(
        employee_id=employee_id,
        fingerprint_hash=data if biometric_type == "fingerprint" else None,
        face_encoding=data if biometric_type == "face" else None,
        biometric_type=biometric_type,
    )
    add_and_flush(db, bio)
    commit_and_refresh(db, bio)
    return {"biometric_id": bio.id, "type": biometric_type, "active": True}


def validate_geo_fence(latitude: float, longitude: float, office_id: int, db: Session) -> dict:
    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    if not office.latitude or not office.longitude:
        return {"valid": True, "reason": "office_has_no_geo_boundary"}
    lat1, lon1 = radians(latitude), radians(longitude)
    lat2, lon2 = radians(float(office.latitude)), radians(float(office.longitude))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    distance_km = 6371 * c
    radius = office.geo_fence_radius_meters / 1000 if office.geo_fence_radius_meters else 0.5
    within = distance_km <= radius
    return {"valid": within, "distance_km": round(distance_km, 3), "fence_radius_km": radius}


def log_geo_fence_event(employee_id: int, latitude: float, longitude: float, is_within: bool, db: Session) -> None:
    log = GeoFenceLog(employee_id=employee_id, latitude=latitude, longitude=longitude, is_within_fence=is_within)
    add_and_flush(db, log)
    commit_only(db)


def generate_qr_token(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.employment_status != "active":
        raise HTTPException(status_code=403, detail="Employee is not active")
    token_data = {
        "employee_id": emp.id,
        "user_id": emp.user_id,
        "country_code": emp.country_code,
        "nonce": secrets.token_hex(16),
        "iat": datetime.now(timezone.utc).isoformat(),
        "exp": datetime.now(timezone.utc).timestamp() + 120,
    }
    payload = json.dumps(token_data, separators=(",", ":"))
    signature = hmac.new(_QR_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    qr_token = f"{payload}.{signature}"
    return {"qr_token": qr_token, "expires_in_seconds": 120, "employee_id": emp.id, "employee_code": emp.employee_code}


def validate_qr_token(qr_token: str, db: Session) -> dict:
    try:
        parts = qr_token.rsplit(".", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid token format")
        payload_b64, signature = parts
        expected = hmac.new(_QR_SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=400, detail="Invalid token signature")
        token_data = json.loads(payload_b64)
        exp = token_data.get("exp", 0)
        if datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(status_code=400, detail="Token expired")
        emp = db.query(Employee).filter(Employee.id == token_data["employee_id"]).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        if emp.employment_status != "active":
            raise HTTPException(status_code=403, detail="Employee is not active")
        user = db.query(User).filter(User.id == emp.user_id).first() if emp.user_id else None
        return {
            "valid": True,
            "employee": {"id": emp.id, "employee_code": emp.employee_code, "department": emp.department, "position": emp.position, "country_code": emp.country_code},
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name} if user else None,
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid token payload")


def revoke_physical_card(employee_id: int, reason: str, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    card = db.query(PhysicalIDCard).filter(PhysicalIDCard.employee_id == employee_id).first()
    if card:
        card.is_revoked = True
        card.revoked_at = _utcnow()
        commit_only(db)
    return {"status": "revoked", "employee_id": employee_id, "reason": reason}
