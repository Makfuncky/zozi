import re

with open('backend/routers/admin_treasury.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

endpoints = []
i = 0
while i < len(lines):
    line = lines[i]
    if re.match(r'\s*@router\.(get|post|put|patch|delete)\(', line):
        decorator_match = re.match(r'\s*@router\.(get|post|put|patch|delete)\(([^)]+)\)', line)
        method = decorator_match.group(1)
        path = decorator_match.group(2)
        
        j = i + 1
        func_name = None
        sig = None
        while j < len(lines):
            stripped = lines[j].strip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                sig_lines = [stripped]
                k = j + 1
                while k < len(lines):
                    sig_lines.append(lines[k].strip())
                    if '):' in lines[k]:
                        break
                    k += 1
                full_sig = ' '.join(sig_lines)
                func_match = re.match(r'(async )?def (\w+)\((.*)\):', full_sig)
                if func_match:
                    func_name = func_match.group(2)
                    sig = func_match.group(3)
                break
            j += 1
        
        if func_name:
            k = j + 1
            while k < len(lines):
                stripped = lines[k].strip()
                if stripped.startswith('@router.'):
                    break
                k += 1
            body = ''.join(lines[j+1:k])
            endpoints.append({
                'method': method,
                'path': path,
                'func_name': func_name,
                'sig': sig,
                'body': body,
            })
            i = k
            continue
    i += 1

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

for ep in endpoints:
    body = ep['body']
    # Remove db: Session = Depends(get_db)
    body = re.sub(r'db: Session = Depends\(get_db\)\s*', '', body)
    # Remove current_user: dict = Depends(require_treasury_access)
    body = re.sub(r'current_user: dict = Depends\(require_treasury_access\)\s*', '', body)
    # Remove Depends(require_treasury_access)
    body = re.sub(r'Depends\(require_treasury_access\)\s*', '', body)
    # Clean up double commas and parens
    body = re.sub(r',\s*\)', ')', body)
    body = re.sub(r'\(\s*,', '(', body)
    
    # Remove extra blank lines
    body_lines = [line for line in body.split('\n') if line.strip()]
    clean_body = '\n'.join(body_lines)
    
    # Clean signature
    sig = ep['sig']
    params = sig.split(',')
    clean_params = []
    for p in params:
        p = p.strip()
        if not p:
            continue
        if 'Depends' in p or 'FastAPIBody' in p or p.startswith('current_user') or p.startswith('db:'):
            continue
        clean_params.append(p)
    
    service_lines.append(f'def {ep["func_name"]}({", ".join(clean_params)}):')
    service_lines.append('    """Migrated from admin_treasury.py endpoint."""')
    for line in clean_body.split('\n'):
        service_lines.append(f'    {line}')
    service_lines.append('')
    service_lines.append('')

with open('backend/services/treasury/treasury_service_migration.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(service_lines))

print(f'Generated migration service with {len(endpoints)} functions')
