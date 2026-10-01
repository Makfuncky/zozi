from __future__ import annotations

"""
QR/Barcode Scanner Provider
============================
Wraps `pyzbar` and `PIL` for decoding QR codes and barcodes from images.
Supports multiple codes per image and returns type information.
"""
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from pyzbar.pyzbar import decode as _pyzbar_decode
    from pyzbar.pyzbar import ZBarSymbol

    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False
    _pyzbar_decode = None
    ZBarSymbol = None

try:
    from PIL import Image as PILImage

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    PILImage = None

HAS_SCANNER = HAS_PYZBAR and HAS_PIL


def _require_scanner() -> None:
    if not HAS_PIL:
        raise RuntimeError("Pillow is not installed. Install with: pip install Pillow")
    if not HAS_PYZBAR:
        raise RuntimeError("pyzbar is not installed. Install with: pip install pyzbar")


def _load_image(image_bytes: bytes):
    if not HAS_PIL:
        raise RuntimeError("Pillow is not installed. Install with: pip install Pillow")
    try:
        return PILImage.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Cannot decode image: {e}") from e


def scan_qr(image_bytes: bytes) -> List[str]:
    _require_scanner()
    img = _load_image(image_bytes)

    symbols = [ZBarSymbol.QRCODE] if ZBarSymbol else None
    results = _pyzbar_decode(img, symbols=symbols) if symbols else _pyzbar_decode(img)

    decoded: List[str] = []
    for result in results:
        if result.type == "QRCODE":
            try:
                decoded.append(result.data.decode("utf-8"))
            except UnicodeDecodeError:
                decoded.append(result.data.decode("latin-1", errors="replace"))
    return decoded


def scan_barcode(image_bytes: bytes) -> List[Dict[str, Any]]:
    _require_scanner()
    img = _load_image(image_bytes)

    barcode_symbols = [
        ZBarSymbol.EAN13,
        ZBarSymbol.EAN8,
        ZBarSymbol.UPCA,
        ZBarSymbol.UPCE,
        ZBarSymbol.CODE128,
        ZBarSymbol.CODE39,
        ZBarSymbol.CODE93,
        ZBarSymbol.CODABAR,
        ZBarSymbol.I25,
        ZBarSymbol.DATABAR,
        ZBarSymbol.DATABAR_EXP,
    ] if ZBarSymbol else None

    results = _pyzbar_decode(img, symbols=barcode_symbols) if barcode_symbols else _pyzbar_decode(img)

    decoded: List[Dict[str, Any]] = []
    for result in results:
        if result.type == "QRCODE":
            continue
        try:
            data = result.data.decode("utf-8")
        except UnicodeDecodeError:
            data = result.data.decode("latin-1", errors="replace")

        rect = result.rect
        decoded.append({
            "data": data,
            "type": result.type,
            "rect": {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width,
                "height": rect.height,
            },
        })
    return decoded


def scan_image(image_bytes: bytes) -> Dict[str, List]:
    _require_scanner()
    img = _load_image(image_bytes)

    results = _pyzbar_decode(img)

    qr_codes: List[str] = []
    barcodes: List[Dict[str, Any]] = []

    for result in results:
        try:
            data = result.data.decode("utf-8")
        except UnicodeDecodeError:
            data = result.data.decode("latin-1", errors="replace")

        if result.type == "QRCODE":
            qr_codes.append(data)
        else:
            rect = result.rect
            barcodes.append({
                "data": data,
                "type": result.type,
                "rect": {
                    "left": rect.left,
                    "top": rect.top,
                    "width": rect.width,
                    "height": rect.height,
                },
            })

    return {"qr_codes": qr_codes, "barcodes": barcodes}


__all__ = [
    "HAS_SCANNER",
    "HAS_PYZBAR",
    "HAS_PIL",
    "scan_qr",
    "scan_barcode",
    "scan_image",
]
