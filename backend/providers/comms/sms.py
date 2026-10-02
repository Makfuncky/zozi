"""100% Free SMS Provider — No Paid APIs.

Methods (all free after hardware cost):
- dev: logs messages (no SMS sent, for development)
- gsm: GSM modem with SIM card (AT commands, proper sequencing)
- android: Android phone as SMS gateway (via ADB or HTTP API)

Hardware needed:
- GSM modem (SIM800/SIM900) + SIM card with prepaid plan
- OR old Android phone with SIM card + SMS Gateway app

Configuration:
- SMS_MODE=dev|gsm|android
- SMS_SERIAL_PORT=COM3 (GSM modem)
- SMS_ANDROID_URL=http://192.168.1.x:8080 (Android SMS Gateway)
- SMS_RETRY_ATTEMPTS=3
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

from infrastructure.observability.circuit_breaker import (
    CircuitBreakerError,
    get_circuit_breaker,
)

from providers._helpers import retry_call

logger = logging.getLogger(__name__)

HAS_SMS = True
SMS_MODE = os.getenv("SMS_MODE", "dev").lower()

SMS_SERIAL_PORT = os.getenv("SMS_SERIAL_PORT", "COM3")
SMS_SERIAL_BAUD = int(os.getenv("SMS_SERIAL_BAUD", "9600"))

SMS_ANDROID_URL = os.getenv("SMS_ANDROID_URL", "")

SMS_RETRY_ATTEMPTS = int(os.getenv("SMS_RETRY_ATTEMPTS", "3"))
SMS_RETRY_DELAY = int(os.getenv("SMS_RETRY_DELAY", "2"))

_SMS_BREAKER = get_circuit_breaker("sms", failure_threshold=5, recovery_timeout=30)


def _try_gsm_send_once(phone_number: str, message: str) -> dict:
    """Single GSM send attempt. Returns a result dict or raises on failure."""
    import serial

    # Truncate to single SMS length
    if len(message) > 160:
        message = message[:157] + "..."

    with serial.Serial(SMS_SERIAL_PORT, SMS_SERIAL_BAUD, timeout=10) as ser:
        # Test modem
        ser.write(b'AT\r\n')
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting).decode(errors="ignore")
        if "OK" not in resp:
            raise RuntimeError("modem_not_responding")

        # Set text mode
        ser.write(b'AT+CMGF=1\r\n')
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting).decode(errors="ignore")
        if "OK" not in resp:
            raise RuntimeError("text_mode_failed")

        # Set character set
        ser.write(b'AT+CSCS="GSM"\r\n')
        time.sleep(0.3)

        # Send recipient
        ser.write(f'AT+CMGS="{phone_number}"\r\n'.encode())
        time.sleep(0.5)
        resp = ser.read(ser.in_waiting).decode(errors="ignore")
        if ">" not in resp:
            raise RuntimeError("no_prompt")

        # Send message body + Ctrl+Z
        ser.write(f'{message}\x1a'.encode())
        time.sleep(3)
        resp = ser.read(ser.in_waiting).decode(errors="ignore")

        if "+CMGS:" in resp:
            return {"sent": True, "channel": "sms", "to": phone_number}
        raise RuntimeError(resp.strip() or "send_failed")


def _send_sms_gsm(phone_number: str, message: str) -> dict:
    """Send SMS via GSM modem using AT commands with proper sequencing.

    Hardware: SIM800/SIM900 modem + SIM card (prepaid plan).
    Cost: Only the SIM card prepaid balance (fractions of a fils per SMS).
    """
    try:
        import serial
    except ImportError:
        logger.warning("[SMS GSM] pyserial not installed. Install: pip install pyserial")
        return {"sent": False, "channel": "sms", "preview": True, "to": phone_number}

    try:
        result, _ = retry_call(
            _try_gsm_send_once,
            phone_number,
            message,
            attempts=SMS_RETRY_ATTEMPTS,
            delay=SMS_RETRY_DELAY,
            return_attempt=True,
        )
        return result
    except Exception as exc:
        return {"sent": False, "channel": "sms", "error": str(exc), "to": phone_number}


def _send_sms_android(phone_number: str, message: str) -> dict:
    """Send SMS via Android phone acting as SMS gateway.

    Requirements:
    - Old Android phone with SIM card
    - SMS Gateway app (free on Play Store) or custom HTTP server
    - Phone connected to same network (WiFi)

    Recommended apps (free):
    - "SMS Gateway" by medyannik (Play Store)
    - "Android SMS Gateway" (F-Droid)

    Setup:
    1. Install SMS Gateway app on Android
    2. Start the server (shows URL like http://192.168.1.x:8080)
    3. Set SMS_ANDROID_URL to that URL
    """
    if not SMS_ANDROID_URL:
        logger.warning("[SMS Android] No gateway URL configured. Set SMS_ANDROID_URL env var.")
        return {"sent": False, "channel": "sms", "preview": True, "to": phone_number}

    payload = json.dumps({
        "phone_number": phone_number,
        "message": message,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{SMS_ANDROID_URL}/sms",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                logger.info("[SMS Android] Sent to %s", phone_number)
                return {"sent": True, "channel": "sms", "to": phone_number, "gateway": "android"}
            else:
                logger.warning("[SMS Android] Failed: %s", result.get("error", "unknown"))
                return {"sent": False, "channel": "sms", "error": result.get("error"), "to": phone_number}
    except urllib.error.HTTPError as exc:
        logger.error("[SMS Android] HTTP error %s", exc.code)
        return {"sent": False, "channel": "sms", "error": f"HTTP {exc.code}", "to": phone_number}
    except Exception as exc:
        logger.error("[SMS Android] Failed: %s", exc)
        return {"sent": False, "channel": "sms", "error": str(exc), "to": phone_number}


def send_sms(phone_number: str, message: str, **kwargs) -> dict:
    """Send an SMS. Behavior depends on SMS_MODE env var.

    All methods are 100% free (no per-message API costs).
    """
    if SMS_MODE == "dev":
        logger.info("[DEV SMS] To: %s\n%s", phone_number, message)
        return {"sent": False, "channel": "sms", "preview": True, "to": phone_number}
    if _SMS_BREAKER.state.value == "open":
        logger.warning("SMS circuit breaker open — skipping send to %s", phone_number)
        return {"sent": False, "channel": "sms", "error": "circuit_breaker_open", "to": phone_number}
    elif SMS_MODE == "gsm":
        return _send_sms_gsm(phone_number, message)
    elif SMS_MODE == "android":
        return _send_sms_android(phone_number, message)
    else:
        logger.warning("[SMS] Unknown mode '%s'", SMS_MODE)
        return {"sent": False, "channel": "sms", "preview": True, "to": phone_number}


__all__ = [
    "HAS_SMS",
    "SMS_MODE",
    "send_sms",
]
