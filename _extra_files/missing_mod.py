import os, sys, importlib, traceback, collections
sys.path.insert(0, os.path.abspath('.'))
files = [f for f in os.listdir('routers') if f.endswith('.py') and f!='__init__.py']
missing = collections.Counter()
for f in sorted(files):
    mod='routers.'+f[:-3]
    try:
        importlib.import_module(mod)
    except Exception as e:
        msg=str(e)
        if 'No module named' in msg:
            # extract the missing name
            import re
            mm=re.search(r"No module named '([^']+)'", msg)
            if mm: missing[mm.group(1)]+=1
print('=== Missing modules referenced by routers (count of routers that fail because of it) ===')
for name,c in missing.most_common():
    print('  %-45s %d'%(name,c))
