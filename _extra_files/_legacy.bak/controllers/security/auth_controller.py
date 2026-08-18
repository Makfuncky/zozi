"""controllers.security.auth_controller controller.

Business logic is delegated to services.security.auth_controller_service (routers -> controllers -> services)."""

from services.security.auth_controller_service import (
    DEFAULT_COUNTRY, DEFAULT_CURRENCY, DEFAULT_LANGUAGE, ForgotPasswordRequest, LoginRequest, PreferencesUpdate,
    PublicResendVerificationRequest, REFERRAL_CODE_LENGTH, REFERRAL_NEW_CUSTOMER_BONUS, REFERRAL_REFERRER_BONUS, REFERRAL_SHARE_DAILY_BONUS, RESET_TOKEN_TTL_HOURS,
    RefreshTokenBody, ResetPasswordRequest, SOCIAL_STATE_COOKIE_PREFIX, SocialLoginJsonRequest, SocialLoginRequest, VERIFY_TOKEN_TTL_HOURS,
    _USER_CACHE_TTL_SECONDS, _build_referral_link, _build_social_redirect_response, _create_social_user, _create_tokens_response, _ensure_referral_code,
    _ensure_verification_delivery_available, _extract_avatar_url, _find_user_for_login, _frontend_social_callback, _generate_totp_provisioning_uri, _generate_unique_referral_code,
    _issue_auth_tokens, _issue_totp_challenge, _log_login_success, _next_logistics_partner_code, _normalize_customer_verification_when_gate_disabled, _oauth_state_cookie_name,
    _persist_last_login, _record_device_fingerprint, _record_login_history, _record_referral_event, _referral_event_description, _resolve_google_identity_token,
    _resolve_or_create_social_user, _resolve_user_from_subject, _serialize_referral_event, _slugify_username, _total_referral_points, _unique_username,
    _user_effective_permissions, _user_email, _user_email_verified, _user_id, _user_phone, _user_profile_image,
    _user_public_payload, _user_role, _user_staff_payload, _user_username, _validate_social_state, _validate_totp_code,
    _verify_totp_code_with_fallback, admin_verify_totp, change_password, claim_share_points, complete_totp_login, disable_totp,
    enable_totp, forgot_password, get_current_user, get_facebook_oauth_start, get_google_oauth_start, get_optional_user,
    get_referral_dashboard, get_referral_history, get_social_providers_status, get_totp_status, get_user_preferences, handle_facebook_oauth_callback,
    handle_google_id_token_login, handle_google_oauth_callback, is_customer_email_verification_required, json_login_user, json_register_user, logger,
    login_user, logout_user, oauth2_scheme, oauth2_scheme_optional, refresh_access_token, register_user,
    resend_verification, resend_verification_public, reset_password, resolve_rate_limit, setup_totp, update_profile,
    update_user_preferences, upload_avatar, verify_email_token
)

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
