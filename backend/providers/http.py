"""Provider wrapper for the aiohttp HTTP client SDK.

All direct `aiohttp` usage in the codebase should import from this provider
module so external SDKs stay isolated under `providers/`.
"""
try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, ClientError, TCPConnector
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None  # type: ignore[assignment]
    ClientSession = None  # type: ignore[assignment]
    ClientTimeout = None  # type: ignore[assignment]
    ClientError = None  # type: ignore[assignment]
    TCPConnector = None  # type: ignore[assignment]

__all__ = ["aiohttp", "ClientSession", "ClientTimeout", "ClientError", "TCPConnector", "HAS_AIOHTTP"]
