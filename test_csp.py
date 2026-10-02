"""Test HTTP transport options for the h11 semicolon problem."""
import h11
import httpx
from backend.middleware.security_headers import CSP_POLICY, CSP_POLICY_DEV, connect_src

print("=== 1. h11 HTTP/1.1 rejection of semicolons ===")
for name, val in [("CSP_POLICY", CSP_POLICY), ("CSP_POLICY_DEV", CSP_POLICY_DEV),
                  ("HSTS", "max-age=31536000; includeSubDomains; preload")]:
    try:
        h11.Response(status_code=200, headers=[(name, val)])
        print(f"  {name}: ACCEPTED by h11")
    except h11.LocalProtocolError as e:
        print(f"  {name}: REJECTED by h11 ({len(val)} chars)")

print("\n=== 2. Multiple CSP header fields (comma-join, HTTP/1.1 compatible) ===")
h1 = ("Content-Security-Policy", CSP_POLICY[:50] + ";")
h2 = ("Content-Security-Policy", CSP_POLICY[50:])
try:
    r = h11.Response(status_code=200, headers=[h1, h2])
    print("  ACCEPTED by h11:", [x for x in r.headers if x[0] == "Content-Security-Policy"])
except h11.LocalProtocolError as e:
    print("  REJECTED:", e)

print("\n=== 3. httpx can receive semicolon headers (client side fine) ===")
try:
    h = httpx.Headers([("Content-Security-Policy", CSP_POLICY)])
    print("  ACCEPTED by httpx:", "Content-Security-Policy" in h)
except Exception as e:
    print("  REJECTED:", e)

print("\n=== 4. h2 HTTP/2 with a semicolon header (h2c) ===")
import h2.connection, h2.config
cfg = h2.config.H2Configuration(client_side=False)
conn = h2.connection.H2Connection(config=cfg)
try:
    conn.send_headers(stream_id=0, headers=[("content-type", "text/html"),
                                            ("content-security-policy", CSP_POLICY)])
    frames = conn.data_to_send()
    print("  ACCEPTED by h2; frames to send:", len(frames), "bytes")
except Exception as e:
    print("  REJECTED by h2:", type(e).__name__, e)

print("\n=== 5. aioquic / HTTP/3 feasibility ===")
try:
    import aioquic
    print("  aioquic imported:", aioquic.__version__)
except ModuleNotFoundError as e:
    print("  aioquic NOT importable:", e)
except Exception as e:
    print("  aioquic import raised:", type(e).__name__, e)
