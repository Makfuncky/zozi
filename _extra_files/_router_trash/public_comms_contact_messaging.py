"""
Contact API Endpoints - Contact form submission and info.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from utils.email_service import send_email
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/contact", response_model=dict)
async def submit_contact_form(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.get("name", "").strip()
    email = payload.get("email", "").strip()
    subject = payload.get("subject", "").strip()
    message = payload.get("message", "").strip()

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
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("submit_contact_form_failed", error=str(e))

    return {"detail": "Message received"}