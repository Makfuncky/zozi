"""Pinpoint what h11 rejects inside the CSP header value."""
import h11

base = "default-src 'self'; script-src 'self'; connect-src 'self'; report-uri /csp-report"
tests = [
    base,                                              # has ' and ;
    base.replace("'", "x"),                            # no quotes
    "max-age=31536000; includeSubDomains; preload",    # HSTS, has ;
    base.split(";")[0] + ";",                          # first directive only
    base[: len("default-src 'self';") ],               # trimmed
    base.replace("; ", ";"),                           # no space after ;
    base.replace(";", "; "),                           # no space after ; (same)
]
for i, t in enumerate(tests):
    try:
        h11.Response(status_code=200, headers=[("Content-Security-Policy", t)])
        print(f"[OK ] test {i}: {len(t):3d} chars | {t[:60]!r}")
    except h11.LocalProtocolError as e:
        print(f"[BAD] test {i}: {len(t):3d} chars | {t[:60]!r} | {e}")