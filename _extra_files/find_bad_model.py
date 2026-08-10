import glob
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "backend"))

import models

base = models.__path__[0]
for path in sorted(glob.glob(base + "/**/*.py", recursive=True)):
    if "__pycache__" in path or path.endswith("__init__.py"):
        continue
    rel = path[len(base) + 1 : -3].replace(os.sep, ".")
    try:
        importlib.import_module("models." + rel)
    except Exception as e:
        print(f"FAIL {rel}: {type(e).__name__}: {e}")
        break
else:
    print("ALL MODEL MODULES IMPORT OK")
