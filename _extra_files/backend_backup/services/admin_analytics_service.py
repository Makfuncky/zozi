"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.admin_analytics_service import ...`)
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

_compute_analytics_overview = _missing_symbol('_compute_analytics_overview')
_compute_analytics_timeseries_payload = _missing_symbol('_compute_analytics_timeseries_payload')
_compute_top_products_payload = _missing_symbol('_compute_top_products_payload')
_compute_user_growth_payload = _missing_symbol('_compute_user_growth_payload')
_store_admin_analytics_snapshot = _missing_symbol('_store_admin_analytics_snapshot')
refresh_admin_analytics_snapshots = _missing_symbol('refresh_admin_analytics_snapshots')

