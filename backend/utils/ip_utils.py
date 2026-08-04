"""
Centralized IP address extraction and validation utilities.
Handles proxy headers, private IPs, and trusted proxy detection.
"""

import ipaddress
import logging
from typing import Optional

from fastapi import Request

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

TRUSTED_PROXY_HEADERS = {
    "X-Forwarded-For",
    "X-Real-IP",
    "CF-Connecting-IP",
    "True-Client-IP",
    "X-AppEngine-Canonical",
    "X-Nginx-Proxy",
    "Fastly-Client-IP",
    "Forwarded",
}


def extract_ip_address(request: Request) -> Optional[str]:
    """
    Extract client IP address from request, respecting proxy headers.
    
    Priority order:
    1. X-Forwarded-For (first IP in chain)
    2. X-Real-IP
    3. CF-Connecting-IP
    4. True-Client-IP
    5. X-AppEngine-Canonical
    6. request.client.host (fallback)
    """
    for header in IP_HEADER_MAPPING:
        value = request.headers.get(header)
        if value:
            ip = _parse_ip_from_header(value)
            if ip and not _is_private_ip(ip):
                return ip
            if ip:
                return ip
    
    client = request.client
    if client:
        return client.host
    
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
