import requests, sys, io
from backend.auth import create_access_token
token = create_access_token({'sub':'supplier@test.com','role':'supplier'})
img = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\output_br_05\image_01.png"
presets = ['clean_commercial','precision_geometry','birefnet_production','ultimate_gaps','marketing_variants','lite_variants']
with open(img,'rb') as f:
    data = f.read()
for p in presets:
    try:
        r = requests.post('http://localhost:8000/supplier/upload/remove-background',
            files={'image': ('img.png', data, 'image/png')},
            data={'preset': p, 'fast_mode': 'false'},
            headers={'Authorization': f'Bearer {token}'}, timeout=120)
        print(p, '->', r.status_code, len(r.content), 'bytes', r.headers.get('content-type'))
    except Exception as e:
        print(p, '-> ERROR', e)
