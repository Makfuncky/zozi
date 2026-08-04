"""
Security Router Service - Database operations for security-related routers.
All SQLAlchemy DB access is centralized here for the routers:
- auth
- fraud_detection  
- iam
- permissions
- incident
- risk
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from data.models import (
    FraudEvent, FraudBlacklist, FraudRule, ManualReviewQueue,
    IPReputation, DeviceFingerprint, User, IncidentWarRoom
)
from data.schemas import (
    FraudEventOut, FraudBlacklistOut, FraudRuleOut, ManualReviewOut,
    IPReputationOut, DeviceFingerprintOut, ThreatFeedStatus,
    FraudDashboardStats, ImpossibleTravelCheck, DeviceStackingCheck,
    ReturnAbuseCheck, IPAccountCheck, BINCheck, LogisticsFraudCheck
)
from models.security.permissions import Permission
from data.services_write_helpers import add_and_flush, commit_only, rollback_only
from services.security.fraud_detection_service import FraudScoringEngine, GraphAnalysisService


# ── Fraud Detection Router Service Functions ───────────────────────────────────

def list_fraud_events_db(
    db: Session,
    page: int = 1,
    size: int = 50,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    min_score: int = 0,
) -> List[FraudEventOut]:
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
        results.append(FraudEventOut(
            id=e.id,
            user_id=e.user_id,
            event_type=e.event_type,
            ip_address=e.ip_address,
            device_hash=e.device_hash,
            fraud_score=int(e.fraud_score),
            triggered_rules=json.loads(e.triggered_rules) if e.triggered_rules else [],
            status=e.status,
            created_at=e.created_at,
        ))
    return results


def list_blacklist_db(
    db: Session,
    entity_type: Optional[str] = None,
    status: str = "active",
    skip: int = 0,
    limit: int = 20,
) -> List[FraudBlacklistOut]:
    """List blacklisted entities."""
    q = db.query(FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    return q.order_by(FraudBlacklist.created_at.desc()).offset(skip).limit(limit).all()


def add_to_blacklist_db(
    db: Session,
    entity_type: str,
    entity_value: str,
    reason: str,
    expires_at: Optional[datetime] = None,
) -> FraudBlacklistOut:
    """Add entity to blacklist."""
    value_hash = hashlib.sha256(entity_value.encode()).hexdigest()

    existing = db.query(FraudBlacklist).filter(
        FraudBlacklist.entity_type == entity_type,
        FraudBlacklist.entity_value_hash == value_hash,
    ).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(400, "Entity already blacklisted")

    entry = FraudBlacklist(
        entity_type=entity_type,
        entity_value_hash=value_hash,
        reason=reason,
        expires_at=expires_at,
    )
    add_and_flush(db, entry)
    commit_only(db)
    return entry


def remove_from_blacklist_db(db: Session, entry_id: int) -> dict:
    """Remove entity from blacklist (whitelist)."""
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    commit_only(db)
    return {"message": "Entity whitelisted"}


def list_rules_db(
    db: Session,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 20,
) -> List[FraudRuleOut]:
    """List fraud detection rules."""
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).offset(skip).limit(limit).all()


def create_rule_db(
    db: Session,
    rule_key: str,
    name: str,
    description: Optional[str],
    weight: int,
    condition_json: Optional[dict],
    is_active: bool,
    is_global: bool,
    country_code: Optional[str],
) -> FraudRule:
    """Create a new fraud detection rule."""
    rule = FraudRule(
        rule_key=rule_key,
        name=name,
        description=description,
        weight=weight,
        condition_json=json.dumps(condition_json) if condition_json else None,
        is_active=is_active,
        is_global=is_global,
        country_code=country_code,
    )
    add_and_flush(db, rule)
    commit_only(db)
    return rule


def list_review_queue_db(
    db: Session,
    status: str = "pending",
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ManualReviewOut]:
    """List items pending manual review."""
    q = db.query(ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    return q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).offset(skip).limit(limit).all()


def assign_review_db(db: Session, review_id: int, assignee_id: int) -> dict:
    """Assign review to an admin."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        from fastapi import HTTPException
        raise HTTPException(404, "Review not found")
    review.assigned_to = assignee_id
    commit_only(db)
    return {"message": "Assigned"}


