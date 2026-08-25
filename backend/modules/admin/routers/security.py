"""Admin security router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .auth import router as auth_router
from .fraud import router as fraud_router
from .threat import router as threat_router
from __future__ import annotations
from datetime import datetime, timezone
from domains.governance.models.user import User
from domains.security.models.fraud import DeviceFingerprint
from domains.security.models.fraud import FraudBlacklist
from domains.security.models.fraud import FraudEvent
from domains.security.models.fraud import FraudRule
from domains.security.models.fraud import IPReputation
from domains.security.models.fraud import ManualReviewQueue
from domains.security.services.core.security_service import add_to_blacklist as _svc_add_to_blacklist
from domains.security.services.core.security_service import create_rule as _svc_create_rule
from domains.security.services.core.security_service import get_threat_feed_status as _svc_get_threat_feed_status
from domains.security.services.fraud.fraud_detection_service import FraudScoringEngine
from domains.security.services.fraud.fraud_detection_service import GraphAnalysisService
from domains.security.services.fraud.fraud_detection_service import ThreatFeedUpdater
from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.redis_client import get_redis
from rbac import detect_ghost_employees
from rbac import detect_impossible_travel
from rbac import get_audit_timeline
from rbac import get_team_health_radar
from rbac import update_flight_risk_score
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
import json
import logging as _l; _l.getLogger(__name__).warning("skip auth_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip fraud_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip threat_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/security", tags=["admin", "security"])

@router.post("/score", response_model=FraudScoreResponse)
def calculate_fraud_score(payload: FraudScoreRequest, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Calculate fraud score for an event."""
    return engine.calculate_score(
        user_id=payload.user_id,
        ip_address=payload.ip_address,
        device_hash=payload.device_hash,
        event_type=payload.event_type,
        amount=payload.amount,
        request_headers=payload.headers,
    )




