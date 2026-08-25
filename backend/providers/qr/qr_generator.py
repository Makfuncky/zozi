from __future__ import annotations

"""
QR Code Generation Provider
===========================
Wraps the `qrcode` library for generating QR codes as PNG bytes.
Provides product, payment, and tracking QR generation utilities.
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    qrcode = None

_ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L if HAS_QRCODE else None,
    "M": ERROR_CORRECT_M if HAS_QRCODE else None,
    "Q": ERROR_CORRECT_Q if HAS_QRCODE else None,
    "H": ERROR_CORRECT_H if HAS_QRCODE else None,
}


def _get_error_correction(level: str = "M"):
    level = level.upper()
    if level not in _ERROR_CORRECTION_LEVELS:
        raise ValueError(
            f"Invalid error correction level '{level}'. Use one of: L, M, Q, H"
        )
    return _ERROR_CORRECTION_LEVELS[level]


def generate_qr(
    data: str,
    *,
    size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> bytes:
    """Generate a QR code as PNG bytes.

    Args:
        data: The string to encode.
        size: Module size (pixels per module). Default 10.
        border: Border width in modules. Default 4.
        error_correction: Error correction level (L, M, Q, H). Default "M".
        fill_color: Foreground color. Default "black".
        back_color: Background color. Default "white".

    Returns:
        PNG-encoded bytes of the QR code image.

    Raises:
        RuntimeError: If the qrcode library is not installed.
        ValueError: If data is empty or error_correction is invalid.
    """
    if not HAS_QRCODE:
        raise RuntimeError("qrcode library is not installed. Install with: pip install qrcode[pil]")
    if not data:
        raise ValueError("data must be a non-empty string")

    qr = qrcode.QRCode(
        version=None,
        error_correction=_get_error_correction(error_correction),
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


def generate_product_qr(product_id: int, base_url: str) -> bytes:
    """Generate a QR code linking to a product page.

    Args:
        product_id: The product's unique identifier.
        base_url: The base URL of the store (e.g. "https://zozi.com").

    Returns:
        PNG-encoded bytes of the QR code image.
    """
    url = base_url.rstrip("/") + f"/products/{product_id}"
    return generate_qr(url, error_correction="M")


def generate_payment_qr(amount: float, currency: str, order_id: str) -> bytes:
    """Generate a QR code for payment with embedded amount and order info.

    Args:
        amount: The payment amount.
        currency: Currency code (e.g. "USD", "OMR").
        order_id: The order identifier.

    Returns:
        PNG-encoded bytes of the QR code image.
    """
    data = f"payment://{order_id}?amount={amount:.2f}&currency={currency.upper()}"
    return generate_qr(data, error_correction="H", size=12)


def generate_tracking_qr(tracking_number: str) -> bytes:
    """Generate a QR code for order tracking.

    Args:
        tracking_number: The tracking/shipment number.

    Returns:
        PNG-encoded bytes of the QR code image.
    """
    data = f"tracking://{tracking_number}"
    return generate_qr(data, error_correction="M")


__all__ = [
    "HAS_QRCODE",
    "generate_qr",
    "generate_product_qr",
    "generate_payment_qr",
    "generate_tracking_qr",
]
