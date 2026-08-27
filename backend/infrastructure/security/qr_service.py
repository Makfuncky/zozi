"""QR token service for employee check-in/check-out.

Law 1 compliant: all employee/user lookups use raw SQL. The column
contract for ``employees`` and ``users`` is documented in
``domains/hr/models/employee_models.py`` and
``domains/governance/models/user.py``.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.utils.config import settings


QR_TOKEN_EXPIRY_SECONDS = 60
_QR_SECRET_KEY: Optional[str] = None


def _get_qr_secret_key() -> str:
    global _QR_SECRET_KEY
    if _QR_SECRET_KEY is None:
        if settings.secret_key:
            _QR_SECRET_KEY = settings.secret_key
        else:
            import warnings
            warnings.warn(
                "SECRET_KEY is not configured; using ephemeral key. QR tokens will not persist across restarts."
            )
            _QR_SECRET_KEY = secrets.token_hex(32)
    return _QR_SECRET_KEY


def _load_employee_with_user(db: Session, employee_id: int) -> dict | None:
    row = db.execute(
        text(
            "SELECT e.id AS employee_id, e.employee_code, e.user_id, "
            "u.id AS user_id_join, u.email, u.full_name "
            "FROM employees e LEFT JOIN users u ON u.id = e.user_id "
            "WHERE e.id = :eid"
        ),
        {"eid": employee_id},
    ).mappings().first()
    return dict(row) if row else None


def generate_qr_token(employee_id: int, db: Session) -> dict:
    row = _load_employee_with_user(db, employee_id)
    if not row:
        raise ValueError("Employee not found")
    if not row.get("user_id_join"):
        raise ValueError("Employee has no linked user account")

    nonce = secrets.token_hex(16)
    timestamp = int(time.time())
    payload = f"{employee_id}:{row['user_id_join']}:{nonce}:{timestamp}"
    signature = hmac.new(
        _get_qr_secret_key().encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    token = f"{employee_id}:{timestamp}:{nonce}:{signature}"
    return {
        "qr_token": token,
        "employee_id": employee_id,
        "employee_code": row.get("employee_code"),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=QR_TOKEN_EXPIRY_SECONDS),
        "user_email": row.get("email"),
        "user_name": row.get("full_name"),
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

        row = _load_employee_with_user(db, employee_id)
        if not row:
            raise ValueError("Employee not found")
        if not row.get("user_id_join"):
            raise ValueError("Employee has no linked user")

        user_id_join = row["user_id_join"]
        payload = f"{employee_id}:{user_id_join}:{nonce}:{timestamp}"
        expected_signature = hmac.new(
            _get_qr_secret_key().encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid QR token signature")

        return {
            "valid": True,
            "employee_id": employee_id,
            "user_id": user_id_join,
            "employee_code": row.get("employee_code"),
            "user_email": row.get("email"),
            "geo_validated": geo_lat is not None and geo_long is not None,
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def generate_static_qr_id_card(employee_id: int, db: Session) -> str:
    row = db.execute(
        text("SELECT id, employee_code FROM employees WHERE id = :eid"),
        {"eid": employee_id},
    ).mappings().first()
    if not row:
        raise ValueError("Employee not found")
    employee_code = row.get("employee_code") or ""

    nonce = secrets.token_hex(8)
    payload = f"ZOZI:EMP:{employee_id}:{employee_code}:{nonce}"
    signature = hmac.new(
        _get_qr_secret_key().encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    return f"{payload}:{signature}"
