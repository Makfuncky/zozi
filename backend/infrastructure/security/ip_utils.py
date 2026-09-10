"""
Centralized IP address extraction and validation utilities.
Handles proxy headers, private IPs, and trusted proxy detection.

Security model:
- Proxy headers (X-Forwarded-For, X-Real-IP, etc.) are ONLY trusted when the
  immediate peer (request.client.host) is a known trusted proxy.
- When the peer is not a trusted proxy, we fall back to the socket peer address
  (request.client.host), which cannot be spoofed by the client.
- This prevents IP spoofing attacks where clients set X-Forwarded-For to rotate
  their apparent IP and bypass per-IP rate limits.
"""
from __future__ import annotations

import ipaddress
import logging
from typing import Optional, Set

from fastapi import Request

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

IP_HEADER_MAPPING = [
    "X-Forwarded-For",
    "X-Real-IP",
    "CF-Connecting-IP",
    "True-Client-IP",
    "X-AppEngine-Canonical",
    "X-Nginx-Proxy",
    "Fastly-Client-IP",
    "X-Forwarded",
    "Forwarded-For",
]


def _get_trusted_proxy_ips() -> Set[str]:
    """Return the set of trusted proxy IPs from settings.

    If ``trusted_proxy_ips`` is not configured, returns an empty set (no proxies
    trusted -- safest default; proxy headers are ignored unless the operator
    explicitly configures trusted proxies).
    """
    raw = getattr(settings, "trusted_proxy_ips", None)
    if not raw:
        return set()
    if isinstance(raw, str):
        return {ip.strip() for ip in raw.split(",") if ip.strip()}
    return {str(ip).strip() for ip in raw if str(ip).strip()}


def _is_trusted_proxy(peer_ip: str) -> bool:
    """Check if the given peer IP is a configured trusted proxy."""
    if not peer_ip:
        return False
    trusted = _get_trusted_proxy_ips()
    if not trusted:
        return False
    return peer_ip in trusted


def extract_ip_address(request: Request) -> Optional[str]:
    """
    Extract client IP address from request, respecting proxy headers ONLY when
    the immediate peer is a configured trusted proxy.

    Priority order (when peer is a trusted proxy):
    1. X-Forwarded-For (first IP in chain)
    2. X-Real-IP
    3. CF-Connecting-IP
    4. True-Client-IP
    5. X-AppEngine-Canonical
    6. request.client.host (fallback)

    When peer is NOT a trusted proxy:
    - request.client.host is used directly (socket peer, not spoofable).
    """
    client = request.client
    peer_ip = client.host if client else None
    peer_is_trusted = _is_trusted_proxy(peer_ip) if peer_ip else False

    if peer_is_trusted:
        for header in IP_HEADER_MAPPING:
            value = request.headers.get(header)
            if value:
                ip = _parse_ip_from_header(value)
                if ip and not _is_private_ip(ip):
                    return ip
                if ip:
                    return ip

    if peer_ip:
        return peer_ip

    return None


def _parse_ip_from_header(value: str) -> Optional[str]:
    """Parse IP from header value, handling comma-separated lists."""
    if not value:
        return None

    parts = value.split(",")
    if parts:
        ip = parts[0].strip()
        return ip if ip else None
    return None


def _is_private_ip(ip: str) -> bool:
    """Check if IP is a private/reserved/internal address."""
    if not ip:
        return True

    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        return True


def is_valid_public_ip(ip: str) -> bool:
    """Check if IP is a valid public IP address."""
    if not ip:
        return False
    return not _is_private_ip(ip)


def set_request_ip(request: Request) -> str:
    """
    Extract and store IP address in request.state for reuse.
    Returns the extracted IP address.
    """
    ip = extract_ip_address(request)
    if ip:
        request.state.client_ip = ip
    else:
        request.state.client_ip = "unknown"
    return request.state.client_ip


def get_request_ip(request: Request) -> str:
    """Get IP from request.state, or extract if not present."""
    if hasattr(request.state, "client_ip"):
        return request.state.client_ip
    return set_request_ip(request)


def get_ip_for_logging(request: Request) -> str:
    """Get IP for logging purposes, with fallback to 'unknown'."""
    try:
        return get_request_ip(request)
    except Exception:
        return "unknown"

