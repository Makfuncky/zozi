"""Law 110 paired tests: fraud_detection_service.py Redis pass-through.

These tests verify the fixed behaviour:
  - Redis ConnectionError in session-anomaly Redis calls is caught and logged.
  - The request still succeeds (pass-through for cache/lookup).
  - IP-reputation lookup failures are logged, not swallowed.
  - No secret, token, or PII appears in log output.
  - Rate-limiting (_check_velocity) still fails closed (returns False on ConnectionError).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from valkey.exceptions import ConnectionError

# Ensure tests._support is importable.
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


class _FakeColumn:
    def __init__(self, name):
        self.name = name

    def desc(self):
        return self


class TestFraudServiceLaw110Paired:
    """Law 110 / Law 296: caching pass-through; rate limit fails closed."""

    def test_session_anomaly_redis_down_passes_through(self):
        """Redis ConnectionError in session-anomaly Redis calls must not raise."""
        from domains.security.services.fraud import fraud_detection_service as fds
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_first = MagicMock(return_value=None)
        mock_order_by.return_value.first = mock_first
        mock_filter.order_by = MagicMock(return_value=mock_order_by)
        mock_query.return_value.filter = MagicMock(return_value=mock_filter)
        mock_db.query = mock_query

        mock_redis = MagicMock()
        mock_redis.smembers.side_effect = ConnectionError("Valkey unreachable")
        mock_redis.sadd.side_effect = ConnectionError("Valkey unreachable")
        mock_redis.expire.side_effect = ConnectionError("Valkey unreachable")

        engine = FraudScoringEngine.__new__(FraudScoringEngine)
        engine.db = mock_db
        engine.redis = mock_redis
        engine.ip_service = MagicMock()
        engine.device_service = MagicMock()
        engine.graph_service = MagicMock()
        engine.ip_linkage_service = MagicMock()

        original_timestamp = getattr(fds.UserLoginHistory, "timestamp", None)
        fds.UserLoginHistory.timestamp = _FakeColumn("timestamp")

        try:
            result = engine.analyze_session_anomaly(
                user_id=1,
                ip_address="127.0.0.1",
                device_hash=None,
                session_id="sess-1",
            )
            assert "anomalies" in result
            assert "concurrent_session" not in result["anomalies"]
        finally:
            if original_timestamp is None:
                try:
                    del fds.UserLoginHistory.timestamp
                except NotImplementedError:
                    pass
            else:
                fds.UserLoginHistory.timestamp = original_timestamp

    def test_session_anomaly_redis_down_logs_warning(self):
        """Redis ConnectionError in session-anomaly must be logged with exc_info=True."""
        from domains.security.services.fraud import fraud_detection_service as fds
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_first = MagicMock(return_value=None)
        mock_order_by.return_value.first = mock_first
        mock_filter.order_by = MagicMock(return_value=mock_order_by)
        mock_query.return_value.filter = MagicMock(return_value=mock_filter)
        mock_db.query = mock_query

        mock_redis = MagicMock()
        mock_redis.smembers.side_effect = ConnectionError("Valkey unreachable")

        engine = FraudScoringEngine.__new__(FraudScoringEngine)
        engine.db = mock_db
        engine.redis = mock_redis
        engine.ip_service = MagicMock()
        engine.device_service = MagicMock()
        engine.graph_service = MagicMock()
        engine.ip_linkage_service = MagicMock()

        original_timestamp = getattr(fds.UserLoginHistory, "timestamp", None)
        fds.UserLoginHistory.timestamp = _FakeColumn("timestamp")

        try:
            with patch(
                "domains.security.services.fraud.fraud_detection_service.logger"
            ) as mock_logger:
                engine.analyze_session_anomaly(
                    user_id=1,
                    ip_address="127.0.0.1",
                    device_hash=None,
                    session_id="sess-1",
                )
                mock_logger.warning.assert_called()
                assert mock_logger.warning.call_args.kwargs.get("exc_info") is True
                msgs = [c.args[0] if c.args else "" for c in mock_logger.warning.call_args_list]
                assert any("active sessions" in (m or "").lower() for m in msgs)
        finally:
            if original_timestamp is None:
                try:
                    del fds.UserLoginHistory.timestamp
                except NotImplementedError:
                    pass
            else:
                fds.UserLoginHistory.timestamp = original_timestamp

    def test_session_anomaly_ip_reputation_failure_logs_warning(self):
        """IP-reputation lookup failure in session anomaly must be logged."""
        from domains.security.services.fraud import fraud_detection_service as fds
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_first = MagicMock(return_value=None)
        mock_order_by.return_value.first = mock_first
        mock_filter.order_by = MagicMock(return_value=mock_order_by)
        mock_query.return_value.filter = MagicMock(return_value=mock_filter)
        mock_db.query = mock_query

        mock_redis = MagicMock()
        mock_redis.smembers.return_value = set()
        mock_redis.sadd.return_value = 1
        mock_redis.expire.return_value = True

        engine = FraudScoringEngine.__new__(FraudScoringEngine)
        engine.db = mock_db
        engine.redis = mock_redis
        engine.ip_service = MagicMock()
        engine.ip_service.check_ip_reputation.side_effect = ConnectionError(
            "Valkey unreachable"
        )
        engine.device_service = MagicMock()
        engine.graph_service = MagicMock()
        engine.ip_linkage_service = MagicMock()

        original_timestamp = getattr(fds.UserLoginHistory, "timestamp", None)
        fds.UserLoginHistory.timestamp = _FakeColumn("timestamp")

        try:
            with patch(
                "domains.security.services.fraud.fraud_detection_service.logger"
            ) as mock_logger:
                result = engine.analyze_session_anomaly(
                    user_id=1,
                    ip_address="127.0.0.1",
                    device_hash=None,
                    session_id="sess-1",
                )
                mock_logger.warning.assert_called_once()
                assert mock_logger.warning.call_args.kwargs.get("exc_info") is True
                assert "anomalies" in result
                assert "cross_border_login" not in result["anomalies"]
        finally:
            if original_timestamp is None:
                try:
                    del fds.UserLoginHistory.timestamp
                except NotImplementedError:
                    pass
            else:
                fds.UserLoginHistory.timestamp = original_timestamp

    def test_rate_limit_path_still_fails_closed(self):
        """Rate-limiting _check_velocity still returns False on ConnectionError."""
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        mock_redis = MagicMock()
        mock_redis.incr.side_effect = ConnectionError("Valkey unreachable")

        engine = FraudScoringEngine.__new__(FraudScoringEngine)
        engine.redis = mock_redis

        result = engine._check_velocity("127.0.0.1", "login")
        assert result is False

    def test_no_secret_or_pii_in_fraud_warning_logs(self):
        """Fraud service warning logs must not contain secrets, tokens, or PII."""
        from domains.security.services.fraud import fraud_detection_service as fds
        from domains.security.services.fraud.fraud_detection_service import (
            FraudScoringEngine,
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_first = MagicMock(return_value=None)
        mock_order_by.return_value.first = mock_first
        mock_filter.order_by = MagicMock(return_value=mock_order_by)
        mock_query.return_value.filter = MagicMock(return_value=mock_filter)
        mock_db.query = mock_query

        mock_redis = MagicMock()
        mock_redis.smembers.side_effect = ConnectionError("Valkey unreachable")

        engine = FraudScoringEngine.__new__(FraudScoringEngine)
        engine.db = mock_db
        engine.redis = mock_redis
        engine.ip_service = MagicMock()
        engine.device_service = MagicMock()
        engine.graph_service = MagicMock()
        engine.ip_linkage_service = MagicMock()

        original_timestamp = getattr(fds.UserLoginHistory, "timestamp", None)
        fds.UserLoginHistory.timestamp = _FakeColumn("timestamp")

        try:
            with patch(
                "domains.security.services.fraud.fraud_detection_service.logger"
            ) as mock_logger:
                engine.analyze_session_anomaly(
                    user_id=1,
                    ip_address="127.0.0.1",
                    device_hash=None,
                    session_id="sess-1",
                )
                for call in mock_logger.warning.call_args_list:
                    msg = str(call)
                    assert "password" not in msg.lower()
                    assert "secret" not in msg.lower()
                    assert "token" not in msg.lower()
                    assert "eyj" not in msg.lower()
        finally:
            if original_timestamp is None:
                try:
                    del fds.UserLoginHistory.timestamp
                except NotImplementedError:
                    pass
            else:
                fds.UserLoginHistory.timestamp = original_timestamp
