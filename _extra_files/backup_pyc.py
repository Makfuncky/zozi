import os, shutil
cache = "scripts/system_trackers/__pycache__"
os.makedirs("_extra_files/pyc_backup", exist_ok=True)
for n in ["system_architecture_audit","database_audit","design_audit","health_audit"]:
    src = os.path.join(cache, n+".cpython-310.pyc")
    dst = os.path.join("_extra_files/pyc_backup", n+".cpython-310.pyc")
    shutil.copy(src, dst)
print("backed up pyc")
