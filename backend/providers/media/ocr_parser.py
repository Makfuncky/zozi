"""Local bill/OCR text parser.

No external OCR API is used. We extract structured fields (vendor, amount, VAT,
date, invoice number) from either:
  * pasted plain-text captured from a bill image (e.g. via the browser's OCR or a
    copy-paste of the printed text), or
  * the original filename / EXIF metadata of an uploaded image.

This keeps the "scan bill -> expense" automation functional offline while still
producing a confident, reviewable result. The UI shows the extracted values for
the admin to confirm before posting.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)


_AMOUNT_RE = re.compile(r"(?:(?:OMR|USD|AED|SAR|QAR|KWD|BHD|EUR|GBP)\s*)?([0-9][0-9,]*\.?[0-9]{0,2})", re.IGNORECASE)
_VAT_RE = re.compile(r"(?:vat|tax|t\.?a\.?x)\s*[:\-]?\s*([0-9][0-9,]*\.?[0-9]{0,2})", re.IGNORECASE)
_DATE_RE = re.compile(r"(?:\b(?:date|issued|dated)\b[:\-]?\s*)?(\d{1,4}[/\-.\s](?:\d{1,2}[/\-.\s])?\d{1,4})", re.IGNORECASE)
_INVOICE_RE = re.compile(r"(?:inv|invoice|bill|receipt)[#\s:.\-]*([A-Za-z0-9\-/]+)", re.IGNORECASE)
_VENDOR_HINTS = ("ltd", "llc", "co.", "company", "supplies", "trading", "store", "market", "group", "tech", "food", "cafe", "restaurant")


def _clean_money(token: str) -> Optional[Decimal]:
    try:
        return Decimal(token.replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _parse_date(token: str) -> Optional[str]:
    for fmt in ("%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(token.replace(" ", "/"), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_bill_text(raw_text: str, filename: Optional[str] = None) -> dict:
    """Extract fields from raw bill text (and optional filename).

    Returns a dict with keys: vendor_name, amount, tax_amount, expense_date,
    invoice_number, confidence (0-1), raw_text.
    """
    text = (raw_text or "").strip()
    result = {
        "vendor_name": None,
        "amount": None,
        "tax_amount": None,
        "expense_date": None,
        "invoice_number": None,
        "confidence": 0.0,
        "raw_text": text,
    }
    if not text:
        # Fall back to filename-based hints.
        if filename:
            inv = _INVOICE_RE.search(filename)
            if inv:
                result["invoice_number"] = inv.group(1)
            result["confidence"] = 0.15
        return result

    # Vendor: first non-empty line, or a line containing a vendor hint.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    vendor = None
    for ln in lines[:6]:
        low = ln.lower()
        if any(h in low for h in _VENDOR_HINTS) or (len(ln) <= 60 and not _AMOUNT_RE.search(ln)):
            vendor = ln
            break
    if not vendor and lines:
        vendor = lines[0]
    result["vendor_name"] = vendor

    # Amount: prefer an explicitly labelled "total/amount/grand/due" line.
    # Exclude 4-digit year-like figures (e.g. from a Date line).
    labelled = None
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in ("total", "amount", "grand total", "amount due", "balance due", "sum")):
            m = _AMOUNT_RE.search(ln)
            if m:
                labelled = _clean_money(m.group(1))
                if labelled is not None:
                    break
    amounts = [_clean_money(m) for m in _AMOUNT_RE.findall(text)]
    amounts = [a for a in amounts if a is not None and not (a == a.to_integral_value() and 1900 <= float(a) <= 2999)]
    if labelled is not None:
        result["amount"] = labelled
    elif amounts:
        result["amount"] = max(amounts)

    # VAT: explicit vat/tax line.
    vat_m = _VAT_RE.search(text)
    if vat_m:
        result["tax_amount"] = _clean_money(vat_m.group(1))

    # Date.
    date_m = _DATE_RE.search(text)
    if date_m:
        result["expense_date"] = _parse_date(date_m.group(1))

    # Invoice number.
    inv_m = _INVOICE_RE.search(text)
    if inv_m:
        result["invoice_number"] = inv_m.group(1)

    # Confidence heuristic.
    score = 0
    if result["vendor_name"]:
        score += 0.3
    if result["amount"] is not None:
        score += 0.4
    if result["tax_amount"] is not None or result["expense_date"]:
        score += 0.15
    if result["invoice_number"]:
        score += 0.15
    result["confidence"] = round(min(score, 1.0), 2)
    return result


def parse_statement_csv(raw_csv: str) -> list[dict]:
    """Parse a simple bank-statement CSV into line dicts.

    Accepts common layouts: expects columns for date, description, amount
    (and optionally reference). Tolerant of header variations.
    Returns list of {txn_date, description, reference, amount}.
    """
    import csv
    import io

    lines = list(csv.reader(io.StringIO(raw_csv)))
    if not lines:
        return []
    header = [h.strip().lower() for h in lines[0]]
    # Map common column names -> canonical.
    def col_index(*names: str) -> Optional[int]:
        for n in names:
            for i, h in enumerate(header):
                if n in h:
                    return i
        return None

    di = col_index("date", "txn date", "posting")
    desc_i = col_index("desc", "narrative", "particulars", "details", "memo")
    amt_i = col_index("amount", "value", "debit/credit", "credit", "debit")
    ref_i = col_index("ref", "reference", "cheque", "check")
    has_header = di is not None or desc_i is not None or amt_i is not None
    rows = lines[1:] if has_header else lines

    out = []
    for row in rows:
        if not row or all(not c.strip() for c in row):
            continue
        if di is None or amt_i is None:
            # Fallback: first cell = date, last numeric = amount, middle = desc.
            date_val = row[0] if row else ""
            desc_val = " ".join(row[1:-1]) if len(row) > 2 else (row[1] if len(row) > 1 else "")
            amt_val = row[-1] if row else ""
        else:
            date_val = row[di] if di < len(row) else ""
            desc_val = row[desc_i] if desc_i is not None and desc_i < len(row) else ""
            amt_val = row[amt_i] if amt_i < len(row) else ""
        ref_val = row[ref_i] if ref_i is not None and ref_i < len(row) else None
        amt = _clean_money(str(amt_val).replace("(", "-").replace(")", ""))
        if amt is None:
            continue
        out.append({
            "txn_date": _parse_date(date_val) or date_val,
            "description": desc_val.strip(),
            "reference": ref_val.strip() if ref_val else None,
            "amount": float(amt),
        })
    return out

