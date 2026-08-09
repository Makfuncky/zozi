import sys, os, re, io
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper
import inspect

REQ = ["uuid","created_at","updated_at","is_deleted","deleted_at","version","created_by","updated_by"]

def all_subclasses(cls):
    out=set(); stack=list(cls.__subclasses__())
    while stack:
        c=stack.pop()
        if c in out: continue
        out.add(c); stack.extend(c.__subclasses__())
    return out

targets=[]
for c in all_subclasses(models.Base):
    try: class_mapper(c)
    except Exception: continue
    if not getattr(c,"__tablename__",None): continue
    cols=set(col.name for col in c.__table__.columns)
    missing=[x for x in REQ if x not in cols]
    if missing==["version"]:
        targets.append(c)

print("PATCH CANDIDATES:", len(targets))
by_file={}
for c in targets:
    fn=inspect.getsourcefile(c)
    lineno=inspect.getsourcelines(c)[1]
    by_file.setdefault(fn,[]).append((c.__name__, lineno))

for fn, items in sorted(by_file.items()):
    print("\nFILE:", fn)
    for name,ln in items:
        print("   line %d: %s" % (ln, name))