@router.get("/events", response_model=list[FraudEventOut])
def list_fraud_events(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    min_score: int = Query(0, ge=0, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/blacklist", response_model=list[FraudBlacklistOut])
def list_blacklist(
    entity_type: Optional[str] = None,
    status: str = Query("active"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/blacklist", response_model=FraudBlacklistOut)
def add_to_blacklist(payload: FraudBlacklistCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Add entity to blacklist."""
    import hashlib
    value_hash = hashlib.sha256(payload.entity_value.encode()).hexdigest()
    
    existing = db.query(FraudBlacklist).filter(
        FraudBlacklist.entity_type == payload.entity_type,
        FraudBlacklist.entity_value_hash == value_hash
    ).first()
    if existing:
        raise HTTPException(400, "Entity already blacklisted")
    
    entry = FraudBlacklist(
        entity_type=payload.entity_type,
        entity_value_hash=value_hash,
        reason=payload.reason,
        expires_at=payload.expires_at,
    )
    db.add(entry)
    db.commit()
    return entry




@router.delete("/blacklist/{entry_id}")
def remove_from_blacklist(entry_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Remove entity from blacklist (whitelist)."""
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db.commit()
    return {"message": "Entity whitelisted"}




@router.get("/rules", response_model=list[FraudRuleOut])
def list_rules(
    is_active: bool = True,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/rules", response_model=FraudRuleOut)
def create_rule(payload: FraudRuleCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new fraud detection rule."""
    rule = FraudRule(
        rule_key=payload.rule_key,
        name=payload.name,
        description=payload.description,
        weight=payload.weight,
        condition_json=json.dumps(payload.condition_json) if payload.condition_json else None,
        is_active=payload.is_active,
        is_global=payload.is_global,
        country_code=payload.country_code,
    )
    db.add(rule)
    db.commit()
    return rule




@router.get("/review", response_model=list[ManualReviewOut])
def list_review_queue(
    status: str = Query("pending"),
    priority: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/review/{review_id}/assign")
def assign_review(
    review_id: int,
    assignee_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/review/{review_id}/resolve")
def resolve_review(
    review_id: int,
    payload: ManualReviewResolve,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/ip-reputation", response_model=list[IPReputationOut])
def list_ip_reputation(
    is_proxy: Optional[bool] = None,
    is_tor: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/devices", response_model=list[DeviceFingerprintOut])
def list_device_fingerprints(
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/threat-feeds/update")
def update_threat_feeds(
    updater: ThreatFeedUpdater = Depends(get_threat_updater),


@router.get("/threat-feeds/status", response_model=ThreatFeedStatus)
def get_threat_feed_status(db: Session = Depends(get_db)):
    """Get threat feed status."""
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()
    
    return ThreatFeedStatus(
        tor_count=tor_count,
        proxy_count=proxy_count,
        hosting_asn_count=hosting_count,
    )




@router.get("/dashboard/stats", response_model=FraudDashboardStats)
def get_dashboard_stats(engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Get fraud dashboard statistics."""
    return engine.get_fraud_dashboard_stats()




@router.post("/check/impossible-travel", response_model=ImpossibleTravelCheck)
def check_impossible_travel(
    user_id: int,
    ip_address: str,
    engine: FraudScoringEngine = Depends(get_fraud_engine)


@router.post("/check/device-stacking", response_model=DeviceStackingCheck)
def check_device_stacking(device_hash: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check device account stacking."""
    from domains.security.services.fraud.fraud_detection_service import GraphAnalysisService
    graph = GraphAnalysisService(engine.db)
    return graph.check_device_account_stacking(device_hash)




@router.post("/check/return-abuse", response_model=ReturnAbuseCheck)
def check_return_abuse(user_id: int, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check return abuse patterns."""
    from domains.security.services.fraud.fraud_detection_service import GraphAnalysisService
    graph = GraphAnalysisService(engine.db)
    return graph.check_return_abuse_pattern(user_id)




@router.post("/check/ip-accounts", response_model=IPAccountCheck)
def check_ip_accounts(ip_address: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check how many accounts are linked to an IP."""
    return engine.check_ip_multiple_accounts(ip_address)




@router.post("/check/bin-fraud", response_model=BINCheck)
def check_bin_fraud(card_bin: str, country_code: Optional[str] = None, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check credit card BIN for fraud indicators."""
    return engine.check_bin_fraud(card_bin, country_code)




@router.post("/check/logistics-fraud", response_model=LogisticsFraudCheck)
def check_logistics_fraud(
    shipment_id: int,
    delivery_proof: Optional[str] = None,
    gps_coords: Optional[str] = None,
    scan_time: Optional[datetime] = None,
    engine: FraudScoringEngine = Depends(get_fraud_engine)


@router.get("/{employee_id}/risk-score")
def get_risk_score(employee_id: int, db: Session = Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db.execute(
            text("""
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                WHERE employee_id = :eid
                ORDER BY recorded_at DESC
            """),
            {"eid": employee_id},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                ORDER BY recorded_at DESC
                LIMIT 200
            """)
        ).fetchall()
    return [
        {
            "employee_id": r[0],
            "metric_name": r[1],
            "score": float(r[2]) if r[2] is not None else None,
            "recorded_at": (r[3].isoformat() if not isinstance(r[3], str) else r[3]) if r[3] else None,
        }
        for r in rows
    ]




@router.get("/ghost-employees")
def ghost_employees(threshold_days: int = Query(30), db: Session = Depends(get_db)):
    return {"ghost_employees": detect_ghost_employees(db, threshold_days)}




@router.get("/impossible-travel")
def impossible_travel(threshold_hours: int = Query(24), db: Session = Depends(get_db)):
    return {"impossible_travels": detect_impossible_travel(db, threshold_hours)}




@router.post("/{employee_id}/risk-score")
def update_risk(employee_id: int, metric: str = Query(...), score: float = Query(...), db: Session = Depends(get_db)):
    return update_flight_risk_score(employee_id, metric, score, db)




@router.get("/team-health/{manager_id}")
def team_health(manager_id: int, db: Session = Depends(get_db)):
    return get_team_health_radar(manager_id, db)




@router.get("/{employee_id}/audit-timeline")
def audit_timeline(employee_id: int, limit: int = Query(100), db: Session = Depends(get_db)):
    return get_audit_timeline(employee_id, db, limit)




@router.post("/score", response_model=FraudScoreResponse)
def calculate_fraud_score(payload: FraudScoreRequest, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Calculate fraud score for an event."""
    return engine.calculate_score(
        user_id=payload.user_id,
        ip_address=payload.ip_address,
        device_hash=payload.device_hash,
        event_type=payload.event_type,
        amount=payload.amount,
        request_headers=payload.headers,
    )




@router.get("/events", response_model=list[FraudEventOut])
def list_fraud_events(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    min_score: int = Query(0, ge=0, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/blacklist", response_model=list[FraudBlacklistOut])
def list_blacklist(
    entity_type: Optional[str] = None,
    status: str = Query("active"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/blacklist", response_model=FraudBlacklistOut)
def add_to_blacklist(payload: FraudBlacklistCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Add entity to blacklist."""
    import hashlib
    value_hash = hashlib.sha256(payload.entity_value.encode()).hexdigest()
    
    existing = db.query(FraudBlacklist).filter(
        FraudBlacklist.entity_type == payload.entity_type,
        FraudBlacklist.entity_value_hash == value_hash
    ).first()
    if existing:
        raise HTTPException(400, "Entity already blacklisted")
    
    entry = FraudBlacklist(
        entity_type=payload.entity_type,
        entity_value_hash=value_hash,
        reason=payload.reason,
        expires_at=payload.expires_at,
    )
    db.add(entry)
    db.commit()
    return entry




@router.delete("/blacklist/{entry_id}")
def remove_from_blacklist(entry_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Remove entity from blacklist (whitelist)."""
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db.commit()
    return {"message": "Entity whitelisted"}




@router.get("/rules", response_model=list[FraudRuleOut])
def list_rules(
    is_active: bool = True,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/rules", response_model=FraudRuleOut)
def create_rule(payload: FraudRuleCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new fraud detection rule."""
    rule = FraudRule(
        rule_key=payload.rule_key,
        name=payload.name,
        description=payload.description,
        weight=payload.weight,
        condition_json=json.dumps(payload.condition_json) if payload.condition_json else None,
        is_active=payload.is_active,
        is_global=payload.is_global,
        country_code=payload.country_code,
    )
    db.add(rule)
    db.commit()
    return rule




@router.get("/review", response_model=list[ManualReviewOut])
def list_review_queue(
    status: str = Query("pending"),
    priority: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/review/{review_id}/assign")
def assign_review(
    review_id: int,
    assignee_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/review/{review_id}/resolve")
def resolve_review(
    review_id: int,
    payload: ManualReviewResolve,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/ip-reputation", response_model=list[IPReputationOut])
def list_ip_reputation(
    is_proxy: Optional[bool] = None,
    is_tor: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/devices", response_model=list[DeviceFingerprintOut])
def list_device_fingerprints(
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/threat-feeds/update")
def update_threat_feeds(
    updater: ThreatFeedUpdater = Depends(get_threat_updater),


@router.get("/threat-feeds/status", response_model=ThreatFeedStatus)
def get_threat_feed_status(db: Session = Depends(get_db)):
    """Get threat feed status."""
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()
    
    return ThreatFeedStatus(
        tor_count=tor_count,
        proxy_count=proxy_count,
        hosting_asn_count=hosting_count,
    )




@router.get("/dashboard/stats", response_model=FraudDashboardStats)
def get_dashboard_stats(engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Get fraud dashboard statistics."""
    return engine.get_fraud_dashboard_stats()




@router.post("/check/impossible-travel", response_model=ImpossibleTravelCheck)
def check_impossible_travel(
    user_id: int,
    ip_address: str,
    engine: FraudScoringEngine = Depends(get_fraud_engine)


@router.post("/check/device-stacking", response_model=DeviceStackingCheck)
def check_device_stacking(device_hash: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check device account stacking."""
    from domains.security.services.fraud.fraud_detection_service import GraphAnalysisService
    graph = GraphAnalysisService(engine.db)
    return graph.check_device_account_stacking(device_hash)




@router.post("/check/return-abuse", response_model=ReturnAbuseCheck)
def check_return_abuse(user_id: int, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check return abuse patterns."""
    from domains.security.services.fraud.fraud_detection_service import GraphAnalysisService
    graph = GraphAnalysisService(engine.db)
    return graph.check_return_abuse_pattern(user_id)




@router.post("/check/ip-accounts", response_model=IPAccountCheck)
def check_ip_accounts(ip_address: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check how many accounts are linked to an IP."""
    return engine.check_ip_multiple_accounts(ip_address)




@router.post("/check/bin-fraud", response_model=BINCheck)
def check_bin_fraud(card_bin: str, country_code: Optional[str] = None, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check credit card BIN for fraud indicators."""
    return engine.check_bin_fraud(card_bin, country_code)




@router.post("/check/logistics-fraud", response_model=LogisticsFraudCheck)
def check_logistics_fraud(
    shipment_id: int,
    delivery_proof: Optional[str] = None,
    gps_coords: Optional[str] = None,
    scan_time: Optional[datetime] = None,
    engine: FraudScoringEngine = Depends(get_fraud_engine)


@router.get("/{employee_id}/risk-score")
def get_risk_score(employee_id: int, db: Session = Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db.execute(
            text("""
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                WHERE employee_id = :eid
                ORDER BY recorded_at DESC
            """),
            {"eid": employee_id},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                ORDER BY recorded_at DESC
                LIMIT 200
            """)
        ).fetchall()
    return [
        {
            "employee_id": r[0],
            "metric_name": r[1],
            "score": float(r[2]) if r[2] is not None else None,
            "recorded_at": (r[3].isoformat() if not isinstance(r[3], str) else r[3]) if r[3] else None,
        }
        for r in rows
    ]




@router.get("/ghost-employees")
def ghost_employees(threshold_days: int = Query(30), db: Session = Depends(get_db)):
    return {"ghost_employees": detect_ghost_employees(db, threshold_days)}




@router.get("/impossible-travel")
def impossible_travel(threshold_hours: int = Query(24), db: Session = Depends(get_db)):
    return {"impossible_travels": detect_impossible_travel(db, threshold_hours)}




@router.post("/{employee_id}/risk-score")
def update_risk(employee_id: int, metric: str = Query(...), score: float = Query(...), db: Session = Depends(get_db)):
    return update_flight_risk_score(employee_id, metric, score, db)




@router.get("/team-health/{manager_id}")
def team_health(manager_id: int, db: Session = Depends(get_db)):
    return get_team_health_radar(manager_id, db)




@router.get("/{employee_id}/audit-timeline")
def audit_timeline(employee_id: int, limit: int = Query(100), db: Session = Depends(get_db)):
    return get_audit_timeline(employee_id, db, limit)



