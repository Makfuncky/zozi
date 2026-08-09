import os, re, tempfile
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models\geography\__init__.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()
s2 = re.sub(r"from \.country_taxes import \*", "from .country_tax import *", s)
print("changed:", s2 != s)
print(repr(s2))
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(s2)
os.replace(tmp, p)
print("done")
