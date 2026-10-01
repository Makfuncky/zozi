import yaml, re, collections
d = yaml.safe_load(open('feature_definitions.yaml', encoding='utf-8'))
be = {'alembic','controllers','core','db','dependencies','events','jobs','middleware','models','providers','routers','scripts','services','tests','tools','uploads','utils'}
fe_web = {'app','components','lib','hooks','services','theme','types','utils','logo','__tests__','styles'}
fe_mob = {'app','components','lib','theme','assets','android','mocks','e2e','scripts','web-dist'}
bad_backend=collections.Counter(); comp_sub=collections.Counter(); bad_fe=collections.Counter()
for f in d['features']:
    for grp, lst in f.get('expected',{}).items():
        for p in lst:
            if p.startswith('backend/'):
                seg = p.split('/')[1]
                if seg not in be: bad_backend[seg]+=1
                if p.startswith('backend/') and '/components/' in p:
                    pass
                # component subfolder check is frontend only
            if p.startswith('frontend/web_app/src/components/'):
                sub = p.split('/')[4] if len(p.split('/'))>4 else ''
                if sub not in {'ui','admin','auth','chat','comms','country','ems','map','supplier'}:
                    comp_sub[sub]+=1
            if p.startswith('frontend/'):
                top = p.split('/')[2]  # web_app / mobile_app / shared
print("NON-P1 backend top-level folders:", dict(bad_backend))
print("Non-P1 web component subfolders:", dict(comp_sub))
