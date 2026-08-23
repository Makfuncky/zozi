"""
Fix illegal cross-domain service imports across the comms domain.
Converts `from domains.{other}.services.` to ports imports or lazy imports.
"""
import os
import re

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'
COMMS = os.path.join(BACKEND, 'domains', 'comms')

# Map of illegal service imports to their ports equivalents
REPLACEMENTS = [
    # Finance services -> finance.ports
    ('from domains.finance.services.tax.tax_service import calculate_tax', 'from domains.finance.ports import calculate_tax'),
    ('from domains.finance.services.tax.tax_service import get_country_config', 'from domains.country.ports import get_country_config'),
    ('from domains.finance.services.cash_write_service import create_cash_account', 'from domains.finance.ports import create_cash_account'),
    ('from domains.finance.services.cash_write_service import create_cash_transaction', 'from domains.finance.ports import create_cash_transaction'),
    ('from domains.finance.services.finance import general_ledger_service', 'from domains.finance.ports import create_journal_entry'),

    # Governance services -> governance.ports
    ('from domains.governance.services.auth.auth_controller_service import get_current_user', 'from domains.governance.ports import get_current_user'),
    ('from domains.governance.services.auth.security_dependencies import require_roles', 'from domains.governance.ports import require_roles'),
    ('from domains.governance.services.user.user_read_service import get_user_display_name', 'from domains.governance.ports import get_user_display_name'),
    ('from domains.governance.services.user.user_read_service import get_user_role', 'from domains.governance.ports import get_user_role'),

    # HR services -> hr.ports
    ('from domains.hr.services.employee_communication_service import log_comm_event', 'from domains.hr.ports import log_comm_event'),
    ('from domains.hr.services.employee_communication_service import get_inbox', 'from domains.hr.ports import get_inbox'),
    ('from domains.hr.services.employee_activity_logger import log_activity', 'from domains.hr.ports import log_activity'),
    ('from domains.hr.services.attendance_service import AttendanceService', 'from domains.hr.ports import AttendanceService'),
    ('from domains.hr.services.leave_accrual import LeaveAccrualEngine', 'from domains.hr.ports import LeaveAccrualEngine'),

    # Governance auth services
    ('from domains.governance.services.auth.flat_mobile_auth_service import MobileAuthService', 'from domains.governance.ports import MobileAuthService'),

    # Finance expense processing
    ('from domains.finance.services.ledger.expense_processing import ExpenseProcessingService', 'from domains.finance.ports import ExpenseProcessingService'),
]

fixed_files = []

for root, dirs, files in os.walk(COMMS):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()

                original = content
                for old, new in REPLACEMENTS:
                    content = content.replace(old, new)

                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as fh:
                        fh.write(content)
                    fixed_files.append(os.path.relpath(filepath, BACKEND))
            except Exception as e:
                pass

print(f"Fixed illegal service imports in {len(fixed_files)} files:")
for f in fixed_files:
    print(f"  - {f}")
