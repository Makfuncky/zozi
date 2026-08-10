import os, sys, traceback
sys.path.insert(0, os.path.abspath('.'))
import importlib
files = [f for f in os.listdir('routers') if f.endswith('.py') and f!='__init__.py']
files.sort()
bad=[]
for f in files:
    mod='routers.'+f[:-3]
    try:
        importlib.import_module(mod)
    except Exception as e:
        tb=traceback.extract_tb(e.__traceback__)
        last=tb[-1] if tb else None
        where = ('%s:%s'%(last.filename.split('backend')[-1], last.lineno)) if last else '?'
        bad.append((mod, type(e).__name__, str(e).split(chr(10))[0][:90], where))
print('total router files:', len(files))
print('IMPORT FAILURES:', len(bad))
for mod,typ,msg,where in bad:
    print('  FAIL %-55s %-22s %s | %s'%(mod, typ, msg, where))
