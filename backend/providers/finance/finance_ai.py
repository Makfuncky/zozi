"""
Finance AI Provider
==================
AI analysis for finance tasks including email parsing, bill extraction, and reconciliation.
Test file: backend/tests/_test_provider/test_finance_ai.py
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class settings:
    finance_ai_timeout = 60
    finance_text_model = "gpt-4o-mini"
    finance_vision_model = "gpt-4o-mini"

logger = logging.getLogger(__name__)


@dataclass
class FinanceAIResult:
    """Result from a finance AI operation."""

    success: bool
    operation: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    error: Optional[str] = None
    raw_text: Optional[str] = None


def parse_email_to_ledger(email_text: str) -> FinanceAIResult:
    """Parse an email body into ledger entries.

    Extracts transaction details from email text including:
    - Date
    - Amount
    - Description
    - Category
    - Payment method

    Args:
        email_text: Raw email body text.

    Returns:
        FinanceAIResult with parsed ledger data.
    """
    import re

    result: Dict[str, Any] = {
        "entries": [],
        "currency": "USD",
    }

    lines = email_text.split("\n")

    amount_patterns = [
        r"\b(?:amount|total|charge|debit|credit)[:\s]*\$?([\d,]+\.?\d*)",
        r"\$([\d,]+\.?\d*)",
    ]

    date_patterns = [
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b",
        r"\b(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b",
    ]

    entry = {}
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if entry:
                result["entries"].append(entry)
                entry = {}
            continue

        for pattern in amount_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    entry["amount"] = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
                break

        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                entry["date"] = match.group(1)
                break

        if "amount" not in entry and line_stripped:
            entry["description"] = entry.get("description", "") + " " + line_stripped

    if entry:
        result["entries"].append(entry)

    confidence = min(1.0, len(result["entries"]) * 0.3 + 0.1)

    return FinanceAIResult(
        success=len(result["entries"]) > 0,
        operation="parse_email_to_ledger",
        data=result,
        confidence=round(confidence, 2),
    )


def extract_bill_fields(image_bytes: bytes) -> FinanceAIResult:
    """Extract bill fields from an image using OCR.

    Args:
        image_bytes: Raw image bytes of a bill.

    Returns:
        FinanceAIResult with extracted bill fields.
    """
    try:
        from .ocr import parse_bill_text
        bill_data = parse_bill_text(image_bytes)

        return FinanceAIResult(
            success=True,
            operation="extract_bill_fields",
            data={
                "vendor": bill_data.get("vendor", ""),
                "date": bill_data.get("date", ""),
                "total": bill_data.get("total", 0.0),
                "tax": bill_data.get("tax", 0.0),
                "items": bill_data.get("items", []),
                "payment_method": bill_data.get("payment_method", ""),
            },
            confidence=0.7,
            raw_text=bill_data.get("raw_text", ""),
        )
    except Exception as exc:
        logger.error("extract_bill_fields failed: %s", exc)
        return FinanceAIResult(
            success=False,
            operation="extract_bill_fields",
            error=str(exc),
        )


def suggest_reconciliation_match(
    transaction: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> FinanceAIResult:
    """Suggest the best reconciliation match for a transaction.

    Args:
        transaction: The transaction to match.
        candidates: List of candidate ledger entries.

    Returns:
        FinanceAIResult with the best match and confidence score.
    """
    if not candidates:
        return FinanceAIResult(
            success=False,
            operation="suggest_reconciliation_match",
            error="No candidates provided",
        )

    best_match = None
    best_score = 0.0

    txn_amount = transaction.get("amount", 0)
    txn_desc = transaction.get("description", "").lower()

    for candidate in candidates:
        score = 0.0

        cand_amount = candidate.get("amount", 0)
        if abs(cand_amount - txn_amount) < 0.01:
            score += 0.5
        elif txn_amount > 0 and cand_amount > 0:
            ratio = min(txn_amount, cand_amount) / max(txn_amount, cand_amount)
            if ratio > 0.95:
                score += 0.4

        cand_desc = candidate.get("description", "").lower()
        if txn_desc and cand_desc:
            common_words = set(txn_desc.split()) & set(cand_desc.split())
            if common_words:
                score += min(0.3, len(common_words) * 0.1)

        if score > best_score:
            best_score = score
            best_match = candidate

    return FinanceAIResult(
        success=best_match is not None,
        operation="suggest_reconciliation_match",
        data={
            "best_match": best_match,
            "confidence": round(best_score, 2),
            "candidates_evaluated": len(candidates),
        },
        confidence=round(best_score, 2),
    )