"""Diagnose and list all accounts domain problems."""
import sys, os, importlib
sys.path.insert(0, '.')

accounts_root = os.path.join('domains', 'accounts')
failed = []
passed = 0

for root, dirs, files in os.walk(accounts_root):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fn in files:
        if not fn.endswith('.py') or fn == '__init__.py': continue
        rel = os.path.relpath(os.path.join(root, fn), 'domains/accounts')[:-3].replace(os.sep, '.')
        mod = f'domains.governance.{rel}'
        try:
            importlib.import_module(mod)
            passed += 1
        except Exception as e:
            failed.append((mod, str(e)))

print(f'Accounts: {passed} OK, {len(failed)} FAIL')
print()

# Group by error type
from collections import defaultdict
by_error = defaultdict(list)
for mod, err in failed:
    # Extract the core error
    if 'cannot import name' in err:
        key = err.split(':')[0] + ': ' + err.split('cannot import name')[1].split('from')[0].strip()
    elif 'already defined' in err:
        key = 'Table already defined: ' + err.split('Table \'')[1].split('\'')[0]
    elif 'No module named' in err:
        key = 'No module named: ' + err.split('No module named')[1].strip()
    elif 'unexpected indent' in err:
        key = 'Indentation error'
    else:
        key = err[:60]
    by_error[key].append(mod)

for error, mods in sorted(by_error.items(), key=lambda x: -len(x[1])):
    print(f'[{len(mods)} modules] {error}')
    for m in mods[:5]:
        print(f'  - {m}')
    if len(mods) > 5:
        print(f'  ... and {len(mods) - 5} more')
    print()
