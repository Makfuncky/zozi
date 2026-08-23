"""controllers.security.auth_controller controller.

Business logic is delegated to services.security.auth_controller_service (routers -> controllers -> services)."""

from domains.governance.services.auth.auth_controller_service import DEFAULT_COUNTRY
from domains.governance.services.auth.auth_controller_service import DEFAULT_CURRENCY
from domains.governance.services.auth.auth_controller_service import DEFAULT_LANGUAGE
from domains.governance.services.auth.auth_controller_service import ForgotPasswordRequest
from domains.governance.services.auth.auth_controller_service import LoginRequest
from domains.governance.services.auth.auth_controller_service import PreferencesUpdate
from domains.governance.services.auth.auth_controller_service import PublicResendVerificationRequest
from domains.governance.services.auth.auth_controller_service import REFERRAL_CODE_LENGTH
from domains.governance.services.auth.auth_controller_service import REFERRAL_NEW_CUSTOMER_BONUS
from domains.governance.services.auth.auth_controller_service import REFERRAL_REFERRER_BONUS
from domains.governance.services.auth.auth_controller_service import REFERRAL_SHARE_DAILY_BONUS
from domains.governance.services.auth.auth_controller_service import RESET_TOKEN_TTL_HOURS
from domains.governance.services.auth.auth_controller_service import RefreshTokenBody
from domains.governance.services.auth.auth_controller_service import ResetPasswordRequest
from domains.governance.services.auth.auth_controller_service import SOCIAL_STATE_COOKIE_PREFIX
from domains.governance.services.auth.auth_controller_service import SocialLoginJsonRequest
from domains.governance.services.auth.auth_controller_service import SocialLoginRequest
from domains.governance.services.auth.auth_controller_service import VERIFY_TOKEN_TTL_HOURS
from domains.governance.services.auth.auth_controller_service import _USER_CACHE_TTL_SECONDS
from domains.governance.services.auth.auth_controller_service import _build_referral_link
from domains.governance.services.auth.auth_controller_service import _build_social_redirect_response
from domains.governance.services.auth.auth_controller_service import _create_social_user
from domains.governance.services.auth.auth_controller_service import _create_tokens_response
from domains.governance.services.auth.auth_controller_service import _ensure_referral_code
from domains.governance.services.auth.auth_controller_service import _ensure_verification_delivery_available
from domains.governance.services.auth.auth_controller_service import _extract_avatar_url
from domains.governance.services.auth.auth_controller_service import _find_user_for_login
from domains.governance.services.auth.auth_controller_service import _frontend_social_callback
from domains.governance.services.auth.auth_controller_service import _generate_totp_provisioning_uri
from domains.governance.services.auth.auth_controller_service import _generate_unique_referral_code
from domains.governance.services.auth.auth_controller_service import _issue_auth_tokens
from domains.governance.services.auth.auth_controller_service import _issue_totp_challenge
from domains.governance.services.auth.auth_controller_service import _log_login_success
from domains.governance.services.auth.auth_controller_service import _next_logistics_partner_code
from domains.governance.services.auth.auth_controller_service import _normalize_customer_verification_when_gate_disabled
from domains.governance.services.auth.auth_controller_service import _oauth_state_cookie_name
from domains.governance.services.auth.auth_controller_service import _persist_last_login
from domains.governance.services.auth.auth_controller_service import _record_device_fingerprint
from domains.governance.services.auth.auth_controller_service import _record_login_history
from domains.governance.services.auth.auth_controller_service import _record_referral_event
from domains.governance.services.auth.auth_controller_service import _referral_event_description
from domains.governance.services.auth.auth_controller_service import _resolve_google_identity_token
from domains.governance.services.auth.auth_controller_service import _resolve_or_create_social_user
from domains.governance.services.auth.auth_controller_service import _resolve_user_from_subject
from domains.governance.services.auth.auth_controller_service import _serialize_referral_event
from domains.governance.services.auth.auth_controller_service import _slugify_username
from domains.governance.services.auth.auth_controller_service import _total_referral_points
from domains.governance.services.auth.auth_controller_service import _unique_username
from domains.governance.services.auth.auth_controller_service import _user_effective_permissions
from domains.governance.services.auth.auth_controller_service import _user_email
from domains.governance.services.auth.auth_controller_service import _user_email_verified
from domains.governance.services.auth.auth_controller_service import _user_id
from domains.governance.services.auth.auth_controller_service import _user_phone
from domains.governance.services.auth.auth_controller_service import _user_profile_image
from domains.governance.services.auth.auth_controller_service import _user_public_payload
from domains.governance.services.auth.auth_controller_service import _user_role
from domains.governance.services.auth.auth_controller_service import _user_staff_payload
from domains.governance.services.auth.auth_controller_service import _user_username
from domains.governance.services.auth.auth_controller_service import _validate_social_state
from domains.governance.services.auth.auth_controller_service import _validate_totp_code
from domains.governance.services.auth.auth_controller_service import _verify_totp_code_with_fallback
from domains.governance.services.auth.auth_controller_service import admin_verify_totp
from domains.governance.services.auth.auth_controller_service import change_password
from domains.governance.services.auth.auth_controller_service import claim_share_points
from domains.governance.services.auth.auth_controller_service import complete_totp_login
from domains.governance.services.auth.auth_controller_service import disable_totp
from domains.governance.services.auth.auth_controller_service import enable_totp
from domains.governance.services.auth.auth_controller_service import forgot_password
from domains.governance.services.auth.auth_controller_service import get_current_user
from domains.governance.services.auth.auth_controller_service import get_facebook_oauth_start
from domains.governance.services.auth.auth_controller_service import get_google_oauth_start
from domains.governance.services.auth.auth_controller_service import get_optional_user
from domains.governance.services.auth.auth_controller_service import get_referral_dashboard
from domains.governance.services.auth.auth_controller_service import get_referral_history
from domains.governance.services.auth.auth_controller_service import get_social_providers_status
from domains.governance.services.auth.auth_controller_service import get_totp_status
from domains.governance.services.auth.auth_controller_service import get_user_preferences
from domains.governance.services.auth.auth_controller_service import handle_facebook_oauth_callback
from domains.governance.services.auth.auth_controller_service import handle_google_id_token_login
from domains.governance.services.auth.auth_controller_service import handle_google_oauth_callback
from domains.governance.services.auth.auth_controller_service import is_customer_email_verification_required
from domains.governance.services.auth.auth_controller_service import json_login_user
from domains.governance.services.auth.auth_controller_service import json_register_user
from domains.governance.services.auth.auth_controller_service import logger
from domains.governance.services.auth.auth_controller_service import login_user
from domains.governance.services.auth.auth_controller_service import logout_user
from domains.governance.services.auth.auth_controller_service import oauth2_scheme
from domains.governance.services.auth.auth_controller_service import oauth2_scheme_optional
from domains.governance.services.auth.auth_controller_service import refresh_access_token
from domains.governance.services.auth.auth_controller_service import register_user
from domains.governance.services.auth.auth_controller_service import resend_verification
from domains.governance.services.auth.auth_controller_service import resend_verification_public
from domains.governance.services.auth.auth_controller_service import reset_password
from domains.governance.services.auth.auth_controller_service import resolve_rate_limit
from domains.governance.services.auth.auth_controller_service import setup_totp
from domains.governance.services.auth.auth_controller_service import update_profile
from domains.governance.services.auth.auth_controller_service import update_user_preferences
from domains.governance.services.auth.auth_controller_service import upload_avatar
from domains.governance.services.auth.auth_controller_service import verify_email_token

