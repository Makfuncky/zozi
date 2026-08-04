"""Tests for middleware helpers (error handling, pagination decorators)."""
import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from utils.middleware_helpers import (
    as_paginated_response,
    handle_service_error,
    raise_not_found,
    raise_bad_request,
    raise_unauthorized,
    raise_forbidden,
)
from utils.error_handler import ErrorCategory


class TestRaiseHelpers:
    def test_raise_not_found(self):
        with pytest.raises(HTTPException) as exc:
            raise_not_found("Product", 42)
        assert exc.value.status_code == 404
        assert "Product" in exc.value.detail
        assert "42" in exc.value.detail

    def test_raise_bad_request(self):
        with pytest.raises(HTTPException) as exc:
            raise_bad_request("invalid input")
        assert exc.value.status_code == 400
        assert "invalid input" in exc.value.detail

    def test_raise_unauthorized(self):
        with pytest.raises(HTTPException) as exc:
            raise_unauthorized()
        assert exc.value.status_code == 401

    def test_raise_unauthorized_custom_message(self):
        with pytest.raises(HTTPException) as exc:
            raise_unauthorized("custom auth error")
        assert "custom auth error" in exc.value.detail

    def test_raise_forbidden(self):
        with pytest.raises(HTTPException) as exc:
            raise_forbidden()
        assert exc.value.status_code == 403

    def test_raise_forbidden_custom_message(self):
        with pytest.raises(HTTPException) as exc:
            raise_forbidden("custom permission error")
        assert "custom permission error" in exc.value.detail


class TestAsPaginatedResponse:
    def test_successful_pagination(self):
        @as_paginated_response()
        def my_handler(page=1, size=20):
            items = [{"id": i} for i in range(10)]
            return items, 100

        result = my_handler(page=1, size=20)
        assert result["items"] == [{"id": i} for i in range(10)]
        assert result["total"] == 100
        assert result["page"] == 1
        assert result["size"] == 20
        assert result["pages"] == 5

    def test_empty_result(self):
        @as_paginated_response()
        def empty_handler(page=1, size=20):
            return [], 0

        result = empty_handler(page=1, size=20)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["pages"] == 0

    def test_single_page(self):
        @as_paginated_response()
        def single_page(page=1, size=20):
            return [{"id": 1}], 1

        result = single_page(page=1, size=20)
        assert result["pages"] == 1

    def test_page_size_clamping(self):
        @as_paginated_response(max_size=50)
        def clamped_handler(page=1, size=200):
            items = [{"id": i} for i in range(min(10, size))]
            return items, 100

        result = clamped_handler(page=1, size=200)
        assert result["size"] == 50  # clamped to max_size


class TestHandleServiceError:
    def test_successful_call(self):
        @handle_service_error()
        def my_handler():
            return "success"

        result = my_handler()
        assert result == "success"

    def test_http_exception_passthrough(self):
        @handle_service_error()
        def raising_handler():
            raise HTTPException(403, "forbidden")

        with pytest.raises(HTTPException) as exc:
            raising_handler()
        assert exc.value.status_code == 403

    def test_unhandled_exception_returns_problem(self):
        @handle_service_error(default_status=500, default_message="Something broke")
        def broken_handler():
            raise ValueError("internal oops")

        result = broken_handler()
        assert isinstance(result, JSONResponse)
        body = result.body.decode()
        assert "500" in body or result.status_code == 500

    def test_service_error_with_custom_status(self):
        @handle_service_error(default_status=502, default_message="Bad gateway")
        def gateway_handler():
            raise RuntimeError("upstream failed")

        result = gateway_handler()
        assert result.status_code == 502


class TestDecoratorComposition:
    def test_pagination_with_service_error(self):
        @handle_service_error()
        @as_paginated_response()
        def composed_handler(page=1, size=20):
            return [{"id": 1}], 10

        result = composed_handler(page=1, size=20)
        assert result["items"] == [{"id": 1}]
        assert result["total"] == 10
