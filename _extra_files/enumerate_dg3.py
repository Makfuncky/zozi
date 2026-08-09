import importlib.util
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
SPEC = importlib.util.spec_from_file_location(
    "arch_audit", REPO / "scripts/system_trackers/system_architecture_audit.py"
)
m = importlib.util.module_from_spec(SPEC)
import sys
sys.modules["arch_audit"] = m
SPEC.loader.exec_module(m)

eff = m.load_rules(REPO, None)
graph = m.build_module_graph(REPO, eff)
rep = m.Report()
m.check_dependency_graph(REPO, rep, eff, graph)

dg3 = [f for f in rep.findings if f.code == "DG3"]
print(f"TOTAL DG3 findings: {len(dg3)}")
pairs = set()
for f in dg3:
    # message: "cross-domain import {sd} -> {td} violates explicit ownership rules"
    msg = f.message
    print(f"  {f.path}:{f.line}  {msg}")
    parts = msg.split("cross-domain import ")[-1].split(" violates")[0]
    sd, td = parts.split(" -> ")
    pairs.add((sd, td))

print("\nUNIQUE (caller_domain -> target_domain) edges to whitelist:")
for sd, td in sorted(pairs):
    print(f"  {sd} -> {td}")
