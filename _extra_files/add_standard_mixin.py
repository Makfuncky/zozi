import os, sys, tempfile

p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models\mixins.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old_import = "from db.mixins import VersionMixin"
new_import = "from db.mixins import AuditMixin, SoftDeleteMixin, VersionMixin"
assert old_import in s, "import line not found"
s = s.replace(old_import, new_import, 1)

standard = '''

class StandardMixin(AuditMixin, SoftDeleteMixin, TenantMixin):
    """Canonical composition for country-scoped tables.

    Combines AuditMixin (created/updated stamps + actors), SoftDeleteMixin
    (is_deleted + reason), and TenantMixin (country isolation, uuid, version).
    Use for country-scoped business entities. For global-only entities use
    ``AuditMixin + SoftDeleteMixin`` directly.
    """
    __abstract__ = True
'''
assert "class StandardMixin" not in s, "StandardMixin already exists"
s = s.rstrip("\n") + "\n" + standard

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(s)
os.replace(tmp, p)
print("models/mixins.py updated with StandardMixin")
