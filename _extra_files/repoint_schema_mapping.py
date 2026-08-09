import json

p = "schema_mapping.json"
s = open(p, encoding="utf-8").read()
old = '"models.communication"'
new = '"models.comms.communication"'
n = s.count(old)
s2 = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s2)
json.loads(s2)
print("replaced", n, "occurrences; JSON valid")
