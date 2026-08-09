files=['backend/models/admin.py','backend/models/commission.py','backend/models/country_control.py','backend/models/logistics.py','backend/models/orders.py','backend/models/payments.py','backend/models/permissions.py','backend/models/products.py','backend/models/user.py']
for f in files:
    p=__import__('pathlib').Path(f)
    t=p.read_text(encoding='utf-8')
    new=t.replace('country_configs.code','country.country_configs.code')
    if new!=t:
        p.write_text(new, encoding='utf-8')
        print('updated', f, t.count('country_configs.code'))