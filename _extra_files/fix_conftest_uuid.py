repo = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
p = repo + r"\tests\conftest.py"
s = open(p, encoding="utf-8").read()
old = "                column.type = Uuid(native=False)"
new = "                column.type = Uuid(native_uuid=False)"
assert old in s, "Uuid(native=False) not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("conftest.py updated: Uuid native -> native_uuid")
