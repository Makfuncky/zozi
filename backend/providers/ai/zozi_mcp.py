"""MCP server for the ZOZI marketplace API.

Exposes the ZOZI e-commerce backend as Model Context Protocol tools so an LLM
agent can authenticate, browse the catalog, inspect and manage orders, and
query users/countries through well-designed, validated interfaces.

Run (stdio, for local agents):
    python -m services.mcp.zozi_mcp

Run (streamable HTTP, for remote clients):
    python -m services.mcp.zozi_mcp --transport streamable_http --port 8001

Environment:
    ZOZI_MCP_API_URL    Base URL of the ZOZI API (default http://127.0.0.1:8000/api/v1)
    ZOZI_MCP_USERNAME   Optional auto-login username on startup
    ZOZI_MCP_PASSWORD   Optional auto-login password on startup
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)


import json
import os
import sys
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator
try:
    from mcp.server.fastmcp import FastMCP
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    class FastMCP:
        """Minimal stand-in used only when the optional ``mcp`` SDK is absent.

        The ZOZI MCP server requires the SDK at runtime; this stub merely lets the
        module import so the rest of the package stays import-clean.
        """

        def __init__(self, name, lifespan=None):
            self.name = name

        def tool(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def resource(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def prompt(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def run(self, transport=None):
            raise RuntimeError(
                "The 'mcp' package is not installed. Install it to run the ZOZI MCP "
                "server (e.g. `pip install mcp`)."
            )

# ---------------------------------------------------------------------------
# Lifespan (defined before the server instance so FastMCP is constructed with
# the lifespan wired in — late attribute assignment may not register with the
# SDK's internal server).  Body names resolve at call time, so forward refs to
# _request / _client / _token / AUTO_* are fine.
# ---------------------------------------------------------------------------


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialise the shared HTTP client and optionally auto-login."""
    global _client, _token
    async with httpx.AsyncClient() as client:
        _client = client
        if AUTO_USERNAME and AUTO_PASSWORD:
            try:
                data = await _request(
                    "POST",
                    "auth/login",
                    json={"username": AUTO_USERNAME, "password": AUTO_PASSWORD},
                )
                _token = data.get("access_token")
            except (RuntimeError, ValueError, TypeError, KeyError) as exc:  # pragma: no cover - best-effort startup
                logger.exception("auto-login failed", error=str(exc))
                print(f"[zozi_mcp] auto-login failed: {exc}", file=sys.stderr)
        yield
    _client = None
    _token = None


# ---------------------------------------------------------------------------
# Server instance (defined here so the @mcp.tool decorators below can bind)
# ---------------------------------------------------------------------------

