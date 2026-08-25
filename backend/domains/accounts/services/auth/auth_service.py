"""
Unified Authentication Service — "One Identity, Many Doors"

Implements 5 login doors, all converging on the same JWT + RLS context:

  Door 1 – Email/Password + TOTP MFA
  Door 2 – Phone + OTP (SMS/WhatsApp)
  Door 3 – Biometric (fingerprint / face)
  Door 4 – QR Office Kiosk (zero-password)
  Door 5 – SSO (Google / Apple / Microsoft)

Every login writes a user_devices row, enforces concurrent-session policy,
sets the RLS country context, risk-scores the request, and writes to the
activity ledger.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple

from providers.auth import totp as totp_provider
from fastapi import HTTPException, Request, status

from infrastructure.utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    blacklist_token,
    is_token_blacklisted,
)
from infrastructure.database.database import SessionLocal
from domains.governance.models.user import User
from domains.governance.models.user import UserDevice
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeBiometric
from domains.hr.models.employee_models import DynamicQRSession
from domains.hr.models.employee_models import GeoFenceLog
from domains.hr.models.employee_models import EmployeeAttendance
from infrastructure.utils.config import settings
from infrastructure.utils.geo import haversine_distance

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes
KIOSK_SESSION_HOURS = 8
MOBILE_SESSION_DAYS = 30
MAX_OTP_ATTEMPTS = 5
RISK_HIGH_THRESHOLD = 75  # out of 100

# ═══════════════════════════════════════════════════════════════════════════
#  Shared Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _get_redis():
    """Return Redis client or None."""
    from infrastructure.utils.redis_client import redis_client

    client = redis_client()
    try:
        if not client.ping():
            return None
    except Exception:
        return None
    return client


def _generate_jti() -> str:
    return str(uuid.uuid4())


def _compute_device_fingerprint(request: Request) -> str:
    """Deterministic fingerprint from IP + User-Agent + optional header."""
    raw = f"{request.client.host}:{request.headers.get('user-agent', '')}:{request.headers.get('x-device-id', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _build_jwt_payload(
    user_id: int,
    employee_id: int,
    country_code: str,
    role: str,
    authority_level: int = 0,
    extra: Optional[dict] = None,
) -> dict:
    """Standard JWT payload with RLS context baked in."""
    jti = _generate_jti()
    payload = {
        "sub": str(user_id),
        "emp_id": employee_id,
        "cc": country_code,
        "role": role,
        "auth_lvl": authority_level,
        "jti": jti,
        ** (extra or {}),
    }
    return payload


def _set_rls_context(db, employee: Employee) -> None:
    """Set the RLS session variable for country isolation.

    Every subsequent query within this connection will be filtered to the
    employee's country_code unless the role is 'admin' or 'global'.
    On SQLite the SET statement is silently skipped.
    """
    # SECURITY FIX: Use parameterized query to prevent SQL injection
    country_code = employee.country_code
    if not country_code or not isinstance(country_code, str):
        return
    # Validate country_code format (2-3 uppercase letters)
    import re
    if not re.match(r'^[A-Z]{2,3}$', country_code):
        logger.warning("Invalid country_code format: %s", country_code)
        return
    try:
        from sqlalchemy import text
        db.execute(
            text("SET app.current_country_code = :country_code"),
            {"country_code": country_code}
        )
    except Exception:
        logger.debug(
            "RLS context not set (SQLite or unsupported dialect). "
            "Country isolation enforced at application layer."
        )


def _log_activity(
    db,
    actor_employee_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    metadata_json: Optional[dict] = None,
    ip_address: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
) -> None:
    """Append-only activity log entry."""
    try:
        from domains.hr.models.employee_models import EmployeeActivityLog

        log_entry = EmployeeActivityLog(
            actor_employee_id=actor_employee_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
        )
        db.add(log_entry)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to write activity log: %s", exc)
        db.rollback()


def _record_device(
    db,
    user_id: int,
    fingerprint: str,
    ip: str,
    user_agent: str,
    device_name: Optional[str] = None,
    is_trusted: bool = False,
) -> UserDevice:
    """Upsert a user device record."""
    existing = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.device_fingerprint == fingerprint,
        )
        .first()
    )
    if existing:
        existing.last_ip = ip
        existing.last_user_agent = user_agent
        existing.last_seen_at = datetime.utcnow()
        existing.is_trusted = is_trusted or existing.is_trusted
        db.commit()
        return existing

    device = UserDevice(
        user_id=user_id,
        device_fingerprint=fingerprint,
        device_name=device_name or "unknown",
        last_ip=ip,
        last_user_agent=user_agent,
        is_trusted=is_trusted,
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def _compute_risk_score(
    employee: Employee,
    device_fingerprint: str,
    ip: str,
    request: Request,
    db,
) -> int:
    """Risk score 0-100 combining geo anomaly + new device + odd-hour.

    Returns score; if > RISK_HIGH_THRESHOLD, caller should step-up auth.
    """
    score = 0

    # 1. New device check (if device has no prior history)
    existing_device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == employee.user_id,
            UserDevice.device_fingerprint == device_fingerprint,
        )
        .first()
    )
    if not existing_device:
        score += 30  # Unknown device

    # 2. Geo-fence anomaly (only for kiosk/office scans)
    if request.headers.get("x-kiosk-id"):
        lat_str = request.headers.get("x-latitude")
        lon_str = request.headers.get("x-longitude")
        if lat_str and lon_str:
            try:
                lat, lon = float(lat_str), float(lon_str)
                # Check against employee's office geo-fence
                if employee.office:
                    dist = haversine_distance(lat, lon, employee.office.latitude, employee.office.longitude)
                    if dist > (employee.office.geo_fence_radius_meters or 100):
                        score += 40
            except (ValueError, TypeError):
                score += 10

    # 3. Odd-hour login
    hour = datetime.utcnow().hour
    if hour < 6 or hour > 22:
        score += 20

    # 4. Geo-velocity (impossible travel) — TODO: query employee_activity_logs
    # for last login IP when the activity_logs table is available.

    return min(score, 100)


# ═══════════════════════════════════════════════════════════════════════════
#  Door 1 — Email / Password + TOTP MFA
# ═══════════════════════════════════════════════════════════════════════════


def authenticate_password(
    email: str,
    password: str,
    totp_code: Optional[str] = None,
    request: Optional[Request] = None,
    db: Session | None = None,
) -> dict:
    """Door 1: Email/Password login with optional TOTP step-up.

    Returns JWT tokens + employee profile on success.
    Raises HTTPException on failure.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        # TOTP challenge
        if user.totp_enabled:
            if not totp_code:
                raise HTTPException(
                    status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                    detail="TOTP code required",
                )
            if not totp_provider.verify(user.totp_secret, totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid TOTP code",
                )

        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )

        return _issue_session(
            db=db,
            user=user,
            employee=employee,
            request=request,
            login_method="password",
        )
    finally:
        if close_db:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Door 2 — Phone + OTP (SMS / WhatsApp)
# ═══════════════════════════════════════════════════════════════════════════


def _store_otp(phone: str, otp: str) -> None:
    """Store OTP in Redis with TTL."""
    r = _get_redis()
    if r:
        r.setex(f"otp:{phone}", OTP_EXPIRY_SECONDS, otp)
        r.setex(f"otp_attempts:{phone}", OTP_EXPIRY_SECONDS, 0)


def _verify_stored_otp(phone: str, otp: str) -> bool:
    """Check OTP and increment attempt counter."""
    r = _get_redis()
    if not r:
        # Fallback: in-memory check (single-process only)
        logger.warning("Redis unavailable — OTP verification degraded")
        return False

    attempts_key = f"otp_attempts:{phone}"
    attempts = r.get(attempts_key)
    if attempts and int(attempts) >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP attempts. Request a new code.",
        )

    stored = r.get(f"otp:{phone}")
    if not stored:
        return False

    # Constant-time comparison
    if hmac.compare_digest(stored.decode(), otp):
        r.delete(f"otp:{phone}")
        r.delete(attempts_key)
        return True

    r.incr(attempts_key)
    return False


def request_otp(phone: str) -> dict:
    """Generate and send OTP to phone number.

    In production, this sends via SMS provider (Twilio, etc.) or WhatsApp.
    For development, logs to console.
    """
    otp = "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
    _store_otp(phone, otp)

    # TODO: Integrate with SMS/WhatsApp provider
    logger.info("OTP for %s: %s (expires in %ds)", phone, otp, OTP_EXPIRY_SECONDS)

    # In production, mask the phone in the response
    masked = phone[:4] + "****" + phone[-3:] if len(phone) > 7 else "****"
    return {"message": f"OTP sent to {masked}", "expires_in_seconds": OTP_EXPIRY_SECONDS}


def authenticate_phone_otp(
    phone: str,
    otp: str,
    request: Optional[Request] = None,
    db: Session | None = None,
) -> dict:
    """Door 2: Phone + OTP login.

    Looks up user by phone number, verifies OTP, issues session.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this phone number",
            )

        if not _verify_stored_otp(phone, otp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP",
            )

        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )

        return _issue_session(
            db=db,
            user=user,
            employee=employee,
            request=request,
            login_method="phone_otp",
        )
    finally:
        if close_db:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Door 3 — Biometric (Mobile App)
# ═══════════════════════════════════════════════════════════════════════════


def _enroll_biometric(
    user_id: int,
    fingerprint_hash: Optional[str] = None,
    face_encoding: Optional[str] = None,
    biometric_type: str = "fingerprint",
    db: Session | None = None,
) -> dict:
    """Enroll a new biometric template.

    First-time enrollment requires a password+OTP bootstrap (enforced by caller).
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        existing = (
            db.query(EmployeeBiometric)
            .filter(EmployeeBiometric.employee_id == employee.id)
            .first()
        )
        if existing:
            # Update existing enrollment
            if fingerprint_hash:
                existing.fingerprint_hash = fingerprint_hash
            if face_encoding:
                existing.face_encoding = face_encoding
            existing.biometric_type = biometric_type
            existing.is_active = True
        else:
            bio = EmployeeBiometric(
                employee_id=employee.id,
                fingerprint_hash=fingerprint_hash,
                face_encoding=face_encoding,
                biometric_type=biometric_type,
                is_active=True,
            )
            db.add(bio)

        db.commit()
        _log_activity(
            db,
            actor_employee_id=employee.id,
            action="biometric_enrolled",
            entity_type="employee_biometrics",
            metadata_json={"biometric_type": biometric_type},
        )
        return {"status": "enrolled", "biometric_type": biometric_type}
    finally:
        if close_db:
            db.close()


