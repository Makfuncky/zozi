from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from models import TreasuryAccount, JournalEntry, AuditLog, Account, FinanceAuditLog
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class TreasuryAdapter:
    """
    Treasury service interface for financial transactions.

    All journal posts are routed through the canonical immutable double-entry
    ledger (`general_ledger_service.create_journal_entry`) so balances stay
    consistent and every entry is auditable.
    """

    def __init__(self, db: Session):
        self.db = db

    def post_journal_entry(
        self,
        entry_type: str,
        amount: Decimal,
        currency: str,
        debit_account_id: int,
        credit_account_id: int,
        description: str,
        reference_id: Optional[int] = None,
        country_code: Optional[str] = None,
    ) -> JournalEntry:
        """Post a manual journal entry (debit one account, credit another)."""
        debit_acct = self.db.query(Account).filter(Account.id == debit_account_id).first()
        credit_acct = self.db.query(Account).filter(Account.id == credit_account_id).first()
        if not debit_acct or not credit_acct:
            raise ValueError("debit/credit account not found")

        entry_out = gl.create_journal_entry(
            self.db,
            JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="manual",
                reference_id=reference_id or 0,
                description=description,
                currency=currency,
                country_code=country_code,
                lines=[
                    JournalLineInput(
                        account_code=debit_acct.code, side="debit",
                        amount=amount, description=description,
                    ),
                    JournalLineInput(
                        account_code=credit_acct.code, side="credit",
                        amount=amount, description=description,
                    ),
                ],
            ),
            user_id=getattr(self, "_user_id", None),
        )
        self._audit("journal_post", entry_out.id, country_code, {"entry_type": entry_type, "amount": str(amount)})
        return self.db.query(JournalEntry).filter(JournalEntry.id == entry_out.id).first()

    def _audit(self, action: str, entity_id: int, country_code, detail: dict) -> None:
        try:
            self.db.add(FinanceAuditLog(
                action=action, entity_type="journal_entry", entity_id=entity_id,
                country_code=country_code, detail=detail,
            ))
            self.db.commit()
        except Exception as e:  # audit must never break the main flow
            logger.warning("finance audit log failed: %s", e)
    
    def generate_payment_batch(
        self,
        payments: list,
        batch_type: str = "payroll",
    ) -> dict:
        """Generate a payment batch for treasury processing."""
        batch = {
            "id": f"BATCH_{_utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": batch_type,
            "payments": payments,
            "total_amount": sum(p.get("amount", 0) for p in payments),
            "generated_at": _utcnow().isoformat(),
        }
        return batch
    
    def reconcile_payment(
        self,
        payment_id: int,
        bank_transaction_id: int,
        status: str,
    ) -> bool:
        """Reconcile a payment with bank transaction."""
        audit = AuditLog(
            event_type="reconciliation",
            actor_id=None,
            action="reconcile",
            resource_type="payment",
            resource_id=payment_id,
            details={
                "bank_transaction_id": bank_transaction_id,
                "status": status,
            },
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
        return True

