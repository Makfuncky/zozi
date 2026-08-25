"""Live session tracker — real-time session and device monitoring for accounts.

Tracks active user sessions, device bindings, and detects anomalous patterns
like impossible travel (logins from geographically distant locations in a
short time window).

Wired to:
- infrastructure/redis/ (session cache, presence)
- accounts/models/core.py (UserSession, UserDevice)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from domains.accounts.models.core import UserSession
from domains.accounts.models.user import User, UserDevice, UserLoginHistory

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

SESSION_CACHE_TTL_SECONDS = 300  # 5 minutes
IMPOSSIBLE_TRAVEL_KM_THRESHOLD = 500  # km
IMPOSSIBLE_TRAVEL_MINUTES_THRESHOLD = 60  # minutes
MAX_CONCURRENT_SESSIONS = 5


# ── Session Tracking ───────────────────────────────────────────────────────


def get_active_sessions(db: Session, user_id: int) -> List[UserSession]:
    """Return all active sessions for a user."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_activity.desc())
        .all()
    )


def count_active_sessions(db: Session, user_id: int) -> int:
    """Return the number of active sessions for a user."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .count()
    )


def enforce_session_limit(db: Session, user_id: int, max_sessions: int = MAX_CONCURRENT_SESSIONS) -> None:
    """Revoke oldest active sessions if the user exceeds the concurrent session limit."""
    active = get_active_sessions(db, user_id)
    if len(active) <= max_sessions:
        return
    # Revoke oldest sessions beyond the limit
    for session in active[max_sessions:]:
        session.is_active = False
    db.commit()


def record_session_activity(db: Session, session_id: int) -> None:
    """Update the last_activity timestamp for a session."""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.last_activity = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()


# ── Device Binding ─────────────────────────────────────────────────────────


def get_user_devices(db: Session, user_id: int) -> List[UserDevice]:
    """Return all registered devices for a user."""
    return (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id)
        .order_by(UserDevice.last_seen_at.desc())
        .all()
    )


def get_trusted_devices(db: Session, user_id: int) -> List[UserDevice]:
    """Return trusted devices for a user."""
    return (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.is_trusted.is_(True))
        .all()
    )


def bind_device(db: Session, user_id: int, device_id: str, device_type: Optional[str] = None) -> UserDevice:
    """Register or update a device binding for a user."""
    device = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == device_id)
        .first()
    )
    if device:
        device.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
        device.is_current = True
    else:
        device = UserDevice(
            user_id=user_id,
            device_id=device_id,
            device_type=device_type,
            is_trusted=False,
            is_current=True,
        )
        db.add(device)
    db.commit()
    db.refresh(device)
    return device


def trust_device(db: Session, user_id: int, device_id: str) -> bool:
    """Mark a user device as trusted."""
    device = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == device_id)
        .first()
    )
    if not device:
        return False
    device.is_trusted = True
    db.commit()
    return True


def revoke_device(db: Session, user_id: int, device_id: str) -> bool:
    """Revoke/unbind a device from a user."""
    device = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == device_id)
        .first()
    )
    if not device:
        return False
    db.delete(device)
    db.commit()
    return True


# ── Impossible Travel Detection ────────────────────────────────────────────


def get_last_login_location(db: Session, user_id: int) -> Optional[Dict[str, float]]:
    """Return the last known login location (lat/lon) from login history."""
    record = (
        db.query(UserLoginHistory)
        .filter(UserLoginHistory.user_id == user_id, UserLoginHistory.success.is_(True))
        .order_by(UserLoginHistory.timestamp.desc())
        .first()
    )
    if record and hasattr(record, "latitude") and hasattr(record, "longitude"):
        if record.latitude and record.longitude:
            return {"lat": float(record.latitude), "lon": float(record.longitude)}
    return None


def detect_impossible_travel(
    db: Session,
    user_id: int,
    current_lat: float,
    current_lon: float,
    current_time: Optional[datetime] = None,
) -> Tuple[bool, Optional[str]]:
    """Detect impossible travel — login from a distant location too soon after the last login.

    Returns (is_suspicious, reason).
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    last_location = get_last_login_location(db, user_id)
    if not last_location:
        return False, None

    last_time = (
        db.query(UserLoginHistory)
        .filter(UserLoginHistory.user_id == user_id, UserLoginHistory.success.is_(True))
        .order_by(UserLoginHistory.timestamp.desc())
        .first()
    )
    if not last_time:
        return False, None

    time_diff_minutes = (current_time - last_time.timestamp).total_seconds() / 60
    if time_diff_minutes <= 0:
        return False, None

    distance_km = _haversine_distance(
        last_location["lat"], last_location["lon"],
        current_lat, current_lon,
    )

    if (
        distance_km > IMPOSSIBLE_TRAVEL_KM_THRESHOLD
        and time_diff_minutes < IMPOSSIBLE_TRAVEL_MINUTES_THRESHOLD
    ):
        speed_kmh = distance_kmh / (time_diff_minutes / 60)
        reason = (
            f"Impossible travel detected: {distance_km:.0f}km in {time_diff_minutes:.0f}min "
            f"(~{speed_kmh:.0f} km/h). Last login: ({last_location['lat']:.2f}, {last_location['lon']:.2f}), "
            f"current: ({current_lat:.2f}, {current_lon:.2f})"
        )
        return True, reason

    return False, None


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth (km)."""
    from math import asin, cos, radians, sin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))
