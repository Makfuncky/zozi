import importlib.util, sys
from pathlib import Path

SRC = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\migration_tracker.py"
spec = importlib.util.spec_from_file_location("mt_verify", SRC)
mt = importlib.util.module_from_spec(spec)
sys.modules["mt_verify"] = mt
spec.loader.exec_module(mt)

class Fake:
    def __init__(self, p):
        self.path = Path(p)

paths = [ln.strip() for ln in Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt").read_text().splitlines()
         if ln.strip() and ln.strip().endswith(".py")]
svcs = [Fake(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\app\services" / Path(p)) for p in paths]
print("raw files:", len(svcs))
print("engine realistic_target (_distinct_service_concept_count):", mt._distinct_service_concept_count(svcs))