def resolve_review_db(
    db: Session,
    review_id: int,
    status: str,
    admin_notes: Optional[str],
    current_user_id: int,
) -> dict:
    """Resolve a manual review."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        from fastapi import HTTPException
        raise HTTPException(404, "Review not found")
    review.status = status
    review.admin_notes = admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user_id
    commit_only(db)
    return {"message": "Resolved"}


def list_ip_reputation_db(
    db: Session,
    is_proxy: Optional[bool] = None,
    is_tor: Optional[bool] = None,
    limit: int = 100,
) -> List[IPReputationOut]:
    """List IP reputation records."""
    q = db.query(IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    return q.order_by(IPReputation.updated_at.desc()).limit(limit).all()


def list_device_fingerprints_db(
    db: Session,
    limit: int = 100,
    min_risk_score: int = 0,
) -> List[DeviceFingerprintOut]:
    """List device fingerprint records."""
    return db.query(DeviceFingerprint).filter(
        DeviceFingerprint.risk_score >= min_risk_score
    ).order_by(DeviceFingerprint.last_seen_at.desc()).limit(limit).all()


def get_threat_feed_status_db(db: Session) -> ThreatFeedStatus:
    """Get threat feed status."""
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()

    return ThreatFeedStatus(
        tor_count=tor_count,
        proxy_count=proxy_count,
        hosting_asn_count=hosting_count,
    )


def get_fraud_dashboard_stats_db(db: Session) -> FraudDashboardStats:
    """Get fraud dashboard statistics."""
    from services.security.fraud_detection_service import FraudScoringEngine
    from utils.redis_client import get_redis
    engine = FraudScoringEngine(db, get_redis())
    return engine.get_fraud_dashboard_stats()


def check_impossible_travel_db(
    db: Session,
    user_id: int,
    ip_address: str,
) -> ImpossibleTravelCheck:
    """Check for impossible travel patterns."""
    from services.security.fraud_detection_service import FraudScoringEngine
    from utils.redis_client import get_redis
    engine = FraudScoringEngine(db, get_redis())
    return engine.check_impossible_travel(user_id, ip_address)


def check_device_stacking_db(db: Session, device_hash: str) -> DeviceStackingCheck:
    """Check device account stacking."""
    graph = GraphAnalysisService(db)
    return graph.check_device_account_stacking(device_hash)


def check_return_abuse_db(db: Session, user_id: int) -> ReturnAbuseCheck:
    """Check return abuse patterns."""
    graph = GraphAnalysisService(db)
    return graph.check_return_abuse_pattern(user_id)


def check_ip_accounts_db(db: Session, ip_address: str) -> IPAccountCheck:
    """Check how many accounts are linked to an IP."""
    from services.security.fraud_detection_service import FraudScoringEngine
    from utils.redis_client import get_redis
    engine = FraudScoringEngine(db, get_redis())
    return engine.check_ip_multiple_accounts(ip_address)


def check_bin_fraud_db(
    db: Session,
    card_bin: str,
    country_code: Optional[str] = None,
) -> BINCheck:
    """Check credit card BIN for fraud indicators."""
    from services.security.fraud_detection_service import FraudScoringEngine
    from utils.redis_client import get_redis
    engine = FraudScoringEngine(db, get_redis())
    return engine.check_bin_fraud(card_bin, country_code)


def check_logistics_fraud_db(
    db: Session,
    shipment_id: int,
    delivery_proof: Optional[str] = None,
    gps_coords: Optional[tuple] = None,
    scan_time: Optional[datetime] = None,
) -> LogisticsFraudCheck:
    """Check for logistics fraud patterns."""
    from services.security.fraud_detection_service import FraudScoringEngine
    from utils.redis_client import get_redis
    engine = FraudScoringEngine(db, get_redis())
    return engine.check_logistics_fraud(shipment_id, delivery_proof, gps_coords, scan_time)


def update_threat_feeds_db(db: Session) -> dict:
    """Manually trigger threat feed update."""
    from services.security.fraud_detection_service import ThreatFeedUpdater
    from utils.redis_client import get_redis
    updater = ThreatFeedUpdater(db, get_redis())
    results = updater.update_threat_feeds()
    return {"message": "Threat feeds updated", "results": results}


# ── Incident Router Service Functions ───────────────────────────────────────────

def get_war_room_db(db: Session, war_room_id: int) -> dict:
    """Get war room details."""
    war_room = db.query(IncidentWarRoom).filter_by(id=war_room_id).first()
    if not war_room:
        return {"exists": False}

    return {
        "id": war_room.id,
        "incident_id": war_room.incident_id,
        "title": war_room.title,
        "severity": war_room.severity,
        "status": war_room.status,
        "started_at": war_room.started_at.isoformat(),
        "action_items": [
            {"id": a.id, "title": a.title, "status": a.status}
            for a in war_room.action_items
        ]
    }


# ── Permissions Router Service Functions ───────────────────────────────────────

def check_user_permission_router(
    db: Session,
    user_id: int,
    permission_slug: str,
    country_code: Optional[str] = None,
) -> bool:
    """Check if user has a specific permission."""
    permission = db.query(Permission).filter(
        Permission.slug == permission_slug,
        Permission.is_active == True
    ).first()
    if not permission:
        return False

    from models.security.permissions import UserPermissionOverride
    user_override = db.query(UserPermissionOverride).filter(
        UserPermissionOverride.user_id == user_id,
        UserPermissionOverride.permission_id == permission.id,
        (
            (UserPermissionOverride.expires_at.is_(None)) |
            (UserPermissionOverride.expires_at > datetime.now(timezone.utc))
        ),
    ).first()
    return bool(user_override and user_override.is_granted)


# ── Auth Router Service Functions ─────────────────────────────────────────────

def find_user_by_credentials(
    db: Session,
    email: Optional[str] = None,
    username: Optional[str] = None,
) -> Optional[User]:
    """Find user by email or username."""
    q = db.query(User)
    if email:
        q = q.filter(User.email == email)
    elif username:
        q = q.filter(User.username == username)
    user = q.first()
    if user:
        return user
    if username and "@" in username and not email:
        return db.query(User).filter(User.email == username).first()
    return None


def find_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Find user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def record_login_history(
    db: Session,
    user: User,
    request: Optional[object] = None,
    success: bool = True,
) -> None:
    """Write a UserLoginHistory record for a login attempt."""
    from data.models import UserLoginHistory
    
    try:
        from utils.ip_utils import get_request_ip
        ip = get_request_ip(request) if request else None
        ua = request.headers.get("user-agent", "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=success,
            country_code=user.country_code,
        )
        add_and_flush(db, history)
        commit_only(db)
    except Exception:
        try:
            rollback_only(db)
        except Exception:
            pass


# ── Risk Router Service Functions ─────────────────────────────────────────────

def get_risk_score_by_employee(
    db: Session,
    employee_id: Optional[int] = None,
    limit: int = 200,
) -> list[dict]:
    """Get risk score records for an employee or all employees."""
    from sqlalchemy import text
    
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
                LIMIT :limit
            """),
            {"limit": limit},
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


def check_user_email_exists(db: Session, email: str) -> bool:
    """Check if a user email already exists."""
    return db.query(User).filter(User.email == email).first() is not None


def check_user_username_exists(db: Session, username: str) -> bool:
    """Check if a username already exists."""
    return db.query(User).filter(User.username == username).first() is not None