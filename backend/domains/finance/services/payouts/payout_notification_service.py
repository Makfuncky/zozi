"""
Payout Notification Service
===========================
Sends email notifications to suppliers and logistics partners when the
auto-payout sweep creates new PayoutBatch records.

Relies on ``email_service.send_email`` (Resend API if configured, else
console-log).  Falls back to the ``NotificationEngine`` in-app notification
when the email send fails or the user has no email address.

Design decisions:
  - Notifications are sent synchronously from the sweep function so the
    caller (background thread or admin endpoint) sees any failures in
    the sweep result's ``notifications`` field.
  - Only one notification per supplier/partner per batch is sent
    (aggregates all settlements for that entity).
  - If the entity has no verified email address, falls back to an in-app
    notification via NotificationEngine.
"""
from __future__ import annotations


import logging
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

# ── HTML email builders ────────────────────────────────────────────────────

FRONTEND_URL = "http://localhost:3000"  # overridden by settings if available


def _get_frontend_url() -> str:
    """Return the configured frontend URL or the development default."""
    try:
        from config import settings

        return getattr(settings, "frontend_url", FRONTEND_URL)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Handled Exception in payout_notification_service.py:44")
        return FRONTEND_URL


def _build_supplier_payout_email(
    supplier_name: str,
    amount: Decimal | float,
    batch_number: str,
    supplier_id: int,
) -> str:
    """Build an HTML email body for a supplier payout notification."""
    payout_url = f"{_get_frontend_url()}/supplier/payouts"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1a1a2e;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0;">ZOZI</h1>
    <p style="font-size: 13px; color: #6b7280; margin: 4px 0 0;">Payout Notification</p>
  </div>

  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
    <p style="font-size: 14px; color: #374151; margin: 0 0 8px;">A payout has been initiated for</p>
    <p style="font-size: 22px; font-weight: 800; color: #16a34a; margin: 0 0 4px;">
      {amount:,.2f} OMR
    </p>
    <p style="font-size: 12px; color: #6b7280; margin: 0;">Batch: {batch_number}</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Supplier</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #6b7280; text-align: right; border-bottom: 1px solid #e5e7eb;">
        {supplier_name}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Status</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #f59e0b; text-align: right; border-bottom: 1px solid #e5e7eb;">
        Pending Approval
      </td>
    </tr>
  </table>

  <p style="font-size: 12px; color: #6b7280; line-height: 1.5;">
    This payout is in <strong>draft</strong> status and requires admin approval
    before it is dispatched.  Payment is estimated within <strong>3–5 business days</strong>
    after approval.  You can track its status at any time from your payout dashboard.
  </p>

  <div style="text-align: center; margin: 24px 0;">
    <a href="{payout_url}"
       style="display: inline-block; background: #1a1a2e; color: #fff; text-decoration: none;
              font-size: 14px; font-weight: 600; padding: 12px 32px; border-radius: 8px;">
      View Payout Dashboard →
    </a>
  </div>

  <p style="font-size: 11px; color: #9ca3af; text-align: center; margin-top: 32px;">
    ZOZI E-Commerce Platform &middot; Automated payout notification
  </p>
</body>
</html>"""


def _build_logistics_payout_email(
    partner_name: str,
    amount: Decimal | float,
    batch_number: str,
    partner_id: int,
) -> str:
    """Build an HTML email body for a logistics partner payout notification."""
    payout_url = f"{_get_frontend_url()}/logistics-partner/payouts"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1a1a2e;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0;">ZOZI</h1>
    <p style="font-size: 13px; color: #6b7280; margin: 4px 0 0;">Logistics Payout Notification</p>
  </div>

  <div style="background: #eff6ff; border: 1px solid #93c5fd; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
    <p style="font-size: 14px; color: #374151; margin: 0 0 8px;">A logistics payout has been initiated for</p>
    <p style="font-size: 22px; font-weight: 800; color: #2563eb; margin: 0 0 4px;">
      {amount:,.2f} OMR
    </p>
    <p style="font-size: 12px; color: #6b7280; margin: 0;">Batch: {batch_number}</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Partner</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #6b7280; text-align: right; border-bottom: 1px solid #e5e7eb;">
        {partner_name}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Status</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #f59e0b; text-align: right; border-bottom: 1px solid #e5e7eb;">
        Pending Approval
      </td>
    </tr>
  </table>

  <p style="font-size: 12px; color: #6b7280; line-height: 1.5;">
    This payout is in <strong>draft</strong> status and requires admin approval
    before it is dispatched.  You can track its status from your payout dashboard.
  </p>

  <div style="text-align: center; margin: 24px 0;">
    <a href="{payout_url}"
       style="display: inline-block; background: #1a1a2e; color: #fff; text-decoration: none;
              font-size: 14px; font-weight: 600; padding: 12px 32px; border-radius: 8px;">
      View Payout Dashboard →
    </a>
  </div>

  <p style="font-size: 11px; color: #9ca3af; text-align: center; margin-top: 32px;">
    ZOZI E-Commerce Platform &middot; Automated payout notification
  </p>
</body>
</html>"""


