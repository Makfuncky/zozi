import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only'

from db.base import Base as DbBase
import models
from models import Base as ModelsBase

print(f"db.base.Base is models.Base: {DbBase is ModelsBase}")
print(f"db.base.Base id: {id(DbBase)}")
print(f"models.Base id: {id(ModelsBase)}")

print(f"\nmodels.Base.metadata tables: {len(models.Base.metadata.tables)}")
print(f"db.base.Base.metadata tables: {len(DbBase.metadata.tables)}")

if len(ModelsBase.metadata.tables) > 0:
    print("\nFirst 10 tables from models.Base.metadata:")
    for key in sorted(ModelsBase.metadata.tables.keys())[:10]:
        t = ModelsBase.metadata.tables[key]
        print(f"  key={repr(key)}, name={repr(t.name)}, schema={repr(t.schema)}")
