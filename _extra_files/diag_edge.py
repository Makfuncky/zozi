import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper
targets = ["EventDeadLetter","EventRetryQueue","InboxEvent","OutboxEvent"]
for t in targets:
    cls = getattr(models, t, None)
    if cls is None:
        # search
        for name in dir(models):
            if name.lower() == t.lower():
                cls = getattr(models, name); break
    if cls is None:
        print(t, "NOT FOUND"); continue
    print("==", t, "module=", cls.__module__, "bases=", [b.__name__ for b in cls.__bases__])
    cols = [c.name for c in cls.__table__.columns]
    print("   cols:", cols)
