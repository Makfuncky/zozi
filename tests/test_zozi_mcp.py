"""Smoke tests for the ZOZI MCP server (backend/zozi_mcp/zozi_mcp.py).

Uses an httpx.MockTransport so every tool's request path, payload, pagination
envelope, formatting, and error handling can be verified without a live API.

Run:  cd backend && python -m pytest ../tests/test_zozi_mcp.py -v
"""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from zozi_mcp import zozi_mcp  # noqa: E402


# ---------------------------------------------------------------------------
# Mock API fixture
# ---------------------------------------------------------------------------


def _json_response(status: int, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("GET", "http://test"))


def _mock_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    method = request.method

    if path == "/api/v1/auth/login" and method == "POST":
        return _json_response(200, {
            "access_token": "mock-jwt-token",
            "token_type": "bearer",
            "user": {"id": 1, "email": "admin@zozi.test", "username": "admin", "role": "admin"},
        })

    if path == "/api/v1/users/me" and method == "GET":
        return _json_response(200, {"id": 1, "email": "admin@zozi.test", "username": "admin", "role": "admin"})

    if path == "/api/v1/products" and method == "GET":
        items = [
            {"id": 1, "name": "Wireless Mouse", "price": 12.5, "currency": "USD", "category": "Electronics", "status": "active"},
            {"id": 2, "name": "Laptop Stand", "price": 34.0, "currency": "USD", "category": "Electronics", "status": "active"},
        ]
        return _json_response(200, {"total": 2, "items": items})

    if path == "/api/v1/products/search" and method == "POST":
        payload = json.loads(request.content or b"{}")
        term = (payload.get("q") or "").lower()
        all_items = [
            {"id": 1, "name": "Wireless Mouse", "price": 12.5, "currency": "USD", "category": "Electronics", "status": "active"},
            {"id": 2, "name": "Laptop Stand", "price": 34.0, "currency": "USD", "category": "Electronics", "status": "active"},
        ]
        filtered = [p for p in all_items if term in p["name"].lower()] if term else all_items
        return _json_response(200, {"total": len(filtered), "items": filtered})

    if path == "/api/v1/products/1" and method == "GET":
        return _json_response(200, {"id": 1, "name": "Wireless Mouse", "price": 12.5, "currency": "USD"})

    if path == "/api/v1/products/barcode/ABC123" and method == "GET":
        return _json_response(200, {"id": 7, "name": "Barcode Item", "barcode": "ABC123"})

    if path == "/api/v1/orders" and method == "GET":
        return _json_response(200, {"total": 1, "items": [{"id": 501, "status": "pending", "total": 99.0, "customer_id": 3}]})

    if path == "/api/v1/orders/501" and method == "GET":
        return _json_response(200, {"id": 501, "status": "pending", "total": 99.0})

    if path == "/api/v1/orders/501/cancel" and method == "POST":
        return _json_response(200, {"id": 501, "status": "cancelled"})

    if path == "/api/v1/users" and method == "GET":
        return _json_response(200, {"total": 2, "items": [{"id": 1, "username": "admin", "role": "admin"}, {"id": 2, "username": "bob", "role": "customer"}]})

    if path == "/api/v1/users/2" and method == "GET":
        return _json_response(200, {"id": 2, "username": "bob", "role": "customer"})

    if path == "/api/v1/countries" and method == "GET":
        return _json_response(200, {"total": 1, "items": [{"id": 1, "name": "Oman", "code": "OM", "currency_code": "OMR", "region": "Middle East"}]})

    # Auth-guarded endpoints return 401 when no token is set
    if path in ("/api/v1/orders", "/api/v1/users") and not request.headers.get("authorization"):
        return _json_response(401, {"detail": "Not authenticated"})

    if path == "/api/v1/orders/404" and method == "GET":
        return _json_response(404, {"detail": "Order not found"})

    return _json_response(404, {"detail": f"unmocked: {method} {path}"})


@pytest.fixture(autouse=True)
def _mcp_env(monkeypatch):
    """Point the server at the mock transport and reset session state."""
    monkeypatch.setattr(zozi_mcp, "API_BASE_URL", "http://test/api/v1")
    monkeypatch.setattr(zozi_mcp, "_token", None)
    client = httpx.AsyncClient(transport=httpx.MockTransport(_mock_handler), base_url="http://test")
    monkeypatch.setattr(zozi_mcp, "_client", client)
    yield
    import asyncio
    asyncio.run(client.aclose())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_tools_registered():
    """All 10 documented tools are registered."""
    from zozi_mcp.zozi_mcp import mcp
    import asyncio
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    expected = {
        "zozi_login", "zozi_get_current_user", "zozi_list_products",
        "zozi_get_product", "zozi_list_orders", "zozi_get_order",
        "zozi_cancel_order", "zozi_list_users", "zozi_get_user",
        "zozi_list_countries",
    }
    assert set(names) == expected, f"missing/extra tools: {set(expected) ^ set(names)}"


