"""Apple Sign-In OAuth provider.

Encapsulates Apple identity-verification (JWT id_token validation against
Apple's JWKS) and the authorization-code token exchange so the auth controller
service orchestrates through these helpers instead of performing vendor HTTP
requests or JWT cryptography directly.

Apple has no userinfo endpoint; the user's identity lives in the id_token
claims, so ``get_apple_userinfo`` decodes/verifies the id_token.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWKClient

import requests

logger = logging.getLogger(__name__)

APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

_TIMEOUT = 15.0


class OAuthProviderError(Exception):
    """Raised when an Apple OAuth vendor call or verification fails."""


def _get_json(url: str, **kwargs: Any) -> Dict[str, Any]:
    try:
        resp = requests.get(url, timeout=_TIMEOUT, **kwargs)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise OAuthProviderError(f"GET {url} failed: {exc}") from exc
    return resp.json()


def _post_json(url: str, **kwargs: Any) -> Dict[str, Any]:
    try:
        resp = requests.post(url, timeout=_TIMEOUT, **kwargs)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise OAuthProviderError(f"POST {url} failed: {exc}") from exc
    return resp.json()


def build_apple_auth_url(
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "name email",
    response_mode: str = "form_post",
) -> str:
    """Build the Apple authorization URL for the sign-in redirect."""
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "response_mode": response_mode,
        "state": state,
    }
    return f"{APPLE_AUTH_URL}?{urlencode(params)}"


def create_apple_client_secret(
    team_id: str,
    client_id: str,
    key_id: str,
    private_key_pem: str,
    max_age: int = 3600,
) -> str:
    """Create Apple's JWT ``client_secret`` (a ES256-signed token)."""
    now = int(time.time())
    payload = {
        "iss": team_id,
        "iat": now,
        "exp": now + max_age,
        "aud": APPLE_ISSUER,
        "sub": client_id,
    }
    headers = {"kid": key_id, "alg": "ES256"}
    return jwt.encode(payload, private_key_pem, algorithm="ES256", headers=headers)


def verify_apple_identity(id_token: str, client_id: Optional[str] = None) -> Dict[str, Any]:
    """Validate an Apple id_token against Apple's JWKS and return its claims."""
    try:
        jwks_client = PyJWKClient(APPLE_KEYS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        decode_kwargs: Dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": APPLE_ISSUER,
        }
        if client_id:
            decode_kwargs["audience"] = client_id
        claims = jwt.decode(id_token, signing_key.key, **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise OAuthProviderError(f"Apple id_token verification failed: {exc}") from exc
    return claims


def exchange_apple_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Exchange an Apple authorization code for tokens."""
    return _post_json(
        APPLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )


def get_apple_userinfo(id_token: str, client_id: Optional[str] = None) -> Dict[str, Any]:
    """Return the Apple user's identity from the id_token claims.

    Apple provides no userinfo endpoint; identity is conveyed in the id_token.
    """
    return verify_apple_identity(id_token, client_id=client_id)
