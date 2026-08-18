# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.treasury.admin_treasury_write_service re-exports for HTTP routers."""
from domains.finance.services.admin_treasury_write_service import create_payout as svc_create_payout
from domains.finance.services.admin_treasury_write_service import process_payout as svc_process_payout
from domains.finance.services.admin_treasury_write_service import verify_payout as svc_verify_payout

from domains.suppliers.services.suppliers_write_service import create_payout
from domains.finance.services.admin_treasury_write_service import process_payout
from domains.governance.services.payouts_service import verify_payout
