import dis, marshal

pyc_path = 'data/__pycache__/routers_security_auth.cpython-310.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

print('Names:', code.co_names)
print('Constants:')
for c in code.co_consts:
    if isinstance(c, str) and len(c) < 200:
        print(f'  {repr(c)}')
    elif not isinstance(c, (int, type(None))):
        print(f'  [{type(c).__name__}]')
print()
print('Disassembly:')
dis.dis(code)
