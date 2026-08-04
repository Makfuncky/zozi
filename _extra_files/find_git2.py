import subprocess, os, pathlib

# Search for .git directory
for root in [pathlib.Path('.'), pathlib.Path('..'), pathlib.Path('../..')]:
    git_path = root / '.git'
    if git_path.exists():
        print(f'Found .git at: {git_path.absolute()}')
        break
else:
    print('No .git found in current or parent dirs')

# Check if .git is a file (worktree) or directory
git_path = pathlib.Path('.git')
print(f'.git type: file={git_path.is_file()}, dir={git_path.is_dir()}')
if git_path.is_file():
    print(f'.git content: {git_path.read_text().strip()}')

# Try git from different directories
for cwd in ['D:\\Projects\\10- E-COMMERCE_WEBSITE\\zozi', 'D:\\Projects\\10- E-COMMERCE_WEBSITE']:
    result = subprocess.run(['git', '-C', cwd, 'show', 'stash@{0}:backend/routers/security/auth.py'], 
                          capture_output=True, text=True, cwd=cwd)
    print(f'\nFrom {cwd}:')
    print(f'  exit: {result.returncode}')
    if result.returncode == 0:
        print(f'  content length: {len(result.stdout)}')
        content = result.stdout
        with open('auth_security_original.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('  Saved to auth_security_original.py')
        print(f'  First 500 chars: {content[:500]}')
    else:
        print(f'  error: {result.stderr.strip()[:300]}')
