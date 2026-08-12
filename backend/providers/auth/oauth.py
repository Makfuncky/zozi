from __future__ import annotations

"""Social OAuth provider (Google + Facebook).

Third-party OAuth vendor HTTP calls (Google tokeninfo/token/userinfo, Facebook
Graph) are encapsulated here so the auth controller service orchestrates through
these helpers instead of performing vendor HTTP requests directly. The
authorization-URL builders below keep the vendor endpoint URLs + query wiring in
this provider layer as well.
"""

import logging
from typing import Any, Dict
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
FACEBOOK_AUTH_URL = "https://www.facebook.com/v20.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v20.0/oauth/access_token"
FACEBOOK_PROFILE_URL = "https://graph.facebook.com/me"

_TIMEOUT = 15.0


class OAuthProviderError(Exception):
    """Raised when a social OAuth vendor HTTP call fails (network or non-2xx)."""


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


def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """Validate a Google identity token via the tokeninfo endpoint."""
    return _get_json(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})


def exchange_google_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for Google tokens."""
    return _post_json(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )


def get_google_userinfo(access_token: str) -> Dict[str, Any]:
    """Fetch the authenticated Google user's profile."""
    return _get_json(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )


def exchange_facebook_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for Facebook tokens."""
    return _get_json(
        FACEBOOK_TOKEN_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )


def get_facebook_profile(access_token: str) -> Dict[str, Any]:
    """Fetch the authenticated Facebook user's profile."""
    return _get_json(
        FACEBOOK_PROFILE_URL,
        params={
            "fields": "id,name,email,picture.width(400).height(400)",
            "access_token": access_token,
        },
    )


def build_google_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "openid email profile",
    prompt: str = "select_account",
) -> str:
    """Build the Google OAuth2 authorization redirect URL."""
    params = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
            "prompt": prompt,
        }
    )
    return f"{GOOGLE_AUTH_URL}?{params}"


def build_facebook_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "email,public_profile",
) -> str:
    """Build the Facebook OAuth2 authorization dialog URL."""
    params = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": scope,
            "response_type": "code",
        }
    )
    return f"{FACEBOOK_AUTH_URL}?{params}"


__all__ = [
    "GOOGLE_AUTH_URL",
    "GOOGLE_TOKENINFO_URL",
    "GOOGLE_TOKEN_URL",
    "GOOGLE_USERINFO_URL",
    "FACEBOOK_AUTH_URL",
    "FACEBOOK_TOKEN_URL",
    "FACEBOOK_PROFILE_URL",
    "OAuthProviderError",
    "verify_google_id_token",
    "exchange_google_code",
    "get_google_userinfo",
    "exchange_facebook_code",
    "get_facebook_profile",
    "build_google_authorization_url",
    "build_facebook_authorization_url",
]
