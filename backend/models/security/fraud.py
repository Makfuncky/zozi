from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin

__all__ = [
    "FraudEvent", "FraudBlacklist", "FraudRule", "ManualReviewQueue", "IPReputation", "DeviceFingerprint", 
    "CreditCardBin", "ReturnAbusePattern", "SupplierFraudIndicator", "LogisticsFraudIndicator", "FraudAlert", 
    "IPAccountLinkage", "VelocityCounter", "FraudScoringLog", "FraudCase", "FraudCaseAssignment",
    "DLPViolation", "MeetingTranscript", "MeetingActionItem", "MeetingRecording"
]

class FraudEvent(Base, TenantMixin):
    __tablename__ = "fraud_events"
    __table_args__ = (
        Index("ix_fraud_event_user", "user_id"),
        Index("ix_fraud_event_type", "event_type"),
        Index("ix_fraud_event_score", "fraud_score"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device_hash = Column(String(64), nullable=True)
    session_id = Column(String(128), nullable=True)
    fraud_score = Column(Numeric(5, 2), nullable=False)
    triggered_rules = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    is_flagged = Column(Boolean, default=False)
    status = Column(String(20), default="logged")
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class FraudBlacklist(Base):
    __tablename__ = "fraud_blacklist"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_value", name="uq_blacklist_identifier"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    identifier_type = Column(String, nullable=False)
    identifier_value = Column(String, nullable=False)
    identifier_value_hash = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=True)

class FraudRule(Base, TenantMixin):
    __tablename__ = "fraud_rules"
    __table_args__ = (Index("ix_fraud_rule_active", "is_active"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Integer, default=10)
    condition_json = Column(Text, nullable=True)
    action = Column(String(50), default="alert")

class ManualReviewQueue(Base):
    __tablename__ = "manual_review_queue"
    __table_args__ = (
        Index("ix_manual_review_status", "status"),
        Index("ix_manual_review_priority", "priority"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    fraud_score = Column(Integer, nullable=False)
    triggered_rules = Column(Text, nullable=True)
    reason = Column(String, nullable=False)
    priority = Column(String, default="medium")
    assigned_to = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class IPReputation(Base, TenantMixin):
    __tablename__ = "ip_reputations"
    __table_args__ = (Index("ix_ip_reputation_ip", "ip_address"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, nullable=False, index=True)
    reputation_score = Column(Numeric(5, 2), default=0)
    is_blocked = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    is_hosting = Column(Boolean, default=False)
    asn = Column(String, nullable=True)

    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    __table_args__ = (Index("ix_device_fingerprint", "fingerprint_hash"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    fingerprint_hash = Column(String, nullable=False, index=True)
    user_agent = Column(String, nullable=True)
    ip_addresses = Column(Text, nullable=True)
    is_trusted = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)
    headless_attempts = Column(Integer, default=0)
    account_count = Column(Integer, default=0)
    first_seen_at = Column(DateTime, default=_utcnow)
    last_seen_at = Column(DateTime, default=_utcnow)

    user = relationship("User")

class CreditCardBin(Base):
    __tablename__ = "credit_card_bins"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(10), unique=True, nullable=False)
    brand = Column(String(50), nullable=True)
    bank = Column(String(100), nullable=True)
    country = Column(String(10), nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

class ReturnAbusePattern(Base):
    __tablename__ = "return_abuse_patterns"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    abuse_type = Column(String(50), nullable=False)
    occurrence_count = Column(Integer, default=1)
    first_occurrence = Column(DateTime, default=_utcnow)
    last_occurrence = Column(DateTime, default=_utcnow)
    is_blocked = Column(Boolean, default=False)

    user = relationship("User")

class SupplierFraudIndicator(Base, TenantMixin):
    __tablename__ = "supplier_fraud_indicators"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    indicator_type = Column(String(50), nullable=False)
    value = Column(String, nullable=True)

class LogisticsFraudIndicator(Base, TenantMixin):
    __tablename__ = "logistics_fraud_indicators"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    indicator_type = Column(String(50), nullable=False)
    value = Column(String, nullable=True)

class FraudAlert(Base, TenantMixin):
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
    created_at = Column(DateTime, default=_utcnow)

class IPAccountLinkage(Base):
    __tablename__ = "ip_account_linkages"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    device_fingerprint = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    interaction_count = Column(Integer, default=1)
    is_suspicious = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=_utcnow)

    user = relationship("User")

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
    created_at = Column(DateTime, default=_utcnow)

class FraudScoringLog(Base, TenantMixin):
    __tablename__ = "fraud_scoring_logs"
    __table_args__ = (
        Index("ix_scoring_event", "event_type", "created_at"),
        Index("ix_scoring_score", "raw_score"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_hash = Column(String(64), nullable=True)
    session_id = Column(String(128), nullable=True)
    raw_score = Column(Integer, nullable=False)
    triggered_rules = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    action_taken = Column(String(50), default="logged")
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")

class FraudCase(Base, TenantMixin):
    __tablename__ = "fraud_cases"
    __table_args__ = (
        Index("ix_fraud_case_status", "status"),
        Index("ix_fraud_case_priority", "priority"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    fraud_score = Column(Integer, nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="open")
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    assigned_to = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

class FraudCaseAssignment(Base):
    __tablename__ = "fraud_case_assignments"

    __table_args__ = ({"schema": "security"},)

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("security.fraud_cases.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    role_at_assignment = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("FraudCase")
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])

class DLPViolation(Base):
    __tablename__ = "dlp_violations"
    __table_args__ = (
        Index("ix_dlp_status", "status"),
        Index("ix_dlp_created_at", "created_at"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    detected_content = Column(Text, nullable=True)
    action_taken = Column(String(50), default="blocked")
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

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
    created_at = Column(DateTime, default=_utcnow)

class MeetingActionItem(Base):
    __tablename__ = "meeting_action_items"
    __table_args__ = (
        Index("ix_action_item_meeting", "meeting_id"),
        Index("ix_action_item_status", "status"), {"schema": "security"})

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("security.meeting_transcripts.id"), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")
    assigned_to = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    due_date = Column(DateTime, nullable=True)

    meeting = relationship("MeetingTranscript", backref="items")
    assignee = relationship("User")

class MeetingRecording(Base):
    __tablename__ = "meeting_recordings"

    __table_args__ = ({"schema": "communication"},)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), nullable=False)
    started_by = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    recording_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(20), default="recording")
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    starter = relationship("User")
