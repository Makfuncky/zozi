import re, glob, os

catalog = {}
for path in glob.glob('backend/domains/*/features.py'):
    text = open(path, encoding='utf-8').read()
    domain = os.path.normpath(path).split(os.sep)[2]
    ids = set()
    for m in re.finditer(r'^\s{4}"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)"\s*:', text, re.M):
        ids.add(m.group(1))
    for m in re.finditer(r"^\s*-\s*['\"]([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)['\"]", text, re.M):
        ids.add(m.group(1))
    for m in re.finditer(r"['\"]([a-z][a-z0-9_]*\.[a-z0-9_.]+)['\"]\s*:", text):
        ids.add(m.group(1))
    catalog[domain] = sorted(ids)

declared = {fid for ids in catalog.values() for fid in ids}
print('Declared features:', len(declared))
print('Per domain:', {d: len(v) for d, v in sorted(catalog.items())})

# Now find references in py, ts, tsx, js excluding tests/e2e/__tests__/features.py
sources = glob.glob('backend/**/*.py', recursive=True) + glob.glob('frontend/**/*.ts', recursive=True) + glob.glob('frontend/**/*.tsx', recursive=True) + glob.glob('frontend/**/*.js', recursive=True)
referenced = {}
for fid in declared:
    refs = []
    for p in sources:
        if '/tests/' in p or '/e2e/' in p or '__tests__' in p or p.endswith('features.py'):
            continue
        try:
            text = open(p, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        if fid in text:
            refs.append(p)
            break
    referenced[fid] = refs

dead = sorted([fid for fid in declared if not referenced[fid]])
print('Dead features:', len(dead))
print('Sample dead:', dead[:20])

# Also find undefined gates
gated = set()
for p in sources:
    if '/tests/' in p or '/e2e/' in p or '__tests__' in p or p.endswith('features.py'):
        continue
    try:
        text = open(p, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'require_feature\(\s*["\']([^"\']+)["\']', text):
        gated.add(m.group(1))

undefined = sorted([fid for fid in gated if fid not in declared])
print('Undefined gates:', len(undefined))
print('Sample undefined:', undefined[:20])
