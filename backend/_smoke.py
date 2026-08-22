import asyncio, sys, httpx, main

CHECKS = [
    ("/openapi.json", "GET", "openapi schema"),
    ("/docs", "GET", "swagger docs"),
    ("/customer/cart", "GET", "customer cart (namespaced)"),
    ("/customer/orders", "GET", "customer orders (namespaced)"),
    ("/supplier/products", "GET", "supplier products (namespaced)"),
    ("/supplier/profile", "GET", "supplier profile (namespaced)"),
    ("/admin/products", "GET", "admin products (namespaced)"),
    ("/admin/categories", "GET", "admin categories (namespaced)"),
    ("/employee/profile", "GET", "employee profile (namespaced)"),
    ("/logistics-partner", "GET", "logistics partner (alias)"),
    ("/api/v1/logistics", "GET", "logistics prefixed root"),
]

async def run():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ok = fail = 0
        lines = []
        for path, method, label in CHECKS:
            try:
                resp = await client.request(method, path)
                status = resp.status_code
            except Exception as e:
                lines.append("ERROR  %-32s %-8s %s -> %s" % (label, method, path, e))
                fail += 1
                continue
            if status == 404:
                lines.append("FAIL   %-32s %-8s %s -> 404 (route missing)" % (label, method, path))
                fail += 1
            else:
                lines.append("PASS   %-32s %-8s %s -> %d" % (label, method, path, status))
                ok += 1
        summary = "\nSMOKE TEST (namespaced): %d passed, %d failed (of %d)" % (ok, fail, len(CHECKS))
        lines.append(summary)
        with open("_smoke_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("\n".join(lines))
        return fail

if __name__ == "__main__":
    sys.exit(1 if asyncio.run(run()) else 0)