mcp = FastMCP("zozi_mcp", lifespan=app_lifespan)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("ZOZI_MCP_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
AUTO_USERNAME = os.getenv("ZOZI_MCP_USERNAME") or None
AUTO_PASSWORD = os.getenv("ZOZI_MCP_PASSWORD") or None
REQUEST_TIMEOUT = 30.0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

_client: Optional[httpx.AsyncClient] = None
_token: Optional[str] = None


def _headers() -> Dict[str, str]:
    """Authorization headers for authenticated requests."""
    if _token:
        return {"Authorization": f"Bearer {_token}"}
    return {}


async def _request(method: str, path: str, **kwargs: Any) -> dict:
    """Reusable, pagination-agnostic API request helper."""
    if _client is None:
        raise RuntimeError("MCP server not initialised — run under the FastMCP lifespan.")
    url = f"{API_BASE_URL}/{path.lstrip('/')}"
    resp = await _client.request(method, url, headers=_headers(), timeout=REQUEST_TIMEOUT, **kwargs)
    if resp.status_code >= 400:
        detail = ""
        try:
            body = resp.json()
            detail = str(body.get("detail") or body)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug("Failed to parse error response body", error=str(e))
            detail = resp.text[:300]
        raise RuntimeError(
            f"ZOZI API error {resp.status_code} on {method} {path}: {detail}"
        )
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json()


def _handle_api_error(e: Exception) -> str:
    """Consistent, actionable error formatting for every tool."""
    if isinstance(e, httpx.TimeoutException):
        return "Error: request timed out. The ZOZI API did not respond in time — retry, or check the server is running."
    if isinstance(e, RuntimeError) and "ZOZI API error" in str(e):
        msg = str(e)
        if "401" in msg:
            return (
                "Error: authentication required. Call zozi_login with valid credentials first, "
                "or set ZOZI_MCP_USERNAME/ZOZI_MCP_PASSWORD."
            )
        if "404" in msg:
            return "Error: resource not found. Check the ID/identifier you passed — it may be wrong or deleted."
        return f"Error: {msg}"
    return f"Error: unexpected failure ({type(e).__name__}): {e}"


def _fmt_datetime(value: Any) -> str:
    """Human-friendly timestamp; falls back to raw value."""
    if value is None:
        return "n/a"
    return str(value).replace("T", " ")[:19]


def _pagination_payload(items: list, total: Any, limit: int, offset: int) -> dict:
    """Standard pagination envelope shared by list tools."""
    total = int(total or 0)
    count = len(items)
    return {
        "total": total,
        "count": count,
        "limit": limit,
        "offset": offset,
        "items": items,
        "has_more": total > offset + count,
        "next_offset": offset + count if total > offset + count else None,
    }


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class LoginInput(BaseModel):
    """Credentials for authenticating to the ZOZI API."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: Optional[str] = Field(
        default=None, description="Account email (provide email or username)", max_length=254
    )
    username: Optional[str] = Field(
        default=None, description="Account username (provide email or username)", max_length=100
    )
    password: str = Field(..., description="Account password", min_length=1, max_length=200)

    @model_validator(mode="after")
    def _require_identifier(self):
        if not self.email and not self.username:
            raise ValueError("Provide either email or username to log in.")
        return self


class ListInput(BaseModel):
    """Shared pagination inputs for list tools."""

    model_config = ConfigDict(extra="forbid")

    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Max results (1-100)", ge=1, le=MAX_LIMIT)
    offset: Optional[int] = Field(default=0, description="Results to skip", ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class ProductListInput(ListInput):
    """Filter inputs for the product catalog."""

    model_config = ConfigDict(extra="forbid")

    category: Optional[str] = Field(default=None, description="Category name filter (e.g. 'Electronics')", max_length=100)
    subcategory: Optional[str] = Field(default=None, description="Subcategory name filter", max_length=100)
    search: Optional[str] = Field(default=None, description="Free-text keyword search", max_length=200)


class ProductGetInput(BaseModel):
    """Fetch a single product by ID or barcode."""

    model_config = ConfigDict(extra="forbid")

    product_id: Optional[int] = Field(default=None, description="Product numeric ID", ge=1)
    barcode: Optional[str] = Field(default=None, description="Product barcode (alternative to product_id)", max_length=64)


class OrderListInput(ListInput):
    """Filter inputs for orders."""

    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = Field(default=None, description="Order status filter (e.g. 'pending', 'shipped', 'delivered', 'cancelled')", max_length=40)
    customer_id: Optional[int] = Field(default=None, description="Filter by customer user ID", ge=1)


class OrderGetInput(BaseModel):
    """Fetch a single order by ID."""

    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., description="Order numeric ID", ge=1)


class OrderCancelInput(BaseModel):
    """Cancel an order."""

    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(..., description="Order numeric ID to cancel", ge=1)
    reason: Optional[str] = Field(default=None, description="Cancellation reason", max_length=300)


class UserGetInput(BaseModel):
    """Fetch a single user by ID."""

    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(..., description="User numeric ID", ge=1)


class CountryListInput(ListInput):
    """Filters for the country registry."""

    model_config = ConfigDict(extra="forbid")

    region: Optional[str] = Field(default=None, description="Region filter (e.g. 'Asia', 'Middle East')", max_length=80)


# ---------------------------------------------------------------------------
# Response formatters
# ---------------------------------------------------------------------------


def _format_products(items: list) -> str:
    lines = ["# Products", ""]
    if not items:
        return "No products found for the given filters."
    for p in items:
        name = p.get("name") or p.get("title") or f"Product {p.get('id')}"
        price = p.get("price") or p.get("selling_price")
        price_str = f"{price} {p.get('currency') or p.get('currency_code') or ''}".strip()
        lines.append(f"## {name} (id={p.get('id')})")
        if price_str:
            lines.append(f"- **Price**: {price_str}")
        if p.get("category"):
            lines.append(f"- **Category**: {p.get('category')}")
        if p.get("status"):
            lines.append(f"- **Status**: {p.get('status')}")
        lines.append("")
    return "\n".join(lines)


def _format_orders(items: list) -> str:
    lines = ["# Orders", ""]
    if not items:
        return "No orders found for the given filters."
    for o in items:
        oid = o.get("id") or o.get("order_id")
        lines.append(f"## Order {oid}")
        lines.append(f"- **Status**: {o.get('status') or 'n/a'}")
        lines.append(f"- **Total**: {o.get('total') or o.get('grand_total') or o.get('amount') or 'n/a'}")
        lines.append(f"- **Placed**: {_fmt_datetime(o.get('created_at') or o.get('order_date'))}")
        if o.get("customer_id") or o.get("user_id"):
            lines.append(f"- **Customer id**: {o.get('customer_id') or o.get('user_id')}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="zozi_login",
    annotations={
        "title": "Log in to ZOZI",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def zozi_login(params: LoginInput) -> str:
    """Authenticate to the ZOZI API and cache the access token for later tools.

    Call this first when tools report authentication errors. The token is held
    in memory for the lifetime of the MCP session.

    Args:
        params (LoginInput): Credentials — either `email` or `username`, plus `password`.

    Returns:
        str: JSON summary of the authenticated user, or an error string.
    """
    try:
        payload = {"password": params.password}
        if params.email:
            payload["email"] = params.email
        if params.username:
            payload["username"] = params.username
        data = await _request("POST", "auth/login", json=payload)
        global _token
        _token = data.get("access_token")
        if not _token:
            return "Error: login succeeded but no access_token was returned."
        user = data.get("user") or {}
        return json.dumps(
            {
                "authenticated": True,
                "user_id": user.get("id"),
                "email": user.get("email"),
                "username": user.get("username"),
                "role": user.get("role"),
                "token_type": data.get("token_type", "bearer"),
            },
            indent=2,
        )
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_get_current_user",
    annotations={
        "title": "Get current user",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_get_current_user() -> str:
    """Return the profile of the currently authenticated user.

    Returns:
        str: JSON profile of the current user, or an error string if not authenticated.
    """
    try:
        data = await _request("GET", "users/me")
        return json.dumps(data, indent=2, default=str)
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_list_products",
    annotations={
        "title": "List ZOZI products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_list_products(params: ProductListInput) -> str:
    """Browse the ZOZI product catalog with optional category/subcategory/keyword filters.

    Args:
        params (ProductListInput):
            - category (Optional[str]): filter by category name
            - subcategory (Optional[str]): filter by subcategory name
            - search (Optional[str]): free-text keyword search
            - limit (Optional[int]): max results, 1-100 (default 20)
            - offset (Optional[int]): pagination offset
            - response_format (Optional[str]): 'markdown' or 'json'

    Returns:
        str: paginated product list in the requested format.
    """
    try:
        if params.search:
            # GET /products ignores unknown query params; keyword search is a
            # real endpoint (POST /products/search) that mirrors the GET filters.
            body = {
                "q": params.search,
                "limit": params.limit,
                "offset": params.offset,
            }
            if params.category:
                body["category"] = params.category
            if params.subcategory:
                body["subcategory"] = params.subcategory
            data = await _request("POST", "products/search", json=body)
        else:
            q = {"limit": params.limit, "offset": params.offset}
            if params.category:
                q["category"] = params.category
            if params.subcategory:
                q["subcategory"] = params.subcategory
            data = await _request("GET", "products", params=q)
        items = data.get("items") or data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
        total = data.get("total") or data.get("total_count") or len(items)
        env = _pagination_payload(items, total, params.limit or DEFAULT_LIMIT, params.offset or 0)
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(env, indent=2, default=str)
        body = _format_products(items)
        body += f"\n\n_Showing {len(items)} of {env['total']} — use offset={env['next_offset']} for more._" if env["has_more"] else ""
        return body
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_get_product",
    annotations={
        "title": "Get product by ID or barcode",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_get_product(params: ProductGetInput) -> str:
    """Fetch full details for a single product by numeric ID or barcode.

    Args:
        params (ProductGetInput): either product_id (int) or barcode (str).

    Returns:
        str: JSON product detail or an error string.
    """
    try:
        if params.product_id is not None:
            data = await _request("GET", f"products/{params.product_id}")
        elif params.barcode:
            data = await _request("GET", f"products/barcode/{params.barcode}")
        else:
            return "Error: provide either product_id or barcode."
        return json.dumps(data, indent=2, default=str)
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_list_orders",
    annotations={
        "title": "List ZOZI orders",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_list_orders(params: OrderListInput) -> str:
    """List orders with optional status/customer filters and pagination.

    Args:
        params (OrderListInput):
            - status (Optional[str]): filter by order status
            - customer_id (Optional[int]): filter by customer user id
            - limit (Optional[int]): max results, 1-100 (default 20)
            - offset (Optional[int]): pagination offset
            - response_format (Optional[str]): 'markdown' or 'json'

    Returns:
        str: paginated order list in the requested format.
    """
    try:
        q = {"limit": params.limit, "offset": params.offset}
        if params.status:
            q["status"] = params.status
        if params.customer_id is not None:
            q["customer_id"] = params.customer_id
        data = await _request("GET", "orders", params=q)
        items = data.get("items") or data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
        total = data.get("total") or data.get("total_count") or len(items)
        env = _pagination_payload(items, total, params.limit or DEFAULT_LIMIT, params.offset or 0)
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(env, indent=2, default=str)
        body = _format_orders(items)
        body += f"\n\n_Showing {len(items)} of {env['total']} — use offset={env['next_offset']} for more._" if env["has_more"] else ""
        return body
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_get_order",
    annotations={
        "title": "Get order details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_get_order(params: OrderGetInput) -> str:
    """Fetch full details for a single order, including items and status history.

    Args:
        params (OrderGetInput): order_id (int).

    Returns:
        str: JSON order detail or an error string.
    """
    try:
        data = await _request("GET", f"orders/{params.order_id}")
        return json.dumps(data, indent=2, default=str)
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_cancel_order",
    annotations={
        "title": "Cancel an order",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def zozi_cancel_order(params: OrderCancelInput) -> str:
    """Request cancellation of an order.

    Requires an authenticated session with cancellation permission; the API
    enforces role/status rules (e.g. shipped orders cannot be cancelled).

    Args:
        params (OrderCancelInput): order_id (int) and optional reason (str).

    Returns:
        str: JSON cancellation result or an actionable error string.
    """
    try:
        data = await _request("POST", f"orders/{params.order_id}/cancel", json={"reason": params.reason} if params.reason else {})
        return json.dumps(data, indent=2, default=str)
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_list_users",
    annotations={
        "title": "List ZOZI users",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_list_users(params: ListInput) -> str:
    """List users (admin only) with pagination.

    Args:
        params (ListInput): limit (1-100, default 20), offset, response_format.

    Returns:
        str: paginated user list in the requested format.
    """
    try:
        data = await _request("GET", "users", params={"limit": params.limit, "offset": params.offset})
        items = data.get("items") or data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
        total = data.get("total") or data.get("total_count") or len(items)
        env = _pagination_payload(items, total, params.limit or DEFAULT_LIMIT, params.offset or 0)
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(env, indent=2, default=str)
        lines = ["# Users", ""]
        for u in items:
            lines.append(f"- **{u.get('username') or u.get('email')}** (id={u.get('id')}, role={u.get('role') or 'n/a'})")
        body = "\n".join(lines)
        body += f"\n\n_Showing {len(items)} of {env['total']} — use offset={env['next_offset']} for more._" if env["has_more"] else ""
        return body
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_get_user",
    annotations={
        "title": "Get user details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_get_user(params: UserGetInput) -> str:
    """Fetch a single user profile by ID (admin only).

    Args:
        params (UserGetInput): user_id (int).

    Returns:
        str: JSON user profile or an error string.
    """
    try:
        data = await _request("GET", f"users/{params.user_id}")
        return json.dumps(data, indent=2, default=str)
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


@mcp.tool(
    name="zozi_list_countries",
    annotations={
        "title": "List ZOZI country registry",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zozi_list_countries(params: CountryListInput) -> str:
    """List countries in the ZOZI marketplace registry (name, code, currency, region).

    Args:
        params (CountryListInput):
            - region (Optional[str]): filter by region
            - limit, offset, response_format

    Returns:
        str: paginated country list in the requested format.
    """
    try:
        q = {"limit": params.limit, "offset": params.offset}
        if params.region:
            q["region"] = params.region
        data = await _request("GET", "countries", params=q)
        items = data.get("items") or data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
        total = data.get("total") or data.get("total_count") or len(items)
        env = _pagination_payload(items, total, params.limit or DEFAULT_LIMIT, params.offset or 0)
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(env, indent=2, default=str)
        lines = ["# Countries", ""]
        for c in items:
            name = c.get("name") or c.get("country_name") or f"Country {c.get('id')}"
            code = c.get("code") or c.get("iso_code") or c.get("country_code") or ""
            lines.append(f"- **{name}** ({code}) — currency: {c.get('currency_code') or c.get('currency') or 'n/a'}, region: {c.get('region') or 'n/a'}")
        body = "\n".join(lines)
        body += f"\n\n_Showing {len(items)} of {env['total']} — use offset={env['next_offset']} for more._" if env["has_more"] else ""
        return body
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        logger.exception("Tool execution failed", error=str(e))
        return _handle_api_error(e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    # FastMCP.run() supports only the transport name — 'stdio' or 'streamable-http'.
    # For remote deployments, serve via uvicorn with FastMCP's ASGI app instead.
    transport = "streamable-http" if "--transport" in sys.argv and "http" in sys.argv else "stdio"
    mcp.run(transport=transport)