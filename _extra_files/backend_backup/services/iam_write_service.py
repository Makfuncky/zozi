"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.iam_write_service import ...`)
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

create_employee_biometric = _missing_symbol('create_employee_biometric')
create_geo_fence_log = _missing_symbol('create_geo_fence_log')
create_physical_id_card = _missing_symbol('create_physical_id_card')
update_employee_biometric = _missing_symbol('update_employee_biometric')
update_physical_id_card = _missing_symbol('update_physical_id_card')

