from __future__ import annotations

"""
OCR Provider
============
Bill/receipt OCR and CSV statement parsing.
Test file: backend/tests/_test_provider/test_ocr.py
"""
import io
import logging
from typing import Dict, Any, Optional


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


np = _LazyNumpy()
Image = _LazyPIL()


class settings:
    ollama_text_model = "gpt-4o-mini"
    ollama_base_url = "http://localhost:11434"
    ocr_timeout = 30

logger = logging.getLogger(__name__)


def _image_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def _bytes_to_image(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGBA")


def _extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using OCR-ready preprocessing."""
    img = _bytes_to_image(image_bytes)
    img_array = np.array(img)

    if img_array.shape[2] == 4:
        rgb = img_array[:, :, :3]
    else:
        rgb = img_array

    gray = None
    try:
        import cv2
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    except Exception:
        gray = np.array(Image.fromarray(rgb).convert("L"))

    if gray is not None:
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=10) if 'cv2' in dir() else gray
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) if 'cv2' in dir() else (None, enhanced)
        return _ocr_read(binary)

    return _ocr_read(gray)


def _ocr_read(image_array: np.ndarray) -> str:
    """Attempt OCR on a preprocessed image array."""
    try:
        import pytesseract
        img = Image.fromarray(image_array)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not installed, OCR unavailable")
        return ""
    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        return ""


def parse_bill_text(image_bytes: bytes) -> Dict[str, Any]:
    """Parse bill/receipt text from an image.

    Args:
        image_bytes: Raw image bytes of a bill or receipt.

    Returns:
        Dict with extracted fields: vendor, date, total, items, taxes, payment_method.
    """
    text = _extract_text_from_image(image_bytes)
    return _parse_bill_text_from_string(text)


def parse_statement_csv(csv_bytes: bytes) -> Dict[str, Any]:
    """Parse a financial statement CSV.

    Args:
        csv_bytes: Raw bytes of a CSV file.

    Returns:
        Dict with parsed statement data: rows, total, columns, summary.
    """
    import csv
    import io as io_module

    text = csv_bytes.decode("utf-8", errors="replace")
    reader = csv.reader(io_module.StringIO(text))
    rows = list(reader)

    if not rows:
        return {"rows": [], "total": 0, "columns": [], "summary": {}}

    columns = rows[0]
    data_rows = rows[1:]

    total = 0.0
    summary = {"row_count": len(data_rows), "columns": columns}

    for row in data_rows:
        for cell in row:
            cell_clean = cell.replace(",", "").replace("$", "").strip()
            try:
                val = float(cell_clean)
                total += val
                break
            except ValueError:
                continue

    return {
        "rows": data_rows,
        "total": round(total, 2),
        "columns": columns,
        "summary": summary,
    }


def _parse_bill_text_from_string(text: str) -> Dict[str, Any]:
    """Extract structured fields from bill text."""
    import re

    result: Dict[str, Any] = {
        "vendor": "",
        "date": "",
        "total": 0.0,
        "subtotal": 0.0,
        "tax": 0.0,
        "items": [],
        "payment_method": "",
        "raw_text": text,
    }

    lines = text.split("\n")
    if lines:
        result["vendor"] = lines[0].strip()

    date_patterns = [
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b",
        r"\b(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b",
    ]
    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                result["date"] = match.group(1)
                break
        if result["date"]:
            break

    total_patterns = [
        r"(?:total|amount due|balance due|grand total)[:\s]*\$?([\d,]+\.?\d*)",
        r"total[:\s]*\$?([\d,]+\.?\d*)",
    ]
    for line in lines:
        for pattern in total_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    result["total"] = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
                break
        if result["total"]:
            break

    tax_patterns = [
        r"(?:tax|vat|gst)[:\s]*\$?([\d,]+\.?\d*)",
    ]
    for line in lines:
        for pattern in tax_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    result["tax"] = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
                break

    payment_patterns = [
        r"(?:paid|payment|method)(?:\s+with\s+)?\s*(cash|card|credit|debit|visa|mastercard|amex|bank transfer|online)",
    ]
    for line in lines:
        for pattern in payment_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                result["payment_method"] = match.group(1)
                break
        if result["payment_method"]:
            break

    return result