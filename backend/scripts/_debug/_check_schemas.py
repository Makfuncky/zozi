import main
from lifespan import _preload_all_models
_preload_all_models()
from infrastructure.database.base import Base
from infrastructure.database.database import engine
from sqlalchemy import text
schemas = set()
for t in Base.metadata.tables.values():
    schemas.add(t.schema)
print('Schemas in ORM:', sorted(s for s in schemas if s))
print('Total tables:', len(Base.metadata.tables))
with engine.connect() as c:
    rows = c.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast') ORDER BY 1"))
    print('Schemas in DB:', [r[0] for r in rows])
