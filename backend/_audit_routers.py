import sys, importlib, traceback
sys.path.insert(0, '.')

routers = [
    'routers.auth','routers.users','routers.products','routers.categories',
    'routers.cart','routers.orders','routers.payments','routers.shipments',
    'routers.reviews','routers.wishlist','routers.notifications','routers.coupons',
    'routers.flash_sales','routers.tickets','routers.returns',
    'routers.admin_users','routers.admin_products','routers.admin_orders',
    'routers.admin_banners','routers.admin_cash','routers.admin_commission',
    'routers.admin_email','routers.admin_logistics','routers.admin_payouts',
    'routers.supplier_products','routers.logistics_orders','routers.logistics_partner',
    'routers.supplier_profile','routers.search','routers.reports','routers.dashboard',
]

ok = []
failures = {}
for r in routers:
    try:
        importlib.import_module(r)
        ok.append(r)
    except Exception as e:
        tb = traceback.format_exc()
        # Get the most specific line
        lines = [l for l in tb.splitlines() if 'ImportError' in l or 'cannot import' in l or 'NameError' in l or 'AttributeError' in l]
        failures[r] = lines[-1] if lines else str(e)

print(f'=== OK ({len(ok)}) ===')
for r in ok:
    print(f'  {r}')
print()
print(f'=== FAILED ({len(failures)}) ===')
for r, e in failures.items():
    print(f'  {r}:\n    {e}')

