import pathlib
targets=['employee_expenses','shift_handover_logs','supplier_onboarding_sync','logistics_partner_locations','parcel_location_trackers','onboarding_pipelines','onboarding_steps']
for t in targets:
    for f in pathlib.Path('models').rglob('*.py'):
        txt=f.read_text(encoding='utf-8')
        if ('__tablename__ = "%s"'%t in txt) or ("__tablename__ = '%s'"%t in txt):
            # find schema line near tablename
            lines=txt.splitlines()
            sch='?'
            for i,line in enumerate(lines):
                if '__tablename__' in line and t in line:
                    for j in range(max(0,i-3), i+1):
                        if 'schema=' in lines[j]:
                            sch=lines[j].strip()[:60]
            print(t,'->',f,'|',sch)