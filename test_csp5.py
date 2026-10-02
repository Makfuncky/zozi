import binascii, h11
from backend.middleware import security_headers

cp = security_headers.CSP_POLICY
test = "default-src 'self'; script-src 'self' " + ("x" * 200)
print("CSP_POLICY[:30] hex:", binascii.hexlify(cp[:30].encode()).decode())
print("test     [:30] hex:", binascii.hexlify(test[:30].encode()).decode())
print()
print("first 30 CSP_POLICY:", repr(cp[:30]))
print("len CSP_POLICY:", len(cp))
print("non-ascii:", [c for c in cp if ord(c) > 127])
print("repr first 60:", repr(cp[:60]))
print()
# Where does prefix test fail vs passing?
for i in range(0, 30):
    p = cp[:i+1]
    try:
        h11.Response(status_code=200, headers=[("Content-Security-Policy", p)])
        r = "OK"
    except h11.LocalProtocolError:
        r = "BAD"
    print(f"  i={i:2d} repr={p[:25]!r} {r}")
