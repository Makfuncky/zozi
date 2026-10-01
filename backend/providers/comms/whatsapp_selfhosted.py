"""100% Free WhatsApp Provider — WhatsApp Web Automation.

No paid APIs. Uses WhatsApp Web via Playwright with:
- Persistent session (scan QR only once)
- Anti-detection measures (real user agent, human-like delays)
- Message queue with rate limiting (avoids bans)

Cost: FREE — just need a phone number with WhatsApp.

Setup:
1. pip install playwright
2. playwright install chromium
3. First run: scan QR code (session saved for reuse)
4. Subsequent runs: auto-login via saved session

Configuration:
- WHATSAPP_MODE=dev|web
- WHATSAPP_SESSION_PATH=./whatsapp_session
- WHATSAPP_RATE_LIMIT=20 (messages per minute max)
"""

from __future__ import annotations

import logging
import os
import time
import urllib.parse
from collections import deque

logger = logging.getLogger(__name__)

# Always available — no external SDK needed
HAS_WHATSAPP = True

# Mode from environment
WHATSAPP_MODE = os.getenv("WHATSAPP_MODE", "dev").lower()

# Session persistence
WHATSAPP_SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session")

# Rate limiting (WhatsApp bans for spam)
WHATSAPP_RATE_LIMIT = int(os.getenv("WHATSAPP_RATE_LIMIT", "20"))  # per minute
WHATSAPP_MIN_DELAY = float(os.getenv("WHATSAPP_MIN_DELAY", "3"))  # seconds between messages

# Rate tracking
_message_timestamps: deque = deque(maxlen=WHATSAPP_RATE_LIMIT)


def _check_rate_limit() -> bool:
    """Check if within rate limits. Returns True if can send."""
    now = time.time()
    while _message_timestamps and now - _message_timestamps[0] > 60:
        _message_timestamps.popleft()
    if len(_message_timestamps) >= WHATSAPP_RATE_LIMIT:
        return False
    _message_timestamps.append(now)
    return True


def _normalize_phone(number: str) -> str:
    """Normalize phone to digits only (no + prefix)."""
    return "".join(c for c in (number or "") if c.isdigit())


def _send_whatsapp_web(to: str, message: str) -> dict:
    """Send WhatsApp message via WhatsApp Web with persistent session.

    This is 100% free — uses WhatsApp Web automation.
    Requires a phone number with WhatsApp installed.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("[WHATSAPP] playwright not installed. Install: pip install playwright && playwright install chromium")
        return {"delivered": False, "channel": "whatsapp", "preview": True, "to": to}

    phone = _normalize_phone(to)
    if not phone:
        logger.error("[WHATSAPP] Invalid phone: %s", to)
        return {"delivered": False, "channel": "whatsapp", "error": "invalid_number", "to": to}

    # Enforce minimum delay between messages
    time.sleep(WHATSAPP_MIN_DELAY)

    # URL-encode the message for the click-to-chat URL
    encoded_msg = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"

    try:
        with sync_playwright() as p:
            # Use real browser profile to avoid detection
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # Create context with saved session (if exists)
            context_args = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1280, "height": 720},
                "locale": "en-US",
            }

            session_file = WHATSAPP_SESSION_PATH
            if os.path.exists(session_file):
                context_args["storage_state"] = session_file

            context = browser.new_context(**context_args)
            page = context.new_page()

            # Navigate to WhatsApp Web
            page.goto(url)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Wait for chat to load (multiple selector fallbacks)
            chat_loaded = False
            selectors = [
                '[data-testid="conversation-compose-box-input"]',
                '[data-testid="chat-input"]',
                'div[contenteditable="true"][data-tab="10"]',
                'div[contenteditable="true"]',
                'div[title="Type a message"]',
            ]

            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    chat_loaded = True
                    break
                except Exception:
                    continue

            if not chat_loaded:
                # Save session for next time (first run needs QR scan)
                os.makedirs(os.path.dirname(session_file) if os.path.dirname(session_file) else ".", exist_ok=True)
                context.storage_state(path=session_file)
                browser.close()

                if not os.path.exists(session_file):
                    logger.warning("[WHATSAPP] First run — scan QR code at %s", session_file)
                else:
                    logger.warning("[WHATSAPP] Chat not loaded — session may have expired")
                return {"delivered": False, "channel": "whatsapp", "preview": True, "to": phone}

            # Human-like typing delay
            time.sleep(1)

            # Find input and type message
            input_selector = None
            for selector in selectors:
                if page.query_selector(selector):
                    input_selector = selector
                    break

            if input_selector:
                # Click to focus
                page.click(input_selector)
                time.sleep(0.5)

                # Clear and type
                page.press(input_selector, "Control+a")
                time.sleep(0.2)
                page.fill(input_selector, message)
                time.sleep(0.5)

                # Send
                page.press(input_selector, "Enter")
                time.sleep(2)

                # Save session
                context.storage_state(path=session_file)
                browser.close()

                logger.info("[WHATSAPP] Sent to %s", phone)
                return {"delivered": True, "channel": "whatsapp", "to": phone}
            else:
                context.storage_state(path=session_file)
                browser.close()
                return {"delivered": False, "channel": "whatsapp", "error": "input_not_found", "to": phone}

    except Exception as exc:
        logger.error("[WHATSAPP] Send failed: %s", exc)
        return {"delivered": False, "channel": "whatsapp", "error": str(exc), "to": phone}


def send_whatsapp_message(
    to: str,
    body: str,
    *,
    preview: bool = False,
) -> dict:
    """Send a WhatsApp message. Behavior depends on WHATSAPP_MODE env var.

    This is 100% free — no paid APIs.
    """
    if preview or WHATSAPP_MODE == "dev":
        logger.info("[DEV WHATSAPP] To: %s\n%s", to, body)
        return {"delivered": False, "channel": "whatsapp", "preview": True, "to": to}
    elif WHATSAPP_MODE == "web":
        if not _check_rate_limit():
            logger.warning("[WHATSAPP] Rate limit exceeded (%d/min)", WHATSAPP_RATE_LIMIT)
            return {"delivered": False, "channel": "whatsapp", "error": "rate_limit_exceeded", "to": to}
        return _send_whatsapp_web(to, body)
    else:
        logger.warning("[WHATSAPP] Unknown mode '%s'", WHATSAPP_MODE)
        return {"delivered": False, "channel": "whatsapp", "preview": True, "to": to}


__all__ = [
    "HAS_WHATSAPP",
    "WHATSAPP_MODE",
    "send_whatsapp_message",
]
