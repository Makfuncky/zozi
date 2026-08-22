"""Per-actor auth request/response models for the admin module.

These are the DTOs for the expanded auth surface (OTP/MFA, social login,
session management, device binding). The core login/register request models
live in ``infrastructure.database.schemas`` (shared) and are reused by the
accounts auth service.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class OtpRequest(BaseModel):
    """Start or verify an OTP challenge."""

    purpose: str  # "login" | "register" | "password_reset" | "device_trust"
    channel: str = "sms"  # "sms" | "email"
    destination: Optional[str] = None  # phone or email; defaults to user's on file
    code: Optional[str] = None  # provided only on the verify step


class DeviceBindingRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    platform: Optional[str] = None
    user_agent: Optional[str] = None
    trusted: bool = False


class SocialLoginRequest(BaseModel):
    provider: str  # "google" | "apple" | "facebook"
    id_token: Optional[str] = None  # OIDC id_token
    access_token: Optional[str] = None  # OAuth access token
    state: Optional[str] = None
    # Dev/test passthrough until real OIDC verification is wired (see social_service).
    provider_user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None


class SessionRevokeRequest(BaseModel):
    session_id: str
