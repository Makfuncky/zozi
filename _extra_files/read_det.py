import os
p = os.path.join("scripts","system_trackers","database_audit.py")
print("exists:", os.path.exists(p))
if os.path.exists(p):
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(900, 1000):
        if i < len(lines):
            print(i, lines[i])
