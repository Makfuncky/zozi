import re, collections

txt = open("scripts/layer_audit_report.txt", encoding="utf-8").read()
cur = None
files = collections.Counter()
rule_files = collections.defaultdict(collections.Counter)
for ln in txt.splitlines():
    m = re.match(r"(V\d_\w+)\s+\((\d+)", ln)
    if m:
        cur = m.group(1)
        continue
    if cur in (None, "V7_SERVICE_DB_WRITE"):
        continue
    fm = re.match(r"\s+(?:\[(\w+)\])?\s*([\w/\\]+\.py):?(\d+)?", ln)
    if fm and fm.group(2):
        rule_files[cur][fm.group(2)] += 1

for rule in sorted(rule_files):
    fs = rule_files[rule]
    print(f"\n=== {rule}  (unique files {len(fs)}) ===")
    for f, c in sorted(fs.items()):
        print(f"  {c:3d}  {f}")
