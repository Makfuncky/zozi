import ast, os

pairs = [
    ('models/communication.py', 'models/comms/communication.py'),
    ('models/core.py', 'models/comms/core.py'),
    ('models/countries.py', 'models/geography/countries.py'),
    ('models/country_enhancements.py', 'models/geography/country_enhancements.py'),
    ('models/marketing.py', 'models/comms/marketing.py'),
    ('models/suppliers.py', 'models/comms/suppliers.py'),
]

def classes(p):
    out = {}
    try:
        t = ast.parse(open(p, encoding='utf-8').read())
    except Exception as e:
        return None, str(e)
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef):
            bases = []
            for b in n.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(b.attr)
            out[n.name] = bases
    return out, None

for flat, pkg in pairs:
    f, fe = classes(flat)
    p, pe = classes(pkg)
    print(f"\n### {flat}  <->  {pkg}")
    if fe:
        print("  FLAT PARSE ERR:", fe)
    if pe:
        print("  PKG PARSE ERR:", pe)
    if f and p:
        fk, pk = set(f), set(p)
        print("  only in FLAT :", sorted(fk - pk))
        print("  only in PKG  :", sorted(pk - fk))
        print("  in BOTH      :", len(fk & pk))
