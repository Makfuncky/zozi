from __future__ import annotations

from .oauth import (
    OAuthProviderError,
    exchange_facebook_code,
    exchange_google_code,
    get_facebook_profile,
    get_google_userinfo,
    verify_google_id_token,
)
from .apple import (
    OAuthProviderError as AppleOAuthProviderError,
    build_apple_auth_url,
    create_apple_client_secret,
    exchange_apple_code,
    get_apple_userinfo,
    verify_apple_identity,
)
from .totp import generate_secret, provisioning_uri, verify as verify_totp
from .jwt import JWTError, decode_token, decode_unverified_claims

__all__ = [
    "OAuthProviderError",
    "verify_google_id_token",
    "exchange_google_code",
    "get_google_userinfo",
    "exchange_facebook_code",
    "get_facebook_profile",
    "build_apple_auth_url",
    "create_apple_client_secret",
    "exchange_apple_code",
    "get_apple_userinfo",
    "verify_apple_identity",
    "generate_secret",
    "provisioning_uri",
    "verify_totp",
    "JWTError",
    "decode_token",
    "decode_unverified_claims",
]
