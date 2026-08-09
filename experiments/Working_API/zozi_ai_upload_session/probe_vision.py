import base64, httpx, json, time

IMG = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\image\image_01.webp"
B64 = base64.b64encode(open(IMG,"rb").read()).decode()

# Test 1: native /api/chat for moondream (vision)
payload_native = {
    "model": "moondream",
    "messages": [{"role":"user","content":"Describe this product briefly.","images":[B64]}],
    "stream": False,
}
# Test 2: /v1/chat/completions with image_url
payload_v1 = {
    "model":"moondream",
    "messages":[{"role":"user","content":[
        {"type":"text","text":"Describe this product briefly."},
        {"type":"image_url","image_url":{"url":f"data:image/webp;base64,{B64}"}}
    ]}],
    "stream":False,
}

for name,payload,url in [("native /api/chat",payload_native,"http://localhost:11434/api/chat"),
                          ("v1 image_url",payload_v1,"http://localhost:11434/v1/chat/completions")]:
    t=time.time()
    try:
        r=httpx.post(url,json=payload,timeout=120)
        print(f"\n=== {name} -> {r.status_code} ({time.time()-t:.1f}s) ===")
        print(r.text[:500])
    except Exception as e:
        print(f"\n=== {name} ERROR ({time.time()-t:.1f}s) ===")
        print(str(e)[:300])
