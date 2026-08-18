"""Auto-migrated service logic from routers/admin_payouts.py."""
from __future__ import annotations
from domains.governance.services.admin_treasury_status_service import _update_bg_status_after_manual_trigger

from fastapi import Depends, HTTPException, Path, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import PayoutCreate, PayoutOut

from domains.accounts.models.user import User
from domains.finance.models.finance import FinanceAutomationLog
from domains.payments.models.payments import Payout

from infrastructure.utils.audit import AuditAction, audit_log

from domains.finance.services.auto_payout_scheduler import get_background_job_status as _get_bg_status

from domains.finance.services.auto_payout_scheduler import run_auto_logistics_payout_sweep as _run_logistics_sweep

from domains.finance.services.auto_payout_scheduler import run_auto_payout_sweep as _run_supplier_sweep

from domains.finance.services.auto_payout_scheduler import start_auto_payout_background_job as _start_bg_job

from domains.finance.services.auto_payout_scheduler import stop_auto_payout_background_job as _stop_bg_job

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.datetime_utils import utcnow

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = "verified"















from domains.governance.services.admin_treasury_status_service import create_payout






















from domains.governance.services.admin_treasury_status_service import list_pending_payouts














from domains.governance.services.admin_treasury_status_service import list_pending_payouts_by_country











from domains.governance.services.admin_treasury_status_service import verify_payout













from domains.governance.services.admin_treasury_status_service import run_auto_payout_sweep














from domains.governance.services.admin_treasury_status_service import process_payout
from domains.governance.services.admin_treasury_status_service import get_background_job_status_endpoint


# === auto-wiring re-exports (migration repair) ===
from domains.governance.services.admin_treasury_status_service import start_background_job
from domains.governance.services.admin_treasury_status_service import stop_background_job
from domains.governance.services.admin_treasury_status_service import trigger_background_job
from domains.governance.services.admin_treasury_status_service import trigger_background_job_kind



