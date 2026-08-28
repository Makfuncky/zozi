"""Governance fraud models — re-exported from security domain (canonical source)."""
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
    SupplierFraudIndicator,
    VelocityCounter,
)
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
