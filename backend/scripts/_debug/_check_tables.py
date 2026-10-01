from sqlalchemy import create_engine, text
e = create_engine('postgresql://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb?sslmode=require')
with e.connect() as c:
    r = c.execute(text("SELECT to_regclass('comms.internal_messages')"))
    print('comms.internal_messages:', r.scalar())
    r = c.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name='internal_messages'"))
    rows = list(r)
    for row in rows:
        print('Found:', row)
    r = c.execute(text("SELECT to_regclass('public.alembic_version')"))
    print('alembic_version:', r.scalar())
    r = c.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"))
    print('Total tables in DB:', r.scalar())
