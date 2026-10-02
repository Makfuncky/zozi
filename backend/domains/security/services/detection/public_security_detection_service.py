"""Fraud Detection Engine router for admin command center."""
import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from domains.security.models.fraud import FraudEvent
from domains.security.models.fraud import FraudBlacklist
from domains.security.models.fraud import FraudRule
from domains.security.models.fraud import ManualReviewQueue
from domains.security.models.fraud import IPReputation
from domains.security.models.fraud import DeviceFingerprint
from infrastructure.database.schemas import FraudScoreRequest, FraudScoreResponse, FraudEventOut, FraudBlacklistCreate, FraudBlacklistOut, FraudRuleCreate, FraudRuleOut, ManualReviewOut, ManualReviewAssign, ManualReviewResolve, IPReputationOut, DeviceFingerprintOut, ThreatFeedStatus, FraudDashboardStats, ImpossibleTravelCheck, DeviceStackingCheck, ReturnAbuseCheck, IPAccountCheck, BINCheck, LogisticsFraudCheck
from infrastructure.utils.dependencies import require_admin
from infrastructure.valkey.client import get_valkey
import json

_IDEMPOTENCY_KEY_HEADER = "X-Idempotency-Key"
_IDEMPOTENCY_TTL_SECONDS = 300
_IDEMPOTENCY_PREFIX = "sec:idempotency"


def _idempotency_key(idempotency_key: Optional[str] = Header(None, alias=_IDEMPOTENCY_KEY_HEADER)) -> Optional[str]:
    return idempotency_key


def _check_idempotency(redis_client: Any, key: str, operation: str) -> Optional[Any]:
    full_key = f"{_IDEMPOTENCY_PREFIX}:{operation}:{key}"
    cached = redis_client.get(full_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _record_idempotency(redis_client: Any, key: str, operation: str, result: Any) -> None:
    full_key = f"{_IDEMPOTENCY_PREFIX}:{operation}:{key}"
    try:
        redis_client.setex(full_key, _IDEMPOTENCY_TTL_SECONDS, json.dumps(result))
    except Exception:
        pass

def list_fraud_events(page: int=Query(1, ge=1), size: int=Query(50, ge=1, le=100), user_id: Optional[int]=None, ip_address: Optional[str]=None, min_score: int=Query(0, ge=0, le=100), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List fraud events with filtering."""
    q = db.query(FraudEvent)
    if user_id:
        q = q.filter(FraudEvent.user_id == user_id)
    if ip_address:
        q = q.filter(FraudEvent.ip_address == ip_address)
    if min_score > 0:
        q = q.filter(FraudEvent.fraud_score >= min_score)
    total = q.count()
    items = q.order_by(FraudEvent.created_at.desc()).offset((page - 1) * size).limit(size).all()
    results = []
    for e in items:
        results.append(FraudEventOut(id=e.id, user_id=e.user_id, event_type=e.event_type, ip_address=e.ip_address, device_hash=e.device_hash, fraud_score=e.fraud_score, triggered_rules=json.loads(e.triggered_rules) if e.triggered_rules else [], status=e.status, created_at=e.created_at))
    return results

def list_blacklist(entity_type: Optional[str]=None, status: str=Query('active'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List blacklisted entities."""
    q = db.query(FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    return q.order_by(FraudBlacklist.created_at.desc()).all()

def add_to_blacklist(payload: FraudBlacklistCreate, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Add entity to blacklist."""
    import hashlib
    value_hash = hashlib.sha256(payload.entity_value.encode()).hexdigest()
    existing = db.query(FraudBlacklist).filter(FraudBlacklist.entity_type == payload.entity_type, FraudBlacklist.entity_value_hash == value_hash).first()
    if existing:
        raise HTTPException(400, 'Entity already blacklisted')
    entry = FraudBlacklist(entity_type=payload.entity_type, entity_value_hash=value_hash, reason=payload.reason, expires_at=payload.expires_at)
    db.add(entry)
    db.commit()
    return entry

def remove_from_blacklist(entry_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)):
    """Remove entity from blacklist (whitelist)."""
    redis = get_valkey()
    if idempotency_key:
        cached = _check_idempotency(redis, idempotency_key, "remove_blacklist")
        if cached is not None:
            return cached
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, 'Entry not found')
    entry.status = 'whitelisted'
    db.commit()
    result = {'message': 'Entity whitelisted'}
    if idempotency_key:
        _record_idempotency(redis, idempotency_key, "remove_blacklist", result)
    return result

def list_rules(is_active: bool=True, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List fraud detection rules."""
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).all()

def create_rule(payload: FraudRuleCreate, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)):
    """Create a new fraud detection rule."""
    redis = get_valkey()
    if idempotency_key:
        cached = _check_idempotency(redis, idempotency_key, "create_rule")
        if cached is not None:
            return cached
    rule = FraudRule(rule_key=payload.rule_key, name=payload.name, description=payload.description, weight=payload.weight, condition_json=json.dumps(payload.condition_json) if payload.condition_json else None, is_active=payload.is_active, is_global=payload.is_global, country_code=payload.country_code)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    result = {"rule_key": rule.rule_key, "id": rule.id}
    if idempotency_key:
        _record_idempotency(redis, idempotency_key, "create_rule", result)
    return rule

def list_review_queue(status: str=Query('pending'), priority: Optional[str]=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List items pending manual review."""
    q = db.query(ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    return q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).all()

def assign_review(review_id: int, assignee_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)):
    """Assign review to an admin."""
    redis = get_valkey()
    if idempotency_key:
        cached = _check_idempotency(redis, idempotency_key, "assign_review")
        if cached is not None:
            return cached
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, 'Review not found')
    review.assigned_to = assignee_id
    db.commit()
    result = {'message': 'Assigned'}
    if idempotency_key:
        _record_idempotency(redis, idempotency_key, "assign_review", result)
    return result

def resolve_review(review_id: int, payload: ManualReviewResolve, current_user: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)):
    """Resolve a manual review."""
    redis = get_valkey()
    if idempotency_key:
        cached = _check_idempotency(redis, idempotency_key, "resolve_review")
        if cached is not None:
            return cached
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, 'Review not found')
    review.status = payload.status
    review.admin_notes = payload.admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user.id
    db.commit()
    result = {'message': 'Resolved'}
    if idempotency_key:
        _record_idempotency(redis, idempotency_key, "resolve_review", result)
    return result

def list_ip_reputation(is_proxy: Optional[bool]=None, is_tor: Optional[bool]=None, limit: int=Query(100, ge=1, le=1000), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List IP reputation records."""
    q = db.query(IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    return q.order_by(IPReputation.updated_at.desc()).limit(limit).all()

def list_device_fingerprints(limit: int=Query(100, ge=1, le=1000), min_risk_score: int=Query(0, ge=0), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """List device fingerprint records."""
    return db.query(DeviceFingerprint).filter(DeviceFingerprint.risk_score >= min_risk_score).order_by(DeviceFingerprint.last_seen_at.desc()).limit(limit).all()

def get_threat_feed_status(_: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Get threat feed status."""
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()
    return ThreatFeedStatus(tor_count=tor_count, proxy_count=proxy_count, hosting_asn_count=hosting_count)


