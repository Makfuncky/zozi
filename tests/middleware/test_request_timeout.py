import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import Request

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _REPO_ROOT / "backend"


def test_request_timeout_middleware_registered():
    sys.path.insert(0, str(_BACKEND_ROOT))
    os.chdir(str(_BACKEND_ROOT))
    from middleware.orchestrator import _FOUNDATION
    assert "RequestTimeoutMiddleware" in [m.__name__ for m in _FOUNDATION]


def test_request_timeout_decorator_sets_override():
    sys.path.insert(0, str(_BACKEND_ROOT))
    os.chdir(str(_BACKEND_ROOT))
    from middleware.request_timeout_middleware import request_timeout

    @request_timeout(seconds=60)
    def fake_handler():
        return "ok"

    assert getattr(fake_handler, "_zozi_request_timeout", None) == 60.0


def test_get_route_timeout_uses_override():
    sys.path.insert(0, str(_BACKEND_ROOT))
    os.chdir(str(_BACKEND_ROOT))
    from middleware.request_timeout_middleware import get_route_timeout, request_timeout

    @request_timeout(seconds=45)
    def fake_handler():
        return "ok"

    scope = {"type": "http", "endpoint": fake_handler}
    request = Request(scope=scope)
    assert get_route_timeout(request, 30.0) == 45.0


def test_get_route_timeout_falls_back_to_default():
    sys.path.insert(0, str(_BACKEND_ROOT))
    os.chdir(str(_BACKEND_ROOT))
    from middleware.request_timeout_middleware import get_route_timeout

    request = Request(scope={"type": "http", "endpoint": lambda: None})
    assert get_route_timeout(request, 30.0) == 30.0


@pytest.mark.asyncio
async def test_request_timeout_middleware_returns_504_on_timeout():
    sys.path.insert(0, str(_BACKEND_ROOT))
    os.chdir(str(_BACKEND_ROOT))
    from unittest.mock import patch
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from middleware.request_timeout_middleware import RequestTimeoutMiddleware

    async def slow_call_next(request):
        await asyncio.sleep(10)
        return JSONResponse(content={"detail": "should not reach"})

    app = FastAPI()
    middleware = RequestTimeoutMiddleware(app)
    middleware._default_timeout = 0.5

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/slow",
        "headers": [],
        "query_string": b"",
        "http_version": "1.1",
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
        "asgi": {"version": "3.0"},
    }

    with patch("middleware.request_timeout_middleware.settings") as mock_settings:
        mock_settings.app_env = "production"
        response = await middleware.dispatch(Request(scope), slow_call_next)
        assert response.status_code == 504
        body = response.body.decode()
        assert "504" in body or "timeout" in body.lower()
