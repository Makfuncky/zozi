import importlib.util, sys
spec = importlib.util.spec_from_file_location('mt', r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\migration_tracker.py')
mt = importlib.util.module_from_spec(spec)
sys.modules['mt'] = mt
spec.loader.exec_module(mt)
r = mt.run_full_audit()
print('HAS tier6 attr:', hasattr(r, 'tier6_cross_folder'))
t6 = getattr(r, 'tier6_cross_folder', None)
print('TIER6 PAIRS:', len(t6) if t6 is not None else 'NONE')
if t6:
    for p in t6:
        a, b = p['a'], p['b']
        print('---')
        print('A:', a.get('rel') or a.get('path'))
        print('B:', b.get('rel') or b.get('path'))
        print('concept:', p.get('concept'), 'jac:', round(p.get('jaccard', 0), 2), 'sizeA:', p.get('sizeA'), 'sizeB:', p.get('sizeB'))
