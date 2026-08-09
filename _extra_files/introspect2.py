import inspect, decompyle3
print("code_deparse:", inspect.signature(decompyle3.code_deparse))
import decompyle3.main as m
print("main funcs:", [n for n in dir(m) if not n.startswith("_")])
if hasattr(m,"decompile_file"):
    print("decompile_file sig:", inspect.signature(m.decompile_file))
