import os
from decompyle3.api import decompile_file
cache = "scripts/system_trackers/__pycache__"
out = "scripts/system_trackers"
names = ["system_architecture_audit","database_audit","design_audit","health_audit"]
for n in names:
    pyc = os.path.join(cache, n + ".cpython-310.pyc")
    outp = os.path.join(out, n + ".py")
    with open(outp, "w", encoding="utf-8") as f:
        decompile_file(pyc, f)
    print("wrote", outp, os.path.getsize(outp), "bytes")