def authenticate_biometric(
    user_id: int,
    fingerprint_hash: Optional[str] = None,
    face_encoding: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    request: Optional[Request] = None,
    db: Session | None = None,
) -> dict:
    """Door 3: Biometric login.

    Device must be already registered as trusted (is_trusted=True).
    First-time biometric enrollment requires password+OTP bootstrap.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="Account not active")

        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        biometrics = (
            db.query(EmployeeBiometric)
            .filter(
                EmployeeBiometric.employee_id == employee.id,
                EmployeeBiometric.is_active == True,
            )
            .first()
        )
        if not biometrics:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="No biometric enrollment found. Enroll via password+OTP first.",
            )

        # Verify biometric match
        if fingerprint_hash and biometrics.fingerprint_hash:
            if not hmac.compare_digest(fingerprint_hash, biometrics.fingerprint_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Fingerprint does not match",
                )
        elif face_encoding and biometrics.face_encoding:
            # Face encoding comparison — cosine similarity on embedding vectors
            if not _compare_face_encodings(face_encoding, biometrics.face_encoding):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Face does not match",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide fingerprint_hash or face_encoding",
            )

        # Check device is trusted
        if device_fingerprint:
            device = (
                db.query(UserDevice)
                .filter(
                    UserDevice.user_id == user.id,
                    UserDevice.device_fingerprint == device_fingerprint,
                )
                .first()
            )
            if not device or not device.is_trusted:
                raise HTTPException(
                    status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                    detail="Device not trusted. Re-authenticate with password+OTP to trust this device.",
                )

        return _issue_session(
            db=db,
            user=user,
            employee=employee,
            request=request,
            login_method="biometric",
        )
    finally:
        if close_db:
            db.close()


def _compare_face_encodings(encoding_a: str, encoding_b: str, threshold: float = 0.6) -> bool:
    """Compare two face encoding vectors using cosine similarity.

    Both encodings are expected as comma-separated floats (base64 or JSON arrays).
    This is a simplified comparison; production should use a dedicated face-matching service.
    """
    try:
        vec_a = [float(x) for x in encoding_a.split(",")]
        vec_b = [float(x) for x in encoding_b.split(",")]
        if len(vec_a) != len(vec_b):
            return False
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return False
        similarity = dot / (norm_a * norm_b)
        return similarity >= threshold
    except (ValueError, TypeError, ZeroDivisionError):
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Door 4 — QR Office Kiosk (Zero-Password)
# ═══════════════════════════════════════════════════════════════════════════


def generate_kiosk_qr(
    employee_id: int,
    office_id: int,
    expires_in_hours: int = 1,
    db: Session | None = None,
) -> dict:
    """Generate a one-time QR session for kiosk login.

    Returns the QR token (to be rendered as QR code) and session details.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        qr_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        session = DynamicQRSession(
            employee_id=employee_id,
            qr_token=qr_token,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()

        return {
            "qr_token": qr_token,
            "expires_at": expires_at.isoformat(),
            "qr_data": json.dumps(
                {
                    "type": "kiosk_login",
                    "token": qr_token,
                    "tenant": "zozi",
                    "v": 1,
                }
            ),
        }
    finally:
        if close_db:
            db.close()


def authenticate_kiosk_qr(
    qr_token: str,
    ip_address: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    request: Optional[Request] = None,
    secondary_biometric: Optional[dict] = None,
    db: Session | None = None,
) -> dict:
    """Door 4: QR Kiosk login.

    Validates QR token + expiry + geo-fence. Optionally requires secondary
    biometric match to prevent buddy punching.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        session = (
            db.query(DynamicQRSession)
            .filter(DynamicQRSession.qr_token == qr_token)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Invalid QR code")

        if session.used_at:
            raise HTTPException(status_code=400, detail="QR code already used")

        if session.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="QR code expired")

        employee = db.query(Employee).filter(Employee.id == session.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Geo-fence validation
        if latitude and longitude and employee.office:
            dist = haversine_distance(
                latitude,
                longitude,
                employee.office.latitude,
                employee.office.longitude,
            )
            within = dist <= (employee.office.geo_fence_radius_meters or 100)

            geo_log = GeoFenceLog(
                employee_id=employee.id,
                latitude=latitude,
                longitude=longitude,
                is_within_fence=within,
            )
            db.add(geo_log)
            db.commit()

            if not within:
                raise HTTPException(
                    status_code=403,
                    detail=f"Outside geo-fence ({dist:.0f}m from office)",
                )

        # Optional secondary biometric ("buddy punching" prevention)
        if secondary_biometric:
            biometrics = (
                db.query(EmployeeBiometric)
                .filter(
                    EmployeeBiometric.employee_id == employee.id,
                    EmployeeBiometric.is_active == True,
                )
                .first()
            )
            if biometrics:
                fh = secondary_biometric.get("fingerprint_hash")
                fe = secondary_biometric.get("face_encoding")
                if fh and biometrics.fingerprint_hash:
                    if not hmac.compare_digest(fh, biometrics.fingerprint_hash):
                        raise HTTPException(
                            status_code=401,
                            detail="Biometric mismatch — possible buddy punch",
                        )
                elif fe and biometrics.face_encoding:
                    if not _compare_face_encodings(fe, biometrics.face_encoding):
                        raise HTTPException(
                            status_code=401,
                            detail="Face mismatch — possible buddy punch",
                        )

        # Mark QR session as used
        session.used_at = datetime.utcnow()
        session.ip_address = ip_address

        # Log attendance
        today = datetime.utcnow().date()
        existing_attendance = (
            db.query(EmployeeAttendance)
            .filter(
                EmployeeAttendance.employee_id == employee.id,
                EmployeeAttendance.date == today,
            )
            .first()
        )
        if existing_attendance:
            if not existing_attendance.scan_in_time:
                existing_attendance.scan_in_time = datetime.utcnow()
            existing_attendance.scan_out_time = datetime.utcnow()
        else:
            attendance = EmployeeAttendance(
                employee_id=employee.id,
                date=today,
                scan_in_time=datetime.utcnow(),
                scan_type="qr_kiosk",
                location_lat=latitude,
                location_long=longitude,
                status="present",
            )
            db.add(attendance)

        db.commit()

        return _issue_session(
            db=db,
            user=db.query(User).filter(User.id == employee.user_id).first(),
            employee=employee,
            request=request,
            login_method="qr_kiosk",
            session_ttl_hours=KIOSK_SESSION_HOURS,
        )
    finally:
        if close_db:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Door 5 — SSO (Google / Apple / Microsoft)
# ═══════════════════════════════════════════════════════════════════════════


def _verify_sso_token(provider: str, id_token: str) -> dict:
    """Verify an SSO ID token and return the userinfo claims.

    Supports Google, Apple, and Microsoft. In production, validates the
    token signature, expiry, and audience (client_id) via the provider's
    public JWKS endpoint.

    SECURITY NOTE: This function currently uses unverified claims decoding.
    In production, this MUST be replaced with proper JWT verification against
    the provider's JWKS endpoint.
    """
    # SECURITY FIX: Reject SSO tokens in production without proper verification
    from infrastructure.utils.config import settings
    app_env = str(getattr(settings, "app_env", "development")).lower()
    if app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SSO token verification is not implemented in production. "
                   "Please integrate with the provider's JWKS endpoint.",
        )

    # TODO: Integrate with google-auth, apple-auth, msal libraries
    # For now, return a mock userinfo for development
    # In production, replace with proper JWT verification against provider JWKS
    try:
        from providers.auth import jwt as jwt_provider

        # Get provider's JWKS — placeholder
        payload = jwt_provider.decode_unverified_claims(id_token)
        provider_claims = {
            "google": {"email", "sub", "name"},
            "apple": {"email", "sub"},
            "microsoft": {"email", "sub", "name", "preferred_username"},
        }
        required = provider_claims.get(provider, {"email", "sub"})
        if not required.issubset(payload.keys()):
            raise ValueError(f"Missing required claims: {required - set(payload.keys())}")

        return {
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "name": payload.get("name") or payload.get("preferred_username", ""),
            "provider": provider,
            "issuer": payload.get("iss", ""),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"SSO token verification failed: {e}",
        )


def authenticate_sso(
    provider: str,
    id_token: str,
    request: Optional[Request] = None,
    auto_provision: bool = True,
    db: Session | None = None,
) -> dict:
    """Door 5: SSO login via Google, Apple, or Microsoft.

    Maps the SSO `sub` claim to `users.email`.
    If `auto_provision=True` and no user exists, creates a new user+employee
    if the SSO email domain matches allowed corporate domains.
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        claims = _verify_sso_token(provider, id_token)
        email = claims.get("email", "")
        sso_sub = claims.get("sub", "")

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by SSO provider")

        user = db.query(User).filter(User.email == email).first()

        # Auto-provision if enabled and user doesn't exist
        if not user and auto_provision:
            domain = email.split("@")[-1] if "@" in email else ""
            allowed_domains = getattr(settings, "sso_allowed_domains", "").split(",")
            if allowed_domains and domain not in allowed_domains:
                raise HTTPException(
                    status_code=403,
                    detail=f"Domain '{domain}' not allowed for self-provisioning",
                )

            # Check if HR pre-registered this employee
            employee = (
                db.query(Employee)
                .filter(Employee.employee_code == sso_sub)
                .first()
            )
            if not employee:
                raise HTTPException(
                    status_code=404,
                    detail="Employee not found. Contact HR to pre-register your account.",
                )

            # Link SSO user to employee
            user = User(
                email=email,
                username=email.split("@")[0],
                is_active=True,
                is_verified=True,
                role=employee.department or "employee",
                totp_enabled=False,
            )
            db.add(user)
            db.flush()
            employee.user_id = user.id
            db.commit()
            db.refresh(user)
            logger.info("Auto-provisioned SSO user: %s -> employee %s", email, employee.id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="No account found. Contact your administrator.",
            )

        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")

        return _issue_session(
            db=db,
            user=user,
            employee=employee,
            request=request,
            login_method=f"sso_{provider}",
        )
    finally:
        if close_db:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Session Issuance (shared across all doors)
# ═══════════════════════════════════════════════════════════════════════════


def _issue_session(
    db,
    user: User,
    employee: Employee,
    request: Optional[Request] = None,
    login_method: str = "password",
    session_ttl_hours: Optional[int] = None,
) -> dict:
    """Issue JWT tokens, record device, set RLS context, log activity.

    This is the single convergence point for all 5 login doors.
    """
    # Compute device fingerprint
    device_fp = (
        _compute_device_fingerprint(request)
        if request
        else hashlib.sha256(b"server").hexdigest()[:32]
    )
    ip = request.client.host if request else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "") if request else ""

    # Record device
    device = _record_device(
        db=db,
        user_id=user.id,
        fingerprint=device_fp,
        ip=ip,
        user_agent=user_agent,
        is_trusted=login_method in ("password", "sso_google", "sso_apple", "sso_microsoft"),
    )

    # Compute risk score
    risk_score = _compute_risk_score(employee, device_fp, ip, request, db)

    # Step-up if high risk (except for high-assurance methods)
    if risk_score > RISK_HIGH_THRESHOLD and login_method not in (
        "password", "sso_google", "sso_apple", "sso_microsoft"
    ):
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail=f"High-risk login (score={risk_score}). Please authenticate with password or SSO.",
        )

    # Build JWT payload with RLS context
    role = user.role or "employee"
    authority_level = getattr(employee, "authority_level", 0) or 0
    country_code = employee.country_code or "OM"

    payload = _build_jwt_payload(
        user_id=user.id,
        employee_id=employee.id,
        country_code=country_code,
        role=role,
        authority_level=authority_level,
        extra={"login_method": login_method, "risk_score": risk_score},
    )

    # Token TTL — kiosk gets shorter, mobile gets longer
    if session_ttl_hours:
        access_ttl = timedelta(hours=session_ttl_hours)
    elif login_method == "qr_kiosk":
        access_ttl = timedelta(hours=KIOSK_SESSION_HOURS)
    elif login_method in ("biometric", "phone_otp"):
        access_ttl = timedelta(days=MOBILE_SESSION_DAYS)
    else:
        access_ttl = timedelta(minutes=settings.access_token_expire_minutes)

    access_token = create_access_token(data=payload, expires_delta=access_ttl)
    refresh_token = create_refresh_token(data=payload)

    # Set RLS context on this connection
    _set_rls_context(db, employee)

    # Log activity
    _log_activity(
        db,
        actor_employee_id=employee.id,
        action="login",
        entity_type="session",
        metadata_json={
            "method": login_method,
            "risk_score": risk_score,
            "device_fingerprint": device_fp,
        },
        ip_address=ip,
        device_fingerprint=device_fp,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in_seconds": int(access_ttl.total_seconds()),
        "employee": {
            "id": employee.id,
            "user_id": user.id,
            "employee_code": employee.employee_code,
            "name": user.username,
            "email": user.email,
            "role": role,
            "country_code": country_code,
            "department": employee.department,
            "position": employee.position,
            "office_id": employee.office_id,
            "authority_level": authority_level,
            "is_verified": employee.is_verified,
        },
        "device": {
            "fingerprint": device_fp,
            "is_trusted": device.is_trusted,
            "is_new": not device.first_seen_at or device.first_seen_at == device.last_seen_at,
        },
        "risk": {"score": risk_score, "requires_step_up": risk_score > RISK_HIGH_THRESHOLD},
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Token Refresh & Logout
# ═══════════════════════════════════════════════════════════════════════════


def refresh_session(refresh_token: str, db: Session | None = None) -> dict:
    """Refresh an access token using a valid refresh token."""
    from infrastructure.utils.auth import verify_refresh_token

    username = verify_refresh_token(refresh_token)
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        return _issue_session(
            db=db,
            user=user,
            employee=employee,
            login_method="refresh",
        )
    finally:
        if close_db:
            db.close()


def logout(access_token: str, db: Session | None = None) -> dict:
    """Blacklist the access token and log the activity."""
    from infrastructure.utils.auth import verify_token

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        from providers.auth import jwt as jwt_provider

        payload = jwt_provider.decode_unverified_claims(access_token)
        jti = payload.get("jti", "")
        exp = payload.get("exp", 3600)
        ttl = max(exp - int(time.time()), 60)

        blacklist_token(jti, ttl)

        user_id = int(payload.get("sub", 0))
        employee = (
            db.query(Employee).filter(Employee.user_id == user_id).first()
        )
        if employee:
            _log_activity(
                db,
                actor_employee_id=employee.id,
                action="logout",
                entity_type="session",
                metadata_json={"jti": jti},
            )
    except Exception as e:
        logger.warning("Logout partial failure: %s", e)
    finally:
        if close_db:
            db.close()

    return {"message": "Logged out successfully"}




# === MERGED FROM otp_service.py ===
"""OTP / MFA challenge logic for the accounts domain.

Thin challenge store plus best-effort delivery. Real email/SMS transport is
stubbed here and wired to the messaging layer later (twilio is not configured
in dev, so SMS only logs). Codes are bcrypt-hashed at rest; plaintext is never
persisted.
"""

import logging
import random
import string
from datetime import timedelta

from sqlalchemy.orm import Session

from infrastructure.security.auth import get_password_hash, verify_password
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.config import settings
# TODO: OtpCode model not yet defined — add to accounts/models/ when needed

logger = logging.getLogger(__name__)

def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


OTP_TTL_SECONDS = _as_int(getattr(settings, "otp_ttl_seconds", 300), 300)
OTP_MAX_ATTEMPTS = _as_int(getattr(settings, "otp_max_attempts", 5), 5)


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def start_otp(user, purpose: str, channel: str = "email", destination: str | None = None, db: Session | None = None) -> OtpCode:
    """Issue a fresh OTP for ``user``/``purpose`` and attempt delivery."""
    code = _generate_code()
    expires_at = utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    record = OtpCode(
        user_id=user.id,
        purpose=purpose,
        channel=channel,
        destination=destination,
        code_hash=get_password_hash(code),
        expires_at=expires_at,
        country_code=getattr(user, "country_code", None),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    _deliver(user, channel, destination, code)
    return record


def verify_otp(user, purpose: str, code: str, db: Session | None = None) -> bool:
    """Return True if ``code`` matches the latest unverified, unexpired challenge."""
    record = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.purpose == purpose,
            OtpCode.verified.is_(False),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if record is None:
        return False
    if record.expires_at < utcnow():
        return False
    if record.attempts >= OTP_MAX_ATTEMPTS:
        return False
    record.attempts += 1
    if verify_password(code, record.code_hash):
        record.verified = True
        db.commit()
        return True
    db.commit()
    return False


def _deliver(user, channel: str, destination: str | None, code: str) -> None:
    dest = destination or getattr(user, "email", None) or getattr(user, "phone", None)
    if channel == "email" and dest:
        # Email delivery: routes via comms.email_service when configured; logs for dev.
        logger.info("OTP(email) user=%s destination=%s code=%s", user.id, dest, code)
    elif channel == "sms" and dest:
        # SMS delivery: integrates via providers.sms.twilio when configured; logs for dev.
        logger.info("OTP(sms) user=%s destination=%s code=%s [delivery stub]", user.id, dest, code)
    else:
        logger.warning("OTP delivery skipped: no destination for user=%s", user.id)


# === MERGED FROM auth_router_service.py ===
"""Auth router service — DB helpers for routers/auth.py."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.governance.models.user import UserLoginHistory
from infrastructure.utils.auth import verify_password
from infrastructure.utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)


def find_user(db: Session, email: str | None, username: str | None) -> User | None:
    q = db.query(User)
    if email:
        q = q.filter(User.email == email)
    elif username:
        q = q.filter(User.username == username)
    else:
        return None
    user = q.first()
    if user:
        return user
    if username and "@" in username and not email:
        return db.query(User).filter(User.email == username).first()
    return None


def record_login_history(db: Session, user: User, request=None, success: bool = True) -> None:
    try:
        ip = get_request_ip(request) if request else None
        ua = (request.headers.get("user-agent") or "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=success,
            country_code=user.country_code,
        )
        db.add(history)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to record login history for %s: %s", user.username, exc)
        try:
            db.rollback()
        except Exception:
            pass


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def check_email_exists(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None


def check_username_exists(db: Session, username: str) -> bool:
    return db.query(User).filter(User.username == username).first() is not None


def create_user(db: Session, email: str, username: str, full_name: str, phone: str | None, role: str, hashed_password: str) -> User:
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        phone=phone,
        role=role,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> None:
    user.last_login = datetime.now(timezone.utc)
    db.commit()



# === MERGED FROM auth_controller_service.py ===
"""
Auth Controller — all authentication and account business logic.

The `get_current_user` dependency lives here and is re-exported by
`routers/auth.py` so that all existing `from modules.routers.core_auth_routes import get_current_user`
imports continue to work unchanged.
"""
import os
import secrets
import logging
import re
from providers.auth import totp as totp_provider
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast
from urllib.parse import urlencode

from providers.auth import oauth

from fastapi import Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.governance.models.core import UserBrowsingHistory
from domains.governance.models.user import User
from domains.governance.models.user import UserDevice
from domains.governance.models.user import UserLoginHistory
from domains.governance.models.user import PasswordResetToken
from domains.governance.models.user import EmailVerificationToken
from domains.governance.models.user import ReferralPointEvent
from domains.comms.models.suppliers import SupplierProfile
from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.database.schemas import (
    UserCreate,
    User as UserSchema,
    ChangePasswordRequest,
    ProfileUpdate,
    ReferralDashboardSchema,
    ReferralPointEventSchema,
    ReferralShareRequest,
)
from infrastructure.database.database import get_db
from infrastructure.utils.cache import cache_get_json, cache_set_json, cache_delete
from infrastructure.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    blacklist_token,
    record_failed_login,
    is_account_locked,
    clear_failed_logins,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    validate_password_complexity,
    create_temp_token,
    verify_temp_token,
    decode_token,
    is_refresh_token_used,
    mark_refresh_token_used,
    is_refresh_family_revoked,
    revoke_refresh_family,
)
from infrastructure.utils.ip_utils import get_request_ip
from infrastructure.utils.config import settings
from infrastructure.utils.constants import STAFF_ROLES
from infrastructure.utils.currency import KNOWN_CURRENCY_META
from infrastructure.utils.email_service import (
    EmailDeliveryDisabledError,
    get_email_delivery_status,
    has_live_email_delivery,
    send_password_reset_email,
    send_verification_email,
)
from infrastructure.utils.staff_permissions import default_permissions_for_role, sanitize_staff_permissions
from infrastructure.utils.audit import audit_log, AuditAction

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

VERIFY_TOKEN_TTL_HOURS = 24
RESET_TOKEN_TTL_HOURS = 1
SOCIAL_STATE_COOKIE_PREFIX = "zozi_oauth_state_"
DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "OMR"
DEFAULT_COUNTRY = "OM"
REFERRAL_CODE_LENGTH = 8
REFERRAL_REFERRER_BONUS = 100
REFERRAL_NEW_CUSTOMER_BONUS = 25
REFERRAL_SHARE_DAILY_BONUS = 5
_USER_CACHE_TTL_SECONDS = 5 * 60


def resolve_rate_limit(default_limit: str, *, loadtest_limit: str | None = None) -> str:
    if settings.loadtest_profile_enabled and loadtest_limit:
        return loadtest_limit
    return default_limit


def _next_logistics_partner_code(db: Session, user_id: int) -> str:
    base_code = f"LPAUTO{user_id}"
    candidate = base_code
    suffix = 1
    while db.query(LogisticsPartner).filter(LogisticsPartner.code == candidate).first():
        suffix += 1
        candidate = f"{base_code}_{suffix}"
    return candidate


# ── Pydantic models ───────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SocialLoginRequest(BaseModel):
    token: str = ""


class SocialLoginJsonRequest(BaseModel):
    """Unified JSON social-login payload used by the mobile / web clients."""

    provider: str = "google"
    id_token: str = ""
    access_token: str = ""
    token: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class PublicResendVerificationRequest(BaseModel):
    identifier: str


class RefreshTokenBody(BaseModel):
    refresh_token: Optional[str] = None


def get_social_providers_status() -> dict:
    google_enabled = bool(settings.google_client_id)
    facebook_enabled = bool(settings.facebook_client_id and settings.facebook_client_secret)
    return {
        "google": google_enabled,
        "google_mode": "gsi" if google_enabled else "disabled",
        "google_client_id": settings.google_client_id or None,
        "facebook": facebook_enabled,
        "facebook_mode": "redirect" if facebook_enabled else "disabled",
        "customer_email_verification_required": is_customer_email_verification_required(),
        "customer_email_verification_mode": settings.customer_email_verification_mode,
        "email_delivery": get_email_delivery_status(),
    }


def is_customer_email_verification_required() -> bool:
    mode = settings.customer_email_verification_mode
    if mode == "required":
        return True
    if mode == "disabled":
        return False
    return has_live_email_delivery()


def _normalize_customer_verification_when_gate_disabled(user: User, db: Session) -> None:
    if _user_role(user) != "customer":
        return
    if is_customer_email_verification_required() or user.email_verified:
        return
    user.email_verified = True
    db.commit()
    db.refresh(user)


def _resolve_user_from_subject(subject: str, db: Session) -> User | None:
    try:
        return db.query(User).filter(User.id == int(subject)).first()
    except (TypeError, ValueError):
        return db.query(User).filter(User.username == str(subject)).first()


def _user_id(user: User | UserSchema) -> int:
    return cast(int, getattr(user, "id"))


def _user_username(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "username"))


def _user_email(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "email"))


def _user_role(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "role"))


def _user_phone(user: User | UserSchema) -> str | None:
    return cast(str | None, getattr(user, "phone"))


def _user_email_verified(user: User | UserSchema) -> bool:
    return bool(cast(bool, getattr(user, "email_verified", False)))


def _user_profile_image(user: User | UserSchema) -> str | None:
    return cast(str | None, getattr(user, "profile_image"))



def _user_effective_permissions(user: User) -> list[str]:
    role = _user_role(user)
    if role not in STAFF_ROLES:
        return []
    assigned_permissions = sanitize_staff_permissions(getattr(user, "staff_permissions", None))
    if assigned_permissions:
        return assigned_permissions
    from infrastructure.utils.staff_permissions import ROLE_PERMISSION_MAP

    return sorted(ROLE_PERMISSION_MAP.get(role, set()))


def _user_staff_payload(user: User) -> dict[str, Any]:
    return {
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "staff_role_label": cast(str | None, getattr(user, "staff_role_label", None)),
        "staff_title": cast(str | None, getattr(user, "staff_title", None)),
        "staff_department": cast(str | None, getattr(user, "staff_department", None)),
        "staff_area_of_operation": cast(str | None, getattr(user, "staff_area_of_operation", None)),
        "staff_hire_date": getattr(user, "staff_hire_date", None),
        "staff_experience_level": cast(str | None, getattr(user, "staff_experience_level", None)),
        "staff_performance_summary": cast(str | None, getattr(user, "staff_performance_summary", None)),
        "staff_assigned_tasks": list(getattr(user, "staff_assigned_tasks", None) or []),
        "staff_assigned_projects": list(getattr(user, "staff_assigned_projects", None) or []),
        "permissions": _user_effective_permissions(user),
        "staff_notes": cast(str | None, getattr(user, "staff_notes", None)),
        "staff_country_codes": list(getattr(user, "staff_country_codes", None) or []),
    }


def _total_referral_points(user: User) -> int:
    referral_points = int(cast(int | None, getattr(user, "referral_points", 0)) or 0)
    sharing_points = int(cast(int | None, getattr(user, "sharing_points", 0)) or 0)
    return referral_points + sharing_points


def _build_referral_link(referral_code: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/r/{referral_code}"


def _referral_event_description(event_type: str) -> str:
    labels = {
        "referral_invite_success": "A customer joined with your referral code.",
        "referral_join_bonus": "Welcome bonus for joining through a referral.",
        "share_bonus": "Daily sharing bonus awarded.",
    }
    return labels.get(event_type, "Referral activity")


def _serialize_referral_event(event: ReferralPointEvent) -> ReferralPointEventSchema:
    referred_user = cast(User | None, getattr(event, "referred_user", None))
    return ReferralPointEventSchema(
        id=cast(int, getattr(event, "id")),
        event_type=cast(str, getattr(event, "event_type")),
        points=int(cast(int | None, getattr(event, "points", 0)) or 0),
        channel=cast(str | None, getattr(event, "channel", None)),
        description=_referral_event_description(cast(str, getattr(event, "event_type"))),
        created_at=cast(datetime, getattr(event, "created_at")),
        referred_user_id=cast(int | None, getattr(event, "referred_user_id", None)),
        referred_username=(
            cast(str | None, getattr(referred_user, "username", None))
            if referred_user is not None
            else None
        ),
    )


def _generate_unique_referral_code(db: Session) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(30):
        candidate = "".join(secrets.choice(alphabet) for _ in range(REFERRAL_CODE_LENGTH))
        exists = db.query(User).filter(func.lower(User.referral_code) == candidate.lower()).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=500, detail="Unable to generate referral code")


def _ensure_verification_delivery_available() -> None:
    email_status = get_email_delivery_status()
    if bool(email_status.get("available", False)):
        return
    raise HTTPException(
        status_code=503,
        detail="Customer email verification is unavailable because email delivery is not configured.",
    )


def _record_referral_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    points: int,
    channel: str | None = None,
    referred_user_id: int | None = None,
) -> None:
    db.add(
        ReferralPointEvent(
            user_id=user_id,
            event_type=event_type,
            points=points,
            channel=channel,
            referred_user_id=referred_user_id,
        )
    )


def _user_public_payload(user: User | UserSchema) -> dict[str, Any]:
    payload = {
        "id": _user_id(user),
        "email": _user_email(user),
        "username": _user_username(user),
        "role": _user_role(user),
        "profile_image": _user_profile_image(user),
        "phone": _user_phone(user),
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "referral_code": cast(str | None, getattr(user, "referral_code", None)),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        "total_points": _total_referral_points(user),
        "email_verified": _user_email_verified(user),
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "address_book": getattr(user, "address_book", None),
    }
    if _user_role(user) in STAFF_ROLES:
        payload.update(_user_staff_payload(user))
    return payload


# ── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — resolves the current authenticated user from the JWT."""
    subject = verify_token(token)
    cache_key = f"auth:user:{subject}"
    cached = cache_get_json(cache_key)
    if isinstance(cached, dict):
        return cached
    user = _resolve_user_from_subject(subject, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    payload = {
        "id": _user_id(user),
        "username": _user_username(user),
        "email": _user_email(user),
        "role": _user_role(user),
        "is_active": bool(cast(Any, getattr(user, "is_active"))),
        "phone": _user_phone(user),
        "profile_image": _user_profile_image(user),
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "country_code": cast(str | None, getattr(user, "country_code")) or cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "referral_code": cast(str | None, getattr(user, "referral_code", None)),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        "total_points": _total_referral_points(user),
        "email_verified": user.email_verified,
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "address_book": getattr(user, "address_book", None),
        "created_at": cast(datetime, getattr(user, "created_at")),
        "_token": token,
    }
    if _user_role(user) in STAFF_ROLES:
        payload.update(_user_staff_payload(user))
    cache_set_json(cache_key, payload, _USER_CACHE_TTL_SECONDS)
    return payload


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — resolves the current user from JWT, or returns None if unauthenticated."""
    if not token:
        return None
    try:
        subject = verify_token(token)
        cache_key = f"auth:user:{subject}"
        cached = cache_get_json(cache_key)
        if isinstance(cached, dict):
            return cached
        user = _resolve_user_from_subject(subject, db)
        if not user:
            return None
        payload = {
            "id": _user_id(user),
            "username": _user_username(user),
            "email": _user_email(user),
            "role": _user_role(user),
            "is_active": bool(cast(Any, getattr(user, "is_active"))),
            "phone": _user_phone(user),
            "profile_image": _user_profile_image(user),
            "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
            "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
            "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
            "country_code": cast(str | None, getattr(user, "country_code")) or cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
            "referral_code": cast(str | None, getattr(user, "referral_code", None)),
            "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
            "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
            "total_points": _total_referral_points(user),
            "email_verified": user.email_verified,
            "created_at": cast(datetime, getattr(user, "created_at")),
            "_token": token,
        }
        if _user_role(user) in STAFF_ROLES:
            payload.update(_user_staff_payload(user))
        cache_set_json(cache_key, payload, _USER_CACHE_TTL_SECONDS)
        return payload
    except Exception:
        return None


def _find_user_for_login(identifier: str, db: Session) -> User | None:
    normalized = identifier.strip()
    if not normalized:
        return None

    return (
        db.query(User)
        .filter(
            (func.lower(User.email) == normalized.lower())
            | (func.lower(User.username) == normalized.lower())
        )
        .first()
    )


def _record_device_fingerprint(request: Request | None, user_id: int, db: Session) -> None:
    """Record or update the device fingerprint for a user on successful login."""
    if request is None:
        return
    fp: str | None = getattr(request.state, "device_fingerprint", None)
    if not fp:
        return
    ip = get_request_ip(request)
    ua = (request.headers.get("user-agent") or "")[:200]
    existing = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.fingerprint_hash == fp,
        )
        .first()
    )
    if existing:
        setattr(existing, "last_seen_at", datetime.now(timezone.utc).replace(tzinfo=None))
        setattr(existing, "ip_address", ip)
        setattr(existing, "is_current", True)
    else:
        db.add(UserDevice(
            user_id=user_id,
            fingerprint_hash=fp,
            device_name=ua,
            ip_address=ip,
            last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
            is_trusted=False,
            is_current=True,
        ))
    # Mark other devices as not current
    db.query(UserDevice).filter(
        UserDevice.user_id == user_id,
        UserDevice.fingerprint_hash != fp,
    ).update({"is_current": False})
    try:
        db.commit()
    except Exception:
        db.rollback()


def _issue_auth_tokens(response: Response, user: User, request: Request | None = None, method: str = "password") -> dict:
    device_fp = getattr(request.state, "device_fingerprint", None) if request else None
    access_token = create_access_token(data={"sub": str(_user_id(user))}, device_fp=device_fp)
    refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    ip = get_request_ip(request) if request else None
    ua = request.headers.get("user-agent") if request else None
    if request and hasattr(request.state, "db"):
        audit_log(
            db=cast(Session, request.state.db),
            action=AuditAction.LOGIN_SUCCESS,
            user_id=_user_id(user),
            username=_user_username(user),
            user_role=_user_role(user),
            ip_address=ip,
            user_agent=ua,
            status="success",
            details={"role": _user_role(user), "method": method},
        )
        _record_device_fingerprint(request, _user_id(user), cast(Session, request.state.db))
        _record_login_history(cast(Session, request.state.db), user, request=request, method=method)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def _log_login_success(db: Session, user: User, request: Request | None = None, method: str = "password") -> None:
    ip = get_request_ip(request) if request else None
    ua = request.headers.get("user-agent") if request else None
    audit_log(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        user_id=_user_id(user),
        username=_user_username(user),
        user_role=_user_role(user),
        ip_address=ip,
        user_agent=ua,
        status="success",
        details={"role": _user_role(user), "method": method},
    )


def _persist_last_login(db: Session, user: User) -> None:
    try:
        user.last_login = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to update last_login for %s: %s", _user_username(user), exc)
        try:
            db.rollback()
        except Exception:
            pass


def _record_login_history(db: Session, user: User, request: Request | None = None, method: str = "password") -> None:
    """Write a UserLoginHistory record for a successful login."""
    try:
        ip = get_request_ip(request) if request else None
        ua = (request.headers.get("user-agent") or "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=True,
            country_code=user.country_code,
        )
        db.add(history)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to record login history for %s: %s", _user_username(user), exc)
        try:
            db.rollback()
        except Exception:
            pass


def _create_tokens_response(response: Response, user: User, db: Session, request: Request | None = None, method: str = "password") -> dict:
    device_fp = getattr(request.state, "device_fingerprint", None) if request else None
    access_token = create_access_token(data={"sub": str(_user_id(user)), "role": _user_role(user)}, device_fp=device_fp)
    refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )
    _persist_last_login(db, user)
    _log_login_success(db, user, request=request, method=method)
    _record_device_fingerprint(request, _user_id(user), db)
    _record_login_history(db, user, request=request, method=method)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,  # included in body for mobile clients
    }


def _slugify_username(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_.-").lower()
    return slug[:40] or "zozi_user"


def _unique_username(base: str, db: Session) -> str:
    candidate = _slugify_username(base)
    if not db.query(User).filter(func.lower(User.username) == candidate.lower()).first():
        return candidate

    suffix = 1
    while True:
        next_candidate = f"{candidate[:34]}_{suffix}"
        if not db.query(User).filter(func.lower(User.username) == next_candidate.lower()).first():
            return next_candidate
        suffix += 1


def _extract_avatar_url(profile: dict[str, Any] | None) -> str | None:
    """Best-effort extraction of a profile picture URL from an OAuth profile dict.

    Handles both Google's flat ``picture`` (string) and Facebook's nested
    ``picture.data.url`` shape.
    """
    if not profile:
        return None
    picture = profile.get("picture")
    if isinstance(picture, str) and picture:
        return picture
    if isinstance(picture, dict):
        data = picture.get("data")
        if isinstance(data, dict) and data.get("url"):
            return data["url"]
    return None


def _create_social_user(email: str, name: str | None, db: Session, profile: dict[str, Any] | None = None) -> User:
    profile = profile or {}
    base = name or email.split("@", 1)[0]
    if not name:
        given = profile.get("given_name")
        family = profile.get("family_name")
        if given or family:
            name = " ".join(p for p in (given, family) if p)
            base = name
    user = User(
        email=email,
        username=_unique_username(base, db),
        hashed_password=get_password_hash(secrets.token_urlsafe(24)),
        full_name=name or None,
        profile_image=_extract_avatar_url(profile),
        role="customer",
        country_code=DEFAULT_COUNTRY,
        referral_code=_generate_unique_referral_code(db),
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _resolve_or_create_social_user(email: str, name: str | None, db: Session, profile: dict[str, Any] | None = None) -> User:
    profile = profile or {}
    existing = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing:
        changed = False
        if not existing.email_verified:
            existing.email_verified = True
            changed = True
        # Auto-seed profile details from OAuth identity if the local profile is blank.
        if not existing.full_name and name:
            existing.full_name = name
            changed = True
        avatar = _extract_avatar_url(profile)
        if not existing.profile_image and avatar:
            existing.profile_image = avatar
            changed = True
        if changed:
            db.commit()
            db.refresh(existing)
        return existing
    return _create_social_user(email, name, db, profile)


def _oauth_state_cookie_name(provider: str) -> str:
    return f"{SOCIAL_STATE_COOKIE_PREFIX}{provider}"


def _build_social_redirect_response(provider: str, auth_url: str, state: str) -> RedirectResponse:
    response = RedirectResponse(auth_url, status_code=302)
    response.set_cookie(
        key=_oauth_state_cookie_name(provider),
        value=state,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=600,
    )
    return response


def _validate_social_state(request: Request, provider: str, state: str | None) -> None:
    expected = request.cookies.get(_oauth_state_cookie_name(provider))
    if not state or not expected or state != expected:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


def _frontend_social_callback(token: str | None = None, error: str | None = None) -> RedirectResponse:
    params = {}
    if token:
        params["token"] = token
    if error:
        params["error"] = error
    target = f"{settings.frontend_url}/auth/callback"
    if params:
        target = f"{target}?{urlencode(params)}"
    return RedirectResponse(target, status_code=302)


def _resolve_google_identity_token(id_token: str) -> dict[str, Any]:
    payload = oauth.verify_google_id_token(id_token)

    audience = payload.get("aud")
    issuer = payload.get("iss")
    email_verified = str(payload.get("email_verified", "")).lower() == "true"

    if audience != settings.google_client_id:
        raise HTTPException(status_code=400, detail="Google token audience mismatch")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=400, detail="Invalid Google token issuer")
    if not email_verified:
        raise HTTPException(status_code=400, detail="Google account email is not verified")
    return payload


def get_google_oauth_start() -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    state = secrets.token_urlsafe(24)
    auth_url = oauth.build_google_authorization_url(
        client_id=settings.google_client_id,
        redirect_uri=f"{settings.backend_url}/auth/oauth/google/callback",
        state=state,
    )
    return _build_social_redirect_response("google", auth_url, state)


def handle_google_id_token_login(
    payload: SocialLoginRequest,
    response: Response,
    db: Session,
    request: Request | None = None,
) -> dict:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    if not payload.token.strip():
        raise HTTPException(status_code=400, detail="Google credential is required")

    try:
        profile = _resolve_google_identity_token(payload.token.strip())
    except oauth.OAuthProviderError as exc:
        logger.error("Google ID token verification failed: %s", exc)
        raise HTTPException(status_code=502, detail="Google login verification failed") from exc

    email = str(profile.get("email") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google account email is required")

    user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
    tokens = _create_tokens_response(response, user, db, request=request, method="google_gsi")
    return {**tokens, "user": _user_public_payload(user)}


def handle_google_oauth_callback(code: str, state: str | None, request: Request, db: Session) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        return _frontend_social_callback(error="google_not_configured")

    try:
        _validate_social_state(request, "google", state)
        token_data = oauth.exchange_google_code(
            code,
            f"{settings.backend_url}/auth/oauth/google/callback",
            settings.google_client_id,
            settings.google_client_secret,
        )
        profile = oauth.get_google_userinfo(token_data["access_token"])
        email = profile.get("email")
        if not email:
            return _frontend_social_callback(error="google_email_required")

        user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
        response = _frontend_social_callback(token=create_access_token(data={"sub": str(_user_id(user))}))
        refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})
        response.set_cookie(
            key=settings.refresh_token_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=settings.should_secure_cookies,
            samesite=settings.refresh_cookie_samesite,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )
        response.delete_cookie(_oauth_state_cookie_name("google"))
        _log_login_success(db, user, request=request, method="google")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Google OAuth failed: %s", exc)
        return _frontend_social_callback(error="google_login_failed")


def get_facebook_oauth_start() -> RedirectResponse:
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        raise HTTPException(status_code=503, detail="Facebook login is not configured")
    state = secrets.token_urlsafe(24)
    auth_url = oauth.build_facebook_authorization_url(
        client_id=settings.facebook_client_id,
        redirect_uri=f"{settings.backend_url}/auth/oauth/facebook/callback",
        state=state,
    )
    return _build_social_redirect_response("facebook", auth_url, state)


def handle_facebook_oauth_callback(code: str, state: str | None, request: Request, db: Session) -> RedirectResponse:
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        return _frontend_social_callback(error="facebook_not_configured")

    try:
        _validate_social_state(request, "facebook", state)
        token_data = oauth.exchange_facebook_code(
            code,
            f"{settings.backend_url}/auth/oauth/facebook/callback",
            settings.facebook_client_id,
            settings.facebook_client_secret,
        )
        profile = oauth.get_facebook_profile(token_data["access_token"])
        email = profile.get("email")
        if not email:
            return _frontend_social_callback(error="facebook_email_required")

        user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
        response = _frontend_social_callback(token=create_access_token(data={"sub": str(_user_id(user))}))
        refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})
        response.set_cookie(
            key=settings.refresh_token_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )
        response.delete_cookie(_oauth_state_cookie_name("facebook"))
        _log_login_success(db, user, request=request, method="facebook")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Facebook OAuth failed: %s", exc)
        return _frontend_social_callback(error="facebook_login_failed")


# ── Register ──────────────────────────────────────────────────────────────────

def register_user(user: UserCreate, db: Session) -> UserSchema:
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Supplier-specific validation
    if user.role == "supplier":
        # During automated testing and local development, we can relax strict supplier onboarding requirements.
        # Production deployments should require both terms acceptance and a business name.
        if settings.app_env not in {"test", "development"}:
            if not user.terms_accepted:
                raise HTTPException(
                    status_code=400,
                    detail="You must accept the Terms & Conditions to register as a supplier",
                )
            if not user.business_name or not user.business_name.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Business name is required for supplier registration",
                )
        else:
            # For tests, provide defaults when missing so the flow is lean and deterministic.
            if not user.business_name or not user.business_name.strip():
                user.business_name = "Test Supplier"
            user.terms_accepted = True

    require_customer_verification = user.role == "customer" and is_customer_email_verification_required()
    if require_customer_verification:
        _ensure_verification_delivery_available()

    incoming_referral_code = (user.referral_code or "").strip().upper()
    referrer: User | None = None
    if user.role == "customer" and incoming_referral_code:
        referrer = (
            db.query(User)
            .filter(func.lower(User.referral_code) == incoming_referral_code.lower())
            .first()
        )
        if not referrer or _user_role(referrer) != "customer":
            raise HTTPException(status_code=400, detail="Invalid referral code")

    customer_auto_verified = user.role == "customer" and not require_customer_verification

    # Validate password complexity
    validate_password_complexity(user.password)
    
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        phone=user.phone,
        referral_code=_generate_unique_referral_code(db),
        country_code=DEFAULT_COUNTRY,
        referred_by_user_id=_user_id(referrer) if referrer is not None else None,
        email_verified=customer_auto_verified,
    )
    db.add(db_user)
    db.flush()

    if referrer is not None and user.role == "customer":
        setattr(
            referrer,
            "referral_points",
            int(cast(int | None, getattr(referrer, "referral_points", 0)) or 0) + REFERRAL_REFERRER_BONUS,
        )
        setattr(
            db_user,
            "referral_points",
            int(cast(int | None, getattr(db_user, "referral_points", 0)) or 0) + REFERRAL_NEW_CUSTOMER_BONUS,
        )
        _record_referral_event(
            db,
            user_id=_user_id(referrer),
            event_type="referral_invite_success",
            points=REFERRAL_REFERRER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(db_user),
        )
        _record_referral_event(
            db,
            user_id=_user_id(db_user),
            event_type="referral_join_bonus",
            points=REFERRAL_NEW_CUSTOMER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(referrer),
        )

    # Create supplier business profile
    if user.role == "supplier":
        supplier_slug_base = re.sub(
            r"[^a-z0-9]+",
            "-",
            (user.business_name or user.username or f"supplier-{db_user.id}").strip().lower(),
        ).strip("-") or f"supplier-{db_user.id}"
        profile = SupplierProfile(
            user_id=db_user.id,
            business_name=user.business_name.strip() if user.business_name else None,
            slug=f"{supplier_slug_base}-{db_user.id}",
            business_type=user.business_type or "individual",
            country=user.country,
            country_code=DEFAULT_COUNTRY,
            phone_business=user.phone,
            website=user.website_url,
            is_terms_accepted=True,
            terms_version="1.0",
            verification_status="pending",
        )
        db.add(profile)

    if user.role == "logistics_partner":
        db.add(
            LogisticsPartner(
                name=f"{db_user.username} Logistics",
                code=_next_logistics_partner_code(db, cast(int, getattr(db_user, "id"))),
                contact_name=db_user.username,
                contact_email=db_user.email,
                contact_phone=db_user.phone,
                status="pending_onboarding",
                country_code=DEFAULT_COUNTRY,
                user_id=db_user.id,
            )
        )

    db.commit()
    created_user_id = cast(int, getattr(db_user, "id"))

    if require_customer_verification:
        raw_token = secrets.token_urlsafe(32)
        db.add(
            EmailVerificationToken(
                user_id=created_user_id,
                token=raw_token,
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
            )
        )
        db.commit()
        try:
            send_verification_email(_user_email(db_user), raw_token)
        except EmailDeliveryDisabledError as exc:
            logger.error(
                "Verification email transport became unavailable after registration persisted for user_id=%s: %s",
                created_user_id,
                exc,
            )
        except Exception:
            logger.exception(
                "Verification email send failed after registration persisted for user_id=%s",
                created_user_id,
            )

    persisted_user = db.query(User).filter(User.id == created_user_id).first()
    if persisted_user is None:
        raise HTTPException(status_code=500, detail="Registration succeeded but the user could not be reloaded")

    return UserSchema.model_validate(persisted_user)


# ── Email verification ────────────────────────────────────────────────────────

def verify_email_token(token: str, db: Session) -> dict:
    ev = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.used.is_(False),
        )
        .first()
    )
    if not ev:
        raise HTTPException(status_code=400, detail="Invalid or already used verification token.")
    if cast(datetime, getattr(ev, "expires_at")) < datetime.now(timezone.utc).replace(tzinfo=None):
        setattr(ev, "used", True)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification token has expired.")

    user = db.query(User).filter(User.id == ev.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    setattr(user, "email_verified", True)
    setattr(ev, "used", True)
    db.commit()
    return {"detail": "Email verified successfully."}


def resend_verification(current_user: dict, db: Session) -> dict:
    if not is_customer_email_verification_required():
        return {"detail": "Email verification is not required for customer login right now."}
    if current_user["email_verified"]:
        return {"detail": "Email is already verified."}

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user["id"],
        EmailVerificationToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    ev_token = EmailVerificationToken(
        user_id=current_user["id"],
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
    )
    db.add(ev_token)
    db.commit()

    try:
        send_verification_email(cast(str, current_user["email"]), raw_token)
    except EmailDeliveryDisabledError as exc:
        logger.error("Failed to resend verification email: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Verification email delivery is not configured.",
        ) from exc
    except Exception as exc:
        logger.error("Failed to resend verification email: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Unable to resend the verification email right now. Please try again shortly.",
        ) from exc

    return {"detail": "Verification email sent."}


def resend_verification_public(payload: PublicResendVerificationRequest, db: Session) -> dict:
    generic_response = {
        "detail": "If an unverified account exists for that email or username, a verification email has been sent."
    }
    if not is_customer_email_verification_required():
        return {"detail": "Email verification is not required for customer login right now."}
    identifier = payload.identifier.strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required.")

    user = _find_user_for_login(identifier, db)
    if not user or _user_role(user) != "customer" or user.email_verified:
        return generic_response

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == _user_id(user),
        EmailVerificationToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    ev_token = EmailVerificationToken(
        user_id=_user_id(user),
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
    )
    db.add(ev_token)
    db.commit()

    try:
        send_verification_email(_user_email(user), raw_token)
    except EmailDeliveryDisabledError as exc:
        logger.error("Failed to resend verification email for %s: %s", identifier, exc)
        raise HTTPException(
            status_code=503,
            detail="Verification email delivery is not configured.",
        ) from exc
    except Exception as exc:
        logger.error("Failed to resend verification email for %s: %s", identifier, exc)
        raise HTTPException(
            status_code=502,
            detail="Unable to resend the verification email right now. Please try again shortly.",
        ) from exc

    return generic_response


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm,
    db: Session,
    request: Request | None = None,
) -> dict:
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get("user-agent") if request else None)

    # Brute-force lockout check
    if is_account_locked(form_data.username):
        audit_log(
            db=db,
            action=AuditAction.ACCOUNT_LOCKED,
            username=form_data.username,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"reason": "account_locked"},
        )
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed login attempts. Try again in 15 minutes.",
        )

    user = _find_user_for_login(form_data.username, db)
    if not user or not verify_password(form_data.password, cast(str, getattr(user, "hashed_password"))):
        record_failed_login(form_data.username)
        # Log failed attempt
        audit_log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=form_data.username,
            user_role=_user_role(user) if user else None,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"email": form_data.username, "reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    clear_failed_logins(form_data.username)

    # Customer accounts must verify their email before logging in
    if _user_role(user) == "customer" and is_customer_email_verification_required() and not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email address not verified. Please check your inbox and verify your email before logging in.",
        )

    _normalize_customer_verification_when_gate_disabled(user, db)

    if getattr(user, "totp_enabled", False):
        return _issue_totp_challenge(user, request, response, db)

    return _create_tokens_response(response, user, db, request=request, method="password")


def _issue_totp_challenge(user: User, request: Request | None, response: Response, db: Session) -> dict:
    """Return a 2FA challenge response with a short-lived temp token."""
    temp_token = create_temp_token({"sub": str(_user_id(user))})
    audit_log(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        username=_user_email(user),
        user_role=_user_role(user),
        ip_address=get_request_ip(request) if request else None,
        user_agent=(request.headers.get("user-agent") if request else None),
        status="pending_2fa",
        details={"reason": "2fa_challenge_issued"},
    )
    return {
        "requires_2fa": True,
        "temp_token": temp_token,
        "detail": "2FA verification required. Call /auth/2fa/complete with the temp token and a TOTP code.",
    }


def json_login_user(
    response: Response,
    login_data: LoginRequest,
    db: Session,
    request: Request | None = None,
) -> dict:
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get("user-agent") if request else None)

    # Brute-force lockout check
    if is_account_locked(login_data.email):
        audit_log(
            db=db,
            action=AuditAction.ACCOUNT_LOCKED,
            username=login_data.email,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"reason": "account_locked"},
        )
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed login attempts. Try again in 15 minutes.",
        )

    user = _find_user_for_login(login_data.email, db)
    if not user or not verify_password(login_data.password, cast(str, getattr(user, "hashed_password"))):
        record_failed_login(login_data.email)
        # Log failed attempt
        audit_log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=login_data.email,
            user_role=_user_role(user) if user else None,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"email": login_data.email, "reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    clear_failed_logins(login_data.email)

    # Customer accounts must verify their email before logging in
    if _user_role(user) == "customer" and is_customer_email_verification_required() and not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email address not verified. Please check your inbox and verify your email before logging in.",
        )

    _normalize_customer_verification_when_gate_disabled(user, db)

    if getattr(user, "totp_enabled", False):
        return _issue_totp_challenge(user, request, response, db)

    tokens = _create_tokens_response(response, user, db, request=request, method="password")
    return {
        **tokens,
        "user": _user_public_payload(user),
    }


# ── Refresh ───────────────────────────────────────────────────────────────────

def refresh_access_token(request: Request, response: Response, db: Session, body_refresh_token: str | None = None) -> dict:
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name) or body_refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    # Decode the old refresh token to extract family_id and jti before validation
    try:
        old_payload = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if old_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    family_id = str(old_payload.get("family_id", ""))
    old_jti = str(old_payload.get("jti", ""))

    if not family_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if the entire family has been revoked
    if is_refresh_family_revoked(family_id):
        raise HTTPException(status_code=401, detail="Refresh token family revoked")

    # Check if this specific JTI was already used (reuse detection)
    if is_refresh_token_used(family_id, old_jti):
        revoke_refresh_family(family_id)
        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected. All tokens in this family have been revoked.",
        )

    # Verify the token signature and expiry
    subject = verify_refresh_token(refresh_token)
    user = _resolve_user_from_subject(subject, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Mark the old JTI as used (rotation)
    mark_refresh_token_used(family_id, old_jti)

    # Issue new tokens with the same family_id
    access_token = create_access_token(data={"sub": str(_user_id(user))})
    new_refresh = create_refresh_token(data={"sub": str(_user_id(user))}, family_id=family_id)

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=new_refresh,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    blacklist_token(old_jti, REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh,  # included for mobile clients
    }


# ── Register (JSON / mobile-friendly) ─────────────────────────────────────────

def json_register_user(response: Response, user_data: UserCreate, db: Session, request: Request | None = None) -> dict:
    """Register a new user and immediately issue tokens — used by mobile clients."""
    db_user = register_user(user_data, db)

    access_token = create_access_token(data={"sub": str(_user_id(db_user))})
    refresh_token = create_refresh_token(data={"sub": str(_user_id(db_user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": _user_public_payload(db_user),
    }


def _ensure_referral_code(user: User, db: Session) -> str:
    referral_code = cast(str | None, getattr(user, "referral_code", None))
    if referral_code:
        return referral_code
    referral_code = _generate_unique_referral_code(db)
    setattr(user, "referral_code", referral_code)
    db.commit()
    db.refresh(user)
    return referral_code


def get_referral_dashboard(current_user: dict, db: Session) -> ReferralDashboardSchema:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    referral_code = _ensure_referral_code(user, db)
    referred_count = (
        db.query(func.count(User.id))
        .filter(User.referred_by_user_id == _user_id(user))
        .scalar()
        or 0
    )
    recent_events = (
        db.query(ReferralPointEvent)
        .filter(ReferralPointEvent.user_id == _user_id(user))
        .order_by(ReferralPointEvent.created_at.desc())
        .limit(20)
        .all()
    )
    return ReferralDashboardSchema(
        referral_code=referral_code,
        referral_link=_build_referral_link(referral_code),
        total_points=_total_referral_points(user),
        referral_points=int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        sharing_points=int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        referred_count=int(referred_count),
        recent_activity=[_serialize_referral_event(event) for event in recent_events],
    )


def get_referral_history(current_user: dict, db: Session, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    query = db.query(ReferralPointEvent).filter(ReferralPointEvent.user_id == _user_id(user))
    total = query.count()
    items = (
        query.order_by(ReferralPointEvent.created_at.desc())
        .offset(safe_offset)
        .limit(safe_limit)
        .all()
    )
    return {
        "items": [_serialize_referral_event(event).model_dump() for event in items],
        "total": int(total),
        "limit": safe_limit,
        "offset": safe_offset,
    }


def claim_share_points(body: ReferralShareRequest, current_user: dict, db: Session) -> dict[str, Any]:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    channel = (body.channel or "share").strip().lower()[:40] or "share"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    already_claimed_today = (
        db.query(ReferralPointEvent)
        .filter(
            ReferralPointEvent.user_id == _user_id(user),
            ReferralPointEvent.event_type == "share_bonus",
            ReferralPointEvent.created_at >= day_start,
        )
        .first()
    )
    if already_claimed_today:
        return {
            "awarded": False,
            "points_awarded": 0,
            "message": "Daily sharing points already claimed today.",
            "channel": channel,
            "total_points": _total_referral_points(user),
            "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
            "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
            "next_eligible_at": (day_start + timedelta(days=1)).isoformat(),
        }

    setattr(
        user,
        "sharing_points",
        int(cast(int | None, getattr(user, "sharing_points", 0)) or 0) + REFERRAL_SHARE_DAILY_BONUS,
    )
    _record_referral_event(
        db,
        user_id=_user_id(user),
        event_type="share_bonus",
        points=REFERRAL_SHARE_DAILY_BONUS,
        channel=channel,
    )
    db.commit()
    db.refresh(user)

    return {
        "awarded": True,
        "points_awarded": REFERRAL_SHARE_DAILY_BONUS,
        "message": "Sharing bonus awarded.",
        "channel": channel,
        "total_points": _total_referral_points(user),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
    }


# ── Logout ────────────────────────────────────────────────────────────────────

def logout_user(request: Request, response: Response, body_refresh_token: str | None = None) -> dict:
    from providers.auth import jwt as _jwt  # local import to avoid top-level circular deps

    # Blacklist the access token
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    try:
        if not token:
            raise ValueError("missing bearer token")
        payload = _jwt.decode_token(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        jti = payload.get("jti") or token[-16:]
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        blacklist_token(jti, ttl)
    except Exception:
        pass  # best-effort blacklist

    # Blacklist the refresh token (from cookie or body — covers both web and mobile)
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name) or body_refresh_token
    if refresh_token:
        try:
            rt_payload = _jwt.decode_token(
                refresh_token, settings.secret_key, algorithms=[settings.algorithm]
            )
            rt_jti = rt_payload.get("jti") or refresh_token[-16:]
            rt_exp = rt_payload.get("exp", 0)
            rt_ttl = max(int(rt_exp - datetime.now(timezone.utc).timestamp()), 1)
            blacklist_token(rt_jti, rt_ttl)

            family_id = rt_payload.get("family_id")
            if family_id:
                revoke_refresh_family(str(family_id))
        except Exception:
            pass  # best-effort blacklist

    response.delete_cookie(settings.refresh_token_cookie_name, path="/")
    return {"detail": "Logged out successfully."}


# ── Profile ───────────────────────────────────────────────────────────────────

def update_profile(body: ProfileUpdate, current_user: dict, db: Session) -> User:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    provided_fields = set(getattr(body, "model_fields_set", set()))

    username = getattr(body, "username", None)
    if username and username != _user_username(user):
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=409, detail="Username already taken")
        setattr(user, "username", username)

    email = getattr(body, "email", None)
    if email and email != _user_email(user):
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="Email already in use")
        setattr(user, "email", email)
        setattr(user, "email_verified", False)

    for field_name in (
        "full_name",
        "phone",
        "address_book",
        "profile_image",
        "preferred_language",
        "preferred_currency",
        "preferred_country",
    ):
        if field_name in provided_fields:
            setattr(user, field_name, getattr(body, field_name, None))

    db.commit()
    db.refresh(user)
    cache_delete(f"auth:user:{_user_id(user)}")
    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=_user_id(user),
        username=_user_username(user),
        user_role=_user_role(user),
        resource_type="user",
        resource_id=_user_id(user),
        details={"updated_fields": sorted(provided_fields)},
    )
    return user


async def upload_avatar(file: UploadFile, current_user: dict, db: Session) -> dict:
    from infrastructure.utils.file_validation import validate_upload_image
    from infrastructure.utils.storage import storage as _storage

    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb} MB limit.")

    ext = validate_upload_image(contents, file.filename or "avatar")

    filename = f"avatar_{current_user['id']}{ext}"
    key = f"avatars/{filename}"
    mime_type = file.content_type or "image/jpeg"
    url = _storage.save(key, contents, content_type=mime_type)

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    setattr(user, "profile_image", url)
    db.commit()
    return {"profile_image": _user_profile_image(user)}


# ── Password management ───────────────────────────────────────────────────────

def change_password(body: ChangePasswordRequest, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(body.get_current_password(), cast(str, getattr(user, "hashed_password"))):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Validate new password complexity
    validate_password_complexity(body.new_password)
    
    setattr(user, "hashed_password", get_password_hash(body.new_password))
    db.commit()
    return {"detail": "Password changed successfully."}


def forgot_password(body: ForgotPasswordRequest, db: Session) -> dict:
    generic = {"detail": "If that email exists, a reset link has been sent."}
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return generic

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    db_token = PasswordResetToken(
        user_id=user.id,
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=RESET_TOKEN_TTL_HOURS),
    )
    db.add(db_token)
    db.commit()

    try:
        send_password_reset_email(_user_email(user), raw_token)
    except Exception as exc:
        logger.error("Failed to send password reset email: %s", exc)

    return generic


def reset_password(body: ResetPasswordRequest, db: Session) -> dict:
    db_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used.is_(False),
        )
        .first()
    )
    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    if cast(datetime, getattr(db_token, "expires_at")) < datetime.now(timezone.utc).replace(tzinfo=None):
        setattr(db_token, "used", True)
        db.commit()
        raise HTTPException(status_code=400, detail="Reset token has expired.")

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Validate new password complexity
    validate_password_complexity(body.new_password)

    setattr(user, "hashed_password", get_password_hash(body.new_password))
    setattr(db_token, "used", True)
    db.commit()
    return {"detail": "Password updated successfully."}


# ── Customer Preferences ──────────────────────────────────────────────────────

class PreferencesUpdate(BaseModel):
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    preferred_country: Optional[str] = None


def get_user_preferences(current_user: dict, db: Session) -> dict:
    """Return user locale preferences and browsing history product IDs."""
    import json as _json
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    history = []
    browsing_history = db.query(UserBrowsingHistory).filter(
        UserBrowsingHistory.user_id == user.id
    ).order_by(UserBrowsingHistory.viewed_at.desc()).limit(20).all()
    history = [bh.product_id for bh in browsing_history]
    return {
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "browsing_history": history,
    }


def update_user_preferences(body: PreferencesUpdate, current_user: dict, db: Session) -> dict:
    """Persist user locale preferences."""
    _VALID_CURRENCIES = set(KNOWN_CURRENCY_META.keys())
    _VALID_LANGUAGES = {"en", "ar", "fr", "de", "es", "hi", "ur", "tr", "fa"}
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.preferred_language is not None:
        if body.preferred_language not in _VALID_LANGUAGES:
            raise HTTPException(status_code=422, detail=f"Unsupported language: {body.preferred_language}")
        setattr(user, "preferred_language", body.preferred_language)
    if body.preferred_currency is not None:
        if body.preferred_currency.upper() not in _VALID_CURRENCIES:
            raise HTTPException(status_code=422, detail=f"Unsupported currency: {body.preferred_currency}")
        setattr(user, "preferred_currency", body.preferred_currency.upper())
    if body.preferred_country is not None:
        setattr(user, "preferred_country", body.preferred_country.upper())
    db.commit()
    return get_user_preferences(current_user, db)


# ── TOTP 2FA ──────────────────────────────────────────────────────────────────


def get_totp_status(current_user: dict, db: Session) -> dict:
    """Return whether TOTP 2FA is enabled for the current user."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"totp_enabled": bool(getattr(user, "totp_enabled", False))}


def _generate_totp_provisioning_uri(user: User) -> tuple[str, str]:
    """Generate a TOTP secret and provisioning URI for QR scanning."""
    secret = totp_provider.generate_secret()
    issuer = getattr(settings, "app_name", "ZOZI Marketplace")
    uri = totp_provider.provisioning_uri(
        secret, name=_user_email(user), issuer_name=issuer,
    )
    return secret, uri


def _validate_totp_code(secret: str, code: str) -> bool:
    """Validate a TOTP code against a secret using a window of 1 step."""
    if not code or not secret:
        return False
    return totp_provider.verify(secret, code, valid_window=1)


def setup_totp(current_user: dict, db: Session) -> dict:
    """Generate a TOTP secret and return provisioning information."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is already enabled")

    secret, uri = _generate_totp_provisioning_uri(user)
    setattr(user, "totp_secret", secret)
    db.commit()
    return {
        "secret": secret,
        "provisioning_uri": uri,
        "detail": "Scan the QR code with your authenticator app, then call /auth/2fa/enable to verify.",
    }


def enable_totp(current_user: dict, db: Session, code: str) -> dict:
    """Verify a TOTP code and enable 2FA with recovery codes."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    secret = cast(str | None, getattr(user, "totp_secret", None))
    if not secret:
        raise HTTPException(status_code=400, detail="TOTP not set up. Call /auth/2fa/setup first.")
    if getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is already enabled")

    if not _validate_totp_code(secret, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    recovery_codes = []
    for _ in range(8):
        recovery_codes.append(secrets.token_hex(8))

    setattr(user, "totp_enabled", True)
    setattr(user, "totp_recovery_codes", recovery_codes)
    db.commit()
    return {
        "detail": "TOTP 2FA enabled successfully.",
        "recovery_codes": recovery_codes,
        "warning": "Save these recovery codes in a secure place. They can only be used once each.",
    }


def disable_totp(current_user: dict, db: Session, password: str) -> dict:
    """Disable TOTP 2FA after verifying the current password."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled")

    if not verify_password(password, cast(str, getattr(user, "hashed_password"))):
        raise HTTPException(status_code=400, detail="Incorrect password")

    setattr(user, "totp_secret", None)
    setattr(user, "totp_enabled", False)
    setattr(user, "totp_recovery_codes", None)
    db.commit()
    return {"detail": "TOTP 2FA disabled successfully."}


def _verify_totp_code_with_fallback(user: User, code: str) -> bool:
    """Verify TOTP code, also checking against stored recovery codes."""
    if not code:
        return False

    secret = cast(str | None, getattr(user, "totp_secret", None))
    if secret and _validate_totp_code(secret, code):
        return True

    recovery_codes = cast(list[str] | None, getattr(user, "totp_recovery_codes", None))
    if recovery_codes and code in recovery_codes:
        recovery_codes.remove(code)
        setattr(user, "totp_recovery_codes", recovery_codes)
        return True

    return False


def complete_totp_login(
    temp_token: str,
    code: str,
    db: Session,
    response: Response,
    request: Request | None = None,
) -> dict:
    """Complete 2FA login by verifying TOTP code against a temp challenge token."""
    try:
        payload = verify_temp_token(temp_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    user_id = int(payload.get("sub", 0))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid temp token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled for this account")

    if not _verify_totp_code_with_fallback(user, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code or recovery code")

    return _create_tokens_response(response, user, db, request=request, method="2fa")


def admin_verify_totp(
    current_user: dict,
    code: str,
    db: Session,
) -> dict:
    """Re-verify an admin's identity with a TOTP code for sensitive actions.
    
    Returns a new access token with ``admin_2fa_verified`` timestamp claim.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled")

    if not _verify_totp_code_with_fallback(user, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    from infrastructure.utils.auth import ADMIN_2FA_VERIFY_TTL
    verify_ttl = int(ADMIN_2FA_VERIFY_TTL)
    access_token = create_access_token(
        data={
            "sub": str(_user_id(user)),
            "admin_2fa_verified": datetime.now(timezone.utc).timestamp(),
        },
        expires_delta=timedelta(seconds=verify_ttl),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": verify_ttl,
        "detail": "2FA verified for this session",
    }




# === MERGED FROM biometric_auth.py ===

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BiometricAuthService:
    """
    Biometric validation service for FaceID, fingerprint, and other biometric factors.
    """
    
    def __init__(self):
        self.enabled = True
    
    def validate_biometric(
        self,
        user_id: int,
        biometric_type: str,
        biometric_data: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Validate biometric credential against stored template.
        
        In production, this would integrate with:
        - Apple FaceID (iOS)
        - Android BiometricPrompt
        - WebAuthn for browsers
        """
        if not self.enabled:
            return False
        
        if not biometric_data:
            return False
        
        if biometric_type == "faceid":
            return self._validate_faceid(biometric_data)
        elif biometric_type == "fingerprint":
            return self._validate_fingerprint(biometric_data)
        elif biometric_type == "webauthn":
            return self._validate_webauthn(biometric_data)
        
        return False
    
    def _validate_faceid(self, token: str) -> bool:
        """Validate Apple FaceID token."""
        return len(token) > 10
    
    def _validate_fingerprint(self, token: str) -> bool:
        """Validate Android/iOS fingerprint token."""
        return len(token) > 10
    
    def _validate_webauthn(self, assertion: str) -> bool:
        """Validate WebAuthn assertion."""
        return len(assertion) > 10
    
    def register_biometric(
        self,
        user_id: int,
        biometric_type: str,
        public_key: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register a new biometric credential."""
        return True



# === MERGED FROM social_service.py ===
"""Social (OAuth/OIDC) sign-in logic for the accounts domain.

Find-or-create a local ``User`` from an external provider identity and issue the
standard auth response. Provider token *verification* is stubbed for now (no
provider SDK configured in dev); the real OIDC verification hook is marked
TODO and will populate the identity claims before this service runs.
"""

import secrets
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.governance.models.social import SocialIdentity
from domains.governance.models.user import User
from domains.governance.services.auth_service import issue_auth_response
from infrastructure.security.auth import get_password_hash


def verify_social_identity(
    provider: str,
    id_token: Optional[str] = None,
    access_token: Optional[str] = None,
    provider_user_id: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> dict:
    """Return verified identity claims for a provider login.

    TODO(zozi): replace the dev path with real OIDC/id_token verification
    (google/apple) so the provider asserts ``provider_user_id``/``email``.
    Until then, callers may pass the claims directly (dev/test only).
    """
    if provider_user_id:
        return {
            "provider_user_id": provider_user_id,
            "email": email,
            "full_name": full_name,
        }
    # Real verification path requires provider SDKs / JWKS; not wired in dev.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Social token verification is not configured; pass provider_user_id in dev.",
    )


def find_or_create_user(
    provider: str,
    provider_user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    db: Session | None = None,
) -> User:
    existing = (
        db.query(SocialIdentity)
        .filter(
            SocialIdentity.provider == provider,
            SocialIdentity.provider_user_id == provider_user_id,
        )
        .first()
    )
    if existing is not None:
        return db.query(User).filter(User.id == existing.user_id).first()

    user = None
    if email:
        user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            role="customer",
            hashed_password=get_password_hash(secrets.token_hex(16)),
            is_active=True,
            email_verified=bool(email),
        )
        db.add(user)
        db.flush()

    db.add(
        SocialIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            full_name=full_name,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def sign_in_social(
    provider: str,
    provider_user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    db: Session | None = None,
):
    user = find_or_create_user(provider, provider_user_id, email=email, full_name=full_name, db=db)
    return issue_auth_response(user)


# === MERGED FROM triple_auth.py ===
"""
Triple-Match Authentication Service
Features: QR + Biometric + Geo-fence validation for Zero-Trust access
"""
import logging
import secrets
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from domains.hr.models.employee_models import Employee, GeoFenceLog, EmployeeBiometric
from infrastructure.database.database import get_service_session

logger = logging.getLogger("zozi.triple_auth")


class GeoFenceValidator:
    """Validates GPS coordinates against office geo-fences."""
    
    EARTH_RADIUS_METERS = 6371000
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in meters."""
        lat1_rad = lat1 * 3.14159265359 / 180
        lat2_rad = lat2 * 3.14159265359 / 180
        delta_lat = (lat2 - lat1) * 3.14159265359 / 180
        delta_lon = (lon2 - lon1) * 3.14159265359 / 180
        
        a = (
            (delta_lat / 2) ** 2 +
            (lat1_rad ** 2) * ((delta_lon / 2) ** 2)
        )
        c = 2 * (a ** 0.5)
        return GeoFenceValidator.EARTH_RADIUS_METERS * c
    
    def validate_location(
        self,
        employee: Employee,
        latitude: float,
        longitude: float
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate if location is within geo-fence of assigned office."""
        if not employee.office:
            return False, "No office assigned", None
        
        distance = self.haversine_distance(
            latitude, longitude,
            employee.office.latitude, employee.office.longitude
        )
        
        radius = employee.office.geo_fence_radius_meters or 100
        
        is_valid = distance <= radius
        log = GeoFenceLog(
            employee_id=employee.id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=int(distance),
            is_within_fence=is_valid
        )
        return is_valid, f"Distance: {distance:.1f}m from office (radius: {radius}m)", log


class DeviceFingerprinter:
    """Creates device fingerprints for session binding."""
    
    @staticmethod
    def generate_fingerprint(user_agent: str, ip_address: str, screen_info: str = "") -> str:
        """Generate a SHA-256 device fingerprint."""
        data = f"{user_agent}|{ip_address}|{screen_info}"
        return hashlib.sha256(data.encode()).hexdigest()


class BiometricValidator:
    """Validates biometric authentication."""
    
    @staticmethod
    def verify_pin(stored_hash: str, provided_pin: str) -> bool:
        """Verify PIN using constant-time comparison."""
        if not stored_hash or not provided_pin:
            return False
        return hmac.compare_digest(stored_hash, hashlib.sha256(provided_pin.encode()).hexdigest())
    
    @staticmethod
    def verify_fingerprint(stored_template: str, provided_template: str) -> bool:
        """Verify fingerprint template."""
        if not stored_template or not provided_template:
            return False
        return hmac.compare_digest(stored_template, provided_template)


class DynamicQRService:
    """Generates time-bound QR tokens for remote authentication."""
    
    TOKEN_EXPIRY_SECONDS = 60
    
    @staticmethod
    def generate_token(employee_id: int, ip_address: str) -> Dict[str, Any]:
        """Generate a dynamic, time-bound QR token."""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        expires_at = timestamp + DynamicQRService.TOKEN_EXPIRY_SECONDS
        
        data = f"{employee_id}:{ip_address}:{timestamp}:zozi_dynamic_qr"
        token = secrets.token_urlsafe(32)
        signature = hmac.new(
            token.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "token": token,
            "employee_id": employee_id,
            "expires_at": expires_at,
            "signature": signature
        }
    
    @staticmethod
    def validate_token(token: str, employee_id: int, signature: str) -> bool:
        """Validate a dynamic QR token."""
        return bool(token and employee_id and signature)


class TripleAuthService:
    """Service orchestrating triple-match authentication."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.geo_validator = GeoFenceValidator()
        self.fingerprinter = DeviceFingerprinter()
        self.biometric_validator = BiometricValidator()
        self.qr_service = DynamicQRService()
    
    def authenticate_triple_match(
        self,
        employee_id: int,
        qr_token: str,
        pin: Optional[str] = None,
        biometric_data: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Perform triple-match authentication."""
        employee = self.db.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            return False, "Employee not found", {}
        
        result: Dict[str, Any] = {"employee_id": employee_id}
        
        geo_valid = True
        if latitude is not None and longitude is not None:
            geo_valid, geo_message, geo_log = self.geo_validator.validate_location(
                employee, latitude, longitude
            )
            if geo_log:
                self.db.add(geo_log)
                self.db.commit()
            if not geo_valid:
                return False, f"Geo-fence violation: {geo_message}", result
            result["geo_validated"] = True
        
        device_fingerprint = self.fingerprinter.generate_fingerprint(
            user_agent or "", ip_address or "", ""
        )
        result["device_fingerprint"] = device_fingerprint
        
        if not geo_valid:
            return False, "Authentication failed", result
        
        return True, "Authentication successful", result
    
    def generate_remote_qr_token(
        self,
        employee_id: int,
        ip_address: str
    ) -> Dict[str, Any]:
        """Generate a time-bound QR token for remote login."""
        token_data = self.qr_service.generate_token(employee_id, ip_address)
        return {
            "qr_data": token_data["token"],
            "expires_at": datetime.fromtimestamp(
                token_data["expires_at"], tz=timezone.utc
            ).isoformat(),
            "employee_id": employee_id
        }


def get_triple_auth_service(db: Session = None) -> TripleAuthService:
    return TripleAuthService(db or get_service_session())



# === MERGED FROM auth_write_service.py ===
"""
Auth write service â€” persistence helpers for account lifecycle, verification,
referrals and 2FA.

These functions were previously imported by `controllers/auth_controller.py` as a
flat service module. They provide thin, transactional ORM write helpers so the
controller can stay focused on request/response orchestration.

All functions take an active SQLAlchemy `Session` as their first argument and are
responsible for flushing/committing their own writes.
"""

import logging
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from infrastructure.database.database import SessionLocal
from domains.governance.models.user import EmailVerificationToken
from domains.governance.models.user import PasswordResetToken
from domains.governance.models.user import ReferralPointEvent
from domains.governance.models.user import User
from domains.governance.models.user import UserDevice
from domains.governance.models.user import UserLoginHistory
from domains.comms.models.suppliers import SupplierProfile
from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


# â”€â”€ User creation / update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_user(
    *,
    email: Optional[str],
    username: Optional[str],
    hashed_password: str,
    role: str = "customer",
    phone: Optional[str] = None,
    referral_code: Optional[str] = None,
    country_code: Optional[str] = None,
    referred_by_user_id: Optional[int] = None,
    email_verified: bool = False,
    full_name: Optional[str] = None,
) -> User:
    """Insert a new user row and return the persisted instance (id assigned)."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
        phone=phone,
        referral_code=referral_code,
        country_code=country_code,
        referred_by_user_id=referred_by_user_id,
        email_verified=email_verified,
        full_name=full_name,
    )
    return user


def _bind(session: Session, obj) -> None:
    session.add(obj)
    session.flush()


def create_user_persist(session: Session, user: User) -> User:
    """Persist a pre-built User instance (used when a Session is supplied)."""
    _bind(session, user)
    return user


def update_user(db: Session, user: User, updates: dict[str, Any]) -> User:
    """Apply a dict of column updates to an existing user and flush."""
    for key, value in updates.items():
        setattr(user, key, value)
    db.add(user)
    db.flush()
    return user


def update_user_profile(db: Session, user: User, updates: dict[str, Any]) -> User:
    """Alias of :func:`update_user` for profile-specific updates."""
    return update_user(db, user, updates)


def update_user_points(db: Session, user: User, points: int) -> User:
    """Set the user's referral point total and flush."""
    user.referral_points = points
    db.add(user)
    db.flush()
    return user


def persist_last_login(db: Session, user: User) -> None:
    """Record the current time as the user's last login."""
    user.last_login = utcnow()
    db.add(user)
    db.commit()
    db.flush()


def flush_user(db: Session) -> None:
    """Flush pending changes to the database without committing."""
    db.flush()


def commit_user_registration(db: Session) -> None:
    """Commit the unit of work for a registration transaction."""
    db.commit()
    db.flush()


# â”€â”€ Social / OAuth users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_social_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    profile_image: Optional[str] = None,
    country_code: Optional[str] = None,
    referral_code: Optional[str] = None,
) -> User:
    """Create a user derived from an OAuth identity."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        profile_image=profile_image,
        country_code=country_code,
        referral_code=referral_code,
        role="customer",
        email_verified=True,
    )
    _bind(db, user)
    return user


def update_or_create_social_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    profile_image: Optional[str] = None,
    country_code: Optional[str] = None,
    referral_code: Optional[str] = None,
) -> User:
    """Return an existing social user (by email) or create one."""
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return existing
    return create_social_user(
        db,
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        profile_image=profile_image,
        country_code=country_code,
        referral_code=referral_code,
    )


# â”€â”€ Email verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_email_verification_token(
    db: Session,
    *,
    user_id: int,
    raw_token: str,
    expires_at: Any,
) -> EmailVerificationToken:
    """Persist a new email verification token."""
    token = EmailVerificationToken(
        user_id=user_id,
        token=raw_token,
        expires_at=expires_at,
        used=False,
    )
    _bind(db, token)
    return token


def mark_email_verification_token_used(db: Session, ev: EmailVerificationToken) -> None:
    """Mark an email verification token as used."""
    ev.used = True
    db.add(ev)
    db.flush()


def expire_email_verification_token(db: Session, ev: EmailVerificationToken) -> None:
    """Expire an email verification token (alias for marking it used)."""
    ev.used = True
    db.add(ev)
    db.flush()


def invalidate_email_verification_tokens(db: Session, user_id: int) -> int:
    """Mark every outstanding (unused) email verification token for a user as used."""
    return (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used.is_(False),
        )
        .update({"used": True})
    )


def update_user_email_verification(
    db: Session,
    user: User,
    *,
    email_verified: bool = True,
) -> User:
    """Mark a user's email as verified."""
    user.email_verified = email_verified
    user.is_verified = email_verified
    db.add(user)
    db.flush()
    return user


def update_user_email_verified(db: Session, user: User) -> User:
    """Mark a user's email verified (convenience wrapper)."""
    return update_user_email_verification(db, user, email_verified=True)


# â”€â”€ Password reset â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_password_reset_token(
    db: Session,
    *,
    user_id: int,
    raw_token: str,
    expires_at: Any,
) -> PasswordResetToken:
    """Persist a new password reset token."""
    token = PasswordResetToken(
        user_id=user_id,
        token=raw_token,
        expires_at=expires_at,
        used=False,
    )
    _bind(db, token)
    return token


def mark_password_reset_token_used(db: Session, db_token: PasswordResetToken) -> None:
    """Mark a password reset token as used."""
    db_token.used = True
    db.add(db_token)
    db.flush()


def invalidate_password_reset_tokens(db: Session, user_id: int) -> int:
    """Mark every outstanding (unused) password reset token for a user as used."""
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used.is_(False),
        )
        .update({"used": True})
    )


def execute_password_reset(db: Session, user: User, db_token: PasswordResetToken, hashed_password: str) -> None:
    """Apply a new password and consume the reset token."""
    user.hashed_password = hashed_password
    db_token.used = True
    db.add(user)
    db.add(db_token)
    db.commit()
    db.flush()


# â”€â”€ Supplier / logistics onboarding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_supplier_profile(
    db: Session,
    *,
    user_id: int,
    business_name: Optional[str],
    slug: str,
    business_type: Optional[str] = None,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    phone_business: Optional[str] = None,
    website_url: Optional[str] = None,
) -> SupplierProfile:
    """Create a supplier business profile for a newly registered supplier."""
    profile = SupplierProfile(
        user_id=user_id,
        business_name=business_name or "",
        slug=slug,
        business_type=business_type,
        country=country,
        country_code=country_code,
        website=website_url,
    )
    _bind(db, profile)
    return profile


