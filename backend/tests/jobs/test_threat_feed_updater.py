"""Regression tests for threat_feed_updater task registration and error path."""
from __future__ import annotations

import os

os.environ["SECRET_KEY"] = "a" * 64

import jobs.threat_feed_updater  # noqa: F401


def test_threat_feed_task_has_celery_attributes():
    """Regression: update_threat_feeds must be a Celery task with proper attrs."""
    from jobs.threat_feed_updater import update_threat_feeds

    assert hasattr(update_threat_feeds, "name"), "update_threat_feeds missing Celery task name"
    assert update_threat_feeds.name == "jobs.threat_feed_updater.update_threat_feeds"
    assert update_threat_feeds.time_limit == 1800
    assert update_threat_feeds.soft_time_limit == 1500
    assert update_threat_feeds.max_retries == 3
    assert update_threat_feeds.default_retry_delay == 60


def test_threat_feed_uses_structlog():
    """Regression: logger must be structlog, not stdlib logging."""
    from jobs.threat_feed_updater import logger

    assert hasattr(logger, "bind"), "logger is not a structlog BoundLogger"
    assert hasattr(logger, "info"), "logger missing structlog info method"


def test_threat_feed_error_path_calls_capture_exception():
    """Error-path: when fetch fails, capture_exception must be called."""
    from unittest import mock

    with mock.patch(
        "jobs.threat_feed_updater.capture_exception"
    ) as mock_capture:
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.text = mock.AsyncMock(side_effect=RuntimeError("boom"))

        mock_cm = mock.MagicMock()
        mock_cm.__aenter__ = mock.AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = mock.AsyncMock(return_value=False)

        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_cm

        from jobs.threat_feed_updater import fetch_ip_list
        import asyncio

        result = asyncio.run(fetch_ip_list(mock_session, "http://example.com/feed"))
        assert result == set()
        mock_capture.assert_called_once()
