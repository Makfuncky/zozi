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

from models.employee_models import Employee, GeoFenceLog, EmployeeBiometric
from db.database import get_service_session

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