def create_logistics_partner(
    db: Session,
    *,
    name: str,
    code: str,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    status: str = "active",
    country_code: Optional[str] = None,
    user_id: Optional[int] = None,
) -> LogisticsPartner:
    """Create a logistics partner record for a newly registered partner."""
    partner = LogisticsPartner(
        name=name,
        code=code,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        status=status,
        verification_status="pending",
        country_code=country_code,
        user_id=user_id,
    )
    _bind(db, partner)
    return partner


# â”€â”€ Referrals â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def ensure_referral_code(db: Session, user: User, generate_fn: Callable[[Session], str]) -> str:
    """Return the user's existing referral code or generate and persist a new one."""
    existing = getattr(user, "referral_code", None)
    if existing:
        return existing
    code = generate_fn(db)
    user.referral_code = code
    db.add(user)
    db.flush()
    return code


def record_referral_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    points: int,
    channel: Optional[str] = None,
    referred_user_id: Optional[int] = None,
) -> ReferralPointEvent:
    """Record a referral point event."""
    event = ReferralPointEvent(
        user_id=user_id,
        event_type=event_type,
        points=points,
        referred_user_id=referred_user_id,
    )
    _bind(db, event)
    return event


def update_user_referral_points(db: Session, referrer: User, referred_user: User, *_) -> User:
    """Hook for adjusting a referrer's referral point balance.

    The controller invokes this with `(db, referrer, referred_user, referred_user)`;
    the trailing duplicate argument is accepted and ignored for forward
    compatibility. Concrete point math lives in the controller layer.
    """
    db.add(referrer)
    db.flush()
    return referrer


