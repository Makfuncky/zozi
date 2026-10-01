"""Regression tests for fraud_monitoring.py canonical location and imports.

Verifies that:
- The legacy root monitoring/fraud_monitoring.py has been removed (CFM-001).
- The canonical copy at backend/jobs/fraud_monitoring.py uses current-architecture
  import paths and does not retain legacy db.database /
  services.fraud_detection / services.notification_service paths.
"""
from __future__ import annotations

import pathlib

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
JOBS_DIR = BACKEND_DIR / "jobs"
FRAUD_MONITORING_PATH = JOBS_DIR / "fraud_monitoring.py"
ROOT_MONITORING_DIR = BACKEND_DIR.parent / "monitoring"
LEGACY_FRAUD_MONITORING_PATH = ROOT_MONITORING_DIR / "fraud_monitoring.py"


def test_legacy_fraud_monitoring_removed():
    """The legacy root monitoring/fraud_monitoring.py must no longer exist."""
    assert not LEGACY_FRAUD_MONITORING_PATH.exists(), (
        f"{LEGACY_FRAUD_MONITORING_PATH} must not exist; "
        "it was a verified duplicate of backend/jobs/fraud_monitoring.py."
    )


def test_canonical_fraud_monitoring_exists():
    """The canonical backend/jobs/fraud_monitoring.py must exist."""
    assert FRAUD_MONITORING_PATH.exists(), (
        f"{FRAUD_MONITORING_PATH} must exist as the single source of truth."
    )


def test_fraud_monitoring_uses_current_architecture_imports():
    """Import paths must follow the current architecture, not the legacy layout."""
    source = FRAUD_MONITORING_PATH.read_text(encoding="utf-8")

    # Current-architecture imports that must be present (canonical copy pattern).
    assert "from infrastructure.database.database import SessionLocal" in source, (
        "fraud_monitoring.py must import SessionLocal from "
        "infrastructure.database.database (current architecture)."
    )
    assert (
        "from domains.governance.services.fraud.fraud_detection import FraudDetectionService"
        in source
    ), (
        "fraud_monitoring.py must import FraudDetectionService from the current "
        "architecture governance fraud package."
    )
    assert (
        "from domains.comms.services.notification.notification_service import NotificationService"
        in source
    ), (
        "fraud_monitoring.py must import NotificationService from the current "
        "architecture comms notification package."
    )


def test_fraud_monitoring_does_not_use_legacy_imports():
    """Old/stale import paths must have been removed."""
    source = FRAUD_MONITORING_PATH.read_text(encoding="utf-8")

    assert "from db.database import" not in source, (
        "Legacy 'db.database' import path must not remain in "
        "fraud_monitoring.py."
    )
    assert "from services.fraud_detection import" not in source, (
        "Legacy 'services.fraud_detection' import path must not remain in "
        "fraud_monitoring.py."
    )
    assert "from services.notification_service import" not in source, (
        "Legacy 'services.notification_service' import path must not remain in "
        "fraud_monitoring.py."
    )


def test_fraud_monitoring_exports_expected_functions():
    """The file must still expose the two public job functions."""
    source = FRAUD_MONITORING_PATH.read_text(encoding="utf-8")

    assert "def run_ghost_employee_detection():" in source, (
        "run_ghost_employee_detection function must be preserved."
    )
    assert "def run_anomaly_detection():" in source, (
        "run_anomaly_detection function must be preserved."
    )
