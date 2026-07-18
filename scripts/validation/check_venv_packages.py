"""Check .venv for readable package metadata"""
import pathlib

venv = pathlib.Path('f:/recovery_recuva_4/Projects/10- E-COMMERCE WEBSITE/zozi/.venv/Lib/site-packages')
if not venv.exists():
    print('site-packages not found')
    exit()

all_meta = list(venv.rglob('METADATA'))
print(f'Total METADATA files: {len(all_meta)}')

ok_metas = []
for mf in all_meta:
    try:
        data = mf.read_bytes()
        if len(data) > 0 and not all(b == 0 for b in data[:50]):
            ok_metas.append(mf)
    except Exception:
        pass

print(f'Readable METADATA files: {len(ok_metas)}')

packages = []
for mf in ok_metas:
    try:
        lines = mf.read_text(encoding='utf-8', errors='replace').split('\n')[:10]
        name = None
        ver = None
        for line in lines:
            if line.startswith('Name:'):
                name = line.split(':', 1)[1].strip()
            if line.startswith('Version:'):
                ver = line.split(':', 1)[1].strip()
        if name and ver:
            packages.append(f'{name}=={ver}')
    except Exception:
        pass

print(f'\n=== ALL READABLE PACKAGES ({len(packages)}) ===')
for p in sorted(packages):
    print(f'  {p}')