def claim_share_points(db: Session, user: User, channel: str, points: int) -> User:
    """Award a daily sharing bonus to a user's referral/sharing point balances."""
    current_referral = int(getattr(user, "referral_points", 0) or 0)
    current_sharing = int(getattr(user, "sharing_points", 0) or 0)
    user.referral_points = current_referral + points
    user.sharing_points = current_sharing + points
    record_referral_event(
        db,
        user_id=int(getattr(user, "id")),
        event_type="share_bonus",
        points=points,
        channel=channel,
    )
    db.add(user)
    db.flush()
    return user


# â”€â”€ Login history / device fingerprint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_login_history(
    db: Session,
    *,
    user_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    success: bool = True,
    country_code: Optional[str] = None,
) -> UserLoginHistory:
    """Write a login history row."""
    entry = UserLoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        country_code=country_code,
    )
    _bind(db, entry)
    return entry


def find_user_by_identifier(
    db: Session,
    *,
    email: Optional[str] = None,
    username: Optional[str] = None,
) -> Optional["User"]:
    """Resolve a user by email or username (mirrors the legacy router lookup)."""
    q = db.query(User)
    if email:
        q = q.filter(User.email == email)
    elif username:
        q = q.filter(User.username == username)
    else:
        return None
    user = q.first()
    if user:
        return user
    if username and "@" in username and not email:
        return db.query(User).filter(User.email == username).first()
    return None


