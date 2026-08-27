"""Treasury Service â€” encapsulates treasury operations."""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session


class TreasuryService:
    """Service for treasury operations."""

    def __init__(self, db: Session):
        self.db = db

    def post_journal_entry(self, **kwargs):
                adapter = TreasuryAdapter(self.db)
        return adapter.post_journal_entry(**kwargs)

    def get_treasury_metrics(self) -> dict:
        return {}

    def get_cash_position(self) -> dict:
        return {}

    def get_vat_liability(self, country_code: Optional[str] = None) -> dict:
        return {}

    def get_supplier_payables(self, country_code: Optional[str] = None) -> dict:
        return {}


def get_treasury_service(db: Session) -> TreasuryService:
    return TreasuryService(db)

