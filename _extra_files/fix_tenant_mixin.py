repo = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
p2 = repo + r"\models\mixins.py"
s2 = open(p2, encoding="utf-8").read()

old_import = "from sqlalchemy import Column, Integer, String, Boolean\nfrom utils.datetime_utils import utcnow as utcnow\n"
new_import = ("from sqlalchemy import Column, Integer, String, Boolean\n"
             "from db.mixins import VersionMixin\n"
             "from utils.datetime_utils import utcnow as utcnow\n")
assert old_import in s2, "old_import not found"
s2 = s2.replace(old_import, new_import, 1)

assert "class TenantMixin:" in s2
s2 = s2.replace("class TenantMixin:", "class TenantMixin(VersionMixin):", 1)

# version line may or may not have a trailing newline (EOF)
old_ver = "    is_active = Column(Boolean, default=True, nullable=False, index=True)\n    version = Column(Integer, nullable=False, default=1)"
assert old_ver in s2, "old_ver not found"
s2 = s2.replace(old_ver, "    is_active = Column(Boolean, default=True, nullable=False, index=True)")

open(p2, "w", encoding="utf-8").write(s2)
print("models/mixins.py updated")
