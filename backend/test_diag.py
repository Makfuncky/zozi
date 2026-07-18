import urllib.request, urllib.error, urllib.parse, json, io, ssl, time
from PIL import Image

BASE = "http://localhost:8000"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(method, path, token=None, data=None, files=None, form=None, timeout=60):
    url = BASE + path
    if files is not None:
        boundary = "----zozidiag"
        body = bytearray()
        if form:
            for k, v in form.items():
                body += f"--{boundary}\r\n".encode()
                body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
                body += f"{v}\r\n".encode()
        for k, (fn, fbytes, ctype) in (files or {}).items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{k}"; filename="{fn}"\r\n'.encode()
            body += f"Content-Type: {ctype}\r\n\r\n".encode()
            body += fbytes + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    elif data is not None:
        body = json.dumps(data).encode()
        headers = {"Content-Type": "application/json"}
    else:
        body = None
        headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

# Login
s, login = req("POST", "/auth/login/json", data={"email": "supplier@test.com", "password": "supplier123"})
token = login.get("access_token")
print("LOGIN", "OK" if token else "FAIL")

# Load real sneaker photo
data = open("sample_sneaker.jpg", "rb").read()

# 1. Synchronous analyze
s, sync = req("POST", "/supplier/upload/ai-analyze", token=token,
              files={"image": ("sample_sneaker.jpg", data, "image/png")})
print("=" * 72)
print("SYNCHRONOUS INSTANT RESULT")
print("source         :", sync.get("source"))
print("name           :", sync.get("product_name_hint"))
print("category       :", sync.get("suggested_category"))
print("subcategory    :", sync.get("suggested_subcategory"))
print("brand          :", sync.get("suggested_brand"))
print("attributes     :", sync.get("detected_attributes"))
print("description    :", str(sync.get("product_description"))[:200])
print("tags           :", sync.get("suggested_tags"))
print("variants       :", sync.get("suggested_variants"))
print("var_options    :", sync.get("variant_options"))
print("photo_analysis :", sync.get("photo_analysis"))
print("copy_job_id    :", sync.get("copy_job_id", "MISSING"))

# 2. Poll background vision job
job_id = sync.get("copy_job_id")
if job_id:
    print("\n" + "=" * 72)
    print("POLLING BACKGROUND VISION JOB")
    for i in range(30):
        time.sleep(10)
        s, job = req("GET", f"/supplier/upload/ai-copy/{job_id}", token=token)
        st = job.get("status")
        print(f"  poll {i*10+10}s -> {st}")
        if st == "done":
            r = job.get("result") or {}
            print("source         :", r.get("source"))
            print("name           :", r.get("product_name_hint"))
            print("category       :", r.get("suggested_category"))
            print("subcategory    :", r.get("suggested_subcategory"))
            print("brand          :", r.get("suggested_brand"))
            print("attributes     :", r.get("detected_attributes"))
            print("description    :", str(r.get("product_description"))[:300])
            print("tags           :", r.get("suggested_tags"))
            print("variants       :", r.get("suggested_variants"))
            print("var_options    :", r.get("variant_options"))
            print("var_labels     :", r.get("variant_labels"))
            print("photo_analysis :", r.get("photo_analysis"))
            print("english_title  :", r.get("english_title"))
            print("arabic_title   :", repr(r.get("arabic_title")))
            print("source         :", r.get("source"))
            break
        if st == "error":
            print("  JOB ERROR:", job.get("error"))
            break
    else:
        print("  JOB NOT COMPLETED WITHIN TIMEOUT")

