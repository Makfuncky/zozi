"""rbac/roles.py - (module, role) -> default feature sets (spec).

Replaces DEFAULT_ROLE_PERMISSION_MAP / ADMIN_PERMISSION_MAP.
"""
from typing import Dict, Set, Tuple

ROLE_FEATURES: Dict[Tuple[str, str], Set[str]] = {
    ("admin", "admin"): {"*"},
    ("admin", "country_finance"): {"finance.reporting.read", "finance.ledger.read"},
    ("employee", "finance_manager"): {"finance.ledger.post", "finance.reporting.*"},
    ("employee", "employee"): {"hr.payslip.view", "finance.expenses.submit"},
    ("supplier", "supplier"): {"finance.payouts.view"},
}
