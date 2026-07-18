import glob, os
base = 'frontend/mobile_app/app'
files = glob.glob(os.path.join(base, '**', '*.tsx'), recursive=True)
for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    if not lines or not lines[0].startswith('import React'): continue
    if len(lines) < 3 or not lines[1].startswith('import {'): continue
    create_idx = next((i for i,l in enumerate(lines) if 'const createStyles' in l), None)
    if create_idx is None: continue
    brace = 0
    end_idx = None
    for i in range(create_idx, len(lines)):
        line = lines[i]
        brace += line.count('{') - line.count('}')
        if brace == 0 and i > create_idx:
            end_idx = i
            break
    if end_idx is None: continue
    rn_end = next((i for i,l in enumerate(lines[end_idx+1:], start=end_idx+1) if l.strip().endswith('} from "react-native";')), None)
    if rn_end is None: continue
    names = [l.strip().strip(',') for l in lines[end_idx+1:rn_end] if l.strip().strip(',')]
    if not names: continue
    rn_import = f'import {{ {", ".join(names)} }} from "react-native";'
    new_lines = [lines[0], rn_import, ''] + lines[create_idx:end_idx+1] + [''] + lines[rn_end+1:]
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    print('fixed', fp)
