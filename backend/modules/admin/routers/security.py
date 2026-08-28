"""Admin security router — thin HTTP layer delegating to security domain services."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Body, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user, require_admin
from rbac.catalog import FEATURE_CATALOG, FEATURE_NAMESPACES, all_features
from rbac.dependencies import require_feature
from domains.security.services.health.flat_risk_service import (
    detect_ghost_employees,
    detect_impossible_travel,
    get_audit_timeline,
    get_team_health_radar,
    update_flight_risk_score,
)
from domains.security.services.iam.security_dependencies import start_otp, verify_otp
from domains.governance.ports import User
from domains.security.services.core.security_service import (
    add_to_blacklist,
    create_rule,
    get_threat_feed_status,
    list_blacklist,
    list_fraud_events,
    list_review_queue,
    list_rules,
    remove_from_blacklist,
)
from domains.security.services.fraud.fraud_detection_service import FraudScoringEngine, ThreatFeedUpdater
from domains.security.services.risk_service import get_risk_scores
from domains.accounts.schemas.user_schemas import OtpRequest

logger = logging.getLogger(__name__)


def _otp_rate_limit(request: Request, user_id: int, suffix: str, max_attempts: int, window: int = 60) -> None:
    """Enforce per-user OTP rate limit using Redis INCR+EXPIRE.

    Raises HTTPException(429) when the limit is exceeded or when Redis is
    unavailable (fail-closed to prevent brute-force / OTP bombing).
    """
    from fastapi import HTTPException, status

    ip_address = "unknown"
    if getattr(request, "client", None) is not None:
        ip_address = request.client.host or "unknown"
    else:
        ip_address = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()

    try:
        from domains.accounts.services.auth.auth_service import _get_redis

        r = _get_redis()
        if r is None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limiting temporarily unavailable. Please try again later.",
            )

        key = f"rate_limit:otp:{suffix}:{ip_address}:{user_id}"
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        count, _ = pipe.execute()
        count = int(count) if count is not None else 0
        if count > max_attempts:
            logger.warning(
                "OTP rate limit exceeded for user %s on %s (count=%s, limit=%s/%ss)",
                user_id, ip_address, count, max_attempts, window,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limiting temporarily unavailable. Please try again later.",
        )


router = APIRouter(tags=["admin", "security"])


class FraudScoreRequest(BaseModel):
    user_id: int | None = None
    ip_address: str | None = None
    device_hash: str | None = None
    event_type: str | None = None
    amount: float | None = None
    headers: dict | None = None


class BlacklistCreateRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_value: str = Field(..., min_length=1, max_length=500)
    reason: str | None = Field(None, max_length=1000)
    expires_at: str | None = None


class RuleCreateRequest(BaseModel):
    rule_key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    weight: float = Field(1.0, ge=0, le=100)
    condition_json: dict | None = None
    is_active: bool = True
    is_global: bool = False
    country_code: str | None = Field(None, max_length=10)


@router.post("/api/v1/admin/security/score")
def calculate_fraud_score(
    payload: FraudScoreRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    engine = FraudScoringEngine(db)
    return engine.calculate_score(
        user_id=payload.user_id,
        ip_address=payload.ip_address,
        device_hash=payload.device_hash,
        event_type=payload.event_type,
        amount=payload.amount,
        request_headers=payload.headers,
    )


@router.get("/api/v1/admin/security/events")
def list_fraud_events_route(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int | None = None,
    ip_address: str | None = None,
    min_score: int = Query(0, ge=0, le=100),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return list_fraud_events(page, size, user_id, ip_address, min_score, _, db)


@router.get("/api/v1/admin/security/blacklist")
def list_blacklist_route(
    entity_type: str | None = None,
    status: str = Query("active"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.policies.read")),
):
    return list_blacklist(entity_type, status, _, db)


@router.post("/api/v1/admin/security/blacklist", status_code=201)
def add_to_blacklist_route(
    payload: BlacklistCreateRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.policies.manage")),
):
    return add_to_blacklist(payload, _, db)


@router.delete("/api/v1/admin/security/blacklist/{entry_id}")
def remove_from_blacklist_route(
    entry_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.policies.manage")),
):
    return remove_from_blacklist(entry_id, _, db)


@router.get("/api/v1/admin/security/rules")
def list_rules_route(
    is_active: bool = True,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.policies.read")),
):
    return list_rules(is_active, _, db)


@router.post("/api/v1/admin/security/rules", status_code=201)
def create_rule_route(
    payload: RuleCreateRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.policies.manage")),
):
    return create_rule(payload, _, db)


@router.get("/api/v1/admin/security/review")
def list_review_queue_route(
    status: str = Query("pending"),
    priority: str | None = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return list_review_queue(status, priority, _, db)


@router.post("/api/v1/admin/security/threat-feeds/update")
def update_threat_feeds(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.manage")),
):
    updater = ThreatFeedUpdater(db)
    return updater.update_all_feeds()


@router.get("/api/v1/admin/security/threat-feeds/status")
def get_threat_feed_status_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return get_threat_feed_status(db)


@router.get("/api/v1/admin/security/{employee_id}/risk-score")
def get_risk_score_route(
    employee_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return get_risk_scores(db, employee_id)


# ── Risk Management (migrated from domains/security/services/health/risk_controller) ──


@router.get("/api/v1/admin/ghost-employees", tags=["security-risk"])
def admin_ghost_employees_route(
    threshold_days: int = Query(30, ge=1, le=365),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return detect_ghost_employees(db, threshold_days)


@router.get("/api/v1/admin/impossible-travel", tags=["security-risk"])
def admin_impossible_travel_route(
    threshold_hours: int = Query(24, ge=1, le=168),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return detect_impossible_travel(db, threshold_hours)


@router.post("/api/v1/admin/{employee_id}/risk-score", tags=["security-risk"])
def admin_update_flight_risk_score_route(
    employee_id: int,
    metric: str = Query(...),
    score: float = Query(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.manage")),
):
    return update_flight_risk_score(employee_id, metric, score, db)


@router.get("/api/v1/admin/team-health/{manager_id}", tags=["security-risk"])
def admin_team_health_route(
    manager_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return get_team_health_radar(manager_id, db)


@router.get("/api/v1/admin/{employee_id}/audit-timeline", tags=["security-risk"])
def admin_audit_timeline_route(
    employee_id: int,
    limit: int = Query(100, ge=1, le=500),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    return get_audit_timeline(employee_id, db, limit)


# ── RBAC catalog (moved from modules/admin/routers/rbac_catalog.py) ───────────


@router.get("/api/v1/rbac/catalog")
def get_rbac_catalog(    _rf_gate: None = Depends(require_feature("security.read"))):
    """Return the full feature catalog for frontend permission sync."""
    return {
        "features": FEATURE_CATALOG,
        "namespaces": list(FEATURE_NAMESPACES),
        "feature_list": all_features(),
    }


# ── OTP / MFA challenge endpoints (moved from modules/admin/routers/auth_otp.py) ──


@router.post("/otp/start", tags=["auth", "otp"])
def start_otp_challenge(
    payload: OtpRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("security.mfa.manage")),
):
    _otp_rate_limit(request, current_user.id, "start", max_attempts=3, window=60)
    start_otp(current_user, purpose=payload.purpose, channel=payload.channel, destination=payload.destination, db=db)
    return {"status": "sent", "channel": payload.channel, "purpose": payload.purpose}


@router.post("/otp/verify", tags=["auth", "otp"])
def verify_otp_challenge(
    payload: OtpRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("security.mfa.manage")),
):
    _otp_rate_limit(request, current_user.id, "verify", max_attempts=5, window=60)
    verified = verify_otp(current_user, purpose=payload.purpose, code=payload.code or "", db=db)
    return {"verified": verified}
