import decompyle3, pkgutil
print("submodules:", [m.name for m in pkgutil.iter_modules(decompyle3.__path__)])
import inspect
for cand in ["api","main","code_deparse","decompile","disas"]:
    mod = getattr(decompyle3, cand, None)
    if mod is not None:
        print(cand, "->", type(mod))
