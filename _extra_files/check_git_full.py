import os, subprocess, pathlib

# Check system for any git installations or repos
root = pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi')

# Check Windows Recycle Bin
for drive in ['C:', 'D:']:
    recycle = pathlib.Path(drive) / '$Recycle.Bin'
    print(f'{drive}\\$Recycle.Bin exists: {recycle.exists()}')

# Check for git globally
result = subprocess.run(['where', 'git'], capture_output=True)
print(f'Git locations: {result.stdout.decode()}')

# Check global git config
home = pathlib.Path(os.path.expanduser('~'))
gitconfig = home / '.gitconfig'
print(f'Git config exists: {gitconfig.exists()}')

# Check for any .git files in parent directories
for p in [root.parent, root.parent.parent, root.parent.parent.parent]:
    git = p / '.git'
    print(f'{p}/.git exists: {git.exists()}')

# Check if the filesystem is NTFS (has previous versions)
import ctypes
result = subprocess.run(['fsutil', 'fsinfo', 'volumeinfo', 'D:'], capture_output=True, shell=True)
print(f'\nVolume info: {result.stdout.decode()}')

# Check for shadow copies
result = subprocess.run(['vssadmin', 'list', 'shadows'], capture_output=True, shell=True)
print(f'\nShadow copies: {result.stdout.decode()[:500]}')

# Try git fsck on any potential git dir
for git_dir in [root / '.git', root / '.git2', pathlib.Path('D:/Projects/10- E-COMMERCE_WEBSITE/.git')]:
    if git_dir.exists():
        print(f'\nFound git dir: {git_dir}')
    else:
        print(f'\nNot found: {git_dir}')

# Check temp dirs
temp = pathlib.Path(os.environ.get('TEMP', 'C:/temp'))
print(f'\nTemp dir: {temp}')
if temp.exists():
    git_in_temp = list(temp.glob('.git'))
    print(f'Git dirs in temp: {git_in_temp}')

# Search for any git-related directories
for path in [root]:
    for item in path.iterdir():
        if 'git' in item.name.lower():
            print(f'Git-related item found: {item}')
