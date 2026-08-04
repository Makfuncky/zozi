import os, pathlib
git_dir = pathlib.Path('.git')
for name in ['commondir', 'gitdir', 'hooks', 'objects', 'refs', 'worktrees']:
    p = git_dir / name
    if p.exists():
        if p.is_file():
            print(f'{name}: FILE - {p.read_text().strip()[:100]}')
        else:
            items = list(p.iterdir())
            print(f'{name}: DIR - {len(items)} items')
            for x in items[:5]:
                print(f'  {x.name}')

# Check worktrees
wt = git_dir / 'worktrees'
if wt.exists():
    for p in wt.iterdir():
        if p.is_dir():
            print(f'worktree dir: {p.name}')
            for f in p.iterdir():
                print(f'  {f.name}')
