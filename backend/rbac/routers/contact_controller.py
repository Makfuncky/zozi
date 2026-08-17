"""Contact form submission endpoint (decorated, auto-router).

Faithful replacement for the hand-written routers/contact.py. Business logic
(strip + required-field check + email send) is kept inline; the route contract
is declared with core.route_contract so the auto-router emits
routers/public_security_contact.py.
"""

from __future__ import annotations

from core.route_contract import post
from infrastructure.utils.email_service import send_email

@post("/contact", deps=["user"], status_code=200, tags=["contact"])
def submit_contact_form(
    name: str = "",
    email: str = "",
    subject: str = "",
    message: str = "",
    current_user=None,
) -> dict:
    name = name.strip()
    email = email.strip()
    subject = subject.strip()
    message = message.strip()

    if not all([name, email, subject, message]):
        return {"detail": "All fields are required"}

    try:
        html_body = f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
        """
        send_email(
            to="support@zozi.com",
            subject=f"Contact Form: {subject}",
            html=html_body,
        )
    except Exception:
        pass

    return {"detail": "Message received"}
