import re
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\accounts\services\auth\auth_service.py"
s = open(p, encoding="utf-8").read()
# Add a default of None to any getattr(user, "x") that lacks a 3rd argument.
pat = re.compile(r'getattr\(user,\s*"([^"]+)"\s*\)')
new, n = pat.subn(r'getattr(user, "\1", None)', s)
open(p, "w", encoding="utf-8").write(new)
print("patched", n, "getattr calls")
# show remaining getattr(user, ...) without default (should be 0)
import re as r2
left = r2.findall(r'getattr\(user,\s*"[^"]+"\s*\)', new)
print("remaining unguarded:", len(left))
