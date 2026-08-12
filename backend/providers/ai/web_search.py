from __future__ import annotations

"""Web search provider.

External search-engine vendor calls (DuckDuckGo HTML scrape) are encapsulated
here so the country-research service layer orchestrates through this helper
instead of performing third-party HTTP requests directly.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DDG_HTML_URL = "https://duckduckgo.com/html/"
_DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; ZoziCountryAI/1.0)"


def duckduckgo_search(
    query: str,
    *,
    user_agent: str = _DEFAULT_USER_AGENT,
    timeout: float = 30.0,
    connect_timeout: float = 10.0,
    snippet_limit: int = 500,
) -> List[Dict[str, Any]]:
    """Run a DuckDuckGo HTML query and return normalized result records.

    Returns an empty list on any failure (network/parse) so the caller can
    degrade gracefully. Each record: ``query``, ``title``, ``href``, ``snippet``,
    ``source``.
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx unavailable; web evidence search skipped")
        return []

    try:
        with httpx.Client(
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            follow_redirects=True,
        ) as client:
            response = client.get(
                _DDG_HTML_URL,
                params={"q": query},
                headers={"User-Agent": user_agent},
            )
        if response.status_code != 200:
            return []
        return [
            {
                "query": query,
                "title": f"Web search: {query}",
                "href": f"https://duckduckgo.com/?q={query}",
                "snippet": (response.text or "")[:snippet_limit],
                "source": "DuckDuckGo",
            }
        ]
    except Exception as exc:
        logger.warning("Web evidence fetch failed for %s: %s", query, exc)
        return []


__all__ = ["duckduckgo_search"]
