"""Regression tests for threat_feed_updater module and error path."""
from __future__ import annotations

import asyncio
import inspect
import logging

import pytest

import jobs.threat_feed_updater  # noqa: F401


def test_threat_feed_update_is_async_function():
    """update_threat_feeds must be an async function."""
    from jobs.threat_feed_updater import update_threat_feeds

    assert inspect.iscoroutinefunction(update_threat_feeds), (
        "update_threat_feeds should be an async function"
    )


def test_threat_feed_logger_is_configured():
    """Logger must be configured and support standard logging methods."""
    from jobs.threat_feed_updater import logger

    assert isinstance(logger, logging.Logger), "logger should be a stdlib Logger"
    assert hasattr(logger, "error"), "logger missing error method"
    assert hasattr(logger, "info"), "logger missing info method"


def test_threat_feed_error_path_logs_and_returns_empty():
    """Error-path: when fetch fails, the error is logged and an empty set is returned."""
    from unittest import mock

    mock_response = mock.MagicMock()
    mock_response.status = 200
    mock_response.text = mock.AsyncMock(side_effect=RuntimeError("boom"))

    mock_cm = mock.MagicMock()
    mock_cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
    mock_cm.__aexit__ = mock.AsyncMock(return_value=False)

    mock_session = mock.MagicMock()
    mock_session.get.return_value = mock_cm

    from jobs.threat_feed_updater import fetch_ip_list

    with mock.patch("jobs.threat_feed_updater.logger") as mock_logger:
        result = asyncio.run(fetch_ip_list(mock_session, "http://example.com/feed"))
        assert result == set()
        mock_logger.error.assert_called_once()
