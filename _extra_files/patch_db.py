import io
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\db\database.py"
s = open(p, encoding="utf-8").read()
old = """pool_size = 20
max_overflow = 30
pool_recycle = 1800
pool_timeout = 10
db_statement_timeout = 60000
POOL_SIZE = pool_size
MAX_OVERFLOW = max_overflow
POOL_RECYCLE = pool_recycle
POOL_TIMEOUT = pool_timeout
DB_STATEMENT_TIMEOUT = db_statement_timeout"""
new = """# Pool tuning is sourced from environment-backed settings (no hardcoded values).
# Override via DB_POOL_SIZE / DB_MAX_OVERFLOW / DB_POOL_RECYCLE / DB_CONNECT_TIMEOUT /
# DB_STATEMENT_TIMEOUT. Defaults are conservative for a direct Postgres connection;
# lower them (e.g. 5/10) when running behind PgBouncer / a connection proxy.
POOL_SIZE = int(getattr(settings, "db_pool_size", 20))
MAX_OVERFLOW = int(getattr(settings, "db_max_overflow", 30))
POOL_RECYCLE = int(getattr(settings, "db_pool_recycle", 1800))
POOL_TIMEOUT = int(getattr(settings, "db_connect_timeout", 10))
DB_STATEMENT_TIMEOUT = int(getattr(settings, "db_statement_timeout", 60000))"""
assert old in s, "OLD BLOCK NOT FOUND"
open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("patched database.py")
