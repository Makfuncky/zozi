"""Celery tasks for email sending."""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.email_tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
    template_name: Optional[str] = None,
    template_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Send an email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content (optional)
        from_email: Sender email (defaults to configured)
        template_name: Template name (for logging)
        template_data: Template variables (for logging)
        
    Returns:
        Send result
    """
    try:
        from infrastructure.utils.email_service import send_email
        
        send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email=from_email,
        )
        
        return {
            "status": "completed",
            "to_email": to_email,
            "subject": subject,
            "template": template_name,
        }
        
    except Exception as exc:
        logger.exception("Email send task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.email_tasks.send_bulk_email",
    max_retries=2,
    default_retry_delay=120,
)
def send_bulk_email_task(
    self,
    recipients: list[str],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
    batch_size: int = 50,
) -> dict[str, Any]:
    """
    Send bulk emails in batches.
    
    Args:
        recipients: List of recipient emails
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content
        from_email: Sender email
        batch_size: Number of emails per batch
        
    Returns:
        Send results
    """
    try:
        from infrastructure.utils.email_service import send_email
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            for email in batch:
                try:
                    send_email(
                        to_email=email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        from_email=from_email,
                    )
                    results["sent"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({"email": email, "error": str(e)})
                    
        return {
            "status": "completed",
            "total": len(recipients),
            **results,
        }
        
    except Exception as exc:
        logger.exception("Bulk email task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.email_tasks.send_password_reset",
    max_retries=3,
    default_retry_delay=60,
)
def send_password_reset_task(
    self,
    email: str,
    reset_token: str,
    frontend_url: str,
) -> dict[str, Any]:
    """Send password reset email."""
    try:
        from infrastructure.utils.email_service import send_password_reset_email
        
        send_password_reset_email(
            email=email,
            reset_token=reset_token,
            frontend_url=frontend_url,
        )
        
        return {"status": "completed", "email": email}
        
    except Exception as exc:
        logger.exception("Password reset email task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.email_tasks.send_verification_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_verification_email_task(
    self,
    email: str,
    verification_token: str,
    frontend_url: str,
) -> dict[str, Any]:
    """Send email verification email."""
    try:
        from infrastructure.utils.email_service import send_verification_email
        
        send_verification_email(
            email=email,
            verification_token=verification_token,
            frontend_url=frontend_url,
        )
        
        return {"status": "completed", "email": email}
        
    except Exception as exc:
        logger.exception("Verification email task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="tasks.email_tasks.health_check")
def health_check() -> dict[str, str]:
    """Health check for email task workers."""
    return {"status": "healthy", "worker": "email_tasks"}
