"""Shipping label helper for the logistics domain.

Wraps the shipping, QR, and barcode providers into a single high-level
``create_shipment_label`` operation. Lives in the services layer so the
``features`` module remains a pure feature-atom catalog.
"""
from __future__ import annotations

from providers.barcode.barcode_generator import generate_code128
from providers.qr.qr_generator import generate_tracking_qr
from providers.shipping.shipping_calculator import (
    calculate_shipping_rate,
    compare_shipping_options,
    estimate_delivery_days,
    get_available_carriers,
)


def create_shipment_label(shipment_data: dict, destination: dict):
    """Generate a shipping label with QR + barcode using shipping/QR/barcode providers."""
    origin = {"country": shipment_data["origin_country"], "city": shipment_data["origin_city"]}
    package = {
        "weight_kg": shipment_data["weight_kg"],
        "length_cm": shipment_data.get("length_cm", 30),
        "width_cm": shipment_data.get("width_cm", 20),
        "height_cm": shipment_data.get("height_cm", 10),
    }
    try:
        rate = calculate_shipping_rate(origin, destination, package)
    except Exception as exc:
        rate = {"error": str(exc)}
    try:
        qr_code = generate_tracking_qr(shipment_data["tracking_number"])
    except Exception as exc:
        qr_code = None
    try:
        barcode = generate_code128(shipment_data["tracking_number"])
    except Exception as exc:
        barcode = None
    return {"rate": rate, "qr_code": qr_code, "barcode": barcode}


__all__ = [
    "create_shipment_label",
    "calculate_shipping_rate",
    "compare_shipping_options",
    "estimate_delivery_days",
    "get_available_carriers",
    "generate_tracking_qr",
    "generate_code128",
]
