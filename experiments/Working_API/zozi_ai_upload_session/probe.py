import asyncio, httpx, json, sys

BACKEND = "http://localhost:8000"
EMAIL = "supplier@zozi.com"
PASS = "supplier123"
IMG = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\image\image_01.webp"

async def main():
    async with httpx.AsyncClient(timeout=30, base_url=BACKEND) as c:
        # login
        r = await c.post("/auth/login", data={"username": EMAIL, "password": PASS})
        print("LOGIN", r.status_code, r.text[:200])
        tok = r.json().get("access_token")
        h = {"Authorization": f"Bearer {tok}"}
        # profile
        p = await c.get("/supplier/profile", headers=h)
        print("PROFILE", p.status_code, p.text[:400])
        # ai analyze
        with open(IMG, "rb") as f:
            data = f.read()
        a = await c.post("/supplier/upload/ai-analyze", headers=h,
                         files={"image": ("image_01.webp", data, "image/webp")})
        print("AI_ANALYZE", a.status_code)
        print(json.dumps(a.json(), indent=2, ensure_ascii=False)[:1500])
        # list products
        lp = await c.get("/supplier/products?limit=3", headers=h)
        print("LIST", lp.status_code, lp.text[:300])

asyncio.run(main())
