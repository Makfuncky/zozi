"""Observability tests for Valkey client fallback (OBS-014, WIR-030).

Verifies that when ``valkey_client()`` cannot reach Valkey and falls back
to ``_NoOpValkey``, it:
  1. Emits a Prometheus ``valkey_fallback_total`` counter increment.
  2. Logs a structured WARNING event.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-must-be-sixty-four-chars-long-minimum")


class TestValkeyClientFallbackObservability:
    """Verify that Valkey fallback emits metrics and logs warnings."""

    def test_noop_fallback_logs_warning_and_increments_metric(self):
        from infrastructure.valkey import client as client_module
        from infrastructure.valkey.client import valkey_client, _NoOpValkey

        # Reset singleton to force re-creation
        client_module._client = None

        mock_client = MagicMock()
        mock_client.ping.side_effect = ConnectionError("Valkey unavailable")

        with patch(
            "infrastructure.valkey.client.valkey.Valkey.from_url",
            return_value=mock_client,
        ):
            with patch.object(
                client_module, "_valkey_fallback_total"
            ) as mock_metric:
                with patch.object(
                    client_module.logger, "warning"
                ) as mock_warning:
                    result = valkey_client()

                    assert isinstance(result, _NoOpValkey)
                    mock_warning.assert_called_once()
                    mock_metric.inc.assert_called_once()
