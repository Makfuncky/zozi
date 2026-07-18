"""
Email service for ZOZI.

Transport precedence:
1. Runtime database configuration (admin-managed)
2. Environment bootstrap settings
3. Console preview in development/test
4. Disabled in other environments
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Any, Optional, cast

from sqlalchemy.orm import Session

from utils.config import settings

logger = logging.getLogger(__name__)

_RUNTIME_CONFIG_LOCK = threading.RLock()
_RUNTIME_CONFIG_CACHE: dict[str, dict[str, object]] = {}
_EMAIL_PURPOSES = (
    "default",
    "promotional",
    "transactional",
    "notification",
    "alert",
    "verification",
    "login_verification",
    "password_reset",
)

_INVISIBLE_SECRET_CHARS = {
    "\u00a0": " ",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\ufeff": "",
}


class EmailDeliveryDisabledError(RuntimeError):
    """Raised when the app is asked to send a real email without a live mail transport."""


def _normalize_runtime_text(value: object) -> str:
    normalized = str(value or "")
    for source, replacement in _INVISIBLE_SECRET_CHARS.items():
        normalized = normalized.replace(source, replacement)
    return normalized.strip()


def _normalize_runtime_secret(value: object) -> str:
    return "".join(_normalize_runtime_text(value).split())


def invalidate_email_runtime_config_cache() -> None:
    with _RUNTIME_CONFIG_LOCK:
        _RUNTIME_CONFIG_CACHE.clear()


def refresh_email_runtime_config_cache(*, force_database: bool = False) -> dict[str, object]:
    with _RUNTIME_CONFIG_LOCK:
        _RUNTIME_CONFIG_CACHE.clear()
        if force_database:
            _RUNTIME_CONFIG_CACHE["force_database"] = {"enabled": True}
            resolved = _load_runtime_email_config()
        else:
            resolved = _load_environment_email_config(configured_provider="environment")
        _RUNTIME_CONFIG_CACHE["resolved"] = resolved
        return resolved


def _normalize_sender_map(default_sender: str, overrides: dict[str, str | None] | None = None) -> dict[str, str]:
    sender_map = {purpose: default_sender for purpose in _EMAIL_PURPOSES}
    if overrides:
        for purpose, value in overrides.items():
            if purpose in sender_map and value:
                sender_map[purpose] = value
    return sender_map


def _load_environment_email_config(
    *,
    configured_provider: str = "environment",
    sender_overrides: dict[str, str | None] | None = None,
) -> dict[str, object]:
    env_sender_map = _normalize_sender_map(settings.email_from, sender_overrides)

    if settings.resend_api_key:
        return {
            "provider": "resend",
            "configured_provider": configured_provider,
            "source": "environment",
            "available": True,
            "live": True,
            "preview_only": False,
            "supports_webhooks": True,
            "from_address": env_sender_map["default"],
            "sender_map": env_sender_map,
            "resend_api_key": settings.resend_api_key,
            "resend_webhook_secret": settings.resend_webhook_secret or os.getenv("RESEND_WEBHOOK_SECRET", ""),
            "resend_api_key_configured": True,
            "resend_webhook_secret_configured": bool(settings.resend_webhook_secret or os.getenv("RESEND_WEBHOOK_SECRET", "")),
            "smtp_password_configured": bool(settings.smtp_password),
        }

    if settings.has_smtp_config:
        return {
            "provider": "smtp",
            "configured_provider": configured_provider,
            "source": "environment",
            "available": True,
            "live": True,
            "preview_only": False,
            "supports_webhooks": False,
            "from_address": env_sender_map["default"],
            "sender_map": env_sender_map,
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_username": settings.smtp_username,
            "smtp_password": settings.smtp_password,
            "smtp_use_tls": settings.smtp_use_tls,
            "smtp_use_ssl": settings.smtp_use_ssl,
            "smtp_timeout_seconds": settings.smtp_timeout_seconds,
            "resend_api_key_configured": bool(settings.resend_api_key),
            "resend_webhook_secret_configured": False,
            "smtp_password_configured": bool(settings.smtp_password),
        }

    if settings.app_env in {"development", "test"}:
        return {
            "provider": "console",
            "configured_provider": configured_provider,
            "source": "fallback",
            "available": True,
            "live": False,
            "preview_only": True,
            "supports_webhooks": False,
            "from_address": env_sender_map["default"],
            "sender_map": env_sender_map,
            "resend_api_key_configured": bool(settings.resend_api_key),
            "resend_webhook_secret_configured": False,
            "smtp_password_configured": bool(settings.smtp_password),
        }

    return {
        "provider": "disabled",
        "configured_provider": configured_provider,
        "source": "fallback",
        "available": False,
        "live": False,
        "preview_only": False,
        "supports_webhooks": False,
        "from_address": env_sender_map["default"],
        "sender_map": env_sender_map,
        "resend_api_key_configured": bool(settings.resend_api_key),
        "resend_webhook_secret_configured": False,
        "smtp_password_configured": bool(settings.smtp_password),
    }


def _load_runtime_email_config() -> dict[str, object]:
    from db.database import SessionLocal
    from models import EmailProviderConfig

    configured_provider = "environment"
    sender_overrides: dict[str, str | None] = {}
    record = None

    db = SessionLocal()
    try:
        record = db.query(EmailProviderConfig).order_by(EmailProviderConfig.id.desc()).first()
    except Exception:
        logger.debug("Email provider config table not available; using environment settings")
    finally:
        db.close()

    if record is not None:
        record_obj = cast(Any, record)
        configured_provider = cast(str, record_obj.provider or "environment").strip().lower()
        sender_overrides = {
            "default": cast(Optional[str], record_obj.email_from_default),
            "promotional": cast(Optional[str], record_obj.email_from_promotional),
            "transactional": cast(Optional[str], record_obj.email_from_transactional),
            "notification": cast(Optional[str], record_obj.email_from_notification),
            "alert": cast(Optional[str], record_obj.email_from_alert),
            "verification": cast(Optional[str], record_obj.email_from_verification),
            "login_verification": cast(Optional[str], record_obj.email_from_login_verification),
            "password_reset": cast(Optional[str], record_obj.email_from_password_reset),
        }
        default_sender = cast(Optional[str], record_obj.email_from_default) or settings.email_from
        sender_map = _normalize_sender_map(default_sender, sender_overrides)

        if configured_provider == "resend" and (cast(Optional[str], record_obj.resend_api_key) or "").strip():
            return {
                "provider": "resend",
                "configured_provider": configured_provider,
                "source": "database",
                "available": True,
                "live": True,
                "preview_only": False,
                "supports_webhooks": True,
                "from_address": sender_map["default"],
                "sender_map": sender_map,
                "resend_api_key": cast(Optional[str], record_obj.resend_api_key),
                "resend_webhook_secret": cast(Optional[str], record_obj.resend_webhook_secret),
                "resend_api_key_configured": True,
                "resend_webhook_secret_configured": bool(record_obj.resend_webhook_secret),
                "smtp_password_configured": bool(record_obj.smtp_password),
            }

        if configured_provider == "smtp" and (cast(Optional[str], record_obj.smtp_host) or "").strip() and sender_map["default"].strip():
            return {
                "provider": "smtp",
                "configured_provider": configured_provider,
                "source": "database",
                "available": True,
                "live": True,
                "preview_only": False,
                "supports_webhooks": False,
                "from_address": sender_map["default"],
                "sender_map": sender_map,
                "smtp_host": cast(Optional[str], record_obj.smtp_host),
                "smtp_port": cast(int, record_obj.smtp_port),
                "smtp_username": cast(Optional[str], record_obj.smtp_username),
                "smtp_password": cast(Optional[str], record_obj.smtp_password),
                "smtp_use_tls": cast(bool, record_obj.smtp_use_tls),
                "smtp_use_ssl": cast(bool, record_obj.smtp_use_ssl),
                "smtp_timeout_seconds": cast(int, record_obj.smtp_timeout_seconds),
                "resend_api_key_configured": bool(record_obj.resend_api_key),
                "resend_webhook_secret_configured": bool(record_obj.resend_webhook_secret),
                "smtp_password_configured": bool(record_obj.smtp_password),
            }

        if configured_provider == "disabled":
            return {
                "provider": "disabled",
                "configured_provider": configured_provider,
                "source": "database",
                "available": False,
                "live": False,
                "preview_only": False,
                "supports_webhooks": False,
                "from_address": sender_map["default"],
                "sender_map": sender_map,
                "resend_api_key_configured": bool(record_obj.resend_api_key),
                "resend_webhook_secret_configured": bool(record_obj.resend_webhook_secret),
                "smtp_password_configured": bool(record_obj.smtp_password),
            }

        return _load_environment_email_config(
            configured_provider=configured_provider,
            sender_overrides=sender_overrides,
        )

    return _load_environment_email_config(configured_provider=configured_provider)


def _get_runtime_email_config() -> dict[str, object]:
    with _RUNTIME_CONFIG_LOCK:
        cached = _RUNTIME_CONFIG_CACHE.get("resolved")
        if cached is not None:
            return cached
        force_database = bool(_RUNTIME_CONFIG_CACHE.get("force_database"))
        if settings.app_env == "test" and not force_database:
            resolved = _load_environment_email_config(configured_provider="environment")
        else:
            resolved = _load_runtime_email_config()
        _RUNTIME_CONFIG_CACHE["resolved"] = resolved
        return resolved


def get_email_sender_address(purpose: str = "transactional") -> str:
    runtime = _get_runtime_email_config()
    sender_map = runtime.get("sender_map") or {}
    normalized_purpose = purpose if purpose in sender_map else "transactional"
    return str(sender_map.get(normalized_purpose) or runtime.get("from_address") or settings.email_from)


def get_email_delivery_status() -> dict[str, object]:
    runtime = dict(_get_runtime_email_config())
    return {
        "available": bool(runtime.get("available", False)),
        "live": bool(runtime.get("live", False)),
        "preview_only": bool(runtime.get("preview_only", False)),
        "provider": str(runtime.get("provider", "disabled")),
        "configured_provider": str(runtime.get("configured_provider", "environment")),
        "source": str(runtime.get("source", "fallback")),
        "from_address": str(runtime.get("from_address", settings.email_from)),
        "sender_map": dict(runtime.get("sender_map") or {}),
        "supports_webhooks": bool(runtime.get("supports_webhooks", False)),
        "resend_api_key_configured": bool(runtime.get("resend_api_key_configured", False)),
        "resend_webhook_secret_configured": bool(runtime.get("resend_webhook_secret_configured", False)),
        "smtp_password_configured": bool(runtime.get("smtp_password_configured", False)),
    }


def has_live_email_delivery() -> bool:
    return bool(get_email_delivery_status()["live"])


def get_resend_webhook_secret() -> str:
    runtime = _get_runtime_email_config()
    return str(runtime.get("resend_webhook_secret") or settings.resend_webhook_secret or os.getenv("RESEND_WEBHOOK_SECRET", ""))


def build_unsubscribe_token(email: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"unsubscribe-{email.strip().lower()}").hex[:16]


def build_unsubscribe_url(email: str) -> str:
    quoted_email = urllib.parse.quote(email.strip().lower())
    token = build_unsubscribe_token(email)
    return f"{settings.frontend_url.rstrip('/')}/newsletter/unsubscribe?email={quoted_email}&token={token}"


def build_email_open_tracking_url(tracking_id: str) -> str:
    return f"{settings.backend_url.rstrip('/')}/email/track/open/{tracking_id}"


def _send_via_resend(
    to: str,
    subject: str,
    html: str,
    *,
    from_address: str,
    api_key: str,
    max_retries: int = 3,
) -> None:
    """Send an email through the Resend API with exponential-backoff retry."""
    import time

    payload = json.dumps({
        "from": from_address,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info("Resend email sent to %s [status %s]", to, resp.status)
                return
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            if exc.code < 500:
                logger.error("Resend API client error %s: %s", exc.code, body)
                raise
            logger.warning(
                "Resend API server error %s on attempt %d/%d: %s",
                exc.code,
                attempt,
                max_retries,
                body,
            )
            last_exc = exc
        except (urllib.error.URLError, OSError) as exc:
            logger.warning(
                "Resend network error on attempt %d/%d: %s",
                attempt,
                max_retries,
                exc,
            )
            last_exc = exc

        if attempt < max_retries:
            time.sleep(2 ** (attempt - 1))

    logger.error("Resend email to %s failed after %d attempts", to, max_retries)
    if last_exc:
        raise last_exc


def _send_via_smtp(to: str, subject: str, html: str, *, from_address: str, transport: dict[str, object]) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(html, subtype="html")

    timeout = max(int(transport.get("smtp_timeout_seconds") or settings.smtp_timeout_seconds), 1)
    smtp_host = _normalize_runtime_text(transport.get("smtp_host") or settings.smtp_host)
    smtp_port = int(transport.get("smtp_port") or settings.smtp_port)
    smtp_username = _normalize_runtime_text(transport.get("smtp_username") or settings.smtp_username or "")
    smtp_password = _normalize_runtime_secret(transport.get("smtp_password") or settings.smtp_password or "")
    smtp_use_tls = bool(
        transport.get("smtp_use_tls") if transport.get("smtp_use_tls") is not None else settings.smtp_use_tls
    )
    smtp_use_ssl = bool(
        transport.get("smtp_use_ssl") if transport.get("smtp_use_ssl") is not None else settings.smtp_use_ssl
    )

    if smtp_use_ssl:
        server: smtplib.SMTP | smtplib.SMTP_SSL
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)

    with server:
        server.ehlo()
        if smtp_use_tls and not smtp_use_ssl:
            server.starttls()
            server.ehlo()
        if smtp_username:
            server.login(smtp_username, smtp_password)
        server.send_message(message)
    logger.info("SMTP email sent to %s", to)


def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    purpose: str = "transactional",
    from_address: str | None = None,
    campaign_recipient_id: int | None = None,
    event_db: Session | None = None,
) -> None:
    """Dispatch an email using the active runtime configuration."""
    from services.email_event_service import is_email_suppressed, record_email_delivery_event

    transport = _get_runtime_email_config()
    resolved_from = from_address or get_email_sender_address(purpose)
    processor = str(transport.get("provider") or "disabled")

    if is_email_suppressed(to):
        logger.warning("Skipping suppressed email delivery to %s", to)
        record_email_delivery_event(
            recipient_email=to,
            processor=processor,
            event_type="suppressed",
            source="application",
            subject=subject,
            purpose=purpose,
            campaign_recipient_id=campaign_recipient_id,
            occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
            payload={"from_address": resolved_from},
            db=event_db,
        )
        return

    if transport.get("provider") == "resend":
        _send_via_resend(
            to,
            subject,
            html,
            from_address=resolved_from,
            api_key=str(transport.get("resend_api_key") or settings.resend_api_key),
        )
    elif transport.get("provider") == "smtp":
        _send_via_smtp(to, subject, html, from_address=resolved_from, transport=transport)
    elif transport.get("provider") == "console":
        logger.warning("Email transport is not configured; using console preview mode for %s", to)
        logger.info(
            "[DEV EMAIL] From: %s | To: %s | Purpose: %s | Subject: %s\n%s",
            resolved_from,
            to,
            purpose,
            subject,
            html,
        )
    else:
        raise EmailDeliveryDisabledError("Email delivery is not configured.")

    record_email_delivery_event(
        recipient_email=to,
        processor=processor,
        event_type="previewed" if transport.get("provider") == "console" else "sent",
        source="application",
        subject=subject,
        purpose=purpose,
        campaign_recipient_id=campaign_recipient_id,
        occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
        payload={"from_address": resolved_from},
        db=event_db,
    )


def send_promotional_email(to: str, subject: str, html: str, tracking_id: str = None) -> None:
    """Send a promotional email with tracking."""
    if tracking_id:
        tracking_pixel = (
            f'<img src="{build_email_open_tracking_url(tracking_id)}" '
            'width="1" height="1" style="display:none;" alt="" />'
        )
        if "</body>" in html.lower():
            html = html.replace("</body>", f"{tracking_pixel}</body>")
        else:
            html = f"{html}\n{tracking_pixel}"

    send_email(to, subject, html, purpose="promotional")


def send_newsletter_welcome_email(to: str, first_name: Optional[str] = None) -> None:
    """Send welcome email to new newsletter subscribers."""
    name = first_name or "there"
    subject = "Welcome to ZOZI Newsletter!"
    html = f"""
