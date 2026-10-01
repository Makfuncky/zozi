"""Regression tests for the authentication middleware.

Covers:
- Refresh token presented as access token is rejected (Law 33)
- Broad except Exception replaced with specific exception handling
- Auth failures log at WARNING level with request metadata
"""
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

from fastapi import HTTPException


def _import_middleware():
    return importlib.import_module("middleware.authentication_middleware")


class _State:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _URL:
    def __init__(self, path: str):
        self.path = path


class _Request:
    def __init__(self, path: str, state=None, client_host="127.0.0.1"):
        self.url = _URL(path)
        self.state = state or _State()
        self.headers = {}
        self.client = MagicMock()
        self.client.host = client_host


@pytest.mark.asyncio
async def test_refresh_token_rejected_as_access_token() -> None:
    middleware_mod = _import_middleware()
    mw = middleware_mod.AuthenticationMiddleware(app=None)

    request = _Request("/api/v1/customer/orders")
    request.headers = {"Authorization": "Bearer refresh_token_here"}

    async def _call_next(_req):
        return MagicMock()

    with patch.object(
        middleware_mod, "decode_token", side_effect=HTTPException(status_code=401, detail="Invalid token type, expected access")
    ):
        response = await mw.dispatch(request, _call_next)

    assert request.state.user is None
    assert request.state.user_id is None
    assert request.state.user_role is None
    assert request.state.staff_country_codes is None


@pytest.mark.asyncio
async def test_broad_except_exception_replaced_with_specific() -> None:
    import inspect

    source = inspect.getsource(_import_middleware().AuthenticationMiddleware.dispatch)
    assert "except Exception" not in source
    assert "except (HTTPException, JWTError, ValueError, TypeError)" in source


@pytest.mark.asyncio
async def test_auth_failure_logs_warning_with_metadata(caplog) -> None:
    import logging

    middleware_mod = _import_middleware()
    mw = middleware_mod.AuthenticationMiddleware(app=None)

    request = _Request("/api/v1/customer/orders", client_host="10.0.0.1")
    request.headers = {"Authorization": "Bearer badtoken"}

    async def _call_next(_req):
        return MagicMock()

    with patch.object(
        middleware_mod,
        "decode_token",
        side_effect=HTTPException(status_code=401, detail="Invalid token type, expected access"),
    ):
        with caplog.at_level(logging.WARNING, logger="middleware.authentication_middleware"):
            await mw.dispatch(request, _call_next)

    assert any("Auth middleware token decode error" in rec.message for rec in caplog.records)
    assert any(rec.__dict__.get("client_host") == "10.0.0.1" for rec in caplog.records)
    assert any(rec.__dict__.get("path") == "/api/v1/customer/orders" for rec in caplog.records)
