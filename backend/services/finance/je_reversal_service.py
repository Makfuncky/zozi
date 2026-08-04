"""Journal Entry Reversal Service — formal reversal/correction of posted JEs.

Allows reversing a journal entry by creating a mirror entry with opposite
sides, referencing the original via `reversal_of_id`.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from data.models import JournalEntry, JournalEntryLine
from services.general_ledger_service import create_journal_entry, get_journal_entry
from data.schemas import JournalEntryCreate, JournalLineInput

logger = logging.getLogger(__name__)


def reverse_journal_entry(
    db: Session,
    original_entry_id: int,
    reason: str,
    user_id: int,
    reversal_date: Optional[datetime] = None,
) -> dict:
    """Reverse a journal entry by creating a mirror entry.

    1. Validates the original entry exists and is not already reversed
    2. Creates a new entry with opposite debit/credit sides
    3. Links via reversal_of_id
    """
    original = db.query(JournalEntry).filter(JournalEntry.id == original_entry_id).first()
    if not original:
        raise ValueError(f"Journal entry #{original_entry_id} not found")
    if original.is_deleted:
        raise ValueError(f"Journal entry #{original_entry_id} is deleted")
    if original.reversal_of_id:
        raise ValueError(f"Journal entry #{original_entry_id} is itself a reversal — cannot reverse a reversal")
    # Check if already reversed
    existing_reversal = db.query(JournalEntry).filter(
        JournalEntry.reversal_of_id == original_entry_id,
        JournalEntry.is_deleted == False,
    ).first()
    if existing_reversal:
        raise ValueError(
            f"Journal entry #{original_entry_id} already reversed by entry #{existing_reversal.id}"
        )

    lines = (
        db.query(JournalEntryLine)
        .filter(JournalEntryLine.entry_id == original_entry_id)
        .all()
    )
    if not lines:
        raise ValueError(f"Journal entry #{original_entry_id} has no lines")

    reversed_lines = []
    for line in lines:
        acct = line.account
        reversed_lines.append(JournalLineInput(
            account_code=acct.code,
            side="credit" if line.side == "debit" else "debit",
            amount=line.amount,
            description=f"REVERSAL: {line.description or ''}",
            entity_type=line.entity_type,
            entity_id=line.entity_id,
        ))

    ref = f"REV-{original.reference_number or original_entry_id}"
    entry_data = JournalEntryCreate(
        entry_date=reversal_date or datetime.utcnow(),
        reference_type="reversal",
        reference_id=original_entry_id,
        reference_number=ref,
        description=f"Reversal of JE #{original_entry_id}: {reason}",
        currency=original.currency,
        lines=reversed_lines,
    )

    new_entry = create_journal_entry(db, entry_data, user_id=user_id)

    # Link reversal
    new_entry_obj = db.query(JournalEntry).filter(JournalEntry.id == new_entry.id).first()
    new_entry_obj.reversal_of_id = original_entry_id
    db.commit()

    return {
        "original_entry_id": original_entry_id,
        "reversal_entry_id": new_entry.id,
        "reference_number": ref,
        "reason": reason,
        "reversal_date": (reversal_date or datetime.utcnow()).isoformat(),
        "lines_reversed": len(reversed_lines),
    }

