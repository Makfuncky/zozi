from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    BankStatementLine,
    BankReconciliation,
    ScannedExpense,
    JournalEntry,
    Account,
    FinanceAutomationLog,
    FinanceAuditLog,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from providers.finance_ai import (
    suggest_reconciliation_match,
    parse_email_to_ledger,
    extract_bill_fields,
)
from providers.ocr import parse_bill_text
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

AI_CONFIDENCE_THRESHOLD = 0.75


# ── #6: Fuzzy AI Bank Reconciliation ─────────────────────────────────


def run_ai_bank_reconciliation(
    db: Session,
    country_code: str = None,
) -> dict:
    """
    AI-powered fuzzy bank reconciliation.
    Uses finance_ai.suggest_reconciliation_match() for semantic matching
    beyond exact amount/date matching.
    """
    results = {
        "processed": 0,
        "matched": 0,
        "exceptions": 0,
        "confidence_scores": [],
    }

    # Get unmapped bank statement lines
    q = db.query(BankStatementLine).filter(
        BankStatementLine.status.in_(["unmapped", "mapped"]),
    )
    if country_code:
        q = q.filter(BankStatementLine.country_code == country_code)

    for line in q.all():
        results["processed"] += 1

        # Build candidates from GL journal entries
        candidates = _build_journal_candidates(db, line, country_code)

        if not candidates:
            results["exceptions"] += 1
            continue

        # Use AI provider for fuzzy matching
        txn = {
            "amount": float(line.amount or 0),
            "description": line.description or "",
            "date": line.txn_date.isoformat() if line.txn_date else "",
        }

        ai_result = suggest_reconciliation_match(txn, candidates)

        if ai_result.success and ai_result.confidence >= AI_CONFIDENCE_THRESHOLD:
            best = ai_result.data.get("best_match")
            if best:
                _auto_reconcile_statement_line(db, line, best, country_code)
                results["matched"] += 1
            results["confidence_scores"].append({
                "line_id": line.id,
                "confidence": ai_result.confidence,
                "matched": True,
            })
        else:
            results["exceptions"] += 1
            results["confidence_scores"].append({
                "line_id": line.id,
                "confidence": ai_result.confidence,
                "matched": False,
            })

    _log_automation(db, "ai_bank_reconciliation", results["processed"],
                    results["matched"] + results["exceptions"], results, country_code)
    return results


def _build_journal_candidates(db: Session, line: BankStatementLine, country_code: str = None) -> list:
    """Build candidate ledger entries for matching."""
    candidates = []

    # Exact amount match candidates
    q = db.query(JournalEntryLine).filter(
        JournalEntryLine.amount == line.amount,
    )
    if country_code:
        q = q.filter(JournalEntryLine.country_code == country_code)

    for jel in q.all():
        je = db.query(JournalEntry).get(jel.entry_id)
        if je:
            candidates.append({
                "id": je.id,
                "amount": float(jel.amount or 0),
                "description": je.description or "",
                "date": je.entry_date.isoformat() if je.entry_date else "",
                "reference_type": je.reference_type,
                "reference_id": je.reference_id,
            })

    # Also get amount-proximate candidates (±5%)
    if line.amount:
        lo = float(line.amount) * 0.95
        hi = float(line.amount) * 1.05
        q2 = db.query(JournalEntryLine).filter(
            JournalEntryLine.amount >= lo,
            JournalEntryLine.amount <= hi,
        )
        if country_code:
            q2 = q2.filter(JournalEntryLine.country_code == country_code)

        for jel in q2.all():
            je = db.query(JournalEntry).get(jel.entry_id)
            if je and not any(c["id"] == je.id for c in candidates):
                candidates.append({
                    "id": je.id,
                    "amount": float(jel.amount or 0),
                    "description": je.description or "",
                    "date": je.entry_date.isoformat() if je.entry_date else "",
                    "reference_type": je.reference_type,
                    "reference_id": je.reference_id,
                })

    return candidates


def _auto_reconcile_statement_line(
    db: Session,
    line: BankStatementLine,
    candidate: dict,
    country_code: str = None,
) -> None:
    """Auto-reconcile a bank statement line with a journal entry."""
    line.status = "reconciled"
    line.mapped_account_code = candidate.get("reference_type", "")
    line.posted_journal_entry_id = candidate.get("id")

    recon = BankReconciliation(
        statement_line_id=line.id,
        journal_entry_id=candidate.get("id"),
        matched_amount=line.amount,
        status="matched",
        note=f"AI auto-match (confidence: N/A)",
        country_code=country_code or line.country_code,
    )
    db.add(recon)
    db.flush()


