import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper

REQ = ["uuid","created_at","updated_at","is_deleted","deleted_at","version","created_by","updated_by"]

def all_subclasses(cls):
    out = set()
    stack = list(cls.__subclasses__())
    while stack:
        c = stack.pop()
        if c in out: continue
        out.add(c)
        stack.extend(c.__subclasses__())
    return out

models_set = set()
for c in all_subclasses(models.Base):
    try:
        class_mapper(c)
    except Exception:
        continue
    if hasattr(c, "__tablename__") and c.__tablename__:
        models_set.add(c)

viol = []
for c in sorted(models_set, key=lambda x: x.__tablename__):
    cols = set(col.name for col in c.__table__.columns)
    missing = [x for x in REQ if x not in cols]
    if missing:
        viol.append((c.__tablename__, c.__module__, c.__name__, missing))

print("TOTAL MODELS:", len(models_set))
print("DBA03 VIOLATIONS (current code):", len(viol))
for t, mod, name, missing in viol:
    print("%-32s %-22s missing=%s" % (t, name, missing))