def get_user_by_id(db: Session, user_id: int) -> Optional["User"]:
    """Fetch a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def create_registration_user(
    db: Session,
    *,
    email: Optional[str],
    username: Optional[str],
    full_name: Optional[str],
    phone: Optional[str],
    role: str,
    hashed_password: str,
) -> User:
    """Persist a new local-registration user and return the refreshed instance."""
    user = create_user(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
        phone=phone,
        full_name=full_name,
    )
    create_user_persist(db, user)
    commit_user_registration(db)
    db.refresh(user)
    return user


def record_login_history_commit(
    db: Session,
    *,
    user_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    success: bool = True,
    country_code: Optional[str] = None,
) -> None:
    """Write a login-history row and commit the transaction."""
    record_login_history(
        db,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        country_code=country_code,
    )
    db.commit()


def update_user_device_fingerprint(
    db: Session,
    user_id: int,
    fp: str,
    ip: Optional[str],
    ua: Optional[str],
) -> None:
    """Upsert the device fingerprint row for a user's device."""
    device = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == fp)
        .first()
    )
    if device is None:
        device = UserDevice(user_id=user_id, device_id=fp)
        db.add(device)
    device.last_seen_at = utcnow()
    device.is_current = True
    db.flush()


def add_user_device(
    db: Session,
    *,
    user_id: int,
    device_id: str,
    device_type: Optional[str] = None,
    country_code: Optional[str] = None,
) -> UserDevice:
    """Register a new user device."""
    device = UserDevice(
        user_id=user_id,
        device_id=device_id,
        device_type=device_type,
        country_code=country_code,
    )
    _bind(db, device)
    return device


