import urllib.request, json

for url in ["http://127.0.0.1:8000/categories", "http://127.0.0.1:8000/products"]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    if isinstance(data, list):
        print(f"GET {url} -> {len(data)} items")
    else:
        total = data.get("total", len(data.get("items", [])))
        keys = list(data.keys())
        print(f"GET {url} -> keys={keys} total={total}")

