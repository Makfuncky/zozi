import re, os
src = open('main.py', encoding='utf-8').read()
m = re.search(r'router_names\s*=\s*\[(.*?)\]', src, re.S)
names = re.findall(r'\(\s*"([^"]+)"', m.group(1))
real = [n for n in names if os.path.exists('routers/%s.py' % n)]
miss = [n for n in names if not os.path.exists('routers/%s.py' % n)]
print('declared in loader:', len(names))
print('REAL files:', len(real))
print('PHANTOM (no file):', len(miss))
print('--- PHANTOM ---')
print(', '.join(miss))
