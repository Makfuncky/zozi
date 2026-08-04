import os, shutil, struct, pathlib

rec_bin = r'D:\$Recycle.Bin\S-1-5-21-1339371623-4152739331-235715422-1002'
restore_dir = pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi/recovered')

items = os.listdir(rec_bin)
info_files = sorted([f for f in items if f.startswith('$I')])
rec_files = [f for f in items if f.startswith('$R')]

# Build mapping from $I -> original path, and $R -> content
recovered = []
for info in info_files:
    full = os.path.join(rec_bin, info)
    try:
        with open(full, 'rb') as fh:
            data = fh.read()
        if len(data) >= 36:
            name_bytes = data[36:]
            original_name = name_bytes.decode('utf-16-le').rstrip('\x00')
            # The $I file corresponds to the $R file with same suffix
            suffix = info[2:]  # remove $I prefix
            rec_file = f'$R{suffix}'
            rec_full = os.path.join(rec_bin, rec_file)
            
            file_size = struct.unpack('<I', data[0:4])[0]
            
            is_dir = False
            try:
                is_dir = os.path.isdir(rec_full) or (os.path.getsize(rec_full) == 0 and 'directory' in str(original_name))
            except:
                pass
            
            recovered.append({
                'info': info,
                'rec_file': rec_file,
                'rec_full': rec_full,
                'original_path': original_name,
                'file_size': file_size,
                'is_dir': is_dir,
                'exists': os.path.exists(rec_full)
            })
    except Exception as e:
        print(f'Error reading {info}: {e}')

# Print summary
print(f'Recovered items: {len(recovered)}')
print('\n=== Directories (can restore) ===')
for r in recovered:
    if r['is_dir']:
        print(f'  {r["original_path"]} (dir)')

print('\n=== Python files ===')
for r in recovered:
    if 'py' in r['original_path'].lower() and not r['is_dir']:
        print(f'  {r["original_path"]} -> {r["rec_file"]} (size={r["file_size"]}, exists={r["exists"]})')

print('\n=== MD files ===')
for r in recovered:
    if 'md' in r['original_path'].lower() and not r['is_dir']:
        actual_size = os.path.getsize(r['rec_full']) if r['exists'] else 0
        print(f'  {r["original_path"]} -> {r["rec_file"]} (info_size={r["file_size"]}, actual_size={actual_size})')

print('\n=== Governance files ===')
for r in recovered:
    if 'governance' in r['original_path'].lower() or 'govern' in r['original_path'].lower():
        print(f'  {r["original_path"]} -> {r["rec_file"]} (is_dir={r["is_dir"]}, exists={r["exists"]})')
        if r['is_dir'] and r['exists']:
            subdir = r['rec_full']
            try:
                for sub in os.listdir(subdir):
                    print(f'    -> {sub}')
            except Exception as e:
                print(f'    Error: {e}')
