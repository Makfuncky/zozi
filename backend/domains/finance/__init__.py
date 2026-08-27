"""Finance domain — public facade.

Exports the public API for the finance domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "FinanceService": ("domains.finance.services.finance_service", "FinanceService"),
    "DataImportService": ("domains.finance.services.data_import_service", "DataImportService"),
    "GeneralLedgerService": ("domains.finance.services.ledger.general_ledger_service", "GeneralLedgerService"),
    "PaymentEngine": ("domains.finance.services.payments.payment_engine", "PaymentEngine"),
    "PaymentOrchestrator": ("domains.finance.services.payments.payment_orchestrator", "PaymentOrchestrator"),
    "PayoutBatchService": ("domains.finance.services.payouts.payout_batch_service", "PayoutBatchService"),
    "CashManagementService": ("domains.finance.services.treasury.cash_management_service", "CashManagementService"),
    "TreasuryService": ("domains.finance.services.treasury.treasury_service", "TreasuryService"),
    # models
    "Payout": ("domains.finance.models.payments", "Payout"),
    "Commission": ("domains.finance.models.commission", "Commission"),
    "GeneralLedger": ("domains.finance.models.general_ledger", "GeneralLedger"),
    # functions
    "process_payment": ("domains.finance.services.payments.payments", "process_payment"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.finance' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
