"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.misc_write_service import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

from services.treasury.cash_write_service import (
    create_cash_account,
    create_cash_transaction,
)

# The following symbols were referenced but have NO definition
# anywhere in the codebase. They are stubbed to fail loudly at
# call time rather than break import of this module.
def _missing_symbol(name):
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{mod}.{name}' is not implemented (refactor gap)")
    return _f

hard_delete_record = _missing_symbol('hard_delete_record')
reset_demo_data = _missing_symbol('reset_demo_data')
restore_record = _missing_symbol('restore_record')
soft_delete_record = _missing_symbol('soft_delete_record')

