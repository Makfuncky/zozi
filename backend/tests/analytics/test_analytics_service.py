"""Tests for FILE-47 AP-28: malformed analytics events are skipped, not counted as 'unknown'."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# _safe_load_chatbot_filters is used inside the module but not importable;
# inject a stub so the module can be imported for testing.
import domains.analytics.services.dashboards.analytics_service as _svc_mod

_svc_mod._safe_load_chatbot_filters = lambda filters_json: {}

from domains.analytics.services.dashboards.analytics_service import get_chatbot_analytics


class _FakeEvent:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_missing_intent_skips_query_event():
    db = MagicMock()
    since = datetime.now(timezone.utc).replace(tzinfo=None)
    good_event = _FakeEvent(
        event_type="query",
        intent="product_search",
        normalized_query="shoes",
        result_count=5,
        filters_json="{}",
        created_at=since,
        session_id="s1",
        user_id="u1",
    )
    bad_event = _FakeEvent(
        event_type="query",
        intent=None,
        normalized_query="bad",
        result_count=0,
        filters_json="{}",
        created_at=since,
        session_id="s2",
        user_id="u2",
    )
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [good_event, bad_event]
    db.query.return_value = mock_query

    result = get_chatbot_analytics("30d", db)

    assert result["total_queries"] == 2  # list length before processing
    # unique_sessions/users count all query_events (pre-loop), but daily_data/top_intents skip malformed
    assert result["unique_sessions"] == 2
    assert result["unique_users"] == 2
    assert result["top_queries"] == [{"query": "shoes", "count": 1}]
    assert result["top_intents"] == [{"intent": "product_search", "count": 1}]
    assert "unknown" not in [item["intent"] for item in result["top_intents"]]
    # daily_data should only contain the good event's day
    assert len(result["daily_data"]) == 1
    assert result["daily_data"][0]["queries"] == 1
    assert result["daily_data"][0]["product_searches"] == 1


def test_missing_created_at_skips_query_event():
    db = MagicMock()
    since = datetime.now(timezone.utc).replace(tzinfo=None)
    good_event = _FakeEvent(
        event_type="query",
        intent="product_search",
        normalized_query="shoes",
        result_count=5,
        filters_json="{}",
        created_at=since,
        session_id="s1",
        user_id="u1",
    )
    bad_event = _FakeEvent(
        event_type="query",
        intent="product_search",
        normalized_query="bad",
        result_count=0,
        filters_json="{}",
        created_at=None,
        session_id="s2",
        user_id="u2",
    )
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [good_event, bad_event]
    db.query.return_value = mock_query

    result = get_chatbot_analytics("30d", db)

    assert result["total_queries"] == 2
    assert len(result["daily_data"]) == 1
    assert result["daily_data"][0]["date"] == str(since.date())
    assert result["daily_data"][0]["queries"] == 1
    assert result["daily_data"][0]["product_searches"] == 1


def test_missing_created_at_skips_click_event():
    db = MagicMock()
    since = datetime.now(timezone.utc).replace(tzinfo=None)
    good_click = _FakeEvent(
        event_type="product_click",
        created_at=since,
        session_id="s1",
    )
    bad_click = _FakeEvent(
        event_type="product_click",
        created_at=None,
        session_id="s2",
    )
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [good_click, bad_click]
    db.query.return_value = mock_query

    result = get_chatbot_analytics("30d", db)

    assert result["total_clicks"] == 2  # list length before filtering
    assert len(result["daily_data"]) == 1
    assert result["daily_data"][0]["date"] == str(since.date())
    assert result["daily_data"][0]["clicks"] == 1


if __name__ == "__main__":
    test_missing_intent_skips_query_event()
    test_missing_created_at_skips_query_event()
    test_missing_created_at_skips_click_event()
    print("All FILE-47 tests passed.")
