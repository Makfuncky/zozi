"""Threat-intelligence vendor provider.

External threat-intel vendor HTTP calls (e.g. the Tor Project exit-node list)
are encapsulated here so the security services orchestrate through these helpers
instead of performing raw third-party HTTP requests directly.
"""

from __future__ import annotations

import logging
import urllib.request
from typing import List

logger = logging.getLogger(__name__)

_TOR_EXIT_LIST_URL = "https://check.torproject.org/torbulkexitlist"
_REQUEST_TIMEOUT = 30.0


def fetch_tor_exit_list() -> List[str]:
    """Fetch the current Tor exit-node IP list.

    Returns a list of IP address strings. On any network/HTTP failure an empty
    list is returned so callers can degrade gracefully.
    """
    try:
        req = urllib.request.Request(
            _TOR_EXIT_LIST_URL, headers={"User-Agent": "zozi/1.0"}
        )
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as response:
            content = response.read().decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch Tor exit list: %s", exc)
        return []

    ips: List[str] = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            ips.append(line)
    return ips


__all__ = ["fetch_tor_exit_list"]
