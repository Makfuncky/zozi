import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rows = json.load(open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\audit_findings_full.json', encoding='utf-8'))
COUNTRY = ['country_admin', 'country_auto_populate', 'country_payouts', 'country_staff']
cf = [r for r in rows if any(c in r['path'] for c in COUNTRY)]
print("COUNTRY domain findings:", len(cf))
for r in sorted(cf, key=lambda x: (x['path'], x['line'] or 0)):
    tag = 'RED' if r['sev'] == 'VIOLATION' else ('YEL' if r['sev'] == 'ADVISORY' else r['sev'])
    print(f"{tag:4} {r['code']:7} {r['path']} L{r['line']} | {r['message'][:120]}")