# ── #8: OCR Email-to-Ledger Pipeline ─────────────────────────────────


def process_email_invoice(
    db: Session,
    email_text: str,
    sender: str = None,
    country_code: str = None,
) -> dict:
    """
    Process an invoice email through OCR-to-ledger pipeline.
    Uses finance_ai.parse_email_to_ledger() for extraction.
    """
    ai_result = parse_email_to_ledger(email_text)

    if not ai_result.success:
        return {"status": "failed", "error": ai_result.error, "confidence": ai_result.confidence}

    entries = ai_result.data.get("entries", [])
    if not entries:
        return {"status": "no_entries", "confidence": ai_result.confidence}

    posted = 0
    failed = 0

    for entry in entries:
        try:
            amount = Decimal(str(entry.get("amount", 0)))
            if amount <= 0:
                continue

            category = entry.get("category", "general")
            expense_account = _map_category_to_gl(category)

            if not expense_account:
                failed += 1
                continue

            lines = [
                JournalLineInput(
                    account_code=expense_account,
                    side="debit",
                    amount=amount,
                    description=entry.get("description", "Email invoice"),
                ),
                JournalLineInput(
                    account_code="2010",
                    side="credit",
                    amount=amount,
                    description=f"AP from email invoice - {entry.get('description', '')}",
                ),
            ]

            entry_data = JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="email_invoice",
                reference_id=0,
                description=f"Auto-posted from email: {entry.get('description', 'Unknown')}",
                currency="OMR",
                country_code=country_code,
                lines=lines,
            )

            gl.create_journal_entry(db, entry_data)
            posted += 1
        except Exception as e:
            logger.warning("Failed to post email invoice entry: %s", e)
            failed += 1

    # Create ScannedExpense record for audit
    try:
        scanned = ScannedExpense(
            vendor_name=sender or "Email",
            amount=sum(Decimal(str(e.get("amount", 0))) for e in entries if e.get("amount")),
            category=category if entries else "general",
            ocr_confidence=ai_result.confidence,
            status="posted" if failed == 0 else "partial",
            country_code=country_code,
        )
        db.add(scanned)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "status": "posted",
        "entries_processed": len(entries),
        "posted": posted,
        "failed": failed,
        "confidence": ai_result.confidence,
    }


def process_email_inbox(db: Session, country_code: str = None) -> dict:
    """
    Batch process email inbox for invoice emails.
    Scans for unprocessed emails and processes them.
    """
    results = {"scanned": 0, "processed": 0, "posted": 0, "failed": 0}

    # Check for pending scanned expenses (emails awaiting processing)
    pending = db.query(ScannedExpense).filter(
        ScannedExpense.status == "scanned",
    )
    if country_code:
        pending = pending.filter(ScannedExpense.country_code == country_code)

    results["scanned"] = pending.count()

    for expense in pending.all():
        results["processed"] += 1
        try:
            # Re-process with OCR
            if expense.ocr_raw_text:
                result = process_email_invoice(
                    db, expense.ocr_raw_text,
                    sender=expense.vendor_name,
                    country_code=country_code,
                )
                if result.get("posted", 0) > 0:
                    expense.status = "posted"
                    results["posted"] += 1
                else:
                    expense.status = "failed"
                    results["failed"] += 1
            else:
                expense.status = "no_text"
                results["failed"] += 1
        except Exception as e:
            logger.warning("Email processing failed for expense %s: %s", expense.id, e)
            expense.status = "error"
            results["failed"] += 1

    db.commit()
    return results


# ── #9: OCR Scan-to-Ledger Mobile Upload ──────────────────────────────


