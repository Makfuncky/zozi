"""
Dedicated notification delivery worker.

Runs as a standalone process that polls for pending notification jobs and
delivers them.  This keeps notification delivery off the API hot path.

Start with::

    python -m settings.notification_worker

Environment variables
---------------------
NOTIFICATION_WORKER_POLL_INTERVAL : int
    Seconds between polls for pending notifications (default 3).
NOTIFICATION_WORKER_IDLE_SHUTDOWN : int
    Seconds of idle time before the worker exits (default 0 = never).
"""
from __future__ import annotations

import logging
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("notification_worker")

POLL_INTERVAL = int(os.getenv("NOTIFICATION_WORKER_POLL_INTERVAL", "3"))
IDLE_SHUTDOWN = int(os.getenv("NOTIFICATION_WORKER_IDLE_SHUTDOWN", "0"))


def _deliver_notification(notification_id: int) -> dict:
    from db.database import SessionLocal
    from models.communication import Notification as NotificationModel
    from models import User

    db = SessionLocal()
    try:
        notification = db.query(NotificationModel).filter(
            NotificationModel.id == notification_id,
            NotificationModel.status == "pending",
        ).first()
        if not notification:
            return {"status": "skipped", "reason": "not_found_or_already_processed"}

        user = db.query(User).filter(User.id == notification.user_id).first()
        if not user:
            db.query(NotificationModel).filter(
                NotificationModel.id == notification_id
            ).update({"status": "failed"})
            db.commit()
            return {"status": "failed", "reason": "user_not_found"}

        channel = notification.channel
        if channel == "email" and user.email:
            from utils.email_service import send_email, get_email_sender_address
            from_addr = get_email_sender_address("notification")
            send_email(
                to=user.email,
                subject=notification.title,
                html=f"<p>{notification.message}</p>",
                purpose="notification",
                from_address=from_addr,
            )
        elif channel == "push":
            logger.info("Push delivery for notification %s (user %s) — push not yet wired", notification_id, user.id)
        elif channel == "sms":
            logger.info("SMS delivery for notification %s (user %s) — SMS not yet wired", notification_id, user.id)

        db.query(NotificationModel).filter(
            NotificationModel.id == notification_id
        ).update({"status": "delivered"})
        db.commit()
        return {"status": "delivered", "notification_id": notification_id}
    except Exception as exc:
        logger.error("Failed to deliver notification %s: %s", notification_id, exc)
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()


def _poll_once() -> int:
    from db.database import SessionLocal
    from models.communication import Notification as NotificationModel

    db = SessionLocal()
    try:
        pending = db.query(NotificationModel).filter(
            NotificationModel.status == "pending"
        ).order_by(NotificationModel.created_at.asc()).limit(20).all()

        for notif in pending:
            logger.info("Processing pending notification %s (channel=%s)", notif.id, notif.channel)
            _deliver_notification(notif.id)

        return len(pending)
    finally:
        db.close()


def main():
    logger.info(
        "Notification worker starting — poll_interval=%ds idle_shutdown=%ds",
        POLL_INTERVAL,
        IDLE_SHUTDOWN,
    )

    idle_seconds = 0
    while True:
        try:
            count = _poll_once()
            if count > 0:
                idle_seconds = 0
                logger.info("Processed %d pending notifications", count)
            else:
                idle_seconds += POLL_INTERVAL
                if IDLE_SHUTDOWN > 0 and idle_seconds >= IDLE_SHUTDOWN:
                    logger.info("Idle shutdown triggered after %ds", idle_seconds)
                    break

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Notification worker shutting down (SIGINT)")
            break
        except Exception:
            logger.error("Notification worker error:\n%s", traceback.format_exc())
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()