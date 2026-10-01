"""Email provider — transport implementations for ZOZI.

Vendor/protocol code (SMTP ``smtplib``, Resend HTTP API, console preview) is
encapsulated here so the email *service* layer (`infrastructure.utils.email_service`) and the
comms services stay free of third-party transport details. The service layer is
responsible for config resolution, suppression and event recording, then calls
:func:`deliver_email` with the already-resolved transport descriptor.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from email.message import EmailMessage
from typing import Any, Optional

logger = logging.getLogger(__name__)

HAS_EMAIL = True


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
    payload = json.dumps({
        "from": from_address,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()

    last_exc: Optional[Exception] = None
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
                exc.code, attempt, max_retries, body,
            )
            last_exc = exc
        except (urllib.error.URLError, OSError) as exc:
            logger.warning("Resend network error on attempt %d/%d: %s", attempt, max_retries, exc)
            last_exc = exc

        if attempt < max_retries:
            time.sleep(2 ** (attempt - 1))

    logger.error("Resend email to %s failed after %d attempts", to, max_retries)
    if last_exc:
        raise last_exc


def _send_via_smtp(
    to: str,
    subject: str,
    html: str,
    *,
    from_address: str,
    transport: dict[str, Any],
    smtp_host: str,
    smtp_port: int,
    smtp_username: str = "",
    smtp_password: str = "",
    smtp_use_tls: bool = False,
    smtp_use_ssl: bool = False,
    smtp_timeout_seconds: int = 30,
) -> None:
    """Send an email through an SMTP server."""
    import smtplib

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(html, subtype="html")

    timeout = max(int(smtp_timeout_seconds), 1)

    server: smtplib.SMTP
    if smtp_use_ssl:
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


def deliver_email(
    to: str,
    subject: str,
    html: str,
    *,
    from_address: str,
    provider: str,
    config: Optional[dict[str, Any]] = None,
) -> None:
    """Dispatch a fully-rendered email via the resolved provider.

    ``config`` is the resolved transport descriptor produced by the email
    service layer (env or DB). Provider-specific values are read defensively
    so a partial config never crashes the caller.
    """
    config = config or {}
    provider = (provider or "disabled").strip().lower()

    if provider == "resend":
        _send_via_resend(
            to,
            subject,
            html,
            from_address=from_address,
            api_key=str(config.get("resend_api_key") or ""),
        )
    elif provider == "smtp":
        _send_via_smtp(
            to,
            subject,
            html,
            from_address=from_address,
            transport=config,
            smtp_host=str(config.get("smtp_host") or ""),
            smtp_port=int(config.get("smtp_port") or 587),
            smtp_username=str(config.get("smtp_username") or ""),
            smtp_password=str(config.get("smtp_password") or ""),
            smtp_use_tls=bool(config.get("smtp_use_tls")),
            smtp_use_ssl=bool(config.get("smtp_use_ssl")),
            smtp_timeout_seconds=int(config.get("smtp_timeout_seconds") or 30),
        )
    elif provider == "console":
        logger.warning("Email transport is not configured; using console preview mode for %s", to)
        logger.info(
            "[DEV EMAIL] From: %s | To: %s | Subject: %s\n%s",
            from_address, to, subject, html,
        )
    else:
        raise RuntimeError("Email delivery is not configured.")


__all__ = ["deliver_email"]

