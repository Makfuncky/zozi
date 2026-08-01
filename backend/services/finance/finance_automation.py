"""Finance Automation Service.

Implements the ERP-level automation requested for the admin Finance module:
  * Bill scanning (OCR) -> expense record -> GL posting
  * Configurable bank-statement line -> GL account mapping
  * Auto bank reconciliation driven by mapping rules
  * Fixed-asset depreciation runs
  * Accrual / reversal engine

All GL writes go through `general_ledger_service.create_journal_entry` so the
immutable, double-entry ledger and audit trail remain the single source of truth.
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    Account, ScannedExpense, BankMappingRule,
    BankStatementImport, BankStatementLine, FixedAsset, Accrual,
    FinanceAutomationLog, JournalEntry,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from utils.money import round_money
from utils.audit_log import AuditAction, audit_log

logger = logging.getLogger(__name__)


# ── OCR / bill scanning ────────────────────────────────────────────────────────


def post_scanned_expense(
    db: Session,
    *,
    employee_id: Optional[int],
    vendor_name: str,
    amount: Decimal,
    currency: str = "OMR",
    expense_date: Optional[datetime] = None,
    tax_amount: Decimal = Decimal("0.00"),
    category: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    ocr_raw_text: Optional[str] = None,
    ocr_confidence: Optional[Decimal] = None,
    expense_account_code: str = "5030",
    country_code: Optional[str] = None,
    reviewed_by: Optional[int] = None,
) -> ScannedExpense:
    """Record a bill scanned by OCR and post it to the GL (expense -> accrued payable).

    Dr.  <expense_account>   (net of VAT)
    Dr.  VAT Payable (2040)  (input VAT, if any)
    Cr.  Accrued Expenses (2080)
    """
    expense_date = expense_date or datetime.utcnow()
    net_amount = round_money(amount - tax_amount)

    scanned = ScannedExpense(
        employee_id=employee_id,
        vendor_name=vendor_name,
        amount=round_money(amount),
        currency=currency,
        expense_date=expense_date,
        tax_amount=round_money(tax_amount),
        category=category,
        description=description,
        image_url=image_url,
        ocr_raw_text=ocr_raw_text,
        ocr_confidence=ocr_confidence,
        expense_account_code=expense_account_code,
        status="posted",
        reviewed_by=reviewed_by,
        country_code=country_code,
    )
    db.add(scanned)
    db.flush()

    lines = [
        JournalLineInput(
            account_code=expense_account_code, side="debit", amount=net_amount,
            description=f"Expense: {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,
        ),
    ]
    if tax_amount > 0:
        lines.append(JournalLineInput(
            account_code="2040", side="debit", amount=round_money(tax_amount),
            description=f"Input VAT on {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,
        ))
    lines.append(JournalLineInput(
        account_code="2080", side="credit", amount=round_money(amount),
        description=f"Accrued expense {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,
    ))

    entry = _post_gl(db, lines, f"OCR scanned expense - {vendor_name}", "scanned_expense",
                     scanned.id, currency, country_code, reviewed_by)
    scanned.posted_journal_entry_id = entry.id
    db.commit()
    db.refresh(scanned)
    return scanned


# ── Bank statement mapping ──────────────────────────────────────────────────────


def create_mapping_rule(
    db: Session,
    *,
    name: str,
    match_pattern: str,
    account_code: str,
    normal_side: str,
    country_code: Optional[str] = None,
    description_contains: Optional[str] = None,
    category: Optional[str] = None,
    priority: int = 100,
    created_by: Optional[int] = None,
) -> BankMappingRule:
    if not _account_exists(db, account_code):
        raise ValueError(f"Account '{account_code}' not found")
    rule = BankMappingRule(
        name=name, match_pattern=match_pattern, account_code=account_code,
        normal_side=normal_side, country_code=country_code,
        description_contains=description_contains, category=category,
        priority=priority, created_by=created_by,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def _account_exists(db: Session, code: str) -> bool:
    return db.query(Account).filter(Account.code == code).first() is not None


def _parse_date(value) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # last resort: try ISO with time
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def _match_rule(db: Session, description: str, country_code: Optional[str]) -> Optional[BankMappingRule]:
    q = db.query(BankMappingRule).filter(BankMappingRule.is_active == True)  # noqa: E712
    if country_code:
        q = q.filter((BankMappingRule.country_code == country_code) | (BankMappingRule.country_code.is_(None)))
    else:
        q = q.filter(BankMappingRule.country_code.is_(None))
    rules = q.order_by(BankMappingRule.priority.asc(), BankMappingRule.id.asc()).all()
    desc = (description or "").lower()
    for rule in rules:
        pattern = (rule.match_pattern or "").lower()
        if not pattern:
            continue
        if pattern in desc:
            return rule
    return None


def import_bank_statement(
    db: Session,
    *,
    lines: list[dict],
    bank_name: Optional[str] = None,
    file_name: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    imported_by: Optional[int] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> BankStatementImport:
    """Bulk import statement lines and auto-map them via mapping rules."""
    imp = BankStatementImport(
        bank_name=bank_name, file_name=file_name, currency=currency,
        country_code=country_code, imported_by=imported_by,
        statement_period_start=period_start, statement_period_end=period_end,
        total_lines=len(lines),
    )
    db.add(imp)
    db.flush()

    matched = 0
    for ln in lines:
        desc = ln.get("description") or ""
        rule = _match_rule(db, desc, country_code)
        line = BankStatementLine(
            import_id=imp.id,
            txn_date=_parse_date(ln.get("txn_date")),
            description=desc,
            reference=ln.get("reference"),
            amount=Decimal(str(ln.get("amount", 0))),
            mapped_account_code=rule.account_code if rule else None,
            mapped_side=rule.normal_side if rule else None,
            mapping_rule_id=rule.id if rule else None,
            status="mapped" if rule else "unmapped",
            country_code=country_code,
        )
        db.add(line)
        if rule:
            matched += 1
    imp.matched_lines = matched
    imp.unmatched_lines = len(lines) - matched
    db.commit()
    db.refresh(imp)
    return imp


def auto_post_mapped_lines(
    db: Session,
    import_id: int,
    *,
    country_code: Optional[str] = None,
    run_by: Optional[int] = None,
) -> dict:
    """Post all mapped-but-unposted statement lines to the GL."""
    lines = (
        db.query(BankStatementLine)
        .filter(BankStatementLine.import_id == import_id,
                BankStatementLine.status == "mapped",
                BankStatementLine.posted_journal_entry_id.is_(None))
        .all()
    )
    posted = 0
    for line in lines:
        side = line.mapped_side or "debit"
        je_lines = [JournalLineInput(
            account_code=line.mapped_account_code, side=side,
            amount=round_money(line.amount),
            description=line.description or "Bank statement line",
            entity_type="bank_statement_line", entity_id=line.id,
        )]
        contra = "1010" if line.mapped_account_code not in ("1010", "1020") else "2080"
        je_lines.append(JournalLineInput(
            account_code=contra, side="credit" if side == "debit" else "debit",
            amount=round_money(line.amount),
            description=f"Bank clearing for {line.description or line.id}",
            entity_type="bank_statement_line", entity_id=line.id,
        ))
        entry = _post_gl(db, je_lines, f"Bank statement: {line.description or line.id}",
                         "bank_statement_line", line.id, "OMR", country_code, run_by)
        line.posted_journal_entry_id = entry.id
        line.status = "posted"
        posted += 1
    db.commit()
    _log_automation(db, "mapping", len(lines), posted, {"import_id": import_id}, run_by, country_code)
    return {"lines": len(lines), "posted": posted}


# ── Fixed asset depreciation ────────────────────────────────────────────────────


def run_depreciation(
    db: Session,
    *,
    as_of: Optional[date] = None,
    country_code: Optional[str] = None,
    run_by: Optional[int] = None,
) -> dict:
    """Straight-line monthly depreciation for all active fixed assets."""
    as_of = as_of or date.today()
    q = db.query(FixedAsset).filter(FixedAsset.status == "active")  # noqa: E712
    if country_code:
        q = q.filter(FixedAsset.country_code == country_code)
    assets = q.all()

    processed = 0
    depreciated = 0
    for asset in assets:
        if asset.last_depreciated_date and asset.last_depreciated_date.date() >= as_of:
            continue
        months = _months_between(asset.last_depreciated_date or asset.purchase_date, as_of)
        if months <= 0:
            continue
        depreciable = round_money(asset.purchase_cost - asset.salvage_value)
        monthly = round_money(depreciable / Decimal(asset.useful_life_months))
        amount = round_money(monthly * months)
        remaining = round_money(depreciable - asset.accumulated_depreciation)
        if amount > remaining:
            amount = remaining
        if amount <= 0:
            asset.status = "fully_depreciated"
            db.flush()
            continue

        je_lines = [
            JournalLineInput(
                account_code=asset.depreciation_account_code, side="debit", amount=amount,
                description=f"Depreciation - {asset.name}", entity_type="fixed_asset", entity_id=asset.id,
            ),
            JournalLineInput(
                account_code=asset.accumulated_depr_account_code, side="credit", amount=amount,
                description=f"Accumulated depreciation - {asset.name}", entity_type="fixed_asset", entity_id=asset.id,
            ),
        ]
        entry = _post_gl(db, je_lines, f"Depreciation {asset.name}", "depreciation",
                         asset.id, "OMR", country_code, run_by)
        asset.accumulated_depreciation = round_money(asset.accumulated_depreciation + amount)
        asset.last_depreciated_date = datetime(as_of.year, as_of.month, as_of.day)
        if asset.accumulated_depreciation >= depreciable:
            asset.status = "fully_depreciated"
        processed += 1
        depreciated += 1
    db.commit()
    _log_automation(db, "depreciation", processed, depreciated, {}, run_by, country_code)
    return {"processed": processed, "depreciated": depreciated}


def _months_between(start: datetime, end: date) -> int:
    """Whole months between a datetime and a date (calendar-month boundaries)."""
    s = start.date() if isinstance(start, datetime) else start
    return (end.year - s.year) * 12 + (end.month - s.month)


# ── Accruals ─────────────────────────────────────────────────────────────────


def create_accrual(
    db: Session,
    *,
    accrual_type: str,
    amount: Decimal,
    expense_account_code: str,
    accrual_account_code: str,
    accrual_date: datetime,
    description: Optional[str] = None,
    reversal_date: Optional[datetime] = None,
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> Accrual:
    accrual = Accrual(
        accrual_type=accrual_type, amount=round_money(amount),
        expense_account_code=expense_account_code, accrual_account_code=accrual_account_code,
        accrual_date=accrual_date, description=description, reversal_date=reversal_date,
        country_code=country_code, created_by=created_by,
    )
    db.add(accrual)
    db.flush()

    if accrual_type == "expense":
        lines = [
            JournalLineInput(account_code=expense_account_code, side="debit", amount=round_money(amount),
                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),
            JournalLineInput(account_code=accrual_account_code, side="credit", amount=round_money(amount),
                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),
        ]
    else:
        lines = [
            JournalLineInput(account_code=accrual_account_code, side="debit", amount=round_money(amount),
                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),
            JournalLineInput(account_code=expense_account_code, side="credit", amount=round_money(amount),
                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),
        ]
    entry = _post_gl(db, lines, f"Accrual: {description or accrual_type}", "accrual",
                     accrual.id, "OMR", country_code, created_by)
    accrual.journal_entry_id = entry.id
    accrual.status = "open"
    db.commit()
    db.refresh(accrual)
    return accrual


def reverse_accrual(db: Session, accrual_id: int, *, run_by: Optional[int] = None) -> Accrual:
    accrual = db.query(Accrual).filter(Accrual.id == accrual_id).first()
    if not accrual:
        raise ValueError(f"Accrual {accrual_id} not found")
    if accrual.status != "open":
        raise ValueError(f"Accrual {accrual_id} is {accrual.status}")
    orig = db.query(JournalEntry).filter(JournalEntry.id == accrual.journal_entry_id).first()
    lines = []
    if orig:
        for l in orig.lines:
            lines.append(JournalLineInput(
                account_code=l.account.code, side="credit" if l.side == "debit" else "debit",
                amount=round_money(l.amount), description=f"Reverse accrual {accrual.id}",
                entity_type="accrual", entity_id=accrual.id,
            ))
    entry = _post_gl(db, lines, f"Reverse accrual {accrual.id}", "accrual_reversal",
                     accrual.id, "OMR", accrual.country_code, run_by)
    accrual.reversal_entry_id = entry.id
    accrual.status = "reversed"
    db.commit()
    db.refresh(accrual)
    return accrual


# ── Helpers ──────────────────────────────────────────────────────────────────


def _post_gl(
    db: Session,
    lines: list[JournalLineInput],
    description: str,
    reference_type: str,
    reference_id: int,
    currency: str,
    country_code: Optional[str],
    user_id: Optional[int],
) -> JournalEntry:
    from services import general_ledger_service as gl

    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
        currency=currency,
        country_code=country_code,
        lines=lines,
    ), user_id=user_id)
    if user_id:
        try:
            audit_log(
                db=db, action=AuditAction.JOURNAL_ENTRY_CREATED, user_id=user_id,
                username=None, user_role=None, resource_type="journal_entry",
                resource_id=entry.get("id") if isinstance(entry, dict) else entry.id,
                details={"reference_type": reference_type, "source": "automation"},
            )
        except Exception:
            pass
    return entry


def _log_automation(
    db: Session, kind: str, processed: int, changed: int,
    detail: dict = None, run_by: Optional[int] = None, country_code: Optional[str] = None,
) -> None:
    log = FinanceAutomationLog(
        kind=kind, records_processed=processed, records_changed=changed,
        detail=detail, run_by=run_by, country_code=country_code,
    )
    db.add(log)
    db.flush()


def import_bank_statement_csv(
    db: Session,
    *,
    raw_csv: str,
    bank_name: Optional[str] = None,
    file_name: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    imported_by: Optional[int] = None,
) -> dict:
    """Parse an uploaded CSV server-side (robust) and import + auto-map lines."""
    from services.ocr_parser import parse_statement_csv

    parsed = parse_statement_csv(raw_csv)
    imp = import_bank_statement(
        db, lines=parsed, bank_name=bank_name, file_name=file_name,
        currency=currency, country_code=country_code, imported_by=imported_by,
    )
    return {"import_id": imp.id, "total_lines": imp.total_lines,
            "matched_lines": imp.matched_lines, "unmatched_lines": imp.unmatched_lines}


def run_daily_automation(
    db: Session, *,
    as_of: Optional[date] = None,
    country_code: Optional[str] = None,
    run_by: Optional[int] = None,
) -> dict:
    """Idempotent per-day automation: depreciation + accrual reversals + orphan scan."""
    as_of = as_of or date.today()
    # 1. Depreciation
    dep = run_depreciation(db, as_of=as_of, country_code=country_code, run_by=run_by)
    # 2. Reverse accruals whose reversal date has passed
    from models import Accrual

    due = db.query(Accrual).filter(
        Accrual.status == "open",
        Accrual.reversal_date.isnot(None),
        Accrual.reversal_date <= datetime(as_of.year, as_of.month, as_of.day),
    ).all()
    reversed_count = 0
    for acc in due:
        try:
            reverse_accrual(db, acc.id, run_by=run_by)
            reversed_count += 1
        except Exception as e:
            logger.warning("accrual reverse failed %s: %s", acc.id, e)
    # 3. Orphan detection (uses corrected reference_type values)
    from services.treasury_engine import TreasuryEngine

    try:
        orphans = TreasuryEngine(db).run_orphan_detector()
    except Exception as e:
        logger.warning("orphan detector failed: %s", e)
        orphans = []
    _log_automation(db, "daily_run", len(due) + len(orphans), reversed_count + dep.get("depreciated", 0),
                    {"depreciated": dep, "accruals_reversed": reversed_count, "orphans": len(orphans)},
                    run_by, country_code)
    db.commit()
    return {"as_of": as_of.isoformat(), "depreciation": dep,
            "accruals_reversed": reversed_count, "orphans": orphans}


def trigger_recurring(
    db: Session, *,
    template_id: int,
    run_date: Optional[datetime] = None,
    run_by: Optional[int] = None,
) -> dict:
    """Generate a journal entry from a recurring template."""
    from models import RecurringTemplate

    tpl = db.query(RecurringTemplate).filter(RecurringTemplate.id == template_id).first()
    if not tpl or not tpl.is_active:
        raise ValueError("recurring template not found/inactive")
    run_date = run_date or _utcnow()
    lines = []
    for ln in (tpl.lines or []):
        lines.append(JournalLineInput(
            account_code=ln["account_code"], side=ln["side"],
            amount=Decimal(str(ln["amount"])), description=ln.get("description"),
        ))
    entry = _post_gl(
        db, lines=lines, description=tpl.description or f"Recurring: {tpl.name}",
        reference_type="recurring", reference_id=tpl.id, currency=tpl.currency,
        country_code=tpl.country_code, user_id=run_by,
    )
    if tpl.next_run_date and isinstance(tpl.next_run_date, datetime):
        # advance ~1 month (safe, dependency-free)
        nd = tpl.next_run_date
        try:
            tpl.next_run_date = nd.replace(month=nd.month % 12 + 1, year=nd.year + (nd.month == 12))
        except ValueError:
            tpl.next_run_date = nd + timedelta(days=30)
    db.commit()
    return {"template_id": tpl.id, "journal_entry_id": entry.id if not isinstance(entry, dict) else entry.get("id")}

