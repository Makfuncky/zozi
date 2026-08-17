import os,sys
print("python", sys.version.split()[0])
hits=[]
for root,_,files in os.walk('.'):
    if '__pycache__' in root or '.venv' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith('.py'):
            p=os.path.join(root,f)
            try: t=open(p,encoding='utf8').read()
            except: continue
            if '_legacy.' in t or 'infrastructure.database' in t:
                hits.append(p)
print("files referencing _legacy./infra.database:", len(hits))
files=0; occ=0
for root,_,fs in os.walk('.'):
    if '__pycache__' in root or '.venv' in root: continue
    for f in fs:
        if f.endswith('.py'):
            p=os.path.join(root,f)
            try: t=open(p,encoding='utf8').read()
            except: continue
            c=t.count('from db')+t.count('import db')
            if c: files+=1; occ+=c
print("files with db imports:", files, "occurrences:", occ)
