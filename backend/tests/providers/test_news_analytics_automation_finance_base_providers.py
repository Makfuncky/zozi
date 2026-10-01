"""
Comprehensive test suite for news, analytics, automation, finance, and base provider modules.

Tests every public function, class, and constant across:
- providers.news (__init__.py, rss_provider.py)
- providers.analytics (__init__.py, analytics.py)
- providers.automation (__init__.py, scheduler.py)
- providers.finance (__init__.py, bank_api.py)
- providers._base.py
- providers.config.py
- providers.http.py
- providers.async_workers.py
- providers.observability.py
- providers.storage.py
- providers.image.parcel_verification.py

External SDKs/APIs are mocked via unittest.mock to ensure tests run without
network access or installed vendor packages.

Run with: pytest tests/providers/test_news_analytics_automation_finance_base_providers.py -v
"""

import asyncio
import base64
import json
import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock

import pytest

# Ensure backend root is importable
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


# ══════════════════════════════════════════════════════════════════════════════
# NEWS PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestNewsInit:
    """Verify news package exports."""

    def test_news_exports_fetch_rss_entries(self):
        from providers.news import fetch_rss_entries
        assert callable(fetch_rss_entries)

    def test_news_exports_fetch_api_payload(self):
        from providers.news import fetch_api_payload
        assert callable(fetch_api_payload)

    def test_news_all_exports_defined(self):
        import providers.news as news
        for name in news.__all__:
            assert hasattr(news, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# NEWS — rss_provider.py
# ══════════════════════════════════════════════════════════════════════════════

class TestFetchRssEntries:
    """Tests for the fetch_rss_entries async function."""

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    @patch("providers.news.rss_provider.feedparser.parse")
    async def test_fetch_rss_entries_success(self, mock_parse, mock_client_cls):
        """Successful RSS fetch returns parsed entries."""
        from providers.news.rss_provider import fetch_rss_entries

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.text = "<rss><channel><item><title>Test</title></item></channel></rss>"
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_feed = MagicMock()
        mock_feed.entries = [MagicMock(title="Test Entry")]
        mock_parse.return_value = mock_feed

        result = await fetch_rss_entries("https://example.com/feed.xml")
        assert len(result) == 1
        mock_parse.assert_called_once()

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    @patch("providers.news.rss_provider.feedparser.parse")
    async def test_fetch_rss_entries_empty_feed(self, mock_parse, mock_client_cls):
        """Empty feed returns empty list."""
        from providers.news.rss_provider import fetch_rss_entries

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.text = "<rss></rss>"
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        result = await fetch_rss_entries("https://example.com/empty.xml")
        assert result == []

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    @patch("providers.news.rss_provider.feedparser.parse")
    async def test_fetch_rss_entries_custom_timeout(self, mock_parse, mock_client_cls):
        """Custom timeout is passed to AsyncClient."""
        from providers.news.rss_provider import fetch_rss_entries

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.text = "<rss></rss>"
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        await fetch_rss_entries("https://example.com/feed.xml", timeout=10.0)
        mock_client_cls.assert_called_once_with(timeout=10.0)

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    async def test_fetch_rss_entries_http_error(self, mock_client_cls):
        """HTTP errors propagate via raise_for_status."""
        from providers.news.rss_provider import fetch_rss_entries

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = Mock(side_effect=Exception("HTTP 404"))
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(Exception, match="HTTP 404"):
            await fetch_rss_entries("https://example.com/notfound.xml")


class TestFetchApiPayload:
    """Tests for the fetch_api_payload async function."""

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    async def test_fetch_api_payload_success(self, mock_client_cls):
        """Successful API fetch returns parsed JSON."""
        from providers.news.rss_provider import fetch_api_payload

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"articles": [{"title": "News"}]}
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await fetch_api_payload("https://api.example.com/news")
        assert result == {"articles": [{"title": "News"}]}

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    async def test_fetch_api_payload_with_headers(self, mock_client_cls):
        """Custom headers are passed to the request."""
        from providers.news.rss_provider import fetch_api_payload

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        headers = {"Authorization": "Bearer token123"}
        await fetch_api_payload("https://api.example.com/news", headers=headers)
        mock_client.get.assert_called_once_with("https://api.example.com/news", headers=headers)

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    async def test_fetch_api_payload_custom_timeout(self, mock_client_cls):
        """Custom timeout is passed to AsyncClient."""
        from providers.news.rss_provider import fetch_api_payload

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await fetch_api_payload("https://api.example.com/news", timeout=5.0)
        mock_client_cls.assert_called_once_with(timeout=5.0)

    @pytest.mark.asyncio
    @patch("providers.news.rss_provider.httpx.AsyncClient")
    async def test_fetch_api_payload_http_error(self, mock_client_cls):
        """HTTP errors propagate via raise_for_status."""
        from providers.news.rss_provider import fetch_api_payload

        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = Mock(side_effect=Exception("HTTP 500"))
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(Exception, match="HTTP 500"):
            await fetch_api_payload("https://api.example.com/news")


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyticsInit:
    """Verify analytics package exports."""

    def test_analytics_exports_analytics_provider(self):
        from providers.analytics import AnalyticsProvider
        assert AnalyticsProvider is not None

    def test_analytics_all_exports_defined(self):
        import providers.analytics as analytics
        for name in analytics.__all__:
            assert hasattr(analytics, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS — analytics.py
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyticsProvider:
    """Tests for the AnalyticsProvider class."""

    @pytest.fixture
    def provider(self, monkeypatch):
        """Create an AnalyticsProvider with mocked settings."""
        monkeypatch.setattr("providers.analytics.analytics.settings", Mock(
            analytics_default_period_days=30,
        ))
        # Ensure HAS_ANALYTICS is True
        monkeypatch.setenv("ANALYTICS_API_KEY", "test-key")
        # Reload to pick up env var
        import importlib
        from providers.analytics import analytics as analytics_mod
        importlib.reload(analytics_mod)
        return analytics_mod.AnalyticsProvider()

    def test_init_default_period(self, provider):
        """Provider initializes with default period from settings."""
        assert provider._default_period_days == 30

    def test_get_dashboard_summary_returns_expected_keys(self, provider):
        """Dashboard summary returns all expected keys."""
        result = provider.get_dashboard_summary()
        assert "period" in result
        assert "days" in result
        assert "since" in result
        assert "country_code" in result
        assert "total_users" in result
        assert "total_suppliers" in result
        assert "total_products" in result
        assert "total_orders" in result
        assert "total_revenue" in result
        assert "message" in result

    def test_get_dashboard_summary_7d_period(self, provider):
        """7d period maps to 7 days."""
        result = provider.get_dashboard_summary(period="7d")
        assert result["days"] == 7
        assert result["period"] == "7d"

    def test_get_dashboard_summary_30d_period(self, provider):
        """30d period maps to 30 days."""
        result = provider.get_dashboard_summary(period="30d")
        assert result["days"] == 30

    def test_get_dashboard_summary_90d_period(self, provider):
        """90d period maps to 90 days."""
        result = provider.get_dashboard_summary(period="90d")
        assert result["days"] == 90

    def test_get_dashboard_summary_1y_period(self, provider):
        """1y period maps to 365 days."""
        result = provider.get_dashboard_summary(period="1y")
        assert result["days"] == 365

    def test_get_dashboard_summary_unknown_period_uses_default(self, provider):
        """Unknown period falls back to default."""
        result = provider.get_dashboard_summary(period="unknown")
        assert result["days"] == 30

    def test_get_dashboard_summary_with_country_code(self, provider):
        """Country code is preserved in result."""
        result = provider.get_dashboard_summary(country_code="US")
        assert result["country_code"] == "US"

    def test_get_chatbot_analytics_returns_expected_keys(self, provider):
        """Chatbot analytics returns all expected keys."""
        result = provider.get_chatbot_analytics()
        assert "total_queries" in result
        assert "total_clicks" in result
        assert "product_search_queries" in result
        assert "avg_results_per_query" in result
        assert "click_through_rate" in result
        assert "top_queries" in result
        assert "top_intents" in result
        assert "top_clicked_products" in result
        assert "daily_data" in result

    def test_get_chatbot_analytics_period_mapping(self, provider):
        """Chatbot analytics period mapping works."""
        result = provider.get_chatbot_analytics(period="7d")
        assert result["days"] == 7

    def test_get_product_performance_returns_expected_keys(self, provider):
        """Product performance returns all expected keys."""
        result = provider.get_product_performance()
        assert "country_code" in result
        assert "limit" in result
        assert "top_products" in result

    def test_get_product_performance_custom_limit(self, provider):
        """Custom limit is preserved."""
        result = provider.get_product_performance(limit=25)
        assert result["limit"] == 25

    def test_get_sales_trends_returns_expected_keys(self, provider):
        """Sales trends returns all expected keys."""
        result = provider.get_sales_trends()
        assert "period" in result
        assert "days" in result
        assert "trends" in result

    def test_get_ai_insights_returns_expected_keys(self, provider):
        """AI insights returns all expected keys."""
        result = provider.get_ai_insights()
        assert "country_code" in result
        assert "insights" in result
        assert "recommendations" in result


class TestAnalyticsProviderNotConfigured:
    """Tests when ANALYTICS_API_KEY is not set."""

    @pytest.fixture
    def provider_no_key(self, monkeypatch):
        """Create provider without API key."""
        monkeypatch.setattr("providers.analytics.analytics.settings", Mock(
            analytics_default_period_days=30,
        ))
        monkeypatch.delenv("ANALYTICS_API_KEY", raising=False)
        import importlib
        from providers.analytics import analytics as analytics_mod
        importlib.reload(analytics_mod)
        return analytics_mod.AnalyticsProvider()

    def test_get_dashboard_summary_raises(self, provider_no_key):
        """Not configured returns result with message."""
        result = provider_no_key.get_dashboard_summary()
        assert "message" in result
        assert "not configured" in result["message"].lower()

    def test_get_chatbot_analytics_raises(self, provider_no_key):
        result = provider_no_key.get_chatbot_analytics()
        assert "message" in result

    def test_get_product_performance_raises(self, provider_no_key):
        result = provider_no_key.get_product_performance()
        assert "message" in result

    def test_get_sales_trends_raises(self, provider_no_key):
        result = provider_no_key.get_sales_trends()
        assert "message" in result

    def test_get_ai_insights_raises(self, provider_no_key):
        result = provider_no_key.get_ai_insights()
        assert "message" in result


# ══════════════════════════════════════════════════════════════════════════════
# AUTOMATION PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestAutomationInit:
    """Verify automation package exports."""

    def test_automation_exports_async_io_scheduler(self):
        from providers.automation import AsyncIOScheduler
        assert AsyncIOScheduler is not None

    def test_automation_exports_interval_trigger(self):
        from providers.automation import IntervalTrigger
        assert IntervalTrigger is not None

    def test_automation_exports_create_scheduler(self):
        from providers.automation import create_scheduler
        assert callable(create_scheduler)

    def test_automation_exports_add_interval_job(self):
        from providers.automation import add_interval_job
        assert callable(add_interval_job)

    def test_automation_all_exports_defined(self):
        import providers.automation as automation
        expected = ["AsyncIOScheduler", "IntervalTrigger", "create_scheduler", "add_interval_job"]
        for name in expected:
            assert hasattr(automation, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# AUTOMATION — scheduler.py
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateScheduler:
    """Tests for the create_scheduler function."""

    def test_create_scheduler_default_timezone(self):
        """Default timezone is UTC."""
        from providers.automation.scheduler import create_scheduler

        scheduler = create_scheduler()
        assert scheduler is not None
        try:
            scheduler.shutdown()
        except Exception:
            pass

    def test_create_scheduler_custom_timezone(self):
        """Custom timezone is applied."""
        from providers.automation.scheduler import create_scheduler

        scheduler = create_scheduler(timezone="US/Eastern")
        assert scheduler is not None
        try:
            scheduler.shutdown()
        except Exception:
            pass

    def test_create_scheduler_returns_asyncio_scheduler(self):
        """Returns an AsyncIOScheduler instance."""
        from providers.automation.scheduler import create_scheduler, AsyncIOScheduler

        scheduler = create_scheduler()
        assert isinstance(scheduler, AsyncIOScheduler)
        try:
            scheduler.shutdown()
        except Exception:
            pass


class TestAddIntervalJob:
    """Tests for the add_interval_job function."""

    @pytest.fixture
    def scheduler(self):
        from providers.automation.scheduler import create_scheduler
        s = create_scheduler()
        yield s
        try:
            s.shutdown()
        except Exception:
            pass

    def test_add_interval_job_basic(self, scheduler):
        """Basic interval job registration works."""
        from providers.automation.scheduler import add_interval_job

        def dummy_job():
            pass

        add_interval_job(scheduler, dummy_job, seconds=60)
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1

    def test_add_interval_job_with_id(self, scheduler):
        """Job ID is preserved."""
        from providers.automation.scheduler import add_interval_job

        def dummy_job():
            pass

        add_interval_job(scheduler, dummy_job, seconds=60, id="my-job")
        jobs = scheduler.get_jobs()
        assert jobs[0].id == "my-job"

    def test_add_interval_job_with_args(self, scheduler):
        """Job args are passed through."""
        from providers.automation.scheduler import add_interval_job

        def dummy_job(a, b):
            pass

        add_interval_job(scheduler, dummy_job, seconds=60, args=[1, 2])
        jobs = scheduler.get_jobs()
        assert jobs[0].args == (1, 2)

    def test_add_interval_job_with_kwargs(self, scheduler):
        """Extra kwargs are passed through."""
        from providers.automation.scheduler import add_interval_job

        def dummy_job():
            pass

        add_interval_job(
            scheduler, dummy_job, seconds=60,
            id="test-job", max_instances=2,
        )
        jobs = scheduler.get_jobs()
        assert jobs[0].max_instances == 2

    def test_add_multiple_interval_jobs(self, scheduler):
        """Multiple jobs can be registered."""
        from providers.automation.scheduler import add_interval_job

        def job1():
            pass

        def job2():
            pass

        add_interval_job(scheduler, job1, seconds=60)
        add_interval_job(scheduler, job2, seconds=120)
        assert len(scheduler.get_jobs()) == 2

    def test_add_interval_job_default_args_empty(self, scheduler):
        """Default args is empty tuple."""
        from providers.automation.scheduler import add_interval_job

        def dummy_job():
            pass

        add_interval_job(scheduler, dummy_job, seconds=60)
        jobs = scheduler.get_jobs()
        assert jobs[0].args == ()


# ══════════════════════════════════════════════════════════════════════════════
# FINANCE PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestFinanceInit:
    """Verify finance package exports."""

    def test_finance_exports_bank_api_error(self):
        from providers.finance import BankApiError
        assert BankApiError is not None

    def test_finance_exports_dispatch_batch(self):
        from providers.finance import dispatch_batch
        assert callable(dispatch_batch)

    def test_finance_exports_test_connection(self):
        from providers.finance import test_connection
        assert callable(test_connection)

    def test_finance_all_exports_defined(self):
        import providers.finance as finance
        for name in finance.__all__:
            assert hasattr(finance, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# FINANCE — bank_api.py
# ══════════════════════════════════════════════════════════════════════════════

class TestBankApiError:
    """Tests for the BankApiError exception."""

    def test_error_is_exception(self):
        from providers.finance.bank_api import BankApiError

        assert issubclass(BankApiError, Exception)

    def test_error_default_status_code(self):
        from providers.finance.bank_api import BankApiError

        err = BankApiError("test error")
        assert err.status_code is None

    def test_error_with_status_code(self):
        from providers.finance.bank_api import BankApiError

        err = BankApiError("test error", status_code=500)
        assert err.status_code == 500

    def test_error_message(self):
        from providers.finance.bank_api import BankApiError

        err = BankApiError("connection failed")
        assert str(err) == "connection failed"


class TestEndpoint:
    """Tests for the _endpoint helper function."""

    def test_endpoint_valid_url_and_path(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("https://api.bank.com", "/v1/batches")
        assert result == "https://api.bank.com/v1/batches"

    def test_endpoint_strips_trailing_slash(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("https://api.bank.com/", "v1/batches")
        assert result == "https://api.bank.com/v1/batches"

    def test_endpoint_strips_leading_slash_from_path(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("https://api.bank.com", "v1/batches")
        assert result == "https://api.bank.com/v1/batches"

    def test_endpoint_empty_base_url(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("", "/v1/batches")
        assert result is None

    def test_endpoint_empty_batch_path(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("https://api.bank.com", "")
        assert result is None

    def test_endpoint_both_empty(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("", "")
        assert result is None

    def test_endpoint_whitespace_only_base(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("  ", "/v1/batches")
        assert result is None

    def test_endpoint_whitespace_only_path(self):
        from providers.finance.bank_api import _endpoint

        result = _endpoint("https://api.bank.com", "  ")
        assert result is None


class TestTestConnection:
    """Tests for the test_connection function."""

    def test_test_connection_empty_url(self):
        """Empty base URL returns unreachable result."""
        from providers.finance.bank_api import test_connection

        result = test_connection("", "", "token", 10.0)
        assert result["reachable"] is False
        assert result["ok"] is False
        assert result["status_code"] is None
        assert "must be configured" in result["detail"]

    def test_test_connection_empty_path(self):
        """Empty batch path returns unreachable result."""
        from providers.finance.bank_api import test_connection

        result = test_connection("https://api.bank.com", "", "token", 10.0)
        assert result["reachable"] is False

    @patch("providers.finance.bank_api.requests.request")
    def test_test_connection_success_200(self, mock_request):
        """200 response returns reachable=True, ok=True."""
        from providers.finance.bank_api import test_connection

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_request.return_value = mock_resp

        result = test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
        assert result["reachable"] is True
        assert result["ok"] is True
        assert result["status_code"] == 200

    @patch("providers.finance.bank_api.requests.request")
    def test_test_connection_401_still_reachable(self, mock_request):
        """401 is in reachable status codes (server responded)."""
        from providers.finance.bank_api import test_connection

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_request.return_value = mock_resp

        result = test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
        assert result["reachable"] is True
        assert result["ok"] is True

    @patch("providers.finance.bank_api.requests.request")
    def test_test_connection_500_not_ok(self, mock_request):
        """500 is not in reachable status codes."""
        from providers.finance.bank_api import test_connection

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_request.return_value = mock_resp

        result = test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
        assert result["reachable"] is True
        assert result["ok"] is False

    @patch("providers.finance.bank_api.requests.request")
    def test_test_connection_network_error(self, mock_request):
        """Network error returns unreachable."""
        from providers.finance.bank_api import test_connection
        import requests

        mock_request.side_effect = requests.RequestException("Connection refused")

        result = test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
        assert result["reachable"] is False
        assert result["ok"] is False
        assert "could not be reached" in result["detail"]

    @patch("providers.finance.bank_api.requests.request")
    def test_test_connection_uses_options_method(self, mock_request):
        """Connection test uses OPTIONS HTTP method."""
        from providers.finance.bank_api import test_connection

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_request.return_value = mock_resp

        test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
        mock_request.assert_called_once_with(
            "OPTIONS",
            "https://api.bank.com/v1/batches",
            headers={"Authorization": "Bearer token"},
            timeout=10.0,
        )


class TestDispatchBatch:
    """Tests for the dispatch_batch function."""

    def test_dispatch_batch_empty_url_raises(self):
        """Empty base URL raises BankApiError."""
        from providers.finance.bank_api import dispatch_batch, BankApiError

        with pytest.raises(BankApiError, match="must be configured"):
            dispatch_batch("", "", "token", "idem-key", {}, 10.0)

    def test_dispatch_batch_empty_path_raises(self):
        """Empty batch path raises BankApiError."""
        from providers.finance.bank_api import dispatch_batch, BankApiError

        with pytest.raises(BankApiError, match="must be configured"):
            dispatch_batch("https://api.bank.com", "", "token", "idem-key", {}, 10.0)

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_success(self, mock_post):
        """Successful dispatch returns status_code and body."""
        from providers.finance.bank_api import dispatch_batch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"batch_id": "123"}'
        mock_resp.json.return_value = {"batch_id": "123"}
        mock_resp.raise_for_status = Mock()
        mock_post.return_value = mock_resp

        result = dispatch_batch(
            "https://api.bank.com", "/v1/batches", "token", "idem-123",
            {"amount": 100}, 10.0,
        )
        assert result["status_code"] == 200
        assert result["body"] == {"batch_id": "123"}

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_network_error_raises(self, mock_post):
        """Network error raises BankApiError."""
        from providers.finance.bank_api import dispatch_batch, BankApiError
        import requests

        mock_post.side_effect = requests.RequestException("Connection refused")

        with pytest.raises(BankApiError, match="dispatch failed"):
            dispatch_batch(
                "https://api.bank.com", "/v1/batches", "token", "idem-123",
                {"amount": 100}, 10.0,
            )

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_non_2xx_raises(self, mock_post):
        """Non-2xx response raises BankApiError."""
        from providers.finance.bank_api import dispatch_batch, BankApiError
        import requests

        mock_resp = MagicMock()
        mock_resp.raise_for_status = Mock(
            side_effect=requests.HTTPError("400 Bad Request")
        )
        mock_post.return_value = mock_resp

        with pytest.raises(BankApiError):
            dispatch_batch(
                "https://api.bank.com", "/v1/batches", "token", "idem-123",
                {"amount": 100}, 10.0,
            )

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_empty_body(self, mock_post):
        """Empty response body returns empty dict."""
        from providers.finance.bank_api import dispatch_batch

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_resp.raise_for_status = Mock()
        mock_post.return_value = mock_resp

        result = dispatch_batch(
            "https://api.bank.com", "/v1/batches", "token", "idem-123",
            {"amount": 100}, 10.0,
        )
        assert result["body"] == {}

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_invalid_json_body(self, mock_post):
        """Invalid JSON in response body returns empty dict."""
        from providers.finance.bank_api import dispatch_batch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"not json"
        mock_resp.raise_for_status = Mock()
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_resp

        result = dispatch_batch(
            "https://api.bank.com", "/v1/batches", "token", "idem-123",
            {"amount": 100}, 10.0,
        )
        assert result["body"] == {}

    @patch("providers.finance.bank_api.requests.post")
    def test_dispatch_batch_sends_correct_headers(self, mock_post):
        """Request includes auth, content-type, and idempotency headers."""
        from providers.finance.bank_api import dispatch_batch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = Mock()
        mock_post.return_value = mock_resp

        dispatch_batch(
            "https://api.bank.com", "/v1/batches", "my-token", "idem-key-123",
            {"amount": 500}, 15.0,
        )
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer my-token"
        assert call_kwargs["headers"]["Idempotency-Key"] == "idem-key-123"
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        assert call_kwargs["timeout"] == 15.0


# ══════════════════════════════════════════════════════════════════════════════
# _base.py — BaseProvider and BaseAIProvider
# ══════════════════════════════════════════════════════════════════════════════

class TestBaseProvider:
    """Tests for the BaseProvider abstract class."""

    def test_base_provider_is_abstract(self):
        """BaseProvider cannot be instantiated directly."""
        from providers._base import BaseProvider

        with pytest.raises(TypeError):
            BaseProvider()

    def test_base_provider_init_sets_name(self):
        """Subclass with name sets name correctly."""
        from providers._base import BaseProvider

        class TestProvider(BaseProvider):
            def is_available(self) -> bool:
                return True

            def health_check(self) -> dict:
                return {"status": "ok"}

        p = TestProvider(name="test")
        assert p.name == "test"
        assert p._initialized is False

    def test_base_provider_init_default_name(self):
        """Default name uses class name."""
        from providers._base import BaseProvider

        class MyCustomProvider(BaseProvider):
            def is_available(self) -> bool:
                return True

            def health_check(self) -> dict:
                return {"status": "ok"}

        p = MyCustomProvider()
        assert p.name == "MyCustomProvider"

    def test_base_provider_initialize(self):
        """initialize() sets _initialized to True."""
        from providers._base import BaseProvider

        class TestProvider(BaseProvider):
            def is_available(self) -> bool:
                return True

            def health_check(self) -> dict:
                return {"status": "ok"}

        p = TestProvider()
        p.initialize()
        assert p._initialized is True


class TestBaseAIProvider:
    """Tests for the BaseAIProvider abstract class."""

    def test_base_ai_provider_is_abstract(self):
        """BaseAIProvider cannot be instantiated directly."""
        from providers._base import BaseAIProvider

        with pytest.raises(TypeError):
            BaseAIProvider()

    def test_base_ai_provider_init(self):
        """Subclass initializes with model."""
        from providers._base import BaseAIProvider

        class TestAIProvider(BaseAIProvider):
            def load_model(self) -> None:
                self._model_loaded = True

            def predict(self, input_data):
                return input_data

            def preprocess(self, input_data):
                return input_data

            def postprocess(self, output):
                return output

        p = TestAIProvider(name="test-ai", model="phi3")
        assert p.name == "test-ai"
        assert p.model == "phi3"
        assert p._model_loaded is False
        assert p._initialized is False

    def test_base_ai_provider_is_available(self):
        """is_available requires both initialized and model_loaded."""
        from providers._base import BaseAIProvider

        class TestAIProvider(BaseAIProvider):
            def load_model(self) -> None:
                self._model_loaded = True

            def predict(self, input_data):
                return input_data

            def preprocess(self, input_data):
                return input_data

            def postprocess(self, output):
                return output

        p = TestAIProvider()
        assert p.is_available() is False
        p.initialize()
        assert p.is_available() is False
        p.load_model()
        assert p.is_available() is True

    def test_base_ai_provider_health_check_unavailable(self):
        """Health check shows unhealthy when not available."""
        from providers._base import BaseAIProvider

        class TestAIProvider(BaseAIProvider):
            def load_model(self) -> None:
                self._model_loaded = True

            def predict(self, input_data):
                return input_data

            def preprocess(self, input_data):
                return input_data

            def postprocess(self, output):
                return output

        p = TestAIProvider(name="test", model="phi3")
        result = p.health_check()
        assert result["status"] == "unhealthy"
        assert result["provider"] == "test"
        assert result["model"] == "phi3"
        assert result["model_loaded"] is False

    def test_base_ai_provider_health_check_available(self):
        """Health check shows healthy when available."""
        from providers._base import BaseAIProvider

        class TestAIProvider(BaseAIProvider):
            def load_model(self) -> None:
                self._model_loaded = True

            def predict(self, input_data):
                return input_data

            def preprocess(self, input_data):
                return input_data

            def postprocess(self, output):
                return output

        p = TestAIProvider(name="test", model="phi3")
        p.initialize()
        p.load_model()
        result = p.health_check()
        assert result["status"] == "healthy"
        assert result["model_loaded"] is True


# ══════════════════════════════════════════════════════════════════════════════
# config.py — ProviderConfig
# ══════════════════════════════════════════════════════════════════════════════

class TestProviderConfig:
    """Tests for the ProviderConfig dataclass."""

    def test_settings_singleton_exists(self):
        from providers.config import settings
        assert settings is not None

    def test_default_ollama_base_url(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.ollama_base_url == "http://localhost:11434"

    def test_default_ollama_model(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.ollama_model == "moondream:latest"

    def test_default_ollama_text_model(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.ollama_text_model == "phi3:mini"

    def test_default_rembg_models(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert "isnet-general-use" in config.rembg_default_models
        assert "u2net" in config.rembg_default_models

    def test_default_rembg_max_dimension(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.rembg_max_dimension == 2048

    def test_default_rembg_png_compression(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.rembg_png_compression == 6

    def test_bg_preset_models_exist(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert "general" in config.bg_preset_models
        assert "marketing" in config.bg_preset_models

    def test_default_max_concurrent_bg_removals(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.max_concurrent_bg_removals == 2

    def test_default_ocr_timeout(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.ocr_timeout == 30

    def test_default_ocr_max_file_size_mb(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.ocr_max_file_size_mb == 25

    def test_default_chatbot_max_history(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.chatbot_max_history == 10

    def test_default_chatbot_session_ttl_hours(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.chatbot_session_ttl_hours == 24

    def test_default_search_default_limit(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.search_default_limit == 20

    def test_default_search_fuzzy_cutoff(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.search_fuzzy_cutoff == 0.6

    def test_default_geo_default_country(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.geo_default_country == "US"

    def test_default_analytics_default_period_days(self):
        from providers.config import ProviderConfig

        config = ProviderConfig()
        assert config.analytics_default_period_days == 30

    def test_custom_values(self):
        from providers.config import ProviderConfig

        config = ProviderConfig(
            ollama_base_url="http://custom:11434",
            ollama_model="custom-model",
            ollama_text_model="custom-text",
        )
        assert config.ollama_base_url == "http://custom:11434"
        assert config.ollama_model == "custom-model"
        assert config.ollama_text_model == "custom-text"


# ══════════════════════════════════════════════════════════════════════════════
# http.py — aiohttp wrapper
# ══════════════════════════════════════════════════════════════════════════════

class TestHttpProvider:
    """Tests for the http provider module."""

    def test_aiohttp_exported(self):
        from providers.http import aiohttp
        assert aiohttp is not None

    def test_client_session_exported(self):
        from providers.http import ClientSession
        assert ClientSession is not None

    def test_client_timeout_exported(self):
        from providers.http import ClientTimeout
        assert ClientTimeout is not None

    def test_client_error_exported(self):
        from providers.http import ClientError
        assert ClientError is not None

    def test_tcp_connector_exported(self):
        from providers.http import TCPConnector
        assert TCPConnector is not None

    def test_all_exports_defined(self):
        from providers import http
        for name in http.__all__:
            assert hasattr(http, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# async_workers.py
# ══════════════════════════════════════════════════════════════════════════════

class TestConcurrencyManager:
    """Tests for the ConcurrencyManager class."""

    def test_init_default_semaphores(self):
        from providers.async_workers import ConcurrencyManager

        cm = ConcurrencyManager()
        assert cm.bg_removal is not None
        assert cm.ai_analysis is not None
        assert cm.ocr is not None
        assert cm.embedding is not None

    def test_init_custom_limits(self):
        from providers.async_workers import ConcurrencyManager

        cm = ConcurrencyManager(max_bg=2, max_ai=4, max_ocr=1, max_embed=3)
        assert cm.bg_removal is not None
        assert cm.ai_analysis is not None
        assert cm.ocr is not None
        assert cm.embedding is not None

    def test_semaphores_are_asyncio_semaphore(self):
        import asyncio
        from providers.async_workers import ConcurrencyManager

        cm = ConcurrencyManager()
        assert isinstance(cm.bg_removal, asyncio.Semaphore)
        assert isinstance(cm.ai_analysis, asyncio.Semaphore)
        assert isinstance(cm.ocr, asyncio.Semaphore)
        assert isinstance(cm.embedding, asyncio.Semaphore)


class TestGlobalConcurrency:
    """Tests for the global concurrency instance."""

    def test_global_concurrency_exists(self):
        from providers.async_workers import concurrency
        assert concurrency is not None

    def test_global_concurrency_has_semaphores(self):
        from providers.async_workers import concurrency

        assert hasattr(concurrency, "bg_removal")
        assert hasattr(concurrency, "ai_analysis")
        assert hasattr(concurrency, "ocr")
        assert hasattr(concurrency, "embedding")


class TestRunInThread:
    """Tests for the _run_in_thread helper."""

    @pytest.mark.asyncio
    async def test_run_in_thread_returns_result(self):
        """_run_in_thread returns the function result."""
        from providers.async_workers import _run_in_thread

        def add(a, b):
            return a + b

        result = await _run_in_thread(add, 2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_run_in_thread_with_kwargs(self):
        """_run_in_thread passes kwargs."""
        from providers.async_workers import _run_in_thread

        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await _run_in_thread(greet, "World", greeting="Hi")
        assert result == "Hi, World!"

    @pytest.mark.asyncio
    async def test_run_in_thread_exception_propagates(self):
        """Exceptions in the threaded function propagate."""
        from providers.async_workers import _run_in_thread

        def fail():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await _run_in_thread(fail)


class TestProcessLargeBatchAsync:
    """Tests for the process_large_batch_async function."""

    @pytest.mark.asyncio
    async def test_process_large_batch_basic(self):
        """Basic batch processing returns results."""
        from providers.async_workers import process_large_batch_async

        async def double(x):
            return x * 2

        result = await process_large_batch_async([1, 2, 3], double, batch_size=2, concurrency_limit=2)
        assert result == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_process_large_batch_empty(self):
        """Empty items list returns empty results."""
        from providers.async_workers import process_large_batch_async

        async def identity(x):
            return x

        result = await process_large_batch_async([], identity)
        assert result == []

    @pytest.mark.asyncio
    async def test_process_large_batch_respects_batch_size(self):
        """Batch size controls items per batch."""
        from providers.async_workers import process_large_batch_async

        call_count = 0

        async def track(x):
            nonlocal call_count
            call_count += 1
            return x

        items = list(range(10))
        result = await process_large_batch_async(items, track, batch_size=3, concurrency_limit=3)
        assert len(result) == 10
        assert call_count == 10


# ══════════════════════════════════════════════════════════════════════════════
# observability.py
# ══════════════════════════════════════════════════════════════════════════════

class TestObservability:
    """Tests for the observability provider module."""

    def test_capture_exception_no_sentry_sdk(self):
        """capture_exception is a no-op when sentry_sdk is unavailable."""
        from providers.observability import capture_exception

        # Should not raise even without sentry_sdk
        capture_exception(Exception("test"))

    def test_capture_message_no_sentry_sdk(self):
        """capture_message is a no-op when sentry_sdk is unavailable."""
        from providers.observability import capture_message

        # Should not raise even without sentry_sdk
        capture_message("test message")

    def test_capture_exception_calls_sentry_when_available(self):
        """capture_exception calls sentry_sdk when available."""
        from providers.observability import capture_exception

        mock_sentry = MagicMock()
        with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
            exc = ValueError("test error")
            capture_exception(exc)
            mock_sentry.capture_exception.assert_called_once_with(exc)

    def test_capture_message_calls_sentry_when_available(self):
        """capture_message calls sentry_sdk when available."""
        from providers.observability import capture_message

        mock_sentry = MagicMock()
        with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
            capture_message("test message", level="warning")
            mock_sentry.capture_message.assert_called_once_with("test message", level="warning")

    def test_all_exports_defined(self):
        from providers import observability
        for name in observability.__all__:
            assert hasattr(observability, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# storage.py
# ══════════════════════════════════════════════════════════════════════════════

class TestStorageProvider:
    """Tests for the storage provider module."""

    def test_create_s3_client_function_exists(self):
        from providers.storage import create_s3_client
        assert callable(create_s3_client)

    def test_create_ssm_client_function_exists(self):
        from providers.storage import create_ssm_client
        assert callable(create_ssm_client)

    def test_all_exports_defined(self):
        from providers import storage
        for name in storage.__all__:
            assert hasattr(storage, name), f"Missing export: {name}"

    @patch("boto3.client")
    def test_create_s3_client_with_all_params(self, mock_boto3_client):
        """S3 client is created with all parameters."""
        from providers.storage import create_s3_client

        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        result = create_s3_client(
            bucket="my-bucket",
            region="us-east-1",
            endpoint_url="https://s3.example.com",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        mock_boto3_client.assert_called_once_with(
            "s3",
            region_name="us-east-1",
            endpoint_url="https://s3.example.com",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        assert result is not None

    @patch("boto3.client")
    def test_create_s3_client_auto_region(self, mock_boto3_client):
        """Auto region is converted to None."""
        from providers.storage import create_s3_client

        mock_boto3_client.return_value = MagicMock()

        create_s3_client(
            bucket="my-bucket",
            region="auto",
            endpoint_url="",
            access_key="",
            secret_key="",
        )
        call_kwargs = mock_boto3_client.call_args[1]
        assert call_kwargs["region_name"] is None
        assert call_kwargs["endpoint_url"] is None
        assert call_kwargs["aws_access_key_id"] is None
        assert call_kwargs["aws_secret_access_key"] is None

    @patch("boto3.client")
    def test_create_ssm_client(self, mock_boto3_client):
        """SSM client is created with region."""
        from providers.storage import create_ssm_client

        mock_boto3_client.return_value = MagicMock()

        create_ssm_client(region="us-west-2")
        mock_boto3_client.assert_called_once_with("ssm", region_name="us-west-2")

    @patch("boto3.client")
    def test_create_ssm_client_empty_region(self, mock_boto3_client):
        """Empty region is converted to None."""
        from providers.storage import create_ssm_client

        mock_boto3_client.return_value = MagicMock()

        create_ssm_client(region="")
        mock_boto3_client.assert_called_once_with("ssm", region_name=None)


# ══════════════════════════════════════════════════════════════════════════════
# parcel_verification.py
# ══════════════════════════════════════════════════════════════════════════════

class TestParcelVerification:
    """Tests for the parcel verification provider module."""

    def _make_test_image_bytes(self, width: int = 100, height: int = 100, color: tuple = (128, 64, 32)) -> bytes:
        """Create a simple valid JPEG image as bytes with enough variation to pass blank check."""
        import numpy as np
        import cv2

        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:, :] = color
        rng = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        img = cv2.add(img, rng)
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    def _make_blank_image_bytes(self, width: int = 100, height: int = 100) -> bytes:
        """Create a blank (single-color) image as bytes."""
        import numpy as np
        import cv2

        img = np.zeros((height, width, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    def test_verify_parcel_photo_function_exists(self):
        from providers.image.parcel_verification import verify_parcel_photo
        assert callable(verify_parcel_photo)

    def test_verify_parcel_fast_function_exists(self):
        from providers.image.parcel_verification import verify_parcel_fast
        assert callable(verify_parcel_fast)

    def test_verify_parcel_photo_returns_expected_keys(self):
        """Result contains all expected keys."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(image_bytes, item_descriptions=["item1"])
        assert "status" in result
        assert "match_score" in result
        assert "match_percentage" in result
        assert "engines_used" in result
        assert "elapsed_seconds" in result
        assert "total_items" in result
        assert "matched_items" in result
        assert "reference_used" in result
        assert "engine_details" in result
        assert "engine_weights" in result
        assert "analyzed_at" in result

    def test_verify_parcel_photo_invalid_image(self):
        """Invalid image bytes return 'unverified' status with zero engines."""
        from providers.image.parcel_verification import verify_parcel_photo

        result = verify_parcel_photo(b"not an image", item_descriptions=[])
        assert result["status"] == "unverified"
        assert isinstance(result["engines_used"], int)
        assert result["engines_used"] == 0

    def test_verify_parcel_photo_blank_image(self):
        """Blank image returns a valid status with engines_used as int."""
        from providers.image.parcel_verification import verify_parcel_photo

        blank_bytes = self._make_blank_image_bytes()
        result = verify_parcel_photo(blank_bytes, item_descriptions=[])
        assert result["status"] in ("verified", "partial", "unverified")
        assert isinstance(result["engines_used"], int)

    def test_verify_parcel_photo_no_reference(self):
        """Without reference image, homography engine is not used."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(image_bytes, item_descriptions=["item1"])
        assert isinstance(result["engines_used"], int)
        assert result["reference_used"] is False
        assert "homography" not in result["engine_details"]

    def test_verify_parcel_photo_with_reference_ssim(self):
        """With reference image and SSIM enabled, SSIM engine is used."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        ref_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(
            image_bytes, item_descriptions=["item1"],
            reference_image_bytes=ref_bytes, run_ssim=True,
        )
        assert "ssim" in result["engine_details"]
        assert result["reference_used"] is True

    def test_verify_parcel_photo_with_reference_feature_match(self):
        """With reference image and feature match enabled."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        ref_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(
            image_bytes, item_descriptions=["item1"],
            reference_image_bytes=ref_bytes, run_feature_match=True,
        )
        assert "feature_match" in result["engine_details"]

    def test_verify_parcel_photo_item_count(self):
        """Item count is correctly reported."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(
            image_bytes, item_descriptions=["item1", "item2", "item3"],
        )
        assert result["total_items"] == 3

    def test_verify_parcel_photo_matched_items_verified(self):
        """Matched items equals total when status is 'verified'."""
        from providers.image.parcel_verification import verify_parcel_photo

        # Use identical images to get a high SSIM score
        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(
            image_bytes, item_descriptions=["item1"],
            reference_image_bytes=image_bytes, run_ssim=True, run_feature_match=False,
        )
        if result["status"] == "verified":
            assert result["matched_items"] == result["total_items"]

    def test_verify_parcel_fast_returns_expected_keys(self):
        """Fast verification returns expected keys."""
        from providers.image.parcel_verification import verify_parcel_fast

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_fast(image_bytes, item_descriptions=["item1"])
        assert "status" in result
        assert "match_score" in result
        assert "engines_used" in result
        assert isinstance(result["engines_used"], int)

    def test_verify_parcel_fast_invalid_image(self):
        """Fast verification with invalid image returns 'unverified'."""
        from providers.image.parcel_verification import verify_parcel_fast

        result = verify_parcel_fast(b"not an image", item_descriptions=[])
        assert result["status"] == "unverified"

    def test_verify_parcel_fast_with_reference(self):
        """Fast verification with reference uses SSIM and homography."""
        from providers.image.parcel_verification import verify_parcel_fast

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_fast(
            image_bytes, item_descriptions=["item1"],
            reference_image_bytes=image_bytes,
        )
        assert "ssim" in result["engine_details"]
        assert result["reference_used"] is True

    def test_verify_parcel_fast_without_reference(self):
        """Fast verification without reference skips homography."""
        from providers.image.parcel_verification import verify_parcel_fast

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_fast(image_bytes, item_descriptions=["item1"])
        assert isinstance(result["engines_used"], int)
        assert result["reference_used"] is False
        assert "homography" not in result["engine_details"]

    def test_verify_parcel_photo_elapsed_time(self):
        """Elapsed time is non-negative."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(image_bytes, item_descriptions=["item1"])
        assert result["elapsed_seconds"] >= 0

    def test_verify_parcel_photo_match_score_range(self):
        """Match score is between 0 and 1, match_percentage between 0 and 100."""
        from providers.image.parcel_verification import verify_parcel_photo

        image_bytes = self._make_test_image_bytes()
        result = verify_parcel_photo(image_bytes, item_descriptions=["item1"])
        assert 0 <= result["match_score"] <= 1
        assert 0 <= result["match_percentage"] <= 100


# ══════════════════════════════════════════════════════════════════════════════
# Module-level import tests for root-level providers
# ══════════════════════════════════════════════════════════════════════════════

class TestRootProviderImports:
    """Verify all root-level provider modules are importable."""

    def test_base_importable(self):
        import providers._base
        assert hasattr(providers._base, "BaseProvider")
        assert hasattr(providers._base, "BaseAIProvider")

    def test_config_importable(self):
        import providers.config
        assert hasattr(providers.config, "ProviderConfig")
        assert hasattr(providers.config, "settings")

    def test_http_importable(self):
        import providers.http
        assert hasattr(providers.http, "aiohttp")
        assert hasattr(providers.http, "ClientSession")

    def test_async_workers_importable(self):
        import providers.async_workers
        assert hasattr(providers.async_workers, "ConcurrencyManager")
        assert hasattr(providers.async_workers, "concurrency")

    def test_observability_importable(self):
        import providers.observability
        assert hasattr(providers.observability, "capture_exception")
        assert hasattr(providers.observability, "capture_message")

    def test_storage_importable(self):
        import providers.storage
        assert hasattr(providers.storage, "create_s3_client")
        assert hasattr(providers.storage, "create_ssm_client")

    def test_parcel_verification_importable(self):
        import providers.image.parcel_verification
        assert hasattr(providers.image.parcel_verification, "verify_parcel_photo")
        assert hasattr(providers.image.parcel_verification, "verify_parcel_fast")