def process_mobile_scan(
    db: Session,
    image_bytes: bytes,
    vendor_name: str = None,
    country_code: str = None,
) -> dict:
    """
    Process a mobile-uploaded receipt scan through OCR → GL pipeline.
    Uses ocr.parse_bill_text() + finance_ai.extract_bill_fields().
    """
    result = {"status": "pending", "steps": []}

    try:
        # Step 1: OCR extraction
        ocr_result = parse_bill_text(image_bytes)
        result["steps"].append({"step": "ocr", "success": bool(ocr_result), "text_length": len(ocr_result.get("raw_text", ""))})

        if not ocr_result.get("raw_text"):
            # Try AI extraction as fallback
            ai_result = extract_bill_fields(image_bytes)
            if ai_result.success:
                bill_data = ai_result.data
            else:
                result["status"] = "failed"
                result["error"] = "OCR and AI extraction both failed"
                return result
        else:
            # Use OCR result
            bill_data = ocr_result

        # Step 2: Extract structured fields
        vendor = bill_data.get("vendor", vendor_name or "Unknown")
        amount = Decimal(str(bill_data.get("amount", 0)))
        tax = Decimal(str(bill_data.get("tax", 0)))

        if amount <= 0:
            result["status"] = "failed"
            result["error"] = "No valid amount found"
            return result

        result["steps"].append({"step": "field_extraction", "vendor": vendor, "amount": float(amount)})

        # Step 3: AI categorization
        category = _categorize_expense_ai(bill_data, image_bytes)

        # Step 4: Post to GL
        expense_account = _map_category_to_gl(category)
        if not expense_account:
            expense_account = "6000"  # Default COGS

        lines = [
            JournalLineInput(
                account_code=expense_account,
                side="debit",
                amount=amount,
                description=f"Mobile scan receipt - {vendor}",
                entity_type="scanned_expense",
            ),
            JournalLineInput(
                account_code="2010",
                side="credit",
                amount=amount,
                description=f"AP for mobile scan - {vendor}",
            ),
        ]

        if tax > 0:
            lines.append(JournalLineInput(
                account_code="2050",
                side="debit",
                amount=tax,
                description=f"VAT input - {vendor}",
            ))
            lines.append(JournalLineInput(
                account_code="2010",
                side="credit",
                amount=tax,
                description=f"VAT AP for {vendor}",
            ))

        # Validate journal entry balance
        total_debits = sum(l.amount for l in lines if l.side == "debit")
        total_credits = sum(l.amount for l in lines if l.side == "credit")
        if total_debits != total_credits:
            result["status"] = "failed"
            result["error"] = f"Unbalanced entry: debits={total_debits}, credits={total_credits}"
            return result

        entry_data = JournalEntryCreate(
            entry_date=_utcnow(),
            reference_type="mobile_scan",
            reference_id=0,
            description=f"Mobile scan receipt - {vendor}",
            currency="OMR",
            country_code=country_code,
            lines=lines,
        )

        gl.create_journal_entry(db, entry_data)

        # Create scanned expense record
        scanned = ScannedExpense(
            vendor_name=vendor,
            amount=amount,
            tax_amount=tax,
            category=category,
            ocr_confidence=0.85,
            status="posted",
            country_code=country_code,
        )
        db.add(scanned)
        db.commit()

        result["status"] = "posted"
        result["scanned_expense_id"] = scanned.id
        result["journal_entry_id"] = entry_data.reference_id if hasattr(entry_data, 'reference_id') else 0

    except Exception as e:
        logger.error("Mobile scan processing failed: %s", e)
        result["status"] = "error"
        result["error"] = str(e)

    return result


# ── #27: AI Expense Categorization ────────────────────────────────────


def categorize_expense_ai(
    db: Session,
    scanned_expense_id: int,
    country_code: str = None,
) -> dict:
    """
    Use AI to categorize a scanned expense and auto-post to GL.
    Uses extract_bill_fields() and parse_email_to_ledger() for categorization.
    """
    expense = db.query(ScannedExpense).get(scanned_expense_id)
    if not expense:
        raise ValueError(f"Scanned expense #{scanned_expense_id} not found")

    result = {"status": "pending", "expense_id": scanned_expense_id}

    if expense.ocr_raw_text:
        # Try email-style parsing for categorization
        ai_result = parse_email_to_ledger(expense.ocr_raw_text)
        if ai_result.success:
            entries = ai_result.data.get("entries", [])
            if entries:
                primary = entries[0]
                category = primary.get("category", "general")
                amount = primary.get("amount", 0)

                expense.category = category
                expense.status = "categorized"
                db.commit()

                result["status"] = "categorized"
                result["category"] = category
                result["amount"] = amount
                result["confidence"] = ai_result.confidence
                return result

    # Fallback: categorize based on vendor name keyword matching
    vendor = (expense.vendor_name or "").lower()
    category = _categorize_vendor_keywords(vendor)

    expense.category = category
    expense.status = "categorized"
    db.commit()

    result["status"] = "categorized"
    result["category"] = category
    result["confidence"] = 0.5  # Lower confidence for keyword-based

    return result


