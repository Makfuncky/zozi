import pathlib, os
root=pathlib.Path(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi')
files=['backend/models/admin.py','backend/models/country_control.py','backend/models/onboarding.py']
repl={'users.id':'core.users.id','employees.id':'hr.employees.id','logistics_partners.id':'logistics.logistics_partners.id','shipments.id':'logistics.shipments.id','onboarding_pipelines.id':'hr.onboarding_pipelines.id'}
for f in files:
    p=root/f
    text=p.read_text(encoding='utf-8')
    out=[]
    changed=0
    for line in text.splitlines():
        if 'ForeignKey(' in line:
            for a,b in repl.items():
                if a in line:
                    line=line.replace(a,b); changed+=1
        out.append(line)
    if changed:
        tmp=p.with_name(p.name+'.tmp_q')
        tmp.write_text("\n".join(out), encoding='utf-8')
        os.replace(tmp, p)
        print(f,'changed:',changed)
    else:
        print(f,'no change')