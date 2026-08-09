import sys, os, json
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper

REQ = ["created_at","updated_at","is_deleted","deleted_at","version","created_by","updated_by","uuid"]
def all_subclasses(cls):
    out=set(); stack=list(cls.__subclasses__())
    while stack:
        c=stack.pop()
        if c in out: continue
        out.add(c); stack.extend(c.__subclasses__())
    return out
rows=[]
for c in all_subclasses(models.Base):
    try: class_mapper(c)
    except Exception: continue
    if not getattr(c,"__tablename__",None): continue
    cols=set(col.name for col in c.__table__.columns)
    if "version" not in cols:
        schema=c.__table__.schema
        rows.append((schema, c.__tablename__))
rows=sorted(set(rows))
print(json.dumps(rows))
