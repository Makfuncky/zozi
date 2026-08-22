"""Provider wrapper for the aiohttp HTTP client SDK.

All direct ``aiohttp`` usage in the codebase should import from this provider
module so external SDKs stay isolated under ``providers/``.

Real implementation relocated from ``providers.http`` (P13 root-leak cleanup).
``providers/http.py`` is now a backward-compatible re-export shim.
"""
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError, TCPConnector

__all__ = ["aiohttp", "ClientSession", "ClientTimeout", "ClientError", "TCPConnector"]
