import io, re

repo = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# ---- db/mixins.py ----
p1 = repo + r"\db\mixins.py"
s1 = open(p1, encoding="utf-8").read()

# 1) Add VersionMixin right after the imports block (before AuditMixin)
version_mixin = '''class VersionMixin:
    """Optimistic-lock revision counter (Constitution §2.9).

    Extracted so AuditMixin and TenantMixin no longer define a duplicate
    ``version`` column (which collided when both were composed on one model).
    """

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(
            Integer, nullable=False, default=1, server_default="1"
        )


'''
assert "class VersionMixin:" not in s1
anchor = "class AuditMixin:"
assert anchor in s1
s1 = s1.replace(anchor, version_mixin + anchor, 1)

# 2) Remove version from AuditMixin
old_version = '''    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=1, server_default="1")


'''
assert old_version in s1
s1 = s1.replace(old_version, "")
open(p1, "w", encoding="utf-8").write(s1)
print("db/mixins.py updated")

# ---- models/mixins.py ----
p2 = repo + r"\models\mixins.py"
s2 = open(p2, encoding="utf-8").read()

# import VersionMixin from db.mixins
old_import = "from sqlalchemy import Column, Integer, String, Boolean\nfrom utils.datetime_utils import utcnow as utcnow\n"
new_import = ("from sqlalchemy import Column, Integer, String, Boolean\n"
             "from db.mixins import VersionMixin\n"
             "from utils.datetime_utils import utcnow as utcnow\n")
assert old_import in s2
s2 = s2.replace(old_import, new_import, 1)

# TenantMixin inherits VersionMixin, drop its own version Column
old_cls = '''class TenantMixin:'''
assert old_cls in s2
s2 = s2.replace(old_cls, "class TenantMixin(VersionMixin):", 1)

old_ver = "    is_active = Column(Boolean, default=True, nullable=False, index=True)\n    version = Column(Integer, nullable=False, default=1)\n"
assert old_ver in s2
s2 = s2.replace(old_ver, "    is_active = Column(Boolean, default=True, nullable=False, index=True)\n", 1)

open(p2, "w", encoding="utf-8").write(s2)
print("models/mixins.py updated")
