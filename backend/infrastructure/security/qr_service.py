from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from domains.hr import ports as hr_ports
from domains.governance import ports as governance_ports
from infrastructure.utils.config import settings


QR_TOKEN_EXPIRY_SECONDS = 60
QR_SECRET_KEY = settings.secret_key

if not QR_SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY is not configured; using ephemeral key. QR tokens will not persist across restarts."
    )
    QR_SECRET_KEY = secrets.token_hex(32)


def generate_qr_token(employee_id: int, db: Session) -> dict:
    Employee = hr_ports.Employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")

    User = getattr(governance_ports, "User")
    user = db.query(User).filter(User.id == emp.user_id).first()
    if not user:
        raise ValueError("Employee has no linked user account")

    nonce = secrets.token_hex(16)
    timestamp = int(time.time())
    payload = f"{employee_id}:{user.id}:{nonce}:{timestamp}"
    signature = hmac.new(
        QR_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    token = f"{employee_id}:{timestamp}:{nonce}:{signature}"
    return {
        "qr_token": token,
        "employee_id": employee_id,
        "employee_code": emp.employee_code,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=QR_TOKEN_EXPIRY_SECONDS),
        "user_email": user.email,
        "user_name": user.full_name,
    }


def validate_qr_token(token: str, db: Session, geo_lat: Optional[float] = None, geo_long: Optional[float] = None) -> dict:
    try:
        parts = token.split(":")
        if len(parts) != 4:
            raise ValueError("Invalid token format")

        employee_id, timestamp_str, nonce, signature = parts
        employee_id = int(employee_id)
        timestamp = int(timestamp_str)

        if time.time() - timestamp > QR_TOKEN_EXPIRY_SECONDS:
            raise ValueError("QR token expired")

        Employee = hr_ports.Employee
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise ValueError("Employee not found")

        User = getattr(governance_ports, "User")
        user = db.query(User).filter(User.id == emp.user_id).first()
        if not user:
            raise ValueError("Employee has no linked user")

        payload = f"{employee_id}:{user.id}:{nonce}:{timestamp}"
        expected_signature = hmac.new(
            QR_SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid QR token signature")

        return {
            "valid": True,
            "employee_id": employee_id,
            "user_id": user.id,
            "employee_code": emp.employee_code,
            "user_email": user.email,
            "geo_validated": geo_lat is not None and geo_long is not None,
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def generate_static_qr_id_card(employee_id: int, db: Session) -> str:
    Employee = hr_ports.Employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")

    nonce = secrets.token_hex(8)
    payload = f"ZOZI:EMP:{employee_id}:{emp.employee_code}:{nonce}"
    signature = hmac.new(
        QR_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    return f"{payload}:{signature}"

