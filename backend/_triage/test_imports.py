import os, sys, importlib, re, traceback

os.environ['SECRET_KEY'] = 'test_secret_key_for_dev_only_1234567890'
os.environ['ENVIRONMENT'] = 'development'

with open('main.py', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'router_names\s*=\s*\[(.*?)\]', content, re.DOTALL)
names = re.findall(r'"([^"]+)"', match.group(1))
print(f'Total router_names entries: {len(names)}')

failed = []
ok = 0
for name in names:
    try:
        importlib.import_module(f'routers.{name}')
        ok += 1
    except Exception:
        try:
            importlib.import_module(f'controllers.{name}')
            ok += 1
        except Exception as e:
            failed.append((name, str(e)[:200]))

print(f'Successfully loaded: {ok}/{len(names)}')
if failed:
    print('FAILED:')
    for name, emsg in failed:
        print(f'  {name}: {emsg}')
else:
    print('ALL ROUTERS LOADED SUCCESSFULLY!')
