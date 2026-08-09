import subprocess, os
cache = "scripts/system_trackers/__pycache__"
out = "scripts/system_trackers"
names = ["system_architecture_audit","database_audit","design_audit","health_audit"]
for n in names:
    pyc = os.path.join(cache, n + ".cpython-310.pyc")
    print("decompiling", n)
    r = subprocess.run(["python","-m","decompyle3","-o",out,pyc], capture_output=True, text=True)
    print("  rc", r.returncode, r.stderr[-300:])
