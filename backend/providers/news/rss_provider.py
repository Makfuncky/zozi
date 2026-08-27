"""News aggregation provider.

Encapsulates the external HTTP fetching + feed parsing for the command-center
news aggregator so the service layer orchestrates through these helpers instead
of performing vendor HTTP requests or feedparser calls directly.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    feedparser = None  # type: ignore[assignment]

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0


async def fetch_rss_entries(url: str, timeout: float = _DEFAULT_TIMEOUT) -> List[Any]:
    """Fetch an RSS/Atom feed and return its parsed entries.

    Returns the list of ``feedparser`` entry objects so existing per-entry
    mapping logic in the service is unaffected.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    return list(getattr(feed, "entries", []))


async def fetch_api_payload(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Fetch a JSON news API payload and return the parsed dict."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers or {})
        resp.raise_for_status()
        return resp.json()
