import json
with open("database_audit_fresh.json") as f:
    rep = json.load(f)
db06 = [f for f in rep["findings"] if f["code"] == "DB06"]
for f in db06:
    print(f"{f['sev']} {f['code']} {f['path']}:{f.get('line','?')} - {f['message']}")
print(f"\nTotal DB06: {len(db06)}")
