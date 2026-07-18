"""One-off script to complete the partial cash management migration."""
from db.database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_city VARCHAR(120)"))
    conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_country VARCHAR(120)"))
    conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_postal_code VARCHAR(40)"))
    conn.execute(text("UPDATE alembic_version SET version_num = '79b533c27897' WHERE version_num = 'z9a0b1c2d3e4'"))
    print("Done: columns added and alembic stamped to 79b533c27897")

