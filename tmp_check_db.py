from sqlalchemy import create_engine, text

url = "postgresql+psycopg2://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb"
e = create_engine(url)
with e.connect() as c:
    r = c.execute(
        text("SELECT COUNT(*) FROM users WHERE email LIKE :a OR email LIKE :b OR email LIKE :c"),
        {"a": "E2eAdmin%", "b": "E2eCustomer%", "c": "E2eFixture%"},
    )
    print("account rows:", r.scalar())
    r = c.execute(text("SELECT email, role, name FROM users WHERE email LIKE :v ORDER BY id"), {"v": "E2e%"})
    for row in r:
        print(row)
