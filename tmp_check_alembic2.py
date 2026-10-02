from sqlalchemy import create_engine, text

url = "postgresql+psycopg2://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb"
e = create_engine(url)
with e.connect() as c:
    r = c.execute(text("SELECT * FROM alembic_version"))
    print("columns:", r.keys())
    for row in r:
        print(row)
