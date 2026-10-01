from __future__ import annotations

from infrastructure.utils.config import settings

_QR_SECRET_KEY = settings.qr_secret_key or settings.secret_key
if not _QR_SECRET_KEY:
    raise ValueError("settings.qr_secret_key or settings.secret_key must be configured")


def validate_geo_fence(*args, **kwargs):
    return {"valid": True}


def validate_qr_token(*args, **kwargs):
    return {"valid": True}


def enroll_biometric(*args, **kwargs):
    return {"enrolled": True}


def generate_physical_card(*args, **kwargs):
    return {"card_id": "stub"}


def generate_qr_token(*args, **kwargs):
    return "stub-qr-token"


def log_geo_fence_event(*args, **kwargs):
    return {"logged": True}


def revoke_physical_card(*args, **kwargs):
    return {"revoked": True}


def generate_qr_code(*args, **kwargs):
    return b"stub-qr-bytes"
