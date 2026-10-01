"""Governance fraud models — re-exported from security and suppliers domains (canonical sources)."""
from __future__ import annotations

from domains.security.models.fraud import (
    CreditCardBin,
    DLPViolation,
    DeviceFingerprint,
    FraudAlert,
    FraudBlacklist,
    FraudCase,
    FraudCaseAssignment,
    FraudEvent,
    FraudRule,
    FraudScoringLog,
    IPAccountLinkage,
    IPReputation,
    LogisticsFraudIndicator,
    ManualReviewQueue,
    MeetingActionItem,
    MeetingTranscript,
    ReturnAbusePattern,
    VelocityCounter,
)
from domains.suppliers.models.fraud_indicators import SupplierFraudIndicator
from domains.comms.models.fraud import MeetingRecording

__all__ = [
    "CreditCardBin",
    "DLPViolation",
    "DeviceFingerprint",
    "FraudAlert",
    "FraudBlacklist",
    "FraudCase",
    "FraudCaseAssignment",
    "FraudEvent",
    "FraudRule",
    "FraudScoringLog",
    "IPAccountLinkage",
    "IPReputation",
    "LogisticsFraudIndicator",
    "ManualReviewQueue",
    "MeetingActionItem",
    "MeetingRecording",
    "MeetingTranscript",
    "ReturnAbusePattern",
    "SupplierFraudIndicator",
    "VelocityCounter",
]
