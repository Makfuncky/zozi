"""Check git repository for recovery potential"""
import pathlib

root = pathlib.Path('f:/recovery_recuva_4/Projects/10- E-COMMERCE WEBSITE/zozi/.git')

if not root.exists():
    print('.git directory NOT FOUND')
    exit()

print('=== GIT REPOSITORY STATUS ===')

# Check HEAD
head = root / 'HEAD'
if head.exists():
    data = head.read_bytes()
    null = all(b==0 for b in data)
    txt = data.decode('utf-8', errors='replace') if not null else 'NULL'
    print(f'HEAD: {len(data)}b null={null} content={txt.strip()[:100]}')

# Check config
cfg = root / 'config'
if cfg.exists():
    data = cfg.read_bytes()
    null = all(b==0 for b in data)
    txt = data.decode('utf-8', errors='replace') if not null else 'NULL'
    print(f'git config: {len(data)} bytes, null={null}')
    if not null:
        print('  ' + txt[:500].replace('\n', '\n  '))

# Check pack files
pack_dir = root / 'objects' / 'pack'
if pack_dir.exists():
    packs = list(pack_dir.glob('*.pack'))
    print(f'\nPack files: {len(packs)}')
    for p in packs:
        data = p.read_bytes()
        is_null = all(b==0 for b in data[:100])
        magic = data[:4] if not is_null else b'NULL'
        print(f'  {p.name}: {len(data)/1024/1024:.1f}MB, null={is_null}, magic={magic}')

# Check loose objects
objects_dir = root / 'objects'
loose = [f for f in objects_dir.rglob('*') if f.is_file() and f.parent.name not in ['pack', 'info']]
print(f'\nLoose objects: {len(loose)}')
ok_loose = 0
for f in loose[:5]:
    data = f.read_bytes()
    null = all(b==0 for b in data[:20])
    if not null:
        ok_loose += 1
    print(f'  {f.parent.name}/{f.name}: {len(data)}b null={null}')

# Check refs
refs_dir = root / 'refs'
if refs_dir.exists():
    print('\n=== REFS ===')
    for f in refs_dir.rglob('*'):
        if f.is_file():
            data = f.read_bytes()
            null = all(b==0 for b in data)
            txt = data.decode('utf-8', errors='replace').strip() if not null else 'NULL'
            print(f'  {f.relative_to(root)}: {txt[:60]}')

# Check COMMIT_EDITMSG
for fname in ['ORIG_HEAD', 'COMMIT_EDITMSG', 'MERGE_HEAD', 'FETCH_HEAD']:
    f = root / fname
    if f.exists():
        data = f.read_bytes()
        null = all(b==0 for b in data)
        txt = data.decode('utf-8', errors='replace').strip() if not null else 'NULL'
        print(f'\n{fname}: {len(data)}b null={null}')
        if not null:
            print(f'  {txt[:200]}')
