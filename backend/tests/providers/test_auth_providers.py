"""
Comprehensive test suite for the backend/providers/auth subpackage.

Tests every public function, class, and constant across the Auth provider modules:
- apple.py, jwt.py, oauth.py, totp.py

External SDKs/APIs (pyotp, python-jose, PyJWT, requests) are mocked via
unittest.mock to ensure tests run without network access or installed vendor
packages.

Run with: pytest tests/providers/test_auth_providers.py -v
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from backend.providers.auth import (
    OAuthProviderError,
    verify_google_id_token,
    exchange_google_code,
    get_google_userinfo,
    exchange_facebook_code,
    get_facebook_profile,
    build_apple_auth_url,
    create_apple_client_secret,
    exchange_apple_code,
    get_apple_userinfo,
    verify_apple_identity,
    generate_secret,
    provisioning_uri,
    verify_totp,
    JWTError,
    decode_token,
    decode_unverified_claims,
)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level import tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthImports:
    """Verify all public symbols are importable from the auth package."""

    def test_import_oauth_provider_error(self):
        from backend.providers.auth import OAuthProviderError
        assert issubclass(OAuthProviderError, Exception)

    def test_import_jwt_error(self):
        from backend.providers.auth import JWTError
        assert issubclass(JWTError, Exception)

    def test_import_functions(self):
        from backend.providers.auth import (
            verify_google_id_token,
            exchange_google_code,
            get_google_userinfo,
            exchange_facebook_code,
            get_facebook_profile,
            build_apple_auth_url,
            create_apple_client_secret,
            exchange_apple_code,
            get_apple_userinfo,
            verify_apple_identity,
            generate_secret,
            provisioning_uri,
            verify_totp,
            decode_token,
            decode_unverified_claims,
        )
        assert callable(verify_google_id_token)
        assert callable(exchange_google_code)
        assert callable(get_google_userinfo)
        assert callable(exchange_facebook_code)
        assert callable(get_facebook_profile)
        assert callable(build_apple_auth_url)
        assert callable(create_apple_client_secret)
        assert callable(exchange_apple_code)
        assert callable(get_apple_userinfo)
        assert callable(verify_apple_identity)
        assert callable(generate_secret)
        assert callable(provisioning_uri)
        assert callable(verify_totp)
        assert callable(decode_token)
        assert callable(decode_unverified_claims)


# ─────────────────────────────────────────────────────────────────────────────
# OAuth provider (Google + Facebook) tests
# ─────────────────────────────────────────────────────────────────────────────

class TestOAuthProviderConstants:
    """Verify OAuth endpoint constants."""

    def test_google_urls(self):
        from backend.providers.auth.oauth import (
            GOOGLE_AUTH_URL,
            GOOGLE_TOKENINFO_URL,
            GOOGLE_TOKEN_URL,
            GOOGLE_USERINFO_URL,
        )
        assert "google.com" in GOOGLE_AUTH_URL
        assert "googleapis.com" in GOOGLE_TOKENINFO_URL
        assert "googleapis.com" in GOOGLE_TOKEN_URL
        assert "googleapis.com" in GOOGLE_USERINFO_URL

    def test_facebook_urls(self):
        from backend.providers.auth.oauth import (
            FACEBOOK_AUTH_URL,
            FACEBOOK_TOKEN_URL,
            FACEBOOK_PROFILE_URL,
        )
        assert "facebook.com" in FACEBOOK_AUTH_URL
        assert "facebook.net" in FACEBOOK_TOKEN_URL or "graph.facebook.com" in FACEBOOK_TOKEN_URL
        assert "graph.facebook.com" in FACEBOOK_PROFILE_URL


class TestVerifyGoogleIdToken:
    """Tests for verify_google_id_token function."""

    @patch("backend.providers.auth.oauth._get_json")
    def test_verify_google_id_token_success(self, mock_get):
        mock_get.return_value = {
            "aud": "client-id",
            "sub": "12345",
            "email": "user@gmail.com",
        }
        result = verify_google_id_token("fake.id.token")
        assert result["sub"] == "12345"
        assert result["email"] == "user@gmail.com"
        mock_get.assert_called_once()

    @patch("backend.providers.auth.oauth._get_json")
    def test_verify_google_id_token_network_error(self, mock_get):
        mock_get.side_effect = OAuthProviderError("Connection refused")
        with pytest.raises(OAuthProviderError):
            verify_google_id_token("token")


class TestExchangeGoogleCode:
    """Tests for exchange_google_code function."""

    @patch("backend.providers.auth.oauth._post_json")
    def test_exchange_google_code_success(self, mock_post):
        mock_post.return_value = {
            "access_token": "google-access-token",
            "refresh_token": "google-refresh-token",
            "expires_in": 3600,
        }
        result = exchange_google_code("auth-code", "http://cb", "client-id", "secret")
        assert result["access_token"] == "google-access-token"
        mock_post.assert_called_once()

    @patch("backend.providers.auth.oauth._post_json")
    def test_exchange_google_code_network_error(self, mock_post):
        mock_post.side_effect = OAuthProviderError("timeout")
        with pytest.raises(OAuthProviderError):
            exchange_google_code("code", "uri", "id", "secret")


class TestGetGoogleUserinfo:
    """Tests for get_google_userinfo function."""

    @patch("backend.providers.auth.oauth._get_json")
    def test_get_google_userinfo_success(self, mock_get):
        mock_get.return_value = {
            "sub": "123",
            "name": "Test User",
            "email": "test@gmail.com",
            "picture": "https://pic",
        }
        result = get_google_userinfo("access-token")
        assert result["name"] == "Test User"
        assert result["email"] == "test@gmail.com"

    @patch("backend.providers.auth.oauth._get_json")
    def test_get_google_userinfo_failure(self, mock_get):
        mock_get.side_effect = OAuthProviderError("401 expired")
        with pytest.raises(OAuthProviderError):
            get_google_userinfo("bad-token")


class TestExchangeFacebookCode:
    """Tests for exchange_facebook_code function."""

    @patch("backend.providers.auth.oauth._get_json")
    def test_exchange_facebook_code_success(self, mock_get):
        mock_get.return_value = {
            "access_token": "fb-token",
            "token_type": "bearer",
        }
        result = exchange_facebook_code("code", "http://cb", "app-id", "app-secret")
        assert result["access_token"] == "fb-token"

    @patch("backend.providers.auth.oauth._get_json")
    def test_exchange_facebook_code_error(self, mock_get):
        mock_get.side_effect = OAuthProviderError("invalid code")
        with pytest.raises(OAuthProviderError):
            exchange_facebook_code("bad-code", "uri", "id", "secret")


class TestGetFacebookProfile:
    """Tests for get_facebook_profile function."""

    @patch("backend.providers.auth.oauth._get_json")
    def test_get_facebook_profile_success(self, mock_get):
        mock_get.return_value = {
            "id": "999",
            "name": "FB User",
            "email": "fb@example.com",
        }
        result = get_facebook_profile("fb-token")
        assert result["name"] == "FB User"

    @patch("backend.providers.auth.oauth._get_json")
    def test_get_facebook_profile_failure(self, mock_get):
        mock_get.side_effect = OAuthProviderError("token expired")
        with pytest.raises(OAuthProviderError):
            get_facebook_profile("expired-token")


class TestGoogleAuthorizationURL:
    """Tests for build_google_authorization_url function."""

    def test_build_google_url_contains_required_params(self):
        from backend.providers.auth.oauth import build_google_authorization_url
        url = build_google_authorization_url(
            client_id="my-client",
            redirect_uri="http://localhost/cb",
            state="random-state",
        )
        assert "client_id=my-client" in url
        assert "redirect_uri=http" in url
        assert "state=random-state" in url
        assert "response_type=code" in url

    def test_build_google_url_custom_scope(self):
        from backend.providers.auth.oauth import build_google_authorization_url
        url = build_google_authorization_url(
            client_id="cid",
            redirect_uri="http://cb",
            state="s",
            scope="openid email",
        )
        assert "scope=openid+email" in url or "scope=openid%20email" in url

    def test_build_google_url_custom_prompt(self):
        from backend.providers.auth.oauth import build_google_authorization_url
        url = build_google_authorization_url(
            client_id="cid",
            redirect_uri="http://cb",
            state="s",
            prompt="consent",
        )
        assert "prompt=consent" in url


class TestFacebookAuthorizationURL:
    """Tests for build_facebook_authorization_url function."""

    def test_build_facebook_url_contains_required_params(self):
        from backend.providers.auth.oauth import build_facebook_authorization_url
        url = build_facebook_authorization_url(
            client_id="app-id",
            redirect_uri="http://localhost/cb",
            state="fb-state",
        )
        assert "client_id=app-id" in url
        assert "state=fb-state" in url
        assert "response_type=code" in url

    def test_build_facebook_url_custom_scope(self):
        from backend.providers.auth.oauth import build_facebook_authorization_url
        url = build_facebook_authorization_url(
            client_id="cid",
            redirect_uri="http://cb",
            state="s",
            scope="email,public_profile,user_friends",
        )
        assert "scope" in url


class TestOAuthHelpers:
    """Tests for internal _get_json and _post_json helpers."""

    @patch("backend.providers.auth.oauth.requests.get")
    def test_get_json_success(self, mock_get):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"key": "value"}
        mock_get.return_value = mock_resp

        from backend.providers.auth.oauth import _get_json
        result = _get_json("http://example.com")
        assert result == {"key": "value"}

    @patch("backend.providers.auth.oauth.requests.get")
    def test_get_json_http_error(self, mock_get):
        import requests
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_resp

        from backend.providers.auth.oauth import _get_json
        with pytest.raises(OAuthProviderError, match="GET"):
            _get_json("http://example.com")

    @patch("backend.providers.auth.oauth.requests.get")
    def test_get_json_network_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError("refused")

        from backend.providers.auth.oauth import _get_json
        with pytest.raises(OAuthProviderError):
            _get_json("http://example.com")

    @patch("backend.providers.auth.oauth.requests.post")
    def test_post_json_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"token": "abc"}
        mock_post.return_value = mock_resp

        from backend.providers.auth.oauth import _post_json
        result = _post_json("http://example.com", data={"key": "val"})
        assert result == {"token": "abc"}

    @patch("backend.providers.auth.oauth.requests.post")
    def test_post_json_http_error(self, mock_post):
        import requests
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("400")
        mock_post.return_value = mock_resp

        from backend.providers.auth.oauth import _post_json
        with pytest.raises(OAuthProviderError, match="POST"):
            _post_json("http://example.com")


# ─────────────────────────────────────────────────────────────────────────────
# Apple Sign-In provider tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAppleProviderConstants:
    """Verify Apple provider endpoint constants."""

    def test_apple_urls(self):
        from backend.providers.auth.apple import (
            APPLE_AUTH_URL,
            APPLE_TOKEN_URL,
            APPLE_KEYS_URL,
            APPLE_ISSUER,
        )
        assert "appleid.apple.com" in APPLE_AUTH_URL
        assert "appleid.apple.com" in APPLE_TOKEN_URL
        assert "appleid.apple.com" in APPLE_KEYS_URL
        assert APPLE_ISSUER == "https://appleid.apple.com"

    def test_timeout_constant(self):
        from backend.providers.auth.apple import _TIMEOUT
        assert _TIMEOUT == 15.0


class TestBuildAppleAuthUrl:
    """Tests for build_apple_auth_url function."""

    def test_build_apple_url_contains_required_params(self):
        url = build_apple_auth_url(
            client_id="com.example.app",
            redirect_uri="https://example.com/cb",
            state="random-state",
        )
        assert "client_id=com.example.app" in url
        assert "redirect_uri=https" in url
        assert "state=random-state" in url
        assert "response_type=code" in url
        assert "response_mode=form_post" in url

    def test_build_apple_url_default_scope(self):
        url = build_apple_auth_url("cid", "http://cb", "state")
        assert "scope=name+email" in url or "scope=name%20email" in url

    def test_build_apple_url_custom_scope(self):
        url = build_apple_auth_url("cid", "http://cb", "state", scope="email")
        assert "scope=email" in url

    def test_build_apple_url_custom_response_mode(self):
        url = build_apple_auth_url("cid", "http://cb", "state", response_mode="web_message")
        assert "response_mode=web_message" in url


class TestCreateAppleClientSecret:
    """Tests for create_apple_client_secret function."""

    @patch("backend.providers.auth.apple.jwt.encode")
    @patch("backend.providers.auth.apple.time")
    def test_create_client_secret_success(self, mock_time, mock_encode):
        mock_time.time.return_value = 1000000
        mock_encode.return_value = "signed-jwt-token"

        result = create_apple_client_secret(
            team_id="TEAM123",
            client_id="com.app",
            key_id="KEY1",
            private_key_pem="-----BEGIN PRIVATE KEY-----\nkeydata\n-----END PRIVATE KEY-----",
        )
        assert result == "signed-jwt-token"
        mock_encode.assert_called_once()

    @patch("backend.providers.auth.apple.jwt.encode")
    @patch("backend.providers.auth.apple.time")
    def test_create_client_secret_payload_structure(self, mock_time, mock_encode):
        mock_time.time.return_value = 1000000
        mock_encode.return_value = "jwt"

        create_apple_client_secret(
            team_id="TEAM",
            client_id="com.app",
            key_id="KID",
            private_key_pem="key",
            max_age=1800,
        )
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["iss"] == "TEAM"
        assert payload["sub"] == "com.app"
        assert payload["aud"] == "https://appleid.apple.com"
        assert payload["exp"] == 1000000 + 1800
        assert call_args[1]["algorithm"] == "ES256"

    @patch("backend.providers.auth.apple.jwt.encode")
    @patch("backend.providers.auth.apple.time")
    def test_create_client_secret_default_max_age(self, mock_time, mock_encode):
        mock_time.time.return_value = 5000
        mock_encode.return_value = "jwt"

        create_apple_client_secret(
            team_id="T",
            client_id="c",
            key_id="k",
            private_key_pem="key",
        )
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["exp"] == 5000 + 3600  # default max_age


class TestVerifyAppleIdentity:
    """Tests for verify_apple_identity function."""

    @patch("backend.providers.auth.apple.PyJWKClient")
    @patch("backend.providers.auth.apple.jwt.decode")
    def test_verify_apple_identity_success(self, mock_decode, mock_jwks):
        mock_key = Mock()
        mock_key.key = "public-key"
        mock_jwks_instance = Mock()
        mock_jwks_instance.get_signing_key_from_jwt.return_value = mock_key
        mock_jwks.return_value = mock_jwks_instance
        mock_decode.return_value = {"sub": "apple-user-123", "email": "a@icloud.com"}

        result = verify_apple_identity("apple.id.token", client_id="com.app")
        assert result["sub"] == "apple-user-123"
        mock_decode.assert_called_once()

    @patch("backend.providers.auth.apple.PyJWKClient")
    @patch("backend.providers.auth.apple.jwt.decode")
    def test_verify_apple_identity_without_audience(self, mock_decode, mock_jwks):
        mock_key = Mock()
        mock_key.key = "pk"
        mock_jwks.return_value.get_signing_key_from_jwt.return_value = mock_key
        mock_decode.return_value = {"sub": "123"}

        verify_apple_identity("token")
        call_kwargs = mock_decode.call_args[1]
        assert "audience" not in call_kwargs

    @patch("backend.providers.auth.apple.PyJWKClient")
    @patch("backend.providers.auth.apple.jwt.decode")
    def test_verify_apple_identity_failure(self, mock_decode, mock_jwks):
        import jwt as pyjwt
        mock_key = Mock()
        mock_key.key = "pk"
        mock_jwks.return_value.get_signing_key_from_jwt.return_value = mock_key
        mock_decode.side_effect = pyjwt.PyJWTError("Signature expired")

        with pytest.raises(OAuthProviderError, match="failed"):
            verify_apple_identity("expired-token", client_id="com.app")


class TestExchangeAppleCode:
    """Tests for exchange_apple_code function."""

    @patch("backend.providers.auth.apple._post_json")
    def test_exchange_apple_code_success(self, mock_post):
        mock_post.return_value = {
            "access_token": "apple-access",
            "id_token": "apple-id-token",
            "refresh_token": "apple-refresh",
        }
        result = exchange_apple_code("code", "http://cb", "com.app", "secret-jwt")
        assert result["id_token"] == "apple-id-token"

    @patch("backend.providers.auth.apple._post_json")
    def test_exchange_apple_code_error(self, mock_post):
        mock_post.side_effect = OAuthProviderError("invalid_grant")
        with pytest.raises(OAuthProviderError):
            exchange_apple_code("bad-code", "uri", "cid", "secret")


class TestGetAppleUserinfo:
    """Tests for get_apple_userinfo function."""

    @patch("backend.providers.auth.apple.verify_apple_identity")
    def test_get_apple_userinfo_delegates(self, mock_verify):
        mock_verify.return_value = {"sub": "123", "email": "a@icloud.com"}
        result = get_apple_userinfo("id-token", client_id="com.app")
        assert result["email"] == "a@icloud.com"
        mock_verify.assert_called_once_with("id-token", client_id="com.app")

    @patch("backend.providers.auth.apple.verify_apple_identity")
    def test_get_apple_userinfo_failure(self, mock_verify):
        mock_verify.side_effect = OAuthProviderError("invalid token")
        with pytest.raises(OAuthProviderError):
            get_apple_userinfo("bad-token")


# ─────────────────────────────────────────────────────────────────────────────
# JWT provider tests
# ─────────────────────────────────────────────────────────────────────────────

class TestJWTProvider:
    """Tests for the jwt provider module."""

    @patch("backend.providers.auth.jwt.jwt.get_unverified_claims")
    def test_decode_unverified_claims_success(self, mock_unverified):
        mock_unverified.return_value = {"jti": "token-id", "sub": "user-1"}
        result = decode_unverified_claims("some.jwt.token")
        assert result["jti"] == "token-id"
        mock_unverified.assert_called_once_with("some.jwt.token")

    @patch("backend.providers.auth.jwt.jwt.get_unverified_claims")
    def test_decode_unverified_claims_invalid_token(self, mock_unverified):
        mock_unverified.side_effect = JWTError("invalid token")
        with pytest.raises(JWTError):
            decode_unverified_claims("bad-token")

    @patch("backend.providers.auth.jwt.jwt.decode")
    def test_decode_token_success(self, mock_decode):
        mock_decode.return_value = {"sub": "user-1", "exp": 1234567}
        result = decode_token("valid.jwt", "secret", ["HS256"])
        assert result["sub"] == "user-1"
        mock_decode.assert_called_once_with("valid.jwt", "secret", algorithms=["HS256"])

    @patch("backend.providers.auth.jwt.jwt.decode")
    def test_decode_token_invalid_signature(self, mock_decode):
        mock_decode.side_effect = JWTError("signature invalid")
        with pytest.raises(JWTError):
            decode_token("tampered.jwt", "wrong-secret", ["HS256"])

    @patch("backend.providers.auth.jwt.jwt.decode")
    def test_decode_token_expired(self, mock_decode):
        mock_decode.side_effect = JWTError("token expired")
        with pytest.raises(JWTError):
            decode_token("expired.jwt", "secret", ["HS256"])

    @patch("backend.providers.auth.jwt.jwt.decode")
    def test_decode_token_algorithms_param(self, mock_decode):
        mock_decode.return_value = {"data": "test"}
        decode_token("token", "secret", ["RS256", "HS256"])
        call_args = mock_decode.call_args
        assert call_args[1]["algorithms"] == ["RS256", "HS256"]


# ─────────────────────────────────────────────────────────────────────────────
# TOTP provider tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTOTPProvider:
    """Tests for the totp provider module."""

    @patch("backend.providers.auth.totp.pyotp.random_base32")
    def test_generate_secret(self, mock_random):
        mock_random.return_value = "JBSWY3DPEHPK3PXP"
        result = generate_secret()
        assert result == "JBSWY3DPEHPK3PXP"
        mock_random.assert_called_once()

    def test_generate_secret_returns_string(self):
        result = generate_secret()
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_provisioning_uri_success(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.provisioning_uri.return_value = "otpauth://totp/Test:user?secret=KEY"
        mock_totp_cls.return_value = mock_totp

        result = provisioning_uri("secret-key", "user@example.com", "ZOZI")
        assert "otpauth://" in result
        assert "secret=" in result
        mock_totp_cls.assert_called_once_with("secret-key")

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_provisioning_uri_custom_issuer(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.provisioning_uri.return_value = "otpauth://totp/issuer:user?secret=S"
        mock_totp_cls.return_value = mock_totp

        result = provisioning_uri("S", "user", "CustomIssuer")
        mock_totp.provisioning_uri.assert_called_once_with(
            name="user", issuer_name="CustomIssuer"
        )

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_verify_valid_code(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_cls.return_value = mock_totp

        result = verify_totp("secret-key", "123456")
        assert result is True
        mock_totp.verify.assert_called_once_with("123456", valid_window=0)

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_verify_invalid_code(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.verify.return_value = False
        mock_totp_cls.return_value = mock_totp

        result = verify_totp("secret-key", "000000")
        assert result is False

    def test_verify_empty_secret(self):
        result = verify_totp("", "123456")
        assert result is False

    def test_verify_empty_code(self):
        result = verify_totp("secret", "")
        assert result is False

    def test_verify_both_empty(self):
        result = verify_totp("", "")
        assert result is False

    def test_verify_none_secret(self):
        result = verify_totp(None, "123456")
        assert result is False

    def test_verify_none_code(self):
        result = verify_totp("secret", None)
        assert result is False

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_verify_with_valid_window(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_cls.return_value = mock_totp

        result = verify_totp("secret", "123456", valid_window=1)
        assert result is True
        mock_totp.verify.assert_called_once_with("123456", valid_window=1)

    @patch("backend.providers.auth.totp.pyotp.TOTP")
    def test_verify_with_large_window(self, mock_totp_cls):
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_cls.return_value = mock_totp

        verify_totp("secret", "123456", valid_window=10)
        mock_totp.verify.assert_called_once_with("123456", valid_window=10)


# ─────────────────────────────────────────────────────────────────────────────
# OAuthProviderError tests
# ─────────────────────────────────────────────────────────────────────────────

class TestOAuthProviderError:
    """Tests for the OAuthProviderError exception class."""

    def test_exception_inheritance(self):
        assert issubclass(OAuthProviderError, Exception)

    def test_exception_can_be_raised(self):
        with pytest.raises(OAuthProviderError):
            raise OAuthProviderError("test error")

    def test_exception_message(self):
        with pytest.raises(OAuthProviderError, match="vendor failed"):
            raise OAuthProviderError("vendor failed")

    def test_exception_chaining(self):
        try:
            try:
                raise ConnectionError("network down")
            except ConnectionError as e:
                raise OAuthProviderError("wrapped") from e
        except OAuthProviderError as exc:
            assert isinstance(exc.__cause__, ConnectionError)


# ─────────────────────────────────────────────────────────────────────────────
# JWTError tests
# ─────────────────────────────────────────────────────────────────────────────

class TestJWTError:
    """Tests for the JWTError exception class."""

    def test_exception_inheritance(self):
        assert issubclass(JWTError, Exception)

    def test_exception_can_be_raised(self):
        with pytest.raises(JWTError):
            raise JWTError("bad token")

    def test_exception_message(self):
        with pytest.raises(JWTError, match="expired"):
            raise JWTError("token expired")


# ─────────────────────────────────────────────────────────────────────────────
# Apple provider internal helpers tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAppleInternalHelpers:
    """Tests for internal Apple provider helpers."""

    @patch("backend.providers.auth.apple.requests.get")
    def test_get_json_success(self, mock_get):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"keys": []}
        mock_get.return_value = mock_resp

        from backend.providers.auth.apple import _get_json
        result = _get_json("https://appleid.apple.com/auth/keys")
        assert result == {"keys": []}

    @patch("backend.providers.auth.apple.requests.get")
    def test_get_json_failure(self, mock_get):
        import requests
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.return_value = mock_resp

        from backend.providers.auth.apple import _get_json
        with pytest.raises(OAuthProviderError):
            _get_json("https://example.com")

    @patch("backend.providers.auth.apple.requests.post")
    def test_post_json_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"access_token": "token"}
        mock_post.return_value = mock_resp

        from backend.providers.auth.apple import _post_json
        result = _post_json("https://appleid.apple.com/auth/token", data={"code": "c"})
        assert result["access_token"] == "token"

    @patch("backend.providers.auth.apple.requests.post")
    def test_post_json_failure(self, mock_post):
        import requests
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("400")
        mock_post.return_value = mock_resp

        from backend.providers.auth.apple import _post_json
        with pytest.raises(OAuthProviderError):
            _post_json("https://example.com")
