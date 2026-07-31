import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only'

from db.base import Base
import models

metadata = Base.metadata

print("Tables in metadata:")
for key in sorted(metadata.tables.keys()):
    t = metadata.tables[key]
    print(f"  key={repr(key)}, name={repr(t.name)}, schema={repr(t.schema)}")