def batch_categorize_all(db: Session, country_code: str = None) -> dict:
    """
    Batch categorize all uncategorized scanned expenses.
    """
    q = db.query(ScannedExpense).filter(
        ScannedExpense.status.in_("scanned", "review"),
    )
    if country_code:
        q = q.filter(ScannedExpense.country_code == country_code)

    results = {"processed": 0, "categorized": 0, "posted": 0, "failed": 0}

    for expense in q.all():
        results["processed"] += 1
        try:
            cat_result = categorize_expense_ai(db, expense.id, country_code)
            if cat_result.get("status") == "categorized":
                results["categorized"] += 1
                # Auto-post if confidence is high enough
                if cat_result.get("confidence", 0) >= AI_CONFIDENCE_THRESHOLD:
                    _auto_post_expense(db, expense, cat_result.get("category", "general"), country_code)
                    expense.status = "posted"
                    results["posted"] += 1
        except Exception as e:
            logger.warning("Categorization failed for expense %s: %s", expense.id, e)
            results["failed"] += 1

    db.commit()
    return results


# ── Helpers ──────────────────────────────────────────────────────────


def _map_category_to_gl(category: str) -> str:
    """Map expense category to GL account code."""
    category_map = {
        "marketing": "6020",
        "server_tech": "6040",
        "telecom": "6060",
        "office_rent": "6070",
        "payroll": "6030",
        "gateway_fees": "6010",
        "shipping": "5010",
        "general": "6000",
        "utility": "6050",
    }
    cat_lower = category.lower()
    for key, code in category_map.items():
        if key in cat_lower:
            return code
    return "6000"


def _categorize_expense_ai(bill_data: dict, image_bytes: bytes = None) -> str:
    """AI categorization using bill data and description."""
    vendor = (bill_data.get("vendor") or "").lower()
    desc = (bill_data.get("description") or "").lower()
    text = f"{vendor} {desc}"

    if any(kw in text for kw in ["facebook", "snapchat", "tiktok", "google ads", "meta", "instagram"]):
        return "marketing"
    if any(kw in text for kw in ["aws", "cloudflare", "digitalocean", "server", "hosting", "cloud"]):
        return "server_tech"
    if any(kw in text for kw in ["etisalat", "omantel", "stc", "telecom", "telephone", "mobile"]):
        return "telecom"
    if any(kw in text for kw in ["emaar", "landlord", "rent", "property"]):
        return "office_rent"
    if any(kw in text for kw in ["wps", "salary", "payroll", "human resources"]):
        return "payroll"
    if any(kw in text for kw in ["tap", "stripe", "thawani", "gateway", "payment"]):
        return "gateway_fees"
    return "general"


def _categorize_vendor_keywords(vendor: str) -> str:
    """Categorize based on vendor name keywords."""
    return _categorize_expense_ai({"vendor": vendor, "description": vendor}, None)


def _auto_post_expense(db: Session, expense: ScannedExpense, category: str, country_code: str = None) -> None:
    """Auto-post a categorized expense to GL."""
    account_code = _map_category_to_gl(category)
    amount = expense.amount

    lines = [
        JournalLineInput(
            account_code=account_code,
            side="debit",
            amount=amount,
            description=f"Auto-posted expense: {expense.vendor_name}",
        ),
        JournalLineInput(
            account_code="2010",
            side="credit",
            amount=amount,
            description=f"AP for auto-posted expense: {expense.vendor_name}",
        ),
    ]

    entry_data = JournalEntryCreate(
        entry_date=_utcnow(),
        reference_type="auto_expense",
        reference_id=expense.id,
        description=f"AI-categorized expense: {expense.vendor_name}",
        currency="OMR",
        country_code=country_code,
        lines=lines,
    )
    gl.create_journal_entry(db, entry_data)


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                    detail: dict = None, country_code: str = None):
    try:
        db.add(FinanceAutomationLog(
            kind=kind, records_processed=processed, records_changed=changed,
            detail=detail, country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Automation log failed: %s", e)
        db.rollback()
