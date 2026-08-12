"""Provider wrapper for the aiohttp HTTP client SDK.

All direct `aiohttp` usage in the codebase should import from this provider
module so external SDKs stay isolated under `providers/`.
"""
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError, TCPConnector

__all__ = ["aiohttp", "ClientSession", "ClientTimeout", "ClientError", "TCPConnector"]
