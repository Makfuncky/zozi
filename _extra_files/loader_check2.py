import re, os
src = open('main.py', encoding='utf-8').read()
m = re.search(r'router_names\s*=\s*\[(.*?)\]', src, re.S)
names = re.findall(r'\(\s*"([^"]+)"', m.group(1))
real = [n for n in names if os.path.exists('routers/%s.py' % n)]
print('REAL declared routers (exist):')
for n in real: print('  ', n)
print()
print('All router .py files on disk:')
for f in sorted(os.listdir('routers')):
    if f.endswith('.py') and f!='__init__.py':
        print('  ', f[:-3])
