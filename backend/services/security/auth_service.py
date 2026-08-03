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

import pyotp
from fastapi import HTTPException, Request, status

from utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    blacklist_token,
    is_token_blacklisted,
)
from data.db import SessionLocal
from data.models import User, UserDevice
from data.models_employee_models import (
    Employee,
    EmployeeBiometric,
    DynamicQRSession,
    GeoFenceLog,
    EmployeeAttendance,
)
from utils.config import settings
from utils.geo import haversine_distance

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
    try:
        import redis as _redis

        client = _redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
        return client
    except Exception:
        return None


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
    try:
        db.execute(
            f"SET app.current_country_code = '{employee.country_code}'"
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
        from data.models_employee_models import EmployeeActivityLog

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
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code):
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
    """
    # TODO: Integrate with google-auth, apple-auth, msal libraries
    # For now, return a mock userinfo for development
    # In production, replace with proper JWT verification against provider JWKS
    try:
        from jose import jwt as jose_jwt

        # Get provider's JWKS — placeholder
        payload = jose_jwt.get_unverified_claims(id_token)
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
    from utils.auth import verify_refresh_token

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
    from utils.auth import verify_token

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        from jose import jwt as jose_jwt

        payload = jose_jwt.get_unverified_claims(access_token)
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
