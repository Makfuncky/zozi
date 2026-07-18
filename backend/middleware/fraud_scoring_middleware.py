"""Fraud scoring middleware for real-time fraud detection.

This middleware intercepts requests and applies fraud scoring to sensitive endpoints
like checkout, login, and payment operations.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from services.fraud_detection_service import FraudScoringEngine
from utils.redis_client import get_redis
from db.database import get_db
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

SENSITIVE_PATHS = {
    "checkout": "/orders/checkout",
    "login": "/auth/login",
    "register": "/auth/register",
    "payout": "/finance/payout",
    "payment": "/payments",
}

EXCLUDE_PATHS = {
    "/admin/fraud",
    "/admin/fraud/events",
    "/admin/fraud/blacklist",
    "/admin/fraud/rules",
    "/admin/fraud/review",
}


class FraudScoringMiddleware(BaseHTTPMiddleware):
    """Middleware that applies fraud scoring to sensitive endpoints."""
    
    def __init__(self, app, db_session=None):
        super().__init__(app)
        self.db = db_session
        self.redis = get_redis()
        self.engine = FraudScoringEngine(db_session, self.redis) if db_session else None
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        is_sensitive = any(
            path.startswith(sensitive_path) 
            for sensitive_path in SENSITIVE_PATHS.values()
        )
        is_excluded = any(path.startswith(exclude_path) for exclude_path in EXCLUDE_PATHS)
        
        if is_sensitive and not is_excluded and self.engine:
            ip_address = get_request_ip(request)
            device_hash = getattr(request.state, "device_fingerprint", None)
            user_id = None
            
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id
            
            headers = dict(request.headers)
            
            try:
                if "checkout" in path:
                    event_type = "checkout"
                elif "login" in path:
                    event_type = "login"
                elif "payout" in path or "payment" in path:
                    event_type = "payout"
                else:
                    event_type = "other"
                
                score_result = self.engine.calculate_score(
                    user_id=user_id,
                    ip_address=ip_address,
                    device_hash=device_hash,
                    event_type=event_type,
                    request_headers=headers,
                )
                
                if score_result.get("is_blocked"):
                    logger.warning(
                        "Request blocked by fraud engine",
                        extra={
                            "path": path,
                            "ip": ip_address,
                            "score": score_result.get("score"),
                            "rules": score_result.get("triggered_rules"),
                        }
                    )
                    return Response(
                        content=json.dumps({"detail": "Request blocked by fraud detection"}),
                        status_code=403,
                        media_type="application/json",
                    )
                
                request.state.fraud_score = score_result.get("score", 0)
                request.state.fraud_action = score_result.get("action", "allow")
                
            except Exception as e:
                logger.error(f"Fraud scoring error: {e}")
        
        return await call_next(request)

