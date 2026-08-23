"""
Authentication Middleware

Resolves the user from the Bearer JWT token and populates request.state.user,
request.state.user_id, request.state.user_role, and request.state.staff_country_codes
so that downstream middleware (country context, fraud detection, impossible travel,
etc.) can access the authenticated user context.

This middleware runs AFTER rate limiting but BEFORE country context (RLS scope setup)
and BEFORE security middleware that needs user context.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.utils.auth import decode_token

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Resolve user from JWT and populate request.state.
    
    This middleware extracts the user identity from the Bearer token
    and makes it available to downstream middleware via request.state.user
    and request.state.user_id.
    """

    async def dispatch(self, request: Request, call_next):
        # Initialize with no user
        request.state.user = None
        request.state.user_id = None
        request.state.user_role = None
        request.state.staff_country_codes = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        request.state.user_id = int(user_id)
                        request.state.user_role = payload.get("role")
                        staff_codes = payload.get("staff_country_codes") or payload.get("country_scope")
                        if staff_codes and isinstance(staff_codes, (list, tuple)):
                            request.state.staff_country_codes = [str(c).upper() for c in staff_codes if c]
                        # Build a minimal user dict for middleware that expects it
                        request.state.user = {
                            "id": request.state.user_id,
                            "role": request.state.user_role,
                            "email": payload.get("email"),
                            "staff_country_codes": request.state.staff_country_codes,
                        }
            except (ValueError, TypeError):
                # Invalid token format - user remains None
                pass
            except Exception as e:
                logger.debug(f"Auth middleware token decode error: {e}")

        response = await call_next(request)
        return response
