import os, re
ROOT=r'D:\Projects\10- E-COMMERCE WEBSITE\zozi'
ROUTERS=os.path.join(ROOT,'backend','routers')
f='logistics_partner.py'
base=f[:-3]; toks=base.split('_')
PREFIXED={'admin','supplier','public','customer','country','system','logistics'}
surface=toks[0]; rest=toks[1:]
print('surface',surface,'rest',rest,'len',len(rest))
src=open(os.path.join(ROUTERS,f),encoding='utf-8',errors='ignore').read()
routes=re.findall(r"@\w+\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]", src)
defs=re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', src)
OP_PRIORITY=['management','tracking','register','registration','login','validation','verify','moderate','report','reporting','sync','import','export','upload','approve','approval','review','status','config','configuration','analytics','dashboard','lookup','search','catalog','messaging','message','pay','payment','payout','refund','create','creation','update','delete','list','get']
text=' '.join(defs+[r[1] for r in routes]).lower()
print('text has verify:', 'verify' in text)
print('text has create:', 'create' in text)
for k in OP_PRIORITY:
    if k in text:
        print('FIRST MATCH:',k); break
else:
    print('NO MATCH -> routes')
