"""Compare actual CSP_POLICY bytes vs a passing string."""
import h11
from backend.middleware import security_headers
from backend.middleware.security_headers import CSP_POLICY, connect_src

base = "default-src 'self'; script-src 'self' " + ("x" * 200)
ok = h11.Response(status_code=200, headers=[("Content-Security-Policy", base)])

def ok2(t):
    try:
        h11.Response(status_code=200, headers=[("Content-Security-Policy", t)])
        return True
    except h11.LocalProtocolError as e:
        print(f"  REJECTED first bad byte at offset {e.__traceback__}"); return False

for name, val in [("CSP_POLICY", CSP_POLICY), ("CSP_POLICY_DEV", security_headers.CSP_POLICY_DEV)]:
    print(f"{name} ({len(val)} chars):", end=" ")
    bad = None
    for i in range(len(val)):
        prefix = val[:i+1]
        try:
            h11.Response(status_code=200, headers=[("Content-Security-Policy", prefix)])
        except h11.LocalProtocolError as e:
            bad = i
            break
    if bad is None:
        print("ACCEPTED (unexpected)")
    else:
        print(f"REJECTED at byte {bad} ({repr(val[bad-8:bad+1])})")
        # What character is there?
        print(f"   ord={ord(val[bad])}  prev={repr(val[bad-1:bad+1])}")
        # Try without that char
        try:
            h11.Response(status_code=200, headers=[("Content-Security-Policy", val[:bad] + val[bad+1:])])
            print("   without it -> ACCEPTED")
        except h11.LocalProtocolError:
            print("   without it -> still REJECTED")