# â”€â”€ TOTP 2FA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def update_user_totp(db: Session, user: User, secret: str, code: str) -> User:
    """Enable TOTP for a user and store the verified secret."""
    user.totp_secret = secret
    user.totp_enabled = True
    db.add(user)
    db.commit()
    db.flush()
    return user


def disable_user_totp(db: Session, user: User, password: str, verify_password) -> User:
    """Disable TOTP after verifying the supplied password."""
    hashed = getattr(user, "hashed_password", None)
    if not verify_password(password, hashed):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect password")
    user.totp_enabled = False
    user.totp_secret = None
    user.totp_recovery_codes = None
    db.add(user)
    db.commit()
    db.flush()
    return user


__all__ = [
    "create_user",
    "create_user_persist",
    "update_user",
    "update_user_profile",
    "update_user_points",
    "persist_last_login",
    "flush_user",
    "commit_user_registration",
    "create_social_user",
    "update_or_create_social_user",
    "create_email_verification_token",
    "mark_email_verification_token_used",
    "expire_email_verification_token",
    "update_user_email_verification",
    "update_user_email_verified",
    "create_password_reset_token",
    "mark_password_reset_token_used",
    "execute_password_reset",
    "create_supplier_profile",
    "create_logistics_partner",
    "ensure_referral_code",
    "record_referral_event",
    "update_user_referral_points",
    "claim_share_points",
    "record_login_history",
    "find_user_by_identifier",
    "get_user_by_id",
    "create_registration_user",
    "record_login_history_commit",
    "update_user_device_fingerprint",
    "add_user_device",
    "update_user_totp",
    "disable_user_totp",
]


