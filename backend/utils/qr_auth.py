"""
QR Code Generation and Validation Service
Implements cryptographic QR codes for employee authentication
"""
import qrcode
import base64
import hmac
import hashlib
import time
import json
from io import BytesIO
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class QRAuthService:
    """Generates and validates cryptographic QR codes for employee authentication."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def generate_login_qr(self, employee_id: int, validity_seconds: int = 60) -> Dict[str, Any]:
        payload = {
            "emp_id": employee_id,
            "ts": int(time.time()),
            "exp": int(time.time()) + validity_seconds
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(self.secret_key, payload_b64.encode(), hashlib.sha256).hexdigest()[:16]
        qr_data = f"ZOZI_AUTH|{payload_b64}|{signature}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.urlsafe_b64encode(buffer.getvalue()).decode()
        
        return {
            "qr_data": qr_data,
            "image_base64": img_base64,
            "expires_at": payload["exp"]
        }
    
    def validate_qr(self, qr_data: str) -> Dict[str, Any]:
        try:
            parts = qr_data.split("|")
            if len(parts) != 3 or parts[0] != "ZOZI_AUTH":
                return {"valid": False, "error": "Invalid QR format"}
            
            payload_b64, signature = parts[1], parts[2]
            expected_sig = hmac.new(self.secret_key, payload_b64.encode(), hashlib.sha256).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_sig):
                return {"valid": False, "error": "Invalid signature"}
            
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            if payload["exp"] < int(time.time()):
                return {"valid": False, "error": "QR expired"}
            
            return {
                "valid": True,
                "employee_id": payload["emp_id"],
                "issued_at": payload["ts"]
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}


_qr_auth_instance: Optional[QRAuthService] = None


def get_qr_auth(secret_key: str) -> QRAuthService:
    global _qr_auth_instance
    if _qr_auth_instance is None:
        _qr_auth_instance = QRAuthService(secret_key)
    return _qr_auth_instance