<h2>Welcome to ZOZI, {name}!</h2>
<p>Thank you for subscribing to our newsletter. You'll be the first to know about:</p>
<ul>
    <li>New product launches</li>
    <li>Exclusive discounts and offers</li>
    <li>Fashion trends and styling tips</li>
    <li>Behind-the-scenes content</li>
</ul>
<p>Stay stylish,<br>The ZOZI Team</p>
<p><small>If you no longer wish to receive these emails, you can <a href="{build_unsubscribe_url(to)}">unsubscribe here</a>.</small></p>
"""
    send_email(to, subject, html, purpose="promotional")


def send_verification_email(to: str, token: str) -> None:
    """Send email verification to new users."""
    subject = "Verify your ZOZI email address"
    url = f"{settings.frontend_url}/verify-email?token={token}"
    html = f"""
<h2>Verify your ZOZI email address</h2>
<p>Click the link below to verify your account (link expires in 24 hours):</p>
<p><a href="{url}">{url}</a></p>
<p>If you did not create a ZOZI account, you can safely ignore this email.</p>
"""
    send_email(to, subject, html, purpose="verification")


def send_promotional_campaign_email(
    to: str,
    subject: str,
    content: str,
    campaign_name: str,
    tracking_id: str,
    first_name: Optional[str] = None,
    *,
    campaign_recipient_id: int | None = None,
    event_db: Session | None = None,
) -> None:
    """Send a promotional campaign email with full branding and tracking."""
    name = first_name or "Valued Customer"
    unsubscribe_url = build_unsubscribe_url(to)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4;">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="background-color: #1f2937; padding: 30px 40px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold;">ZOZI</h1>
                            <p style="color: #d1d5db; margin: 5px 0 0 0; font-size: 14px;">Fashion & Lifestyle</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="color: #1f2937; margin: 0 0 20px 0; font-size: 24px;">Hi {name},</h2>

                            {content}

                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{settings.frontend_url}/products" style="background-color: #32CD32; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Shop Now</a>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px 40px; border-top: 1px solid #e5e7eb;">
                            <p style="color: #6b7280; font-size: 14px; margin: 0 0 15px 0; text-align: center;">
                                Stay stylish with ZOZI
                            </p>
                            <p style="color: #9ca3af; font-size: 12px; margin: 0; text-align: center;">
                                You're receiving this email because you subscribed to our newsletter.<br>
                                <a href="{unsubscribe_url}" style="color: #6b7280;">Unsubscribe</a> | <a href="{settings.frontend_url}/profile" style="color: #6b7280;">Update Preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>

                <p style="color: #9ca3af; font-size: 11px; margin: 20px 0 0 0; text-align: center;">
                    ZOZI Marketplace | {settings.frontend_url}
                </p>
            </td>
        </tr>
    </table>

    <img src="{build_email_open_tracking_url(tracking_id)}" width="1" height="1" style="display:none;" alt="" />
</body>
</html>
"""
    send_email(
        to,
        subject,
        html,
        purpose="promotional",
        campaign_recipient_id=campaign_recipient_id,
        event_db=event_db,
    )


def send_password_reset_email(to: str, token: str) -> None:
    url = f"{settings.frontend_url}/reset-password?token={token}"
    html = f"""
<h2>Reset your ZOZI password</h2>
<p>Click the link below to reset your password (link expires in 1 hour):</p>
<p><a href="{url}">{url}</a></p>
<p>If you did not request a password reset, you can safely ignore this email.</p>
"""
    send_email(to, "Reset your ZOZI password", html, purpose="password_reset")


def send_login_otp_email(to: str, otp_code: str, expires_minutes: int = 10) -> None:
    """Send a one-time login verification code to the user."""
    html = f"""
<h2>Your ZOZI login verification code</h2>
<p>Use the code below to complete your sign-in (expires in {expires_minutes} minutes):</p>
<div style="text-align:center;margin:24px 0;">
  <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1f2937;background:#f3f4f6;padding:12px 24px;border-radius:8px;display:inline-block;">{otp_code}</span>
</div>
<p>If you did not request this code, you can safely ignore this email. Someone may have mistyped their email address.</p>
"""
    send_email(to, "Your ZOZI login verification code", html, purpose="login_verification")

