p = r"backend\models\catalog\products.py"
s = open(p, encoding="utf-8").read()

repls = [
    ('        Index("ix_po_country", "country_code"), {"schema": "trading"})',
     '        Index("ix_po_country", "country_code"),\n'
     '        Index("ix_purchase_orders_country_created", "country_code", "created_at"),\n'
     '        {"schema": "trading"})'),
    ('        Index("ix_so_country", "country_code"), {"schema": "trading"})',
     '        Index("ix_so_country", "country_code"),\n'
     '        Index("ix_sales_orders_country_created", "country_code", "created_at"),\n'
     '        {"schema": "trading"})'),
    ('        Index("ix_trade_deals_country", "country_code"), {"schema": "finance"})',
     '        Index("ix_trade_deals_country", "country_code"),\n'
     '        Index("ix_trade_deals_country_created", "country_code", "created_at"),\n'
     '        {"schema": "finance"})'),
]
for old, new in repls:
    assert old in s, f"anchor missing: {old!r}"
    s = s.replace(old, new, 1)

open(p, "w", encoding="utf-8").write(s)
print("OK: added DBA31 composites to PurchaseOrder, SalesOrder, TradeDeal")
