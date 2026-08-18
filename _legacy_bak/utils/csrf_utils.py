"""CSRF token helpers for the router layer.

Routers must not import from ``middleware`` directly (Grid Line: routers may
only depend on controllers, schemas, auth-dependencies and ``get_db``). The
canonical token generator lives in ``middleware.csrf_middleware``; this thin
re-export keeps that single implementation while giving routers a permitted
import surface.
"""

from middleware.csrf_middleware import generate_csrf_token, get_csrf_token_from_request

__all__ = ["generate_csrf_token", "get_csrf_token_from_request"]
