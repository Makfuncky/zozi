import re, pathlib

pat = re.compile(r'ForeignKey\(\s*(["\'])users\.id\1')
rep = 'ForeignKey("security.users.id"'
total = 0
files = {}
for p in pathlib.Path('models').rglob('*.py'):
    if '__pycache__' in str(p):
        continue
    t = p.read_text(encoding='utf-8')
    n = len(pat.findall(t))
    if n:
        t2 = pat.sub(rep, t)
        p.write_text(t2, encoding='utf-8')
        files[str(p)] = n
        total += n
print('REPLACED total=%d across %d files' % (total, len(files)))
for k, v in sorted(files.items()):
    print('  ', k.replace('models/', ''), v)
