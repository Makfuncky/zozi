#!python
"""
Cryptographic Webhook Verification
Implements HMAC signature verification for webhook authenticity
"""

import hmac
import hashlib
import time
import json
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WebhookProviderConfig:
    """Configuration for webhook provider."""
    name: str
    secret: str
    signature_header: str
    signature_prefix: str
    tolerance: int = 300


class WebhookVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for cryptographic webhook verification.
    Implements HMAC signature verification with replay attack protection.
    """

    PROVIDERS: Dict[str, WebhookProviderConfig] = {
        "stripe": WebhookProviderConfig(
            name="stripe",
            secret=settings.stripe_webhook_secret,
            signature_header="Stripe-Signature",
            signature_prefix="v1=",
            tolerance=300,
        ),
        "tap": WebhookProviderConfig(
            name="tap",
            secret=settings.tap_webhook_secret,
            signature_header="Tap-Signature",
            signature_prefix="v1=",
            tolerance=300,
        ),
        "paypal": WebhookProviderConfig(
            name="paypal",
            secret=getattr(settings, 'paypal_webhook_secret', ''),
            signature_header="PayPal-Transmission-Sig",
            signature_prefix="",
            tolerance=300,
        ),
        "resend": WebhookProviderConfig(
            name="resend",
            secret=settings.resend_webhook_secret,
            signature_header="Resend-Signature",
            signature_prefix="t=",
            tolerance=300,
        ),
    }

    WEBHOOK_PATHS = {
        "/payments/webhook",
        "/payments/tap/webhook",
        "/email/webhooks",
    }

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if not any(path.startswith(w) for w in self.WEBHOOK_PATHS):
            return await call_next(request)

        provider = self._identify_provider(path)
        if not provider:
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        if not await self._verify_webhook(request, provider):
            logger.warning(f"Webhook verification failed for {provider.name}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid webhook signature"},
            )

        return await call_next(request)

    def _identify_provider(self, path: str) -> Optional[WebhookProviderConfig]:
        """Identify webhook provider from path."""
        path_lower = path.lower()
        
        if path_lower.startswith("/payments/webhook/"):
            parts = path_lower.split("/")
            if len(parts) >= 4:
                provider_name = parts[3]
                config = self.PROVIDERS.get(provider_name)
                if config:
                    return config
        
        if path_lower == "/payments/tap/webhook":
            return self.PROVIDERS.get("tap")
        
        if path_lower.startswith("/payments/tap/webhook"):
            return self.PROVIDERS.get("tap")
        
        if path_lower == "/email/webhooks":
            return self.PROVIDERS.get("resend")
        
        return None

    async def _verify_webhook(
        self,
        request: Request,
        provider: WebhookProviderConfig,
    ) -> bool:
        """Verify webhook signature."""
        try:
            body = await request.body()
            signature_header = request.headers.get(provider.signature_header, "")

            if not signature_header:
                return False

            timestamp = self._extract_timestamp(signature_header, provider)
            if timestamp is None:
                return False

            if abs(time.time() - timestamp) > provider.tolerance:
                logger.warning("Webhook signature expired")
                return False

            expected_signature = self._compute_signature(
                body, provider.secret, timestamp
            )
            provided_signature = self._extract_signature(signature_header, provider)

            if not provided_signature:
                return False

            return hmac.compare_digest(expected_signature, provided_signature)

        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return False

    def _extract_timestamp(self, signature_header: str, provider: WebhookProviderConfig) -> Optional[int]:
        """Extract timestamp from signature header."""
        try:
            parts = signature_header.split(",")
            for part in parts:
                if part.startswith("t="):
                    return int(part.split("=")[1])
        except Exception:
            pass
        return None

    def _extract_signature(self, signature_header: str, provider: WebhookProviderConfig) -> Optional[str]:
        """Extract signature from signature header."""
        try:
            parts = signature_header.split(",")
            for part in parts:
                if part.startswith(provider.signature_prefix):
                    return part.replace(provider.signature_prefix, "")
        except Exception:
            pass
        return None

    def _compute_signature(
        self,
        payload: bytes,
        secret: str,
        timestamp: int,
    ) -> str:
        """Compute HMAC signature."""
        try:
            payload_str = payload.decode('utf-8')
        except UnicodeDecodeError:
            payload_str = payload.decode('latin-1')
        signed_payload = f"{timestamp}.{payload_str}"
        return hmac.new(
            secret.encode(),
            signed_payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    provider: str = "stripe",
) -> bool:
    """
    Verify webhook signature externally.
    Useful for testing and manual verification.
    """
    if provider == "stripe":
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    if provider == "tap":
        expected = hmac.new(
            secret.encode(),
            f"{int(time.time())}.{payload.decode('utf-8', errors='replace')}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    return False


def compute_webhook_signature(
    payload: bytes,
    secret: str,
    timestamp: Optional[int] = None,
) -> str:
    """
    Compute webhook signature for testing.
    """
    if timestamp is None:
        timestamp = int(time.time())

    try:
        payload_str = payload.decode('utf-8')
    except UnicodeDecodeError:
        payload_str = payload.decode('latin-1')
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    return f"t={timestamp},v1={signature}"


def redis_client():
    """Get Redis client for replay protection."""
    try:
        import redis
        from utils.config import settings
        return redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=5)
    except Exception:
        return None


class ReplayAttackProtection:
    """Protects against replay attacks."""

    def __init__(self, window_seconds: int = 300):
        self.redis = redis_client()
        self.window = window_seconds

    def is_replayed(self, signature: str) -> bool:
        """Check if signature has been seen before."""
        if not self.redis:
            return False

        try:
            key = f"signature:{signature}"
            if self.redis.exists(key):
                return True

            self.redis.setex(key, self.window, "1")
            return False
        except Exception:
            return False

