import os, tempfile

def patch(path, repls):
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    for a, b in repls:
        assert a in s, "NOT FOUND in %s: %r" % (path, a)
        s = s.replace(a, b)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(s)
    os.replace(tmp, path)
    print("patched", path)

root = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# 1. country shims -> correct geography module
patch(os.path.join(root, "models/country/country_legal.py"), [
    ("re-export from models.geography.country_legals", "re-export from models.geography.country_legal"),
    ("from models.geography.country_legals import *", "from models.geography.country_legal import *"),
])
patch(os.path.join(root, "models/country/country_tax.py"), [
    ("re-export from models.geography.country_taxes", "re-export from models.geography.country_tax"),
    ("from models.geography.country_taxes import *", "from models.geography.country_tax import *"),
])
# 2. data/orm_models
patch(os.path.join(root, "data/orm_models.py"), [
    ("from models.security.permissions_json import *", "from models.security.permissions import *"),
])
# 3. controllers/admin_controller
patch(os.path.join(root, "controllers/admin_controller.py"), [
    ("from controllers.security.permissions_json import (", "from controllers.security.permissions import ("),
])
# 4. tests/conftest
patch(os.path.join(root, "tests/conftest.py"), [
    ("import models.security.permissions_json", "import models.security.permissions"),
])
# 5. models/__init__.py shim registry (module paths)
patch(os.path.join(root, "models/__init__.py"), [
    ('"country_taxes": "country.country_taxes",', '"country_taxes": "country.country_tax",'),
    ('("security", ("permissions_json", "incident", "fraud")),', '("security", ("permissions", "incident", "fraud")),'),
    ('"country_legals", "country_taxes")),', '"country_legal", "country_tax")),'),
])
print("ALL PATCHED")
