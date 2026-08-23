"""Deprecated alias — supplier-cash-management symbols moved to the finance domain.

The canonical supplier cash-management / ledger / settlement functions now live in
``domains.finance.services.cash_management_service`` (and its treasury submodule).
This module is retained as a merge-not-delete placeholder so that any legacy
import of ``domains.suppliers.services.cash_management_controller_service``
continues to resolve; it intentionally exports nothing new.
"""

from __future__ import annotations

__all__ = []
