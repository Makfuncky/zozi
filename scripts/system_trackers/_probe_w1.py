import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import system_architecture_audit as A

repo = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
rep = A.Report()
eff: dict = {}
A.check_layer_writes(repo, rep, eff)
w1 = [f for f in rep.findings if f.code == "W1"]
print("W1 count:", len(w1))
for f in w1:
    print(f.loc(), f.message)
