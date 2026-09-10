from __future__ import annotations

"""
Finance AI domain service.

Pure business logic for parsing financial documents (emails, ledger entries)
and suggesting reconciliation matches. Lives in the domain layer per
ARCHITECTURE_DIAGRAM.md (domains/finance/services/) rather than providers/,
because providers must only wrap external SDKs.
"""
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal  # Law 19: Decimal in money paths
from typing import Any, Dict, List, Optional

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


__all__ = [
    "FinanceAIResult",
    "parse_email_to_ledger",
    "suggest_reconciliation_match",
    "extract_bill_fields",
]


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

    entry: Dict[str, Any] = {}
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
                    entry["amount"] = str(Decimal(match.group(1).replace(",", "")))  # Law 19: Decimal only
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

    best_match: Optional[Dict[str, Any]] = None
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


def extract_bill_fields(image_bytes: bytes) -> FinanceAIResult:
    """Extract bill fields from an image via the OCR provider.

    Calls the ``providers.ai.finance_ai.extract_bill_fields`` SDK wrapper
    and adapts the result into a ``FinanceAIResult`` envelope. Domains
    call this function rather than the provider directly so the
    envelope shape stays consistent.

    Args:
        image_bytes: Raw image bytes of a bill.

    Returns:
        FinanceAIResult with extracted bill fields.
    """
    from providers.ai.finance_ai import extract_bill_fields as _provider_call

    bill_data = _provider_call(image_bytes)
    if "error" in bill_data and "vendor" not in bill_data:
        return FinanceAIResult(
            success=False,
            operation="extract_bill_fields",
            error=str(bill_data.get("error")),
        )

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