import glob, os

base = 'frontend/mobile_app/app'
files = glob.glob(os.path.join(base, '**', '*.tsx'), recursive=True)
for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        text = f.read()
    if 'const styles = createStyles(theme)' not in text or 'const createStyles = (theme' not in text:
        continue

    lines = text.splitlines()
    idx_style = [i for i, l in enumerate(lines) if 'const styles = createStyles(theme)' in l]
    idx_create = [i for i, l in enumerate(lines) if 'const createStyles = (theme' in l]
    if not idx_style or not idx_create:
        continue
    # only move if createStyles is defined after styles call
    if idx_create[0] < idx_style[0]:
        continue

    start = idx_create[0]
    brace = 0
    end = None
    for i in range(start, len(lines)):
        l = lines[i]
        brace += l.count('{') - l.count('}')
        if brace == 0 and i > start:
            end = i
            break

    if end is None:
        for i in range(start, len(lines)):
            if lines[i].strip() == '});':
                end = i
                break

    if end is None:
        print('Could not locate end for', fp)
        continue

    block = lines[start:end + 1]
    lines = lines[:start] + lines[end + 1:]

    insert = 0
    while insert < len(lines) and (lines[insert].startswith('import ') or lines[insert].startswith('from ') or lines[insert].strip() == ''):
        insert += 1

    lines = lines[:insert] + [''] + block + [''] + lines[insert:]

    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('Updated', fp)
