"""Domain tests for security — fraud detection, IAM, and threat intelligence."""
from __future__ import annotations

import pytest


class TestSecurityServiceImports:
    """Smoke tests: verify security service modules are importable."""

    def test_import_fraud_detection_service(self):
        from domains.security.services.fraud import fraud_detection_service

        assert fraud_detection_service is not None

    def test_import_iam_service(self):
        from domains.security.services.iam import iam_service

        assert iam_service is not None

    def test_import_security_service(self):
        from domains.security.services.core import security_service

        assert security_service is not None

    def test_import_security_models(self):
        from domains.security.models.fraud import FraudEvent, FraudRule, FraudBlacklist

        assert FraudEvent is not None
        assert FraudRule is not None
        assert FraudBlacklist is not None

    def test_import_security_schemas(self):
        from domains.security.schemas.security_schemas import FraudEventOut, FraudRuleOut

        assert FraudEventOut is not None
        assert FraudRuleOut is not None

    def test_import_security_ports(self):
        from domains.security.ports import get_fraud_event_by_id

        assert callable(get_fraud_event_by_id)

    def test_import_security_features(self):
        from domains.security.features import SECURITY_FEATURES

        assert isinstance(SECURITY_FEATURES, (list, tuple, set))


class TestFraudDetection:
    """Tests for fraud detection operations."""

    def test_fraud_detection_has_scoring_engine(self):
        from domains.security.services.fraud.fraud_detection_service import FraudScoringEngine

        assert FraudScoringEngine is not None

    def test_fraud_detection_has_velocity_check(self):
        from domains.security.services.fraud.fraud_detection_service import check_velocity_limits

        assert callable(check_velocity_limits)

    def test_fraud_event_model_fields(self, db_session):
        from domains.security.models.fraud import FraudEvent

        event = FraudEvent(
            user_id=1,
            ip_address="127.0.0.1",
            fraud_score=75,
            risk_level="high",
        )
        db_session.add(event)
        db_session.flush()

        assert event.id is not None
        assert event.user_id == 1
        assert event.fraud_score == 75

    def test_fraud_rule_model_fields(self, db_session):
        from domains.security.models.fraud import FraudRule

        rule = FraudRule(
            name="Test Rule",
            rule_type="velocity",
            threshold=10,
            is_active=True,
        )
        db_session.add(rule)
        db_session.flush()

        assert rule.id is not None
        assert rule.name == "Test Rule"
        assert rule.is_active is True


class TestIAMOperations:
    """Tests for IAM operations."""

    def test_iam_service_has_geo_fence_validator(self):
        from domains.security.services.iam.iam_service import GeoFenceValidator

        assert GeoFenceValidator is not None
        assert hasattr(GeoFenceValidator, "haversine_distance")

    def test_geo_fence_haversine(self):
        from domains.security.services.iam.iam_service import GeoFenceValidator

        distance = GeoFenceValidator.haversine_distance(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

    def test_security_service_list_fraud_events(self):
        from domains.security.services.core.security_service import list_fraud_events

        assert callable(list_fraud_events)

    def test_security_metrics_exists(self):
        from domains.security.services.core.security_metrics import SecurityMetricsCollector

        assert SecurityMetricsCollector is not None
