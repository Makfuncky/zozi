from sqlalchemy import create_engine, text
e = create_engine('postgresql://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb?sslmode=require')
with e.connect() as c:
    r = c.execute(text("SELECT to_regclass('catalog.products'), to_regclass('suppliers.suppliers'), to_regclass('customers.customers')"))
    print('catalog.products / suppliers.suppliers / customers.customers:', r.fetchone())
