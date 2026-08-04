"""Fraud Detection Engine router for admin command center."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import (
    FraudScoreRequest, FraudScoreResponse, FraudBlacklistCreate,
    FraudEventOut, FraudBlacklistOut, FraudRuleOut, FraudRuleCreate,
    ManualReviewOut, ManualReviewResolve, IPReputationOut,
    DeviceFingerprintOut, ThreatFeedStatus, FraudDashboardStats,
    ImpossibleTravelCheck, DeviceStackingCheck, ReturnAbuseCheck,
    IPAccountCheck, BINCheck, LogisticsFraudCheck,
)
from services.security.fraud_detection_service import FraudScoringEngine, ThreatFeedUpdater
from services.security.security_router_service import (
    list_fraud_events_db, list_blacklist_db, add_to_blacklist_db, remove_from_blacklist_db,
    list_rules_db, create_rule_db, list_review_queue_db, assign_review_db, resolve_review_db,
    list_ip_reputation_db, list_device_fingerprints_db, get_threat_feed_status_db,
    get_fraud_dashboard_stats_db, check_impossible_travel_db, check_device_stacking_db,
    check_return_abuse_db, check_ip_accounts_db, check_bin_fraud_db,
    check_logistics_fraud_db, update_threat_feeds_db,
)
from utils.dependencies import require_admin

router = APIRouter()


def get_fraud_engine(db: Session = Depends(get_db)) -> FraudScoringEngine:
    return FraudScoringEngine(db, None)


def get_threat_updater(db: Session = Depends(get_db)) -> ThreatFeedUpdater:
    return ThreatFeedUpdater(db, None)


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
    return list_fraud_events_db(db, page=page, size=size, user_id=user_id, ip_address=ip_address, min_score=min_score)


@router.get("/blacklist", response_model=list[FraudBlacklistOut])
def list_blacklist(
    entity_type: Optional[str] = None,
    status: str = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List blacklisted entities."""
    return list_blacklist_db(db, entity_type=entity_type, status=status, skip=skip, limit=limit)


@router.post("/blacklist", response_model=FraudBlacklistOut)
def add_to_blacklist(payload: FraudBlacklistCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Add entity to blacklist."""
    return add_to_blacklist_db(
        db,
        entity_type=payload.entity_type,
        entity_value=payload.entity_value,
        reason=payload.reason,
        expires_at=payload.expires_at,
    )


@router.delete("/blacklist/{entry_id}")
def remove_from_blacklist(entry_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Remove entity from blacklist (whitelist)."""
    return remove_from_blacklist_db(db, entry_id=entry_id)


@router.get("/rules", response_model=list[FraudRuleOut])
def list_rules(
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List fraud detection rules."""
    return list_rules_db(db, is_active=is_active, skip=skip, limit=limit)


@router.post("/rules", response_model=FraudRuleOut)
def create_rule(payload: FraudRuleCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new fraud detection rule."""
    return create_rule_db(
        db,
        rule_key=payload.rule_key,
        name=payload.name,
        description=payload.description,
        weight=payload.weight,
        condition_json=payload.condition_json,
        is_active=payload.is_active,
        is_global=payload.is_global,
        country_code=payload.country_code,
    )


@router.get("/review", response_model=list[ManualReviewOut])
def list_review_queue(
    status: str = Query("pending"),
    priority: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List items pending manual review."""
    return list_review_queue_db(db, status=status, priority=priority, skip=skip, limit=limit)


@router.post("/review/{review_id}/assign")
def assign_review(
    review_id: int,
    assignee_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign review to an admin."""
    return assign_review_db(db, review_id=review_id, assignee_id=assignee_id)


@router.post("/review/{review_id}/resolve")
def resolve_review(
    review_id: int,
    payload: ManualReviewResolve,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Resolve a manual review."""
    return resolve_review_db(
        db,
        review_id=review_id,
        status=payload.status,
        admin_notes=payload.admin_notes,
        current_user_id=current_user.id,
    )


@router.get("/ip-reputation", response_model=list[IPReputationOut])
def list_ip_reputation(
    is_proxy: Optional[bool] = None,
    is_tor: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List IP reputation records."""
    return list_ip_reputation_db(db, is_proxy=is_proxy, is_tor=is_tor, limit=limit)


@router.get("/devices", response_model=list[DeviceFingerprintOut])
def list_device_fingerprints(
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List device fingerprint records."""
    return list_device_fingerprints_db(db, limit=limit, min_risk_score=min_risk_score)


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
    return get_threat_feed_status_db(db)


@router.get("/dashboard/stats", response_model=FraudDashboardStats)
def get_dashboard_stats(engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Get fraud dashboard statistics."""
    return get_fraud_dashboard_stats_db(engine.db)


@router.post("/check/impossible-travel", response_model=ImpossibleTravelCheck)
def check_impossible_travel(
    user_id: int,
    ip_address: str,
    engine: FraudScoringEngine = Depends(get_fraud_engine)
):
    """Check for impossible travel patterns."""
    return check_impossible_travel_db(engine.db, user_id=user_id, ip_address=ip_address)


@router.post("/check/device-stacking", response_model=DeviceStackingCheck)
def check_device_stacking(device_hash: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check device account stacking."""
    return check_device_stacking_db(engine.db, device_hash=device_hash)


@router.post("/check/return-abuse", response_model=ReturnAbuseCheck)
def check_return_abuse(user_id: int, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check return abuse patterns."""
    return check_return_abuse_db(engine.db, user_id=user_id)


@router.post("/check/ip-accounts", response_model=IPAccountCheck)
def check_ip_accounts(ip_address: str, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check how many accounts are linked to an IP."""
    return check_ip_accounts_db(engine.db, ip_address=ip_address)


@router.post("/check/bin-fraud", response_model=BINCheck)
def check_bin_fraud(card_bin: str, country_code: Optional[str] = None, engine: FraudScoringEngine = Depends(get_fraud_engine)):
    """Check credit card BIN for fraud indicators."""
    return check_bin_fraud_db(engine.db, card_bin=card_bin, country_code=country_code)


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

    return check_logistics_fraud_db(engine.db, shipment_id=shipment_id, delivery_proof=delivery_proof, coords=coords, scan_time=scan_time)

