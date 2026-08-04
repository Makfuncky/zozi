import pathlib
git_dir = pathlib.Path('.git')
ftype = "file" if git_dir.is_file() else "dir"
print(f'Type: {ftype}')
print(f'Contents:')
for item in sorted(git_dir.iterdir()):
    print(f'  {item.name}')
