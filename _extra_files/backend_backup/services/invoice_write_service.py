"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.invoice_write_service import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

# The following symbols were referenced but have NO definition
# anywhere in the codebase. They are stubbed to fail loudly at
# call time rather than break import of this module.
def _missing_symbol(name):
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{mod}.{name}' is not implemented (refactor gap)")
    return _f

create_invoice_with_items = _missing_symbol('create_invoice_with_items')
update_invoice = _missing_symbol('update_invoice')

