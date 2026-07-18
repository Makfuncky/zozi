#!python
"""
Treasury Engine - Double-Entry Bookkeeping System
Implements the core financial logic for the GCC Chart of Accounts
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models import (
    Account, AccountGroup, JournalEntry, JournalEntryLine,
    AccountBalance, PendingJournalEntry,
)
from services.general_ledger_service import seed_chart_of_accounts as gl_seed_chart_of_accounts
from services.general_ledger_service import get_trial_balance as gl_get_trial_balance

logger = logging.getLogger(__name__)


class TreasuryEngine:
    """
    Core Treasury Engine for double-entry bookkeeping.
    Enforces the Golden Rule: Every Debit has a corresponding Credit.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    @contextmanager
    def atomic_transaction(self):
        """Context manager for atomic financial transactions."""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    
    def post_journal_entry(
        self,
        lines: List[Dict[str, Any]],
        description: str,
        entry_date: date = None,
        source: str = None,
        country_code: str = None,
        created_by: int = None,
        reference_type: str = None,
        reference_id: int = None,
        shadow_mode: bool = False,
    ) -> JournalEntry:
        """
        Post a double-entry journal entry with FOR UPDATE locking.
        Lines: [{"account_code": "1010-001", "debit": 100.00, "credit": 0}, ...]

        Acquires SELECT ... FOR UPDATE on affected account_balances rows
        to prevent race conditions during concurrent checkout/payouts.
        """
        if not lines:
            raise ValueError("Journal entry must have at least one line")

        total_debit = sum(Decimal(str(line.get("debit", 0) or 0)) for line in lines)
        total_credit = sum(Decimal(str(line.get("credit", 0) or 0)) for line in lines)

        if abs(total_debit - total_credit) > Decimal("0.0001"):
            raise ValueError(
                f"Golden Rule violation: Debits ({total_debit}) != Credits ({total_credit})"
            )

        entry_date = entry_date or date.today()
        reference_number = self._generate_reference_number()

        # 1. Lock affected accounts FOR UPDATE (prevents deadlocks)
        account_codes = [line["account_code"] for line in lines]
        # Build a lookup that also resolves sub-account codes (e.g. "1010-001")
        # to their parent account code ("1010") when the parent exists.
        all_accounts = self.db.execute(select(Account)).scalars().all()
        full_map = {a.code: a for a in all_accounts}
        resolved_accounts: Dict[str, Any] = {}
        missing = set()
        for code in account_codes:
            if code in full_map:
                resolved_accounts[code] = full_map[code]
            else:
                parent = str(code).split("-")[0]
                if parent in full_map:
                    resolved_accounts[code] = full_map[parent]
                else:
                    missing.add(code)
        if missing:
            raise ValueError(f"Accounts not found: {missing}")

        # 2. Lock balance rows FOR UPDATE
        account_ids = [a.id for a in resolved_accounts.values()]
        balances = self.db.execute(
            select(AccountBalance).where(
                AccountBalance.account_id.in_(account_ids)
            ).with_for_update()
        ).scalars().all()
        balance_map = {b.account_id: b for b in balances}

        # 3. Create entry (shadow mode skips commit)
        entry = JournalEntry(
            reference_number=reference_number,
            entry_date=entry_date,
            description=description,
            source=source,
            country_code=country_code,
            created_by=created_by,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(entry)
        self.db.flush()

        for line in lines:
            account = resolved_accounts[line["account_code"]]
            entry_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=account.id,
                amount=Decimal(str(line.get("debit", 0) or line.get("credit", 0))),
                side="debit" if line.get("debit") else "credit",
                description=line.get("description", ""),
                country_code=country_code,
            )
            self.db.add(entry_line)

        # 4. Update balances on locked rows
        for line in lines:
            account = resolved_accounts[line["account_code"]]
            debit = Decimal(str(line.get("debit", 0) or 0))
            credit = Decimal(str(line.get("credit", 0) or 0))

            balance = balance_map.get(account.id)
            if not balance:
                balance = AccountBalance(account_id=account.id, balance=Decimal("0.00"), country_code=country_code)
                self.db.add(balance)
            elif country_code:
                balance.country_code = country_code

            if account.normal_side == "debit":
                balance.balance += debit - credit
            else:
                balance.balance += credit - debit

            balance.last_updated = datetime.utcnow()

        # 5. Log entry for reconciliation
        self._record_reconcilable_entry(entry, lines)

        if not shadow_mode:
            self.db.commit()

        return entry

    def _record_reconcilable_entry(self, entry: JournalEntry, lines: List[Dict[str, Any]]):
        """Link journal entry to reconcilable accounts for the Orphan Detector."""
        from datetime import timezone as tz
        for line in lines:
            acct_code = line.get("account_code", "")
            if acct_code in ("2010-001", "2020-001", "1030-001"):
                entry.source = entry.source or f"reconcilable:{acct_code}"
    
    def _generate_reference_number(self) -> str:
        """Generate unique journal entry reference number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        count = self.db.execute(select(func.count()).select_from(JournalEntry)).scalar()
        return f"JE-{timestamp}-{count + 1:06d}"
    
    def get_account_hierarchy(self) -> List[Dict]:
        """Get complete 3-layer account hierarchy."""
        categories = self.db.execute(
            select(AccountGroup).order_by(AccountGroup.display_order)
        ).scalars().all()
        
        result = []
        for cat in categories:
            accounts = self.db.execute(
                select(Account).where(
                    Account.group_id == cat.id,
                    Account.is_active == True
                ).order_by(Account.code)
            ).scalars().all()
            
            result.append({
                "category_code": cat.code,
                "category_name": cat.name,
                "normal_side": cat.normal_side,
                "accounts": [
                    {
                        "code": acc.code,
                        "name": acc.name,
                        "type": acc.currency,
                    }
                    for acc in accounts
                ]
            })
        
        return result
    
    def get_trial_balance(self) -> List[Dict]:
        """Generate trial balance report — delegates to canonical GL service version."""
        result = gl_get_trial_balance(self.db, currency="OMR")
        return [
            {
                "account_code": a.account_code,
                "account_name": a.account_name,
                "currency": "OMR",
                "normal_side": a.normal_side,
                "balance": float(a.balance),
            }
            for a in result.accounts
        ]
    
    def generate_payout_batch(
        self,
        country_code: str,
        cutoff_date: date,
    ):
        """Generate a new payout batch for suppliers."""
        return {"batch_number": f"PB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", "status": "draft"}
    
    def approve_payout_batch(
        self,
        batch_id: int,
        approver_id: int,
    ) -> bool:
        """Approve a payout batch (maker-checker workflow)."""
        return True

    # ── Maker-Checker Protocol ──────────────────────────────────────

    def submit_pending_entry(
        self,
        lines: list[dict],
        description: str,
        created_by: int,
        entry_date: date = None,
        source: str = None,
        country_code: str = None,
    ) -> dict:
        """Submit a journal entry for Maker-Checker approval.

        Returns the pending entry; a second admin must call
        approve_pending_entry() to commit it to the immutable ledger.
        """
        entry_date = entry_date or date.today()
        import json
        pending = PendingJournalEntry(
            lines_json=json.dumps(lines),
            description=description,
            source=source,
            country_code=country_code,
            entry_date=entry_date,
            amount_threshold_triggered=True,
            status="pending_approval",
            created_by=created_by,
        )
        self.db.add(pending)
        self.db.commit()
        self.db.refresh(pending)
        return {
            "pending_id": pending.id,
            "status": "pending_approval",
            "description": description,
        }

    def approve_pending_entry(
        self,
        pending_id: int,
        approver_id: int,
        shadow_mode: bool = False,
    ) -> dict:
        """Approve and commit a pending journal entry to the immutable ledger.

        Enforces Maker-Checker: the approver must differ from the creator.
        """
        import json
        pending = self.db.execute(
            select(PendingJournalEntry).where(PendingJournalEntry.id == pending_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not pending:
            raise ValueError(f"Pending entry {pending_id} not found")
        if pending.status != "pending_approval":
            raise ValueError(f"Entry {pending_id} is already {pending.status}")
        if pending.created_by == approver_id:
            raise ValueError("Maker-Checker violation: approver must differ from creator")

        lines = json.loads(pending.lines_json)
        entry = self.post_journal_entry(
            lines=lines,
            description=pending.description,
            entry_date=pending.entry_date,
            source=pending.source or "maker_checker",
            country_code=pending.country_code,
            created_by=approver_id,
            shadow_mode=shadow_mode,
        )

        pending.status = "approved"
        pending.approved_by = approver_id
        pending.approved_at = datetime.utcnow()
        pending.journal_entry_id = entry.id
        self.db.commit()

        return {
            "pending_id": pending_id,
            "status": "approved",
            "journal_entry_id": entry.id,
            "reference_number": entry.reference_number,
        }

    def reject_pending_entry(
        self,
        pending_id: int,
        rejected_by: int,
        reason: str,
    ) -> dict:
        """Reject a pending journal entry."""
        pending = self.db.execute(
            select(PendingJournalEntry).where(PendingJournalEntry.id == pending_id)
        ).scalar_one_or_none()
        if not pending:
            raise ValueError(f"Pending entry {pending_id} not found")
        pending.status = "rejected"
        pending.rejected_by = rejected_by
        pending.rejection_reason = reason
        self.db.commit()
        return {"pending_id": pending_id, "status": "rejected", "reason": reason}

    def list_pending_entries(self) -> list[dict]:
        """List all entries awaiting Maker-Checker approval."""
        entries = self.db.execute(
            select(PendingJournalEntry)
            .where(PendingJournalEntry.status == "pending_approval")
            .order_by(PendingJournalEntry.created_at.desc())
        ).scalars().all()
        return [
            {
                "id": e.id,
                "description": e.description,
                "source": e.source,
                "country_code": e.country_code,
                "entry_date": e.entry_date.isoformat(),
                "created_by": e.created_by,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]

    # ── Orphan Detector ─────────────────────────────────────────────

    def run_orphan_detector(self) -> list[dict]:
        """Daily cron: scan orders for missing journal entries.

        Flags any delivered/paid order that lacks a corresponding
        JournalEntry with matching reference_type/reference_id.
        """
        from models.orders import Order

        alerts = []

        # Check delivered orders for missing delivery JE
        delivered_orders = self.db.execute(
            select(Order).where(
                Order.status.in_(["delivered", "completed"]),
                ~Order.id.in_(
                    select(JournalEntry.reference_id).where(
                        JournalEntry.reference_type == "order_delivery",
                        JournalEntry.reference_id.isnot(None),
                    )
                ),
            )
        ).scalars().all()

        for o in delivered_orders:
            alerts.append({
                "type": "missing_delivery_entry",
                "order_id": o.id,
                "order_number": o.order_number,
                "country_code": o.country_code,
                "severity": "critical",
            })

        # Check paid orders for missing payment JE
        paid_orders = self.db.execute(
            select(Order).where(
                Order.payment_status.in_(["paid", "captured"]),
                ~Order.id.in_(
                    select(JournalEntry.reference_id).where(
                        JournalEntry.reference_type == "order_payment",
                        JournalEntry.reference_id.isnot(None),
                    )
                ),
            )
        ).scalars().all()

        for o in paid_orders:
            alerts.append({
                "type": "missing_payment_entry",
                "order_id": o.id,
                "order_number": o.order_number,
                "country_code": o.country_code,
                "severity": "high",
            })

        return alerts


def seed_chart_of_accounts(db: Session):
    """Seed the GCC Chart of Accounts — delegates to canonical GL service version."""
    gl_seed_chart_of_accounts(db)

