"""Find h11's header value length threshold."""
import h11

def ok(t):
    try:
        h11.Response(status_code=200, headers=[("Content-Security-Policy", t)])
        return True
    except h11.LocalProtocolError:
        return False

# CSP is 366 chars; start from short and grow
for n in range(10, 600, 10):
    t = "default-src 'self'; script-src 'self' " + ("x" * n)
    flag = "OK" if ok(t) else "BAD"
    print(f"[{flag}] len={n:4d}")
