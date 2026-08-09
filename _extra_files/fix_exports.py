import os, re, tempfile
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models\_exports.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()
repls = [
    ("from .security.permissions_json import *", "from .security.permissions import *"),
    ("from .country.country_legals import *", "from .country.country_legal import *"),
    ("from .country.country_taxes import *", "from .country.country_tax import *"),
]
for a, b in repls:
    assert a in s, "not found: " + a
    s = s.replace(a, b)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(s)
os.replace(tmp, p)
print("_exports.py fixed")
