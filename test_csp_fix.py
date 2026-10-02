import h11
from backend.middleware import security_headers

print("h11 acceptance of security headers after fix:")
for name in ["CSP_POLICY", "CSP_POLICY_DEV"]:
    val = getattr(security_headers, name)
    try:
        h11.Response(status_code=200, headers=[("Content-Security-Policy", val)])
        result = "ACCEPTED"
    except h11.LocalProtocolError:
        result = "REJECTED"
    print(f"  {name}: {len(val)} chars, trailing_space={val.endswith(' ')}, h11={result}")

hsts = "max-age=31536000; includeSubDomains; preload"
try:
    h11.Response(status_code=200, headers=[("Strict-Transport-Security", hsts)])
    print(f"  HSTS: {len(hsts)} chars, h11=ACCEPTED")
except h11.LocalProtocolError:
    print(f"  HSTS: h11=REJECTED")

print("\nCSP_POLICY actual value:")
print(security_headers.CSP_POLICY)
