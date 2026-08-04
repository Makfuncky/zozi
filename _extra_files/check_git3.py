import os, pathlib, sys

root = pathlib.Path(r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi')
git_dir = root / '.git'
print(f'git_dir: {git_dir}, exists: {git_dir.exists()}')

for name in ['commondir', 'gitdir', 'hooks', 'objects', 'refs', 'worktrees']:
    p = git_dir / name
    exists = p.exists()
    print(f'{name}: exists={exists}')
    if exists:
        if p.is_file():
            print(f'  FILE - {p.read_text().strip()[:100]}')
        else:
            items = list(p.iterdir())
            print(f'  DIR - {len(items)} items')
            for x in list(items)[:5]:
                print(f'    {x.name}')

# Check worktrees
wt = git_dir / 'worktrees'
if wt.exists():
    print(f'worktrees exists')
    for p in wt.iterdir():
        if p.is_dir():
            print(f'  worktree: {p.name}')
            for f in p.iterdir():
                print(f'    {f.name}')
                if f.is_file():
                    try:
                        content = f.read_text().strip()
                        print(f'      content: {content[:100]}')
                    except:
                        pass
