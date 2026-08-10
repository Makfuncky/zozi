import sys, traceback, importlib
sys.path.insert(0, r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend')
mods = 'routers.public_treasury_api_access','routers.public_treasury_cash_position','routers.public_treasury_operations','routers.public_treasury_payments','routers.admin_treasury_identity','routers.admin_treasury_reporting','routers.admin_treasury_status','routers.supplier_payouts'
for m in ['routers.public_treasury_api_access','routers.public_treasury_cash_position','routers.public_treasury_operations','routers.public_treasury_payments','routers.admin_treasury_identity','routers.admin_treasury_reporting','routers.admin_treasury_status','routers.supplier_payouts']:
    try:
        importlib.import_module(m)
        print('OK  ', m)
    except Exception as e:
        print('FAIL', m, '->', type(e).__name__, e)
