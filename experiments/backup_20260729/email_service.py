"""
Email service for ZOZI.

• If RESEND_API_KEY is set → sends real email via Resend REST API.
• Otherwise → logs the email content to console (dev/test mode).
"""

from __future__ import annotations

import logging
import urllib.request
import urllib.error
import json
from config import settings

logger = logging.getLogger(__name__)


def _send_via_resend(to: str, subject: str, html: str) -> None:
    """Send an email through the Resend API (no extra dependencies needed)."""
    payload = json.dumps({
        "from": settings.email_from,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Resend email sent to %s [status %s]", to, resp.status)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        logger.error("Resend API error %s: %s", exc.code, body)
        raise


def send_email(to: str, subject: str, html: str) -> None:
    """Dispatch an email, falling back to console-log in dev if no API key."""
    if settings.resend_api_key:
        _send_via_resend(to, subject, html)
    else:
        logger.info(
            "[DEV EMAIL] To: %s | Subject: %s\n%s",
            to, subject, html,
        )


# ── Pre-built message builders ────────────────────────────────────────────────

def send_verification_email(to: str, token: str) -> None:
    url = f"{settings.frontend_url}/verify-email?token={token}"
    html = f"""
<h2>Verify your ZOZI email address</h2>
<p>Click the link below to verify your account (link expires in 24 hours):</p>
<p><a href="{url}">{url}</a></p>
<p>If you did not create a ZOZI account, you can safely ignore this email.</p>
"""
    send_email(to, "Verify your ZOZI email address", html)


def send_password_reset_email(to: str, token: str) -> None:
    url = f"{settings.frontend_url}/reset-password?token={token}"
    html = f"""
<h2>Reset your ZOZI password</h2>
<p>Click the link below to reset your password (link expires in 1 hour):</p>
<p><a href="{url}">{url}</a></p>
<p>If you did not request a password reset, you can safely ignore this email.</p>
"""
    send_email(to, "Reset your ZOZI password", html)

