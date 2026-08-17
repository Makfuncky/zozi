import re
import textwrap

with open('backend/routers/admin_treasury.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all endpoint functions with decorators
pattern = r'(@router\.(?:get|post|put|patch|delete)\([^)]*\)\s+(?:async )?def (\w+)\((.*?)\):(.*?)(?=@router\.|\Z)'
matches = re.finditer(pattern, content, re.DOTALL)

service_lines = [
    '"""Treasury service — migrated from routers/admin_treasury.py."""',
    'from __future__ import annotations',
    '',
    'from datetime import date, datetime',
    'from decimal import Decimal',
    'from typing import Optional',
    '',
    'from fastapi import HTTPException',
    'from sqlalchemy import func, select',
    'from sqlalchemy.orm import Session, joinedload',
    '',
    'from models import (',
    '    Account,',
    '    AccountBalance,',
    '    CashFlowForecast,',
    '    CashPositionSnapshot,',
    '    GatewaySettlementSchedule,',
    '    Invoice,',
    '    JournalEntry,',
    '    JournalEntryLine,',
    '    PayoutBatch,',
    '    PayoutBatchItem,',
    '    SupplierSettlement,',
    '    TreasuryAccount,',
    '    VATRemittance,',
    ')',
    'from models.admin import LogisticsCODRemittanceReceipt',
    'from models.employee_models import Employee',
    'from models.logistics import LogisticsPartner',
    'from models.orders import Order as OrderModel',
    'from models.payments import LogisticsPartnerPayout, Payment, Payout',
    'from services.treasury.treasury_engine import TreasuryEngine',
    'from utils.constants import (',
    '    CASH_ACCOUNT,',
    '    DEFAULT_PAGE_SIZE,',
    '    INPUT_VAT_ACCOUNT,',
    '    MAX_PAGE_SIZE,',
    '    OUTPUT_VAT_ACCOUNT,',
    '    PAYABLES_ACCOUNT,',
    '    TREASURY_ROLES,',
    ')',
    'from utils.country_rls import get_country_or_404',
    '',
    '',
    'def require_treasury_access(current_user: dict) -> dict:',
    '    if current_user.get("role", "").lower() not in TREASURY_ROLES:',
    '        raise HTTPException(status_code=403, detail="Treasury access required")',
    '    return current_user',
    '',
    '',
]

count = 0
for i, m in enumerate(matches):
    method = m.group(1)
    path = m.group(2)
    func_name = m.group(3)
    sig = m.group(4).strip()
    body = m.group(5).strip()
    
    # Clean up signature: remove FastAPI-specific params
    params = sig.split(',')
    clean_params = []
    for p in params:
        p = p.strip()
        if not p:
            continue
        if 'Depends' in p or 'FastAPIBody' in p or p.startswith('current_user') or p.startswith('db:'):
            continue
        if p.startswith('country_code: str = Path') or p.startswith('batch_id: int = Path'):
            clean_params.append(p)
        elif p.startswith('limit: int') or p.startswith('page: int') or p.startswith('page_size: int'):
            clean_params.append(p)
        elif p.startswith('start_date:') or p.startswith('end_date:') or p.startswith('as_of_date:') or p.startswith('status:'):
            clean_params.append(p)
        elif p.startswith('country_code: Optional') or p.startswith('include_deleted:') or p.startswith('sort_order:'):
            clean_params.append(p)
        elif p.startswith('title:') or p.startswith('subtitle:') or p.startswith('image_url:') or p.startswith('link:'):
            clean_params.append(p)
        elif p.startswith('cta_label:') or p.startswith('cta_url:') or p.startswith('banner_type:') or p.startswith('is_active:'):
            clean_params.append(p)
        elif p.startswith('bg_color:') or p.startswith('text_color:') or p.startswith('subtitle_color:') or p.startswith('btn_bg_color:'):
            clean_params.append(p)
        elif p.startswith('btn_text_color:') or p.startswith('badge_text:') or p.startswith('badge_color:') or p.startswith('effect:'):
            clean_params.append(p)
        elif p.startswith('layout_json:') or p.startswith('video_url:') or p.startswith('admin:') or p.startswith('_:') or p.startswith('body:') or p.startswith('payload:'):
            continue
        else:
            clean_params.append(p)
    
    # Clean body: remove db: Session = Depends(get_db) and current_user deps
    clean_body = body
    clean_body = re.sub(r'db: Session = Depends\(get_db\)\s*', '', clean_body)
    clean_body = re.sub(r'current_user: dict = Depends\(require_treasury_access\)\s*', '', clean_body)
    clean_body = re.sub(r'Depends\(require_treasury_access\)\s*', '', clean_body)
    clean_body = re.sub(r',\s*\)', ')', clean_body)
    clean_body = re.sub(r'\(\s*,', '(', clean_body)
    
    # Remove extra blank lines
    clean_body = '\n'.join(line for line in clean_body.split('\n') if line.strip())
    
    service_lines.append(f'def {func_name}({", ".join(clean_params)}):')
    service_lines.append('    """Migrated from admin_treasury.py endpoint."""')
    for line in clean_body.split('\n'):
        service_lines.append(f'    {line}')
    service_lines.append('')
    service_lines.append('')
    count += 1

with open('backend/services/treasury/treasury_service_migration.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(service_lines))

print(f'Generated migration service with {count} functions')