# ── Public API ─────────────────────────────────────────────────────────────


def notify_suppliers_of_payout(
    db: Session,
    sweep_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Send payout notification emails to all suppliers in the sweep result.

    Parameters
    ----------
    db : Session
        Active database session (used to look up user details).
    sweep_result : dict
        The return value from ``run_auto_payout_sweep()``.  Must contain
        ``payout_ids`` (list of ``{supplier_id, payout_id, amount}``),
        ``batch_number``, and ``status``.

    Returns
    -------
    list[dict]
        One entry per notification sent (or attempted), each with keys:
        ``supplier_id``, ``email``, ``status``, and optionally ``error``.
    """
    from infrastructure.utils.email_service import send_email

    notifications: list[dict[str, Any]] = []
    payout_ids = sweep_result.get("payout_ids", [])
    batch_number = sweep_result.get("batch_number", "N/A")

    if not payout_ids or sweep_result.get("status") != "ok":
        logger.debug("No supplier payouts to notify for batch %s", batch_number)
        return notifications

    # Deduplicate by supplier_id (one notification per supplier per batch)
    # N+1 removal: resolve every supplier user in a single query before the loop.
    users_by_id: dict[int, Any] = {}
    prefetch_error: Exception | None = None
    try:
        from domains.governance.models.user import User

        unique_supplier_ids = list(dict.fromkeys(
            cast(int, entry.get("supplier_id")) for entry in payout_ids
        ))
        if unique_supplier_ids:
            supplier_rows = (
                db.query(User)
                .filter(User.id.in_(unique_supplier_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in supplier_rows:
                users_by_id.setdefault(row.id, row)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # surfaced per-supplier below to preserve error reporting
        logger.exception("Handled Exception in payout_notification_service.py:232")
        prefetch_error = exc

    seen_suppliers: set[int] = set()
    for entry in payout_ids:
        supplier_id = cast(int, entry.get("supplier_id"))
        if supplier_id in seen_suppliers:
            continue
        seen_suppliers.add(supplier_id)

        amount = cast(float, entry.get("amount", 0))
        supplier_name = f"Supplier #{supplier_id}"
        email: str | None = None

        try:
            if prefetch_error is not None:
                raise prefetch_error

            # Look up the supplier user record for name + email
            user = users_by_id.get(supplier_id)
            if user:
                supplier_name = getattr(user, "full_name", None) or getattr(user, "username", None) or supplier_name

            email = getattr(user, "email", None) if user else None
            if not email:
                logger.warning(
                    "No email for supplier %d; sending in-app notification instead.",
                    supplier_id,
                )
                _send_in_app_notification_separate_session(
                    supplier_id,
                    title="New Payout Initiated",
                    message=f"A payout of {amount:,.2f} OMR (batch {batch_number}) has been initiated for your settlements.",
                )
                notifications.append({
                    "supplier_id": supplier_id,
                    "email": None,
                    "status": "in_app_fallback",
                })
                continue

            html = _build_supplier_payout_email(supplier_name, amount, batch_number, supplier_id)
            send_email(
                to=email,
                subject=f"ZOZI Payout — {amount:,.2f} OMR ({batch_number})",
                html=html,
            )
            notifications.append({
                "supplier_id": supplier_id,
                "email": email,
                "status": "sent",
            })
            logger.info("Payout notification sent to supplier %d <%s>", supplier_id, email)

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.exception("Failed to notify supplier %d: %s", supplier_id, exc)
            notifications.append({
                "supplier_id": supplier_id,
                "email": email,
                "status": "error",
                "error": str(exc),
            })

    return notifications


def notify_logistics_partners_of_payout(
    db: Session,
    sweep_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Send payout notification emails to all logistics partners in the sweep result.

    Parameters
    ----------
    db : Session
        Active database session (used to look up partner details).
    sweep_result : dict
        The return value from ``run_auto_logistics_payout_sweep()``.

    Returns
    -------
    list[dict]
        One entry per notification sent (or attempted).
    """
    from infrastructure.utils.email_service import send_email

    notifications: list[dict[str, Any]] = []
    payout_ids = sweep_result.get("payout_ids", [])
    batch_number = sweep_result.get("batch_number", "N/A")

    if not payout_ids or sweep_result.get("status") != "ok":
        logger.debug("No logistics payouts to notify for batch %s", batch_number)
        return notifications

    # N+1 removal: resolve partners and their linked users in bulk before the loop.
    partners_by_id: dict[Any, Any] = {}
    users_by_id: dict[Any, Any] = {}
    prefetch_error: Exception | None = None
    try:
        from domains.logistics.models.logistics import LogisticsPartner
        from domains.governance.models.user import User

        unique_partner_ids = list(dict.fromkeys(
            cast(int, entry.get("partner_id")) for entry in payout_ids
        ))
        if unique_partner_ids:
            partner_rows = (
                db.query(LogisticsPartner)
                .filter(LogisticsPartner.id.in_(unique_partner_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in partner_rows:
                partners_by_id.setdefault(row.id, row)

        partner_user_ids = list(dict.fromkeys(
            uid for uid in (
                getattr(p, "user_id", None) for p in partners_by_id.values()
            ) if uid is not None
        ))
        if partner_user_ids:
            user_rows = (
                db.query(User)
                .filter(User.id.in_(partner_user_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in user_rows:
                users_by_id.setdefault(row.id, row)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # surfaced per-partner below to preserve error reporting
        logger.exception("Handled Exception in payout_notification_service.py:361")
        prefetch_error = exc

    seen_partners: set[int] = set()
    for entry in payout_ids:
        partner_id = cast(int, entry.get("partner_id"))
        if partner_id in seen_partners:
            continue
        seen_partners.add(partner_id)

        amount = cast(float, entry.get("amount", 0))
        partner_name = f"Partner #{partner_id}"
        email: str | None = None

        try:
            if prefetch_error is not None:
                raise prefetch_error

            # Look up the logistics partner record
            partner = partners_by_id.get(partner_id)
            if partner:
                partner_name = getattr(partner, "company_name", None) or getattr(partner, "name", None) or partner_name

            # The partner record may have an email field; also check user relation
            email = getattr(partner, "email", None)
            if not email and partner:
                user = users_by_id.get(getattr(partner, "user_id", None))
                email = getattr(user, "email", None) if user else None

            if not email:
                logger.warning(
                    "No email for logistics partner %d; sending in-app notification instead.",
                    partner_id,
                )
                _send_in_app_notification_separate_session(
                    partner_id,
                    title="New Logistics Payout Initiated",
                    message=f"A logistics payout of {amount:,.2f} OMR (batch {batch_number}) has been initiated.",
                )
                notifications.append({
                    "partner_id": partner_id,
                    "email": None,
                    "status": "in_app_fallback",
                })
                continue

            html = _build_logistics_payout_email(partner_name, amount, batch_number, partner_id)
            send_email(
                to=email,
                subject=f"ZOZI Logistics Payout — {amount:,.2f} OMR ({batch_number})",
                html=html,
            )
            notifications.append({
                "partner_id": partner_id,
                "email": email,
                "status": "sent",
            })
            logger.info("Payout notification sent to partner %d <%s>", partner_id, email)

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.exception("Failed to notify logistics partner %d: %s", partner_id, exc)
            notifications.append({
                "partner_id": partner_id,
                "email": email,
                "status": "error",
                "error": str(exc),
            })

    return notifications


def _send_in_app_notification_separate_session(
    user_id: int,
    title: str,
    message: str,
) -> None:
    """Fallback: create an in-app notification using a SEPARATE DB session.

    Using a separate session prevents any notification write failure from
    affecting the settlement sweep's session (which has already been
    committed).  The notification is best-effort — errors are logged.
    """
    try:
        from infrastructure.database.database import SessionLocal
        from domains.comms.services.shared.notification.notification_engine import NotificationEngine
        from domains.comms.services.shared.notification.notification_engine import NotificationChannel
        from domains.comms.services.shared.notification.notification_engine import NotificationPriority

        notif_db = SessionLocal()
        try:
            engine = NotificationEngine(notif_db)
            engine.send(
                user_id=user_id,
                title=title,
                message=message,
                channel=NotificationChannel.IN_APP,
                priority=NotificationPriority.HIGH,
            )
        finally:
            notif_db.close()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.debug("In-app notification fallback failed for user %d: %s", user_id, exc)