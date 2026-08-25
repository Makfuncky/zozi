"""Identity administration service.

Backend for ``admin_identity_operations`` router. Owns user lifecycle
operations (list / get / update / archive / restore / delete / role / active /
force-password-reset) scoped to a country. The router delegates here so it
performs no direct ``db.query``/``db.add``/``db.commit`` and does not import
other controllers.

Row-level scoping is applied through the canonical utils (``get_country_or_404``
and the request RLS context) rather than bespoke SQL in the router.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.governance.services.users.users_service import update_user_role, toggle_user_active
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.pagination import paginated_response


def _scope(db: Session, country_code: str):
    """Validate the country and activate request RLS for it."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)


def list_users_by_country(
    db: Session,
    country_code: str,
    page: int = 1,
    size: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        q = db.query(User).filter(User.country_code == country_code.upper())
        if role:
            q = q.filter(User.role == role)
        if search:
            q = q.filter(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        if not include_deleted:
            q = q.filter(User.is_deleted.is_(False))
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()


def get_user_in_country(db: Session, country_code: str, user_id: int) -> User:
    _scope(db, country_code)
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id, User.country_code == country_code.upper())
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    finally:
        clear_rls_context()


def update_user_in_country(
    db: Session, country_code: str, user_id: int, payload
) -> User:
    user = get_user_in_country(db, country_code, user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    """Fetch a user by primary key (no 404; returns None if absent)."""
    return db.query(User).filter(User.id == user_id).first()


def list_all_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    """List users across all countries (admin console, no RLS scoping)."""
    return db.query(User).offset(skip).limit(limit).all()


def get_user_by_id_or_404(db: Session, user_id: int) -> User:
    """Fetch a user by primary key, raising 404 when absent."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user_by_id(db: Session, user_id: int, payload) -> User:
    """Apply an update payload to a user loaded by id (no country scoping).

    Behaviour-preserving extraction of the inline ``.put("/me")`` and
    ``.put("/{user_id}")`` handlers in ``routers.admin_identity_operations_api``
    and ``routers.public_identity_operations``: load, apply the unset-excluded
    fields, commit once, refresh and return the row.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def archive_user(db: Session, country_code: str, user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
    user = get_user_in_country(db, country_code, user_id)
    user.is_deleted = True
    db.commit()
    return {"message": "User archived", "id": user_id, "reason": reason}


def restore_user(db: Session, country_code: str, user_id: int) -> Dict[str, Any]:
    user = get_user_in_country(db, country_code, user_id)
    user.is_deleted = False
    db.commit()
    return {"message": "User restored", "id": user_id}


def bulk_archive_users(db: Session, country_code: str, payload, reason: Optional[str] = None) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        ids = payload.ids if payload else []
        count = 0
        for uid in ids:
            user = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if user:
                user.is_deleted = True
                count += 1
        db.commit()
        return {"message": f"{count} users archived", "count": count, "reason": reason}
    finally:
        clear_rls_context()


def bulk_toggle_active(db: Session, country_code: str, user_ids: List[int], is_active: bool = True) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        count = 0
        for uid in user_ids:
            user = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if user:
                user.is_active = is_active
                count += 1
        db.commit()
        return {"message": f"Updated {count} users", "updated": count}
    finally:
        clear_rls_context()


def bulk_restore_users(db: Session, country_code: str, payload) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        ids = payload.ids if payload else []
        count = 0
        for uid in ids:
            user = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if user:
                user.is_deleted = False
                count += 1
        db.commit()
        return {"message": f"{count} users restored", "count": count}
    finally:
        clear_rls_context()


def hard_delete_user(db: Session, country_code: str, user_id: int, acting_user: dict, delete_orders: bool = False) -> Dict[str, Any]:
    user = get_user_in_country(db, country_code, user_id)
    db.delete(user)
    db.commit()
    return {"message": "User hard-deleted", "id": user_id}


def set_user_role(db: Session, country_code: str, user_id: int, role: str, acting_user: dict) -> Dict[str, Any]:
    get_user_in_country(db, country_code, user_id)
    return update_user_role(user_id, role, acting_user, db)


def set_user_active(db: Session, country_code: str, user_id: int, acting_user: dict) -> Dict[str, Any]:
    get_user_in_country(db, country_code, user_id)
    return toggle_user_active(user_id, acting_user, db)


def force_reset_password(db: Session, country_code: str, user_id: int, new_password: str, acting_user: dict) -> Dict[str, Any]:
    from infrastructure.utils.auth import get_password_hash

    user = get_user_in_country(db, country_code, user_id)
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password reset", "id": user_id}


def delete_user_admin(db: Session, country_code: str, user_id: int, acting_user: dict, delete_orders: bool = False) -> Dict[str, Any]:
    return hard_delete_user(db, country_code, user_id, acting_user, delete_orders=delete_orders)


# === MERGED FROM identity_service.py ===
"""Identity (customer-facing) service.

Backend for ``public_identity_operations`` router. Owns profile reads/updates
and user listing so the router performs no direct ``db.query``/``db.commit``
and never instantiates ORM models.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from domains.governance.models.user import User
from infrastructure.database.schemas import UserOut


def get_profile(db: Session, current_user: dict) -> User:
    user = db.query(User).filter(User.id == current_user.get("id")).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_profile(db: Session, current_user: dict, payload) -> User:
    user = get_profile(db, current_user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


def delete_user(db: Session, user_id: int) -> dict:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": "User deleted", "id": user_id}


# === MERGED FROM iam_service.py ===
"""
Identity & Access Management service with QR login, geo-fencing, and device fingerprinting.
"""
from __future__ import annotations

import hashlib
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from math import radians, sin, cos, sqrt, atan2

from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.governance.models.user import UserDevice
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import Office, GeoFenceLog


class GeoFenceValidator:
    """Validates geo-fence boundaries for office locations."""
    
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers."""
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * sqrt(a) * atan2(sqrt(a), sqrt(1 - a))
        
        return GeoFenceValidator.EARTH_RADIUS_KM * c
    
    @staticmethod
    def is_within_geo_fence(
        scan_lat: float,
        scan_long: float,
        office_lat: float,
        office_long: float,
        radius_meters: int
    ) -> bool:
        """Check if scan location is within office geo-fence."""
        distance_km = GeoFenceValidator.haversine_distance(
            scan_lat, scan_long, office_lat, office_long
        )
        return (distance_km * 1000) <= radius_meters


class DeviceFingerprinter:
    """Generates device fingerprints for session binding."""
    
    @staticmethod
    def generate_fingerprint(user_agent: str, ip_address: str, accept_headers: str = "") -> str:
        """Generate a device fingerprint from request headers."""
        data = f"{user_agent}|{ip_address}|{accept_headers}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class IAMService:
    """Service for identity management, QR login, and geo-fencing."""
    
    def __init__(self, db: Session):
        self.db = db
        self.geo_validator = GeoFenceValidator()
        self.fingerprinter = DeviceFingerprinter()
    
    def generate_qr_login_token(self, user_id: int, device_id: str) -> str:
        """Generate a secure QR login token for device pairing."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        return hashlib.sha256(f"{user_id}:{token}:{device_id}".encode()).hexdigest()
    
    def validate_qr_token(self, user_id: int, token: str, device_id: str) -> bool:
        """Validate a QR login token."""
        expected = self.generate_qr_login_token(user_id, device_id)
        return secrets.compare_digest(token, expected)
    
    def register_device(
        self,
        user_id: int,
        device_id: str,
        device_type: str,
        device_name: str,
        ip_address: str,
        user_agent: str,
    ) -> UserDevice:
        """Register a new device for user."""
        existing = (
            self.db.query(UserDevice)
            .filter(UserDevice.device_id == device_id, UserDevice.user_id == user_id)
            .first()
        )
        if existing:
            existing.last_seen = datetime.now(timezone.utc)
            existing.is_trusted = existing.is_trusted
            self.db.commit()
            return existing
        
        device = UserDevice(
            user_id=user_id,
            device_id=device_id,
            device_type=device_type,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            last_seen=datetime.now(timezone.utc),
            is_trusted=False,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device
    
    def validate_geo_fence(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        allowed_countries: list[str],
    ) -> Tuple[bool, str]:
        """Validate if coordinates are within allowed geo-fence."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == user_id)
            .first()
        )
        if not employee or not employee.office_id:
            return True, "No office assignment"
        
        office = self.db.query(Office).filter(Office.id == employee.office_id).first()
        if not office:
            return True, "Office not found"
        
        distance = self.geo_validator.haversine_distance(
            latitude, longitude,
            office.latitude or 0, office.longitude or 0
        )
        distance_meters = distance * 1000
        
        if distance_meters > office.geo_fence_radius_meters:
            return False, f"Outside geo-fence ({distance_meters:.0f}m > {office.geo_fence_radius_meters}m)"
        
        return True, "Within geo-fence"
    
    def log_geo_scan(
        self,
        employee_id: int,
        latitude: float,
        longitude: float,
        is_within_fence: bool,
        device_fingerprint: str = None,
    ) -> GeoFenceLog:
        """Log a geo-fence scan attempt."""
        log = GeoFenceLog(
            employee_id=employee_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=0,
            scanned_at=datetime.now(timezone.utc),
            is_within_fence=is_within_fence,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def check_device_trust(self, device_id: str, user_id: int) -> bool:
        """Check if device is trusted for user."""
        device = (
            self.db.query(UserDevice)
            .filter(UserDevice.device_id == device_id, UserDevice.user_id == user_id)
            .first()
        )
        return device.is_trusted if device else False
    
    def trust_device(self, device_id: str, user_id: int) -> bool:
        """Mark device as trusted after 2FA."""
        device = (
            self.db.query(UserDevice)
            .filter(UserDevice.device_id == device_id, UserDevice.user_id == user_id)
            .first()
        )
        if device:
            device.is_trusted = True
            self.db.commit()
            return True
        return False
    
    def get_or_create_employee(self, user_id: int) -> Optional[Employee]:
        """Get or create employee record for user."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == user_id)
            .first()
        )
        return employee
    
    def detect_impossible_travel(
        self,
        employee_id: int,
        ip_address: str,
        timestamp: datetime = None
    ) -> Tuple[bool, str]:
        """Detect impossible travel based on IP and previous location."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        logs = (
            self.db.query(GeoFenceLog)
            .filter(GeoFenceLog.employee_id == employee_id)
            .order_by(GeoFenceLog.scanned_at.desc())
            .limit(2)
            .all()
        )
        
        if len(logs) < 2:
            return False, "Insufficient data"
        
        prev_log = logs[1]
        time_diff_hours = (timestamp - prev_log.scanned_at).total_seconds() / 3600
        
        if time_diff_hours < 0.5:
            distance_km = self.geo_validator.haversine_distance(
                logs[0].latitude, logs[0].longitude,
                prev_log.latitude, prev_log.longitude
            )
            if distance_km > 100:
                return True, f"Impossible travel detected: {distance_km:.1f}km in {time_diff_hours*60:.0f}min"
        
        return False, "Travel OK"


def create_iam_service(db: Session) -> IAMService:
    return IAMService(db)


def generate_qr_code(user_id: int, purpose: str = "access") -> str:
    """Generate a QR code token for mobile access."""
    from domains.hr.models.employee_models import DynamicQRSession
    from infrastructure.utils.datetime_utils import utcnow
    from datetime import timedelta
    
    qr_token = secrets.token_urlsafe(32)
    return qr_token