__all__ = [
    "DEFAULT_COUNTRY", "DEFAULT_CURRENCY", "DEFAULT_LANGUAGE", "ForgotPasswordRequest", "LoginRequest", "PreferencesUpdate",
    "PublicResendVerificationRequest", "REFERRAL_CODE_LENGTH", "REFERRAL_NEW_CUSTOMER_BONUS", "REFERRAL_REFERRER_BONUS", "REFERRAL_SHARE_DAILY_BONUS", "RESET_TOKEN_TTL_HOURS",
    "RefreshTokenBody", "ResetPasswordRequest", "SOCIAL_STATE_COOKIE_PREFIX", "SocialLoginJsonRequest", "SocialLoginRequest", "VERIFY_TOKEN_TTL_HOURS",
    "_USER_CACHE_TTL_SECONDS", "_build_referral_link", "_build_social_redirect_response", "_create_social_user", "_create_tokens_response", "_ensure_referral_code",
    "_ensure_verification_delivery_available", "_extract_avatar_url", "_find_user_for_login", "_frontend_social_callback", "_generate_totp_provisioning_uri", "_generate_unique_referral_code",
    "_issue_auth_tokens", "_issue_totp_challenge", "_log_login_success", "_next_logistics_partner_code", "_normalize_customer_verification_when_gate_disabled", "_oauth_state_cookie_name",
    "_persist_last_login", "_record_device_fingerprint", "_record_login_history", "_record_referral_event", "_referral_event_description", "_resolve_google_identity_token",
    "_resolve_or_create_social_user", "_resolve_user_from_subject", "_serialize_referral_event", "_slugify_username", "_total_referral_points", "_unique_username",
    "_user_effective_permissions", "_user_email", "_user_email_verified", "_user_id", "_user_phone", "_user_profile_image",
    "_user_public_payload", "_user_role", "_user_staff_payload", "_user_username", "_validate_social_state", "_validate_totp_code",
    "_verify_totp_code_with_fallback", "admin_verify_totp", "change_password", "claim_share_points", "complete_totp_login", "disable_totp",
    "enable_totp", "forgot_password", "get_current_user", "get_facebook_oauth_start", "get_google_oauth_start", "get_optional_user",
    "get_referral_dashboard", "get_referral_history", "get_social_providers_status", "get_totp_status", "get_user_preferences", "handle_facebook_oauth_callback",
    "handle_google_id_token_login", "handle_google_oauth_callback", "is_customer_email_verification_required", "json_login_user", "json_register_user", "logger",
    "login_user", "logout_user", "oauth2_scheme", "oauth2_scheme_optional", "refresh_access_token", "register_user",
    "resend_verification", "resend_verification_public", "reset_password", "resolve_rate_limit", "setup_totp", "update_profile",
    "update_user_preferences", "upload_avatar", "verify_email_token"
]
