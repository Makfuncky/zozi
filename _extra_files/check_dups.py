import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper
def allsub(cls):
    out=set(); st=list(cls.__subclasses__())
    while st:
        c=st.pop()
        if c in out: continue
        out.add(c); st.extend(c.__subclasses__())
    return out
dups=0
for c in allsub(models.Base):
    try: class_mapper(c)
    except Exception: continue
    if not getattr(c,"__tablename__",None): continue
    names=[col.name for col in c.__table__.columns]
    seen=set(); 
    for n in names:
        if n in seen:
            print("DUP", c.__tablename__, n); dups+=1
        seen.add(n)
print("duplicate columns found:", dups)
