import importlib.util, sys, json
from pathlib import Path
spec = importlib.util.spec_from_file_location('mt', r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\migration_tracker.py')
mt = importlib.util.module_from_spec(spec)
sys.modules['mt'] = mt
spec.loader.exec_module(mt)

from collections import defaultdict
paths = [l.strip().split(':')[-1].strip() for l in open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt', encoding='utf-8') if l.strip()]
groups = defaultdict(list)
for p in paths:
    stem = Path(p).stem
    ct = mt._concept_tokens(stem)
    # key by sorted tuple of concept tokens
    key = tuple(sorted(ct))
    groups[key].append(p)

total = len(paths)
distinct = len(groups)
multi = {k:v for k,v in groups.items() if len(v)>1}
print('ENGINE _concept_tokens:')
print('  total files      :', total)
print('  distinct concepts:', distinct)
print('  redundant (remove if 1/file/concept):', total - distinct)
print('  multi-groups     :', len(multi), ' covering', sum(len(v) for v in multi.values()), 'files')