@pytest.mark.asyncio
async def test_login_stores_token():
    result = await zozi_mcp.zozi_login(
        zozi_mcp.LoginInput(username="admin", password="secret")
    )
    data = json.loads(result)
    assert data["authenticated"] is True
    assert data["role"] == "admin"
    assert zozi_mcp._token == "mock-jwt-token"


@pytest.mark.asyncio
async def test_list_products_markdown():
    result = await zozi_mcp.zozi_list_products(
        zozi_mcp.ProductListInput(limit=10, response_format=zozi_mcp.ResponseFormat.MARKDOWN)
    )
    assert "Wireless Mouse" in result
    assert "Laptop Stand" in result


@pytest.mark.asyncio
async def test_list_products_json_pagination():
    result = await zozi_mcp.zozi_list_products(
        zozi_mcp.ProductListInput(limit=10, response_format=zozi_mcp.ResponseFormat.JSON)
    )
    data = json.loads(result)
    assert data["total"] == 2
    assert data["count"] == 2
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_get_product_by_id_and_barcode():
    by_id = await zozi_mcp.zozi_get_product(zozi_mcp.ProductGetInput(product_id=1))
    assert json.loads(by_id)["name"] == "Wireless Mouse"
    by_barcode = await zozi_mcp.zozi_get_product(zozi_mcp.ProductGetInput(barcode="ABC123"))
    assert json.loads(by_barcode)["barcode"] == "ABC123"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_get_product_requires_identifier():
    result = await zozi_mcp.zozi_get_product(zozi_mcp.ProductGetInput())
    assert result.startswith("Error: provide either product_id or barcode.")


@pytest.mark.asyncio
async def test_list_products_keyword_search_routes_to_search_endpoint():
    """Keyword search must POST to /products/search (GET ignores unknown params)."""
    result = await zozi_mcp.zozi_list_products(
        zozi_mcp.ProductListInput(
            search="mouse",
            response_format=zozi_mcp.ResponseFormat.MARKDOWN,
        )
    )
    assert "Wireless Mouse" in result
    assert "Laptop Stand" not in result


@pytest.mark.asyncio
async def test_login_requires_email_or_username():
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        zozi_mcp.LoginInput(password="secret")


@pytest.mark.asyncio
async def test_login_accepts_email_or_username():
    by_email = zozi_mcp.LoginInput(email="a@b.test", password="secret")
    assert by_email.email == "a@b.test"
    by_user = zozi_mcp.LoginInput(username="admin", password="secret")
    assert by_user.username == "admin"


@pytest.mark.asyncio
async def test_list_orders_and_get_order():
    listed = await zozi_mcp.zozi_list_orders(
        zozi_mcp.OrderListInput(response_format=zozi_mcp.ResponseFormat.MARKDOWN)
    )
    assert "Order 501" in listed
    got = await zozi_mcp.zozi_get_order(zozi_mcp.OrderGetInput(order_id=501))
    assert json.loads(got)["status"] == "pending"


@pytest.mark.asyncio
async def test_cancel_order():
    result = await zozi_mcp.zozi_cancel_order(zozi_mcp.OrderCancelInput(order_id=501))
    assert json.loads(result)["status"] == "cancelled"


@pytest.mark.asyncio
async def test_list_and_get_users():
    listed = await zozi_mcp.zozi_list_users(zozi_mcp.ListInput(response_format=zozi_mcp.ResponseFormat.MARKDOWN))
    assert "admin" in listed and "bob" in listed
    got = await zozi_mcp.zozi_get_user(zozi_mcp.UserGetInput(user_id=2))
    assert json.loads(got)["username"] == "bob"


@pytest.mark.asyncio
async def test_list_countries():
    result = await zozi_mcp.zozi_list_countries(zozi_mcp.CountryListInput(response_format=zozi_mcp.ResponseFormat.MARKDOWN))
    assert "Oman" in result and "OM" in result


@pytest.mark.asyncio
async def test_404_error_message_is_actionable():
    result = await zozi_mcp.zozi_get_order(zozi_mcp.OrderGetInput(order_id=404))
    assert "resource not found" in result.lower()
    assert "Check the ID" in result


@pytest.mark.asyncio
async def test_missing_input_validation():
    with pytest.raises(Exception):
        await zozi_mcp.zozi_get_order(zozi_mcp.OrderGetInput())  # order_id required
