import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rows = json.load(open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\audit_findings_full.json', encoding='utf-8'))
print("TOTAL findings:", len(rows))
# severity distribution
from collections import Counter
sev = Counter(r['sev'] for r in rows)
print("SEV distribution:", dict(sev))
code = Counter(r['code'] for r in rows)
print("CODE distribution:", dict(code))

COUNTRY = ['country_admin', 'country_auto_populate', 'country_payouts', 'country_staff']
cf = [r for r in rows if any(c in r['path'] for c in COUNTRY)]
print("\n=== COUNTRY DOMAIN findings:", len(cf))
csev = Counter(r['sev'] for r in cf)
print("country SEV:", dict(csev))
ccode = Counter((r['sev'], r['code']) for r in cf)
print("country (sev,code):", dict(ccode))
# list red
print("\n--- RED in country domain ---")
for r in sorted(cf, key=lambda x: (x['path'], x['line'] or 0)):
    if r['sev'] != '🔴':
        continue
    print(r['sev'], r['code'], r['path'], 'L'+str(r['line']), '|', r['message'][:90])
print("\n--- YELLOW in country domain ---")
for r in sorted(cf, key=lambda x: (x['path'], x['line'] or 0)):
    if r['sev'] != '🟡':
        continue
    print(r['sev'], r['code'], r['path'], 'L'+str(r['line']), '|', r['message'][:90])
