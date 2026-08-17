import re, json
from collections import defaultdict

lines = [l.strip() for l in open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt', encoding='utf-8') if l.strip()]

STOP = {
 'service','services','controller','controllers','handler','handlers','manager','managers',
 'helper','helpers','util','utils','common','base','abstract','interface','impl',
 'write','read','create','update','delete','get','list','bulk','batch','query','router','routes',
 'ops','operations','operation','admin','public','core','api','unified','fallback','engine',
 'background','scheduler','scheduling','worker','background','v1','v2','v3','new','old','temp',
 '_job','job','jobs','legacy','sync','upload','uploads','download','mgr','svc','fn','func','function'
}

def concept(rel):
    folder = rel.split('/')[0]
    name = rel.split('/')[-1].replace('.py','').lower()
    # strip leading folder token if present
    toks = re.split(r'[_\-]', name)
    kept = [t for t in toks if t and t not in STOP]
    if not kept:
        kept = [t for t in toks if t]
    return folder, tuple(kept)

groups = defaultdict(list)
for l in lines:
    rel = l.split(':')[-1].strip()
    folder, c = concept(rel)
    groups[c].append(rel)

print('TOTAL FILES:', len(lines))
print('DISTINCT CONCEPTS (normalized):', len(groups))
multi = {k:v for k,v in groups.items() if len(v) > 1}
print('CONCEPTS WITH >1 FILE:', len(multi))
print('FILES IN MULTI GROUPS:', sum(len(v) for v in multi.values()))
print()
print('==== MULTI-FILE CONCEPT GROUPS (the redundant ones) ====')
for k in sorted(multi, key=lambda k:-len(multi[k])):
    print(f'[{len(multi[k])}] {(" ".join(k)) or "(generic)"}:')
    for f in multi[k]:
        print('     ', f)
