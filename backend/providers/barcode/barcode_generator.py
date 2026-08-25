from __future__ import annotations

"""
Barcode Management Provider
============================
Wraps the `python-barcode` library for generating EAN-13, UPC-A, Code128,
and Code39 barcodes as PNG bytes. Includes checksum validation utilities.
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import barcode as barcode_lib
    from barcode.writer import ImageWriter

    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False
    barcode_lib = None
    ImageWriter = None


def _require_barcode() -> None:
    if not HAS_BARCODE:
        raise RuntimeError(
            "python-barcode library is not installed. Install with: pip install python-barcode[pil]"
        )


def _generate_barcode(barcode_class_name: str, data: str, **kwargs) -> bytes:
    _require_barcode()
    if not data:
        raise ValueError("data must be a non-empty string")

    try:
        cls = getattr(barcode_lib, barcode_class_name)
    except AttributeError:
        raise ValueError(f"Unsupported barcode type: {barcode_class_name}")

    writer = ImageWriter()
    for key, value in kwargs.items():
        setattr(writer, key, value)

    code = cls(data, writer=writer)
    buffer = io.BytesIO()
    code.write(buffer, options={"write_text": True, "module_height": 15.0})
    buffer.seek(0)
    return buffer.read()


def generate_ean13(code: str) -> bytes:
    _require_barcode()
    code = code.strip().replace(" ", "").replace("-", "")

    if len(code) == 12:
        code = code + calculate_ean13_check_digit(code)
    elif len(code) == 13:
        if not validate_ean13(code):
            raise ValueError(f"Invalid EAN-13 check digit for code: {code}")
    else:
        raise ValueError(f"EAN-13 code must be 12 or 13 digits, got {len(code)}")

    return _generate_barcode("ean13", code)


def generate_upca(code: str) -> bytes:
    _require_barcode()
    code = code.strip().replace(" ", "").replace("-", "")

    if len(code) == 11:
        code = code + _calculate_upca_check_digit(code)
    elif len(code) == 12:
        if not validate_upca(code):
            raise ValueError(f"Invalid UPC-A check digit for code: {code}")
    else:
        raise ValueError(f"UPC-A code must be 11 or 12 digits, got {len(code)}")

    return _generate_barcode("upca", code)


def generate_code128(data: str) -> bytes:
    return _generate_barcode("code128", data)


def generate_code39(data: str) -> bytes:
    return _generate_barcode("code39", data)


def validate_ean13(code: str) -> bool:
    code = code.strip().replace(" ", "").replace("-", "")
    if len(code) != 13 or not code.isdigit():
        return False
    expected = calculate_ean13_check_digit(code[:12])
    return code[12] == expected


def validate_upca(code: str) -> bool:
    code = code.strip().replace(" ", "").replace("-", "")
    if len(code) != 12 or not code.isdigit():
        return False
    expected = _calculate_upca_check_digit(code[:11])
    return code[11] == expected


def calculate_ean13_check_digit(code: str) -> str:
    code = code.strip().replace(" ", "").replace("-", "")
    if len(code) != 12 or not code.isdigit():
        raise ValueError(f"EAN-13 base code must be 12 digits, got {len(code)}")

    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code))
    remainder = total % 10
    check = (10 - remainder) % 10
    return str(check)


def _calculate_upca_check_digit(code: str) -> str:
    code = code.strip().replace(" ", "").replace("-", "")
    if len(code) != 11 or not code.isdigit():
        raise ValueError(f"UPC-A base code must be 11 digits, got {len(code)}")

    odd_sum = sum(int(code[i]) for i in range(0, 11, 2))
    even_sum = sum(int(code[i]) for i in range(1, 11, 2))
    total = odd_sum * 3 + even_sum
    remainder = total % 10
    check = (10 - remainder) % 10
    return str(check)


__all__ = [
    "HAS_BARCODE",
    "generate_ean13",
    "generate_upca",
    "generate_code128",
    "generate_code39",
    "validate_ean13",
    "validate_upca",
    "calculate_ean13_check_digit",
]
