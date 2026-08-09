"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from routers.public_email_controller_access import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

from routers.public_accounting_access import router

