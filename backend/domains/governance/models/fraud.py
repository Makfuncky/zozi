from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from . import Base


class CreditCardBin(Base):
    __tablename__ = "credit_card_bins"
    id = Column(Integer, primary_key=True, index=True)


class DLPViolation(Base):
    __tablename__ = "dlp_violations"
    id = Column(Integer, primary_key=True, index=True)


class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    id = Column(Integer, primary_key=True, index=True)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    id = Column(Integer, primary_key=True, index=True)


class FraudBlacklist(Base):
    __tablename__ = "fraud_blacklist"
    id = Column(Integer, primary_key=True, index=True)


class FraudCase(Base):
    __tablename__ = "fraud_cases"
    id = Column(Integer, primary_key=True, index=True)


class FraudCaseAssignment(Base):
    __tablename__ = "fraud_case_assignments"
    id = Column(Integer, primary_key=True, index=True)


class FraudEvent(Base):
    __tablename__ = "fraud_events"
    id = Column(Integer, primary_key=True, index=True)


class FraudRule(Base):
    __tablename__ = "fraud_rules"
    id = Column(Integer, primary_key=True, index=True)


class FraudScoringLog(Base):
    __tablename__ = "fraud_scoring_logs"
    id = Column(Integer, primary_key=True, index=True)


class IPAccountLinkage(Base):
    __tablename__ = "ip_account_linkages"
    id = Column(Integer, primary_key=True, index=True)


class IPReputation(Base):
    __tablename__ = "ip_reputation"
    id = Column(Integer, primary_key=True, index=True)


class LogisticsFraudIndicator(Base):
    __tablename__ = "logistics_fraud_indicators"
    id = Column(Integer, primary_key=True, index=True)


class ManualReviewQueue(Base):
    __tablename__ = "manual_review_queue"
    id = Column(Integer, primary_key=True, index=True)


class MeetingActionItem(Base):
    __tablename__ = "meeting_action_items"
    id = Column(Integer, primary_key=True, index=True)


class MeetingRecording(Base):
    __tablename__ = "meeting_recordings"
    id = Column(Integer, primary_key=True, index=True)


class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"
    id = Column(Integer, primary_key=True, index=True)


class ReturnAbusePattern(Base):
    __tablename__ = "return_abuse_patterns"
    id = Column(Integer, primary_key=True, index=True)


class SupplierFraudIndicator(Base):
    __tablename__ = "supplier_fraud_indicators"
    id = Column(Integer, primary_key=True, index=True)


class VelocityCounter(Base):
    __tablename__ = "velocity_counters"
    id = Column(Integer, primary_key=True, index=True)
