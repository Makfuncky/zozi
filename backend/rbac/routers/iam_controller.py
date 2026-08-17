"""controllers.identity.iam_controller controller.

Coordinates IAM business rules and delegates ALL persistence to
``services.identity.iam_service``. It must not issue ``db.query`` directly
and must not perform commits.

The HTTP contract is declared with ``core.route_contract`` decorators
so the auto-router emits ``routers/public_identity_iam.py``.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from core.route_contract import post

from domains.accounts.services.iam_service import (
    enroll_biometric as service_enroll_biometric,
    generate_physical_card as service_generate_physical_card,
    generate_qr_token as service_generate_qr_token,
    log_geo_fence_event as service_log_geo_fence_event,
    revoke_physical_card as service_revoke_physical_card,
    validate_geo_fence as service_validate_geo_fence,
    validate_qr_token as service_validate_qr_token,
)
import structlog
logger = structlog.get_logger(__name__)

@post("/{employee_id}/card", deps=["db"], tags=["iam"])
def generate_physical_card(employee_id: int, db: Session) -> dict:
    return service_generate_physical_card(employee_id, db)

@post("/{employee_id}/biometric", deps=["db"], query=["biometric_type", "data"], tags=["iam"])
def enroll_biometric(employee_id: int, biometric_type: str, data: str, db: Session) -> dict:
    return service_enroll_biometric(employee_id, biometric_type, data, db)

@post("/geo/validate", deps=["db"], query=["latitude", "longitude", "office_id"], tags=["iam"])
def validate_geo_fence(latitude: float, longitude: float, office_id: int, db: Session) -> dict:
    return service_validate_geo_fence(latitude, longitude, office_id, db)

@post("/{employee_id}/geo-log", deps=["db"], query=["latitude", "longitude", "is_within"], tags=["iam"])
def log_geo_fence_event(employee_id: int, latitude: float, longitude: float, is_within: bool, db: Session) -> dict:
    service_log_geo_fence_event(employee_id, latitude, longitude, is_within, db)
    return {"status": "logged"}

@post("/{employee_id}/qr-token", deps=["db"], tags=["iam"])
def generate_qr_token(employee_id: int, db: Session) -> dict:
    return service_generate_qr_token(employee_id, db)

@post("/qr-login", deps=["db"], query=["qr_token"], tags=["iam"])
def validate_qr_token(qr_token: str, db: Session) -> dict:
    return service_validate_qr_token(qr_token, db)

@post("/{employee_id}/revoke", deps=["db"], query=["reason"], tags=["iam"])
def revoke_physical_card(employee_id: int, reason: str, db: Session) -> dict:
    return service_revoke_physical_card(employee_id, reason, db)
