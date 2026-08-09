import py_compile, glob
bad=[]
for f in glob.glob("**/*.py", recursive=True):
    try:
        py_compile.compile(f, doraise=True, quiet=1)
    except py_compile.PyCompileError as e:
        bad.append((f, str(e).splitlines()[-1]))
for f,msg in bad:
    print(f"  {f}  ::  {msg}")
print("TOTAL BAD:", len(bad))