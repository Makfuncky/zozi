import sys, importlib, os
os.chdir(r'F:\recovery_recuva_4\Projects\10- E-COMMERCE WEBSITE\zozi\backend')
sys.path.insert(0, r'F:\recovery_recuva_4\Projects\10- E-COMMERCE WEBSITE\zozi\backend')
routers = ['auth','users','products','categories','cart','orders','payments','shipments','reviews','wishlist','addresses','notifications','coupons','banners','flash_sales','tickets','returns','search','upload','referrals','chatbot','ai_image','currency','email','translate','public_suppliers','product_verification','supplier','supplier_profile','supplier_products','supplier_orders','supplier_payouts','supplier_documents','supplier_analytics','logistics','logistics_orders','logistics_partner','admin','admin_users','admin_products','admin_orders','admin_analytics','admin_banners','admin_cash','admin_commission','admin_email','admin_logistics','admin_payouts','admin_settings']
ok=0; fail=0
for r in routers:
    try:
        importlib.import_module('routers.' + r)
        print('OK: ' + r)
        ok+=1
    except Exception as e:
        print('FAIL: ' + r + ' -- ' + type(e).__name__ + ': ' + str(e)[:150])
        fail+=1
print(f'SUMMARY: {ok} ok, {fail} failed')

