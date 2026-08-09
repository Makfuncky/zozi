src = open('scripts/system_trackers/system_architecture_audit.py', encoding='utf-8', errors='replace').read()
import re
for kw in ['RED', 'YEL']:
    for m in re.finditer(kw + r'\s*=\s*["\'](\w+)["\']', src):
        print(kw, '=', m.group(1))
    for m in re.finditer(r'(RED|YEL)\s*[:=]\s*"([^"]+)"', src):
        print(m.group(1), '=', m.group(2))
# look at how add maps sev; find where rep.add with sev
print('--- main tail ---')
i = src.find('def main')
print(src[i+200:i+900])
