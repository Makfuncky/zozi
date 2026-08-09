import os, tempfile
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models\geography\__init__.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()
s = s.replace("from .country_legals import *", "from .country_legal import *")
s = s.replace("from .country_taxes import *", "from .country_tax import *")
assert "country_legals" not in s
assert "country_taxes" not in s
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(s)
os.replace(tmp, p)
print("geography/__init__.py fixed")
