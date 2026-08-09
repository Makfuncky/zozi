import importlib.util
for m in ["uncompyle6","decompyle3","pycdc","xdis"]:
    try:
        importlib.import_module(m); print("HAVE", m)
    except Exception as e:
        print("no", m)
import sys
print("python", sys.version.split()[0])
