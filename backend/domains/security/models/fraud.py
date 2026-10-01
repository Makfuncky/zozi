from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "FraudEvent", "FraudBlacklist", "FraudRule", "ManualReviewQueue", "IPReputation", "DeviceFingerprint", 
    "CreditCardBin", "ReturnAbusePattern", "LogisticsFraudIndicator", "FraudAlert", 
    "IPAccountLinkage", "VelocityCounter", "FraudScoringLog", "FraudCase", "FraudCaseAssignment",
    "DLPViolation", "MeetingTranscript", "MeetingActionItem"
]


class FraudEvent(Base):
    __tablename__ = "fraud_events"
    __table_args__ = (
        Index("ix_fraud_event_user", "user_id"),
        Index("ix_fraud_event_type", "event_type"),
        Index("ix_fraud_event_score", "fraud_score"),
        CheckConstraint("status_code IN ('logged', 'reviewing', 'flagged', 'dismissed', 'escalated', 'resolved')", name="chk_fraud_events_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete='CASCADE'), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device_hash = Column(String(64), nullable=True)
    session_id = Column(String(128), nullable=True)
    fraud_score = Column(Numeric(5, 2), nullable=False)
    triggered_rules = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    is_flagged = Column(Boolean, default=False)
    status_code = Column(String(20), default="logged")
    reviewed_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)
    
    user = relationship("User", foreign_keys=[user_id], backref="fraud_events")
    reviewer = relationship("User", foreign_keys=[reviewed_by_id], backref="fraud_reviewed_events")


class FraudBlacklist(Base):
    __tablename__ = "fraud_blacklists"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_value", name="uq_blacklist_identifier"),
        CheckConstraint("status_code IN ('active', 'inactive', 'expired')", name="chk_fraud_blacklist_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    identifier_type = Column(String(50), nullable=False)
    identifier_value = Column(String(100), nullable=False)
    identifier_value_hash = Column(String(100), nullable=True)
    reason = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    status_code = Column(String(50), default="active")
    created_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)


class FraudRule(Base):
    __tablename__ = "fraud_rules"
    __table_args__ = (Index("ix_fraud_rule_active", "is_active"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Integer, default=10)
    condition_json = Column(Text, nullable=True)
    action = Column(String(50), default="alert")
    is_active = Column(Boolean, default=True)
    is_global = Column(Boolean, default=True)
    country_code = Column(String(2), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


class ManualReviewQueue(Base):
    __tablename__ = "manual_review_queues"
    __table_args__ = (
        Index("ix_manual_review_status", "status_code"),
        Index("ix_manual_review_priority", "priority"),
        CheckConstraint("status_code IN ('queued', 'in_review', 'approved', 'rejected', 'escalated')", name="chk_manual_review_queue_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    fraud_score = Column(Integer, nullable=False)
    triggered_rules = Column(Text, nullable=True)
    reason = Column(String(255), nullable=False)
    priority = Column(String(50), default="medium")
    assigned_to_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    admin_notes = Column(Text, nullable=True)
    status_code = Column(String(50), default="queued")
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


class IPReputation(Base):
    __tablename__ = "ip_reputations"
    __table_args__ = (Index("ix_ip_reputation_ip", "ip_address"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(255), nullable=False, index=True)
    reputation_score = Column(Numeric(5, 2), default=0)
    is_blocked = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    is_hosting = Column(Boolean, default=False)
    asn = Column(String(255), nullable=True)
    country_code = Column(String(2), nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    __table_args__ = (Index("ix_device_fingerprint", "fingerprint_hash"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    fingerprint_hash = Column(String(255), nullable=False, index=True)
    user_agent = Column(String(255), nullable=True)
    ip_addresses = Column(Text, nullable=True)
    is_trusted = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)
    headless_attempts = Column(Integer, default=0)
    account_count = Column(Integer, default=0)
    first_seen_at = Column(DateTime, default=_utcnow)
    last_seen_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    user = relationship("User", backref="device_fingerprints")


class CreditCardBin(Base):
    __tablename__ = "credit_card_bins"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(10), unique=True, nullable=False)
    brand = Column(String(50), nullable=True)
    bank = Column(String(100), nullable=True)
    country = Column(String(10), nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


class ReturnAbusePattern(Base):
    __tablename__ = "return_abuse_patterns"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    abuse_type = Column(String(50), nullable=False)
    occurrence_count = Column(Integer, default=1)
    first_occurrence = Column(DateTime, default=_utcnow)
    last_occurrence = Column(DateTime, default=_utcnow)
    is_blocked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    user = relationship("User", backref="return_abuse_patterns")


class LogisticsFraudIndicator(Base):
    __tablename__ = "logistics_fraud_indicators"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete='CASCADE'), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    fraud_score = Column(Numeric(5, 2), nullable=False)
    triggered_rules = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")
    details = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)


class IPAccountLinkage(Base):
    __tablename__ = "ip_account_linkages"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    device_fingerprint = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)
    interaction_count = Column(Integer, default=1)
    is_suspicious = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    user = relationship("User", backref="ip_account_linkages")


class VelocityCounter(Base):
    __tablename__ = "fraud_velocity_counters"
    __table_args__ = (Index("ix_velocity_key", "key", "window_start"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, index=True)
    count = Column(Integer, default=1)
    window_start = Column(DateTime, default=_utcnow)
    window_end = Column(DateTime, nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


class FraudScoringLog(Base):
    __tablename__ = "fraud_scoring_logs"
    __table_args__ = (
        Index("ix_scoring_event", "event_type", "created_at"),
        Index("ix_scoring_score", "raw_score"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete='CASCADE'), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    device_hash = Column(String(64), nullable=True)
    session_id = Column(String(128), nullable=True)
    raw_score = Column(Integer, nullable=False)
    triggered_rules = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    action_taken = Column(String(50), default="logged")
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)
    
    user = relationship("User", backref="fraud_scoring_logs")


class FraudCase(Base):
    __tablename__ = "fraud_cases"
    __table_args__ = (
        Index("ix_fraud_case_status", "status_code"),
        Index("ix_fraud_case_priority", "priority"),
        CheckConstraint("status_code IN ('open', 'investigating', 'resolved', 'closed', 'dismissed')", name="chk_fraud_cases_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    fraud_score = Column(Integer, nullable=False)
    priority = Column(String(20), default="medium")
    status_code = Column(String(20), default="open")
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    assignee = relationship("User", foreign_keys=[assigned_to_id])
    creator = relationship("User", foreign_keys=[created_by_id])


class FraudCaseAssignment(Base):
    __tablename__ = "fraud_case_assignments"
    
    __table_args__ = ({"schema": "security"},)
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("security.fraud_cases.id", ondelete='CASCADE'), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    role_at_assignment = Column(String(50), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)
    
    case = relationship("FraudCase")
    assignee = relationship("User", foreign_keys=[assigned_to_id])
    assigner = relationship("User", foreign_keys=[assigned_by_id])


class DLPViolation(Base):
    __tablename__ = "dlp_violations"
    __table_args__ = (
        Index("ix_dlp_status", "status_code"),
        Index("ix_dlp_created_at", "created_at"),
        CheckConstraint("status_code IN ('pending', 'reviewing', 'action_taken', 'dismissed', 'escalated')", name="chk_dlp_violations_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True)
    detected_content = Column(Text, nullable=True)
    action_taken = Column(String(50), default="blocked")
    status_code = Column(String(20), default="pending")
    reviewed_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)
    
    sender = relationship("User", foreign_keys=[sender_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])


class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"
    __table_args__ = (Index("ix_transcript_room", "room_id"), {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), nullable=False)
    language = Column(String(10), default="en")
    segments = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)


class MeetingActionItem(Base):
    __tablename__ = "meeting_action_items"
    __table_args__ = (
        Index("ix_action_item_meeting", "meeting_id"),
        Index("ix_action_item_status", "status_code"),
        CheckConstraint("status_code IN ('pending', 'in_progress', 'completed', 'cancelled', 'deferred')", name="chk_meeting_action_items_status_valid"),
        {"schema": "security"})
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("security.meeting_transcripts.id", ondelete='CASCADE'), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    action = Column(String(255), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    status_code = Column(String(20), default="pending")
    assigned_to_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    due_date = Column(DateTime, nullable=True)
    
    meeting = relationship("MeetingTranscript", backref="items")
    assignee = relationship("User")


