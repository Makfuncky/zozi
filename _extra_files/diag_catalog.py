import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from models.mixins import TenantMixin, StandardMixin, AuditMixin, SoftDeleteMixin, CreatedByMixin
from db.mixins import VersionMixin

DBA03 = ["uuid","created_at","updated_at","is_deleted","deleted_at","created_by","updated_by","version","country_code","is_active"]

def bases_name(m):
    return [b.__name__ for b in m.__bases__]

import importlib, inspect
from models import catalog
mods = [catalog.products, catalog.ai_upload]
for mod in mods:
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, models.Base) and obj.__module__ in ("models.catalog.products","models.catalog.ai_upload"):
            cols = set(c.name for c in obj.__table__.columns)
            present = [c for c in DBA03 if c in cols]
            missing = [c for c in DBA03 if c not in cols]
            print("%-22s table=%-26s bases=%s" % (obj.__name__, obj.__tablename__, bases_name(obj)))
            print("    present : %s" % present)
            print("    missing : %s" % missing)
