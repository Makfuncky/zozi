from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from data.models import User, Employee, UserDevice
from services.iam_service import generate_qr_code
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class MobileAuthService:
    """
    Mobile-specific authentication service.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_dynamic_qr(self, user_id: int, purpose: str = "access") -> str:
        """Generate a dynamic QR code for mobile access."""
        return generate_qr_code(user_id, purpose)
    
    def register_device(
        self,
        user_id: int,
        device_name: str,
        platform: str,
        fingerprint: str,
    ) -> dict:
        """Register a device for the user."""
        device = UserDevice(
            user_id=user_id,
            fingerprint_hash=fingerprint,
            device_name=device_name,
            ip_address=None,
            is_trusted=False,
            is_current=True,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return {"device_id": device.id, "registered": True}
    
    def validate_biometric(
        self,
        user_id: int,
        biometric_token: str,
        platform: str,
    ) -> dict:
        """Validate biometric credential."""
        from services.biometric_auth import BiometricAuthService
        
        bio_service = BiometricAuthService()
        bio_type = "faceid" if platform == "ios" else "fingerprint"
        
        if bio_service.validate_biometric(user_id, bio_type, biometric_token):
            return {"valid": True, "session_token": secrets.token_urlsafe(32)}
        
        return {"valid": False}
    
    def geo_fenced_check_in(
        self,
        user_id: int,
        lat: float,
        lon: float,
        office_id: Optional[int] = None,
    ) -> dict:
        """Perform geo-fenced check-in."""
        from services.geo_fence_service import GeoFenceService
        
        geo_service = GeoFenceService(self.db)
        
        if office_id and not geo_service.is_within_fence(lat, lon, "office", office_id):
            return {"status": "outside_boundary", "check_in": False}
        
        return {"status": "checked_in", "check_in": True}

