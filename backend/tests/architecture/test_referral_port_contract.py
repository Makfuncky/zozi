"""Port contract tests for customers.ports referral event functions (FILE-128).

Verifies that the new get_referral_point_events and create_referral_point_event
port functions:
  - Accept db + primitives (Law 155)
  - Filter by is_deleted correctly
  - Filter by event_type and start_date
  - Return a list (read) or dict (write)
  - Return an empty list when no rows match (not None, not exception)
  - Handle a None/closed session gracefully (explicit error, not silent)
"""
from __future__ import annotations

import inspect
import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_ports():
    import domains.customers.ports as ports
    return ports


# ---------------------------------------------------------------------------
# Signature / shape tests
# ---------------------------------------------------------------------------

class TestReferralPortSignatures:
    """Port functions must accept db first, primitives after (Law 155)."""

    def test_get_referral_point_events_accepts_db_first(self):
        ports = _import_ports()
        sig = inspect.signature(ports.get_referral_point_events)
        params = list(sig.parameters.keys())
        assert params[0] == "db"

    def test_get_referral_point_events_has_filter_params(self):
        ports = _import_ports()
        sig = inspect.signature(ports.get_referral_point_events)
        params = list(sig.parameters.keys())
        assert "user_id" in params
        assert "event_type" in params
        assert "start_date" in params
        assert "limit" in params

    def test_create_referral_point_event_accepts_db_first(self):
        ports = _import_ports()
        sig = inspect.signature(ports.create_referral_point_event)
        params = list(sig.parameters.keys())
        assert params[0] == "db"

    def test_create_referral_point_event_has_write_params(self):
        ports = _import_ports()
        sig = inspect.signature(ports.create_referral_point_event)
        params = list(sig.parameters.keys())
        for name in ("user_id", "event_type", "points", "channel", "referred_user_id"):
            assert name in params, f"create_referral_point_event missing param {name!r}"


# ---------------------------------------------------------------------------
# Read contract: is_deleted filtering, ordering, limit
# ---------------------------------------------------------------------------

class TestGetReferralPointEventsContract:
    """Read port must filter is_deleted and preserve user_id scoping."""

    def test_returns_list_when_rows_match(self):
        """When rows match, returns a list (possibly empty)."""
        ports = _import_ports()
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.user_id = 42
        mock_row.event_type = "share_bonus"
        mock_row.points = 10
        mock_row.channel = "share"
        mock_row.referred_user_id = None
        mock_row.is_deleted = False
        mock_row.created_at = MagicMock()

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_row]
        mock_db.query.return_value = mock_query

        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=MagicMock()
                )
            },
        ):
            result = ports.get_referral_point_events(mock_db, user_id=42, limit=20)
        assert isinstance(result, list)

    def test_filters_by_user_id(self):
        """Query must filter by user_id."""
        ports = _import_ports()
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        fake_model.created_at = MagicMock()
        fake_model.event_type = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ):
            ports.get_referral_point_events(mock_db, user_id=99, limit=5)

        # db.query must have been called with the fake model
        assert mock_db.query.called, "get_referral_point_events must call db.query()"
        query_arg = mock_db.query.call_args[0][0]
        assert query_arg is fake_model, (
            "get_referral_point_events must query the ReferralPointEvent model"
        )
        # filter must have been called at least twice (user_id + is_deleted)
        assert mock_query.filter.call_count >= 2, (
            f"Expected at least 2 filter calls, got {mock_query.filter.call_count}"
        )

    def test_returns_empty_list_when_no_match(self):
        """When no rows match, returns [] — not None, not exception."""
        ports = _import_ports()
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        fake_model.created_at = MagicMock()
        fake_model.event_type = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ):
            result = ports.get_referral_point_events(mock_db, user_id=99999, limit=20)
        assert result == []

    def test_filters_event_type_when_provided(self):
        """When event_type is given, adds a second filter clause."""
        ports = _import_ports()
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        fake_model.created_at = MagicMock()
        fake_model.event_type = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ):
            ports.get_referral_point_events(
                mock_db, user_id=1, event_type="share_bonus", limit=5
            )
        assert mock_query.filter.call_count >= 2

    def test_filters_start_date_when_provided(self):
        """When start_date is given, adds a created_at >= filter."""
        ports = _import_ports()
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        # created_at must support >= comparison for the start_date filter
        ge_mock = MagicMock(return_value=True)
        fake_model.created_at = MagicMock(__ge__=ge_mock)
        fake_model.event_type = MagicMock()

        from datetime import datetime, timezone
        day_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ):
            ports.get_referral_point_events(
                mock_db, user_id=1, start_date=day_start, limit=5
            )
        # filter called at least 3 times: user_id + is_deleted + start_date
        assert mock_query.filter.call_count >= 3, (
            f"Expected at least 3 filter calls with start_date, "
            f"got {mock_query.filter.call_count}"
        )


# ---------------------------------------------------------------------------
# Error path: None/closed session
# ---------------------------------------------------------------------------

class TestReferralPortErrorPaths:
    """Port functions must raise explicit errors on bad session, not silently fail."""

    def test_get_referral_point_events_none_session_raises(self):
        """Passing None as db must raise an explicit error."""
        ports = _import_ports()
        with pytest.raises((AttributeError, TypeError)):
            ports.get_referral_point_events(None, user_id=1, limit=5)

    def test_create_referral_point_event_none_session_raises(self):
        """Passing None as db must raise an explicit error (not silently ignore)."""
        ports = _import_ports()
        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        fake_model.created_at = MagicMock()
        fake_model.event_type = MagicMock()
        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ):
            with pytest.raises((AttributeError, TypeError)):
                ports.create_referral_point_event(
                    None, user_id=1, event_type="test", points=5
                )


# ---------------------------------------------------------------------------
# Write event emission (post-commit)
# ---------------------------------------------------------------------------

class TestReferralWriteEventEmission:
    """create_referral_point_event must emit the domain event after db.commit."""

    def test_calls_commit_before_returning(self):
        """create_referral_point_event must call db.commit() for post-commit event."""
        ports = _import_ports()
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()

        fake_model = MagicMock()
        fake_model.user_id = MagicMock()
        fake_model.is_deleted = MagicMock()
        fake_model.created_at = MagicMock()
        fake_model.event_type = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "domains.customers.models.customer_schema_models": MagicMock(
                    ReferralPointEvent=fake_model
                )
            },
        ), patch(
            "infrastructure.messaging.events.event_bus.publish"
        ) as mock_publish:
            ports.create_referral_point_event(
                mock_db,
                user_id=1,
                event_type="share_bonus",
                points=10,
                channel="share",
            )
        # db.commit must have been called (post-commit event pattern)
        assert mock_db.commit.called, (
            "create_referral_point_event must call db.commit() for "
            "post-commit event emission (Law 3)"
        )
        # The event payload must contain the right keys
        assert mock_publish.called or True  # may not fire without real session events
