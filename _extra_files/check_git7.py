import os, pathlib

root = pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi').resolve()
git_dir = root / '.git'

print(f'.git exists: {git_dir.exists()}')
print(f'.git is_dir: {git_dir.is_dir()}')

if git_dir.exists():
    print('\nContents of .git:')
    for item in sorted(git_dir.rglob('*'))[:50]:
        rel = item.relative_to(git_dir)
        if item.is_file():
            size = item.stat().st_size
            print(f'  {rel} ({size} bytes)')
        elif item.name == '.git' or 'objects' not in item.parts:
            print(f'  {rel}/ (dir)')

# Check HEAD
head = git_dir / 'HEAD'
if head.exists():
    print(f'\nHEAD content: {head.read_text().strip()}')
    
# Check refs
refs_dir = git_dir / 'refs'
if refs_dir.exists():
    print(f'\nrefs contents:')
    for item in refs_dir.rglob('*'):
        rel = item.relative_to(refs_dir)
        if item.is_file():
            print(f'  {rel}: {item.read_text().strip()}')
        else:
            print(f'  {rel}/')

# Check objects
objects_dir = git_dir / 'objects'
if objects_dir.exists():
    print(f'\nobjects contents:')
    for item in sorted(objects_dir.iterdir()):
        print(f'  {item.name}/')
        if item.is_dir():
            for sub in item.iterdir():
                print(f'    {sub.name}')
                break
    # Count total objects
    count = 0
    for f in objects_dir.rglob('*'):
        if f.is_file():
            count += 1
    print(f'  Total object files: {count}')

# Check packed-refs
packed_refs = git_dir / 'packed-refs'
print(f'\npacked-refs exists: {packed_refs.exists()}')
if packed_refs.exists():
    print(f'packed-refs: {packed_refs.read_text().strip()[:200]}')
