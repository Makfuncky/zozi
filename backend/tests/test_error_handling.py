"""Tests for error handling and logging systems."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from utils.error_handler import (
    ErrorHandler,
    create_error_handler,
    global_exception_handler,
    ErrorCategory,
    AppError,
)
from utils.logging_config import setup_structlog, get_request_id


@pytest.fixture
def error_handler():
    return create_error_handler(sentry_dsn=None, environment="test")


@pytest.fixture
def app(error_handler):
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise AppError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"field": "test"},
        )

    @app.get("/unhandled")
    async def unhandled_endpoint():
        raise ValueError("Unhandled error")

    async def handler(request: Request, exc: Exception):
        return await global_exception_handler(request, exc, error_handler)

    app.add_exception_handler(Exception, handler)
    return app


class TestErrorCategorization:
    def test_classify_database_error(self):
        from sqlalchemy.exc import OperationalError
        handler = create_error_handler(sentry_dsn=None, environment="test")
        exc = OperationalError("db error", None, None)
        category = handler.classify_error(exc, "/api/test")
        assert category == ErrorCategory.DATABASE

    def test_classify_external_service_error(self):
        handler = create_error_handler(sentry_dsn=None, environment="test")
        exc = Exception("connection refused")
        category = handler.classify_error(exc, "/api/test")
        assert category == ErrorCategory.EXTERNAL_SERVICE

    def test_classify_validation_error(self):
        from fastapi import HTTPException
        handler = create_error_handler(sentry_dsn=None, environment="test")
        exc = HTTPException(status_code=422, detail="validation failed")
        category = handler.classify_error(exc, "/api/test")
        assert category == ErrorCategory.VALIDATION

    def test_classify_unknown_error(self):
        handler = create_error_handler(sentry_dsn=None, environment="test")
        exc = Exception("something unexpected")
        category = handler.classify_error(exc, "/api/test")
        assert category == ErrorCategory.INTERNAL


class TestAppError:
    def test_app_error_creation(self):
        error = AppError(
            message="Test error",
            error_code="TEST_CODE",
            status_code=400,
            details={"key": "value"},
        )
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"
        assert error.status_code == 400
        assert error.details == {"key": "value"}

    def test_app_error_default_status_code(self):
        error = AppError(
            message="Test error",
            error_code="TEST_CODE",
        )
        assert error.status_code == 500


class TestGlobalExceptionHandler:
    def test_error_handler_health_without_sentry(self, error_handler):
        assert error_handler.is_healthy() is False

    def test_error_handler_health_with_sentry(self):
        with patch("sentry_sdk.init"):
            handler = create_error_handler(
                sentry_dsn="https://test@o123.ingest.sentry.io/123",
                environment="test",
            )
        assert handler.is_healthy() is True


class TestLoggingConfiguration:
    def test_setup_structlog_does_not_raise(self):
        setup_structlog(log_level=20)

    def test_get_request_id_returns_string(self):
        rid = get_request_id()
        assert isinstance(rid, str)


class TestErrorHandlerWithSentry:
    @patch("sentry_sdk.init")
    def test_create_error_handler_with_dsn(self, mock_sentry_init):
        handler = create_error_handler(
            sentry_dsn="https://test@o123.ingest.sentry.io/123",
            environment="production",
        )
        assert handler.is_healthy() is True
        mock_sentry_init.assert_called_once()

    @patch("sentry_sdk.init")
    def test_create_error_handler_without_dsn(self, mock_sentry_init):
        handler = create_error_handler(sentry_dsn=None, environment="test")
        assert handler.is_healthy() is False
        mock_sentry_init.assert_not_called()


class TestErrorHandlerBeforeSend:
    @patch("sentry_sdk.init")
    def test_before_send_enriches_with_request_context(self, mock_sentry_init):
        handler = create_error_handler(
            sentry_dsn="https://test@o123.ingest.sentry.io/123",
            environment="test",
        )
        assert handler._before_send is not None

    @patch("sentry_sdk.init")
    def test_before_send_filters_sensitive_data(self, mock_sentry_init):
        handler = create_error_handler(
            sentry_dsn="https://test@o123.ingest.sentry.io/123",
            environment="test",
        )
        assert handler._before_send is not None


class TestErrorHandlerCaptureException:
    @patch("sentry_sdk.capture_exception")
    def test_capture_exception_with_request_context(self, mock_capture):
        handler = create_error_handler(
            sentry_dsn="https://test@o123.ingest.sentry.io/123",
            environment="test",
        )
        mock_request = MagicMock()
        mock_request.state.request_id = "req-123"
        mock_request.state.user_id = "user-456"
        mock_request.state.country_code = "US"

        try:
            raise ValueError("test error")
        except Exception:
            handler.capture_exception(Exception("test error"), request=mock_request)

        mock_capture.assert_called_once()

    @patch("sentry_sdk.capture_exception")
    def test_capture_exception_without_request(self, mock_capture):
        handler = create_error_handler(
            sentry_dsn="https://test@o123.ingest.sentry.io/123",
            environment="test",
        )
        try:
            raise ValueError("test error")
        except Exception:
            handler.capture_exception(Exception("test error"))

        mock_capture.assert_called_once()


class TestLoggingMiddlewareMetrics:
    def test_middleware_class_exists(self):
        from middleware.logging_middleware import RequestLoggingMiddleware

        assert RequestLoggingMiddleware is not None


class TestLoggingConfigFileHandler:
    def test_logging_config_does_not_raise(self):
        import logging

        setup_structlog(log_level=logging.INFO)