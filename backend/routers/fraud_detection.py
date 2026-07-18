"""Fraud Detection Engine router for admin command center."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import (
    FraudEvent, FraudBlacklist, FraudRule, ManualReviewQueue,
    IPReputation, DeviceFingerprint, User
)
from db.schemas import (
    FraudScoreRequest, FraudScoreResponse, FraudEventOut,
    FraudBlacklistCreate, FraudBlacklistOut, FraudRuleCreate, FraudRuleOut,
    ManualReviewOut, ManualReviewAssign, ManualReviewResolve,
    IPReputationOut, DeviceFingerprintOut, ThreatFeedStatus,
    FraudDashboardStats, ImpossibleTravelCheck, DeviceStackingCheck,
    ReturnAbuseCheck, IPAccountCheck, BINCheck, LogisticsFraudCheck
)
from services.fraud_detection_service import FraudScoringEngine, ThreatFeedUpdater
from utils.dependencies import require_admin
from utils.redis_client import get_redis
import json

router = APIRouter()


def get_fraud_engine(db: Session = Depends(get_db)) -> FraudScoringEngine:
    return FraudScoringEngine(db, get_redis())


def get_threat_updater(db: Session = Depends(get_db)) -> ThreatFeedUpdater:
    return ThreatFeedUpdater(db, get_redis())


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
):
    """List fraud events with filtering."""
    q = db.query(FraudEvent)
    if user_id:
        q = q.filter(FraudEvent.user_id == user_id)
    if ip_address:
        q = q.filter(FraudEvent.ip_address == ip_address)
    if min_score > 0:
        q = q.filter(FraudEvent.fraud_score >= min_score)
    total = q.count()
    items = q.order_by(FraudEvent.created_at.desc()).offset((page-1)*size).limit(size).all()
    
    results = []
    for e in items:
        results.append(FraudEventOut(
            id=e.id,
            user_id=e.user_id,
            event_type=e.event_type,
            ip_address=e.ip_address,
            device_hash=e.device_hash,
            fraud_score=e.fraud_score,
            triggered_rules=json.loads(e.triggered_rules) if e.triggered_rules else [],
            status=e.status,
            created_at=e.created_at,
        ))
    return results


@router.get("/blacklist", response_model=list[FraudBlacklistOut])
def list_blacklist(
    entity_type: Optional[str] = None,
    status: str = Query("active"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List blacklisted entities."""
    q = db.query(FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    return q.order_by(FraudBlacklist.created_at.desc()).all()


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
):
    """List fraud detection rules."""
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).all()


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
):
    """List items pending manual review."""
    q = db.query(ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    return q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).all()


@router.post("/review/{review_id}/assign")
def assign_review(
    review_id: int,
    assignee_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign review to an admin."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.assigned_to = assignee_id
    db.commit()
    return {"message": "Assigned"}


@router.post("/review/{review_id}/resolve")
def resolve_review(
    review_id: int,
    payload: ManualReviewResolve,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Resolve a manual review."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.status = payload.status
    review.admin_notes = payload.admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user.id
    db.commit()
    return {"message": "Resolved"}


@router.get("/ip-reputation", response_model=list[IPReputationOut])
def list_ip_reputation(
    is_proxy: Optional[bool] = None,
    is_tor: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List IP reputation records."""
    q = db.query(IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    return q.order_by(IPReputation.updated_at.desc()).limit(limit).all()


@router.get("/devices", response_model=list[DeviceFingerprintOut])
def list_device_fingerprints(
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List device fingerprint records."""
    return db.query(DeviceFingerprint).filter(
        DeviceFingerprint.risk_score >= min_risk_score
    ).order_by(DeviceFingerprint.last_seen_at.desc()).limit(limit).all()


@router.post("/threat-feeds/update")
def update_threat_feeds(
    updater: ThreatFeedUpdater = Depends(get_threat_updater),
):
    """Manually trigger threat feed update."""
    results = updater.update_threat_feeds()
    return {"message": "Threat feeds updated", "results": results}


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
):
    """Check for impossible travel patterns."""
    return engine.check_impossible_travel(user_id, ip_address)


@router.post("/check/device-stacking", response_model=DeviceStackingCheck)
def check_device_stacking(device_hash: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check device account stacking."""
    from services.fraud_detection_service import GraphAnalysisService
    graph = GraphAnalysisService(engine.db)
    return graph.check_device_account_stacking(device_hash)


@router.post("/check/return-abuse", response_model=ReturnAbuseCheck)
def check_return_abuse(user_id: int, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check return abuse patterns."""
    from services.fraud_detection_service import GraphAnalysisService
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
):
    """Check for logistics fraud patterns."""
    coords = None
    if gps_coords:
        try:
            lat, lon = map(float, gps_coords.split(","))
            coords = (lat, lon)
        except ValueError:
            pass
    
    return engine.check_logistics_fraud(shipment_id, delivery_proof, coords, scan_time)

