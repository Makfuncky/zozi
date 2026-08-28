"""Security domain — feature + service smoke tests.

Laws 4 (features), 2 (thin routers), 33/38/43 (security invariants).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


class TestSecurityFeatureAtoms:
    """Law 4 — representative security feature atoms in rbac catalog."""

    @pytest.mark.parametrize(
        "feature",
        [
            "security.read",
            "security.events.read",
            "security.events.manage",
            "security.sessions.read",
            "security.sessions.manage",
            "security.mfa.manage",
            "security.api_keys.manage",
            "security.policies.manage",
            "security.incident.manage",
            "fraud.detection.view",
            "fraud.detection.manage",
            "fraud.investigation",
            "threat.monitoring.view",
            "threat.monitoring.manage",
            "threat.response",
        ],
    )
    def test_feature_in_catalog(self, feature):
        from tests._support.laws import assert_feature_in_catalog

        assert_feature_in_catalog(feature)


class TestSecurityServiceImports:
    """Law 2 — service layer is importable."""

    def test_import_fraud_detection_service(self):
        from domains.security.services.fraud import fraud_detection_service

        assert fraud_detection_service is not None

    def test_import_iam_service(self):
        from domains.security.services.iam import iam_service

        assert iam_service is not None

    def test_import_security_service(self):
        from domains.security.services.core import security_service

        assert security_service is not None

    def test_import_security_metrics(self):
        from domains.security.services.core.security_metrics import (
            SecurityMetricsCollector,
        )

        assert SecurityMetricsCollector is not None


class TestSecurityModelPersistence:
    """Laws 6/23 — models persist with audit columns."""

    def test_fraud_event_persists(self, db_session):
        from domains.security.models.fraud import FraudEvent

        event = FraudEvent(
            user_id=1,
            event_type="test",
            fraud_score=50,
            ip_address="127.0.0.1",
        )
        db_session.add(event)
        db_session.flush()

        assert event.id is not None
        assert event.created_at is not None
        assert event.is_deleted is False

    def test_fraud_rule_persists(self, db_session):
        from domains.security.models.fraud import FraudRule

        rule = FraudRule(
            rule_key="test_rule_001",
            name="Test Rule",
            condition_json="{}",
        )
        db_session.add(rule)
        db_session.flush()

        assert rule.id is not None
        assert rule.is_deleted is False


class TestSecurityFraudDetection:
    """Law 43 — fraud detection service is functional."""

    def test_fraud_scoring_engine_exists(self):
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        assert FraudScoringEngine is not None

    def test_velocity_check_callable(self):
        from domains.security.services.fraud.fraud_detection_service import (
            check_velocity_limits,
        )

        assert callable(check_velocity_limits)


class TestSecurityGeoFence:
    """Law 33 — geo-fence validator is functional."""

    def test_geo_fence_haversine(self):
        from domains.security.services.iam.iam_service import GeoFenceValidator

        distance = GeoFenceValidator.haversine_distance(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

    def test_geo_fence_haversine_real_distance(self):
        from domains.security.services.iam.iam_service import GeoFenceValidator

        # Dubai -> Abu Dhabi ~150 km
        distance = GeoFenceValidator.haversine_distance(
            25.2048, 55.2708, 24.4539, 54.3773
        )
        assert 100 < distance < 200
