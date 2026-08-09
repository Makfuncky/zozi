import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
sys.path.insert(0, str(ROOT / "scripts" / "system_trackers"))
import system_architecture_audit as A

class FakeReport:
    def __init__(self):
        self.findings = []
        self.counters = {}
    def add(self, sev, code, domain, path, message, intended="", line=None, priority=None, count=1, examples=None):
        self.findings.append((sev, code, domain, path, line, message))
        self.counters[code] = self.counters.get(code, 0) + count

rep = FakeReport()
eff = {"write_verbs": set(A.DEFAULT_WRITE_VERBS), "read_verbs": set(A.DEFAULT_READ_VERBS)}
# Point repo at backend only by limiting? check_layer_writes scans backend/routers etc.
# We instead call the inner scan manually by replicating the loop but only for admin_users.
# Simpler: monkeypatch is hard; just run full check_layer_writes and filter.
A.check_layer_writes(ROOT, rep, eff)

w1 = [(f) for f in rep.findings if f[1] == "W1"]
print("TOTAL W1 findings:", len(w1))
from collections import Counter
by_file = Counter(f[3] for f in w1)
for path, c in sorted(by_file.items()):
    print(f"  {c:3d}  {path}")
