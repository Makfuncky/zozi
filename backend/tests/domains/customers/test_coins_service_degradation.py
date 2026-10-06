"""Law 75 paired tests: zozi_coins_service.py must log warnings on Redis errors.

These tests verify the fixed behaviour:
  - Every bare except block now logs with exc_info=True.
  - The operation still degrades safely (return values unchanged).
  - No secret, token, PII, or coin balance appears in log output.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure tests._support is importable.
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


class TestCoinsServiceLaw75Paired:
    """Law 75 / Law 298: no event silently dropped."""

    def test_acquire_redemption_lock_logs_warning_on_redis_error(self):
        """_acquire_redemption_lock logs warning when Redis raises."""
        from domains.customers.services.coins.zozi_coins_service import (
            _acquire_redemption_lock,
        )

        mock_redis = MagicMock()
        mock_redis.set.side_effect = ConnectionError("Valkey unreachable")

        with patch(
            "domains.customers.services.coins.zozi_coins_service.get_valkey_client",
            return_value=mock_redis,
        ):
            with patch(
                "domains.customers.services.coins.zozi_coins_service.logger"
            ) as mock_logger:
                result = _acquire_redemption_lock(1)
                assert result is True
                mock_logger.warning.assert_called_once()
                call_kwargs = mock_logger.warning.call_args
                assert call_kwargs.kwargs.get("exc_info") is True
                log_msg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("msg", "")
                assert "coin" in log_msg.lower() or "lock" in log_msg.lower()

    def test_release_redemption_lock_logs_warning_on_redis_error(self):
        """_release_redemption_lock logs warning when Redis raises."""
        from domains.customers.services.coins.zozi_coins_service import (
            _release_redemption_lock,
        )

        mock_redis = MagicMock()
        mock_redis.delete.side_effect = ConnectionError("Valkey unreachable")

        with patch(
            "domains.customers.services.coins.zozi_coins_service.get_valkey_client",
            return_value=mock_redis,
        ):
            with patch(
                "domains.customers.services.coins.zozi_coins_service.logger"
            ) as mock_logger:
                _release_redemption_lock(1)
                mock_logger.warning.assert_called_once()
                assert mock_logger.warning.call_args.kwargs.get("exc_info") is True

    def test_check_idempotency_key_logs_warning_on_redis_error(self):
        """_check_idempotency_key logs warning when Redis raises."""
        from domains.customers.services.coins.zozi_coins_service import (
            _check_idempotency_key,
        )

        mock_redis = MagicMock()
        mock_redis.get.side_effect = ConnectionError("Valkey unreachable")

        with patch(
            "domains.customers.services.coins.zozi_coins_service.get_valkey_client",
            return_value=mock_redis,
        ):
            with patch(
                "domains.customers.services.coins.zozi_coins_service.logger"
            ) as mock_logger:
                result = _check_idempotency_key("idem-key")
                assert result is None
                mock_logger.warning.assert_called_once()
                assert mock_logger.warning.call_args.kwargs.get("exc_info") is True

    def test_store_idempotency_result_logs_warning_on_redis_error(self):
        """_store_idempotency_result logs warning when Redis raises."""
        from domains.customers.services.coins.zozi_coins_service import (
            _store_idempotency_result,
        )

        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Valkey unreachable")

        with patch(
            "domains.customers.services.coins.zozi_coins_service.get_valkey_client",
            return_value=mock_redis,
        ):
            with patch(
                "domains.customers.services.coins.zozi_coins_service.logger"
            ) as mock_logger:
                _store_idempotency_result("idem-key", {"event_id": 1})
                mock_logger.warning.assert_called_once()
                assert mock_logger.warning.call_args.kwargs.get("exc_info") is True

    def test_no_coin_balance_or_pii_in_warning_logs(self):
        """Warning logs must not contain coin balances, secrets, or PII."""
        from domains.customers.services.coins.zozi_coins_service import (
            _acquire_redemption_lock,
            _check_idempotency_key,
            _release_redemption_lock,
            _store_idempotency_result,
        )

        for fn, args in [
            (_acquire_redemption_lock, (1,)),
            (_release_redemption_lock, (1,)),
            (_check_idempotency_key, ("idem-key",)),
            (_store_idempotency_result, ("idem-key", {"event_id": 1, "user_id": 1, "points": -10})),
        ]:
            mock_redis = MagicMock()
            mock_redis.set.side_effect = ConnectionError("Valkey unreachable")
            mock_redis.delete.side_effect = ConnectionError("Valkey unreachable")
            mock_redis.get.side_effect = ConnectionError("Valkey unreachable")
            mock_redis.setex.side_effect = ConnectionError("Valkey unreachable")

            with patch(
                "domains.customers.services.coins.zozi_coins_service.get_valkey_client",
                return_value=mock_redis,
            ):
                with patch(
                    "domains.customers.services.coins.zozi_coins_service.logger"
                ) as mock_logger:
                    fn(*args)
                    for call in mock_logger.warning.call_args_list:
                        msg = str(call)
                        assert "10" not in msg  # coin amount
                        assert "password" not in msg.lower()
                        assert "secret" not in msg.lower()
                        assert "token" not in msg.lower()
