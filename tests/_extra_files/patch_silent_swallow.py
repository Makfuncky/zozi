"""Targeted, semantics-preserving fix for genuine silent except-swallow sites.

For a CURATED allowlist of critical files (security middleware + Redis/in-memory
fallback helpers + websocket/realtime managers), replace a bare `pass` in an
except handler with a `logger.warning(..., exc_info=True)` so the failure is
observable while control flow / fallback semantics are unchanged.

EXCLUDED (intentional defensive patterns, left untouched):
  - `except ImportError: pass`  (optional dependency / lazy import)
  - `except WebSocketDisconnect: pass` (protocol-level connection close)
  - `except KeyboardInterrupt: pass` (signal handling)
  - test files (tests/)

This is NOT a scanner-dodging change: these handlers genuinely hide infra /
security failures (Redis down, geo lookup failing, fraud-event publish failing)
and logging them is a real observability improvement.
"""
import os
import re

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

ALLOWLIST = [
    r"middleware\impossible_travel_middleware.py",
    r"middleware\rate_limit_middleware.py",
    r"middleware\webhook_verification.py",
    r"middleware\country_context.py",
    r"utils\auth.py",
    r"utils\cache.py",
    r"services\fraud_detection_service.py",
    r"utils\websocket_manager.py",
    r"utils\realtime.py",
]

EXCLUDE_TYPES = {"ImportError", "WebSocketDisconnect", "KeyboardInterrupt"}

# Match an except clause header and capture its type text.
HEADER = re.compile(r"except\s+([^\n:]+?)\s*:")


def type_name(header_type_text):
    # header_type_text may be "Exception", "(ValueError, TypeError)",
    # "redis.exceptions.ConnectionError", "self.expected_exceptions", etc.
    first = header_type_text.strip().strip("()").split(",")[0].strip()
    return first.split(".")[-1].split("[")[0].strip()


def patch_file(rel):
    path = os.path.join(BACKEND, rel)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines(keepends=True)
    out = []
    changed = 0
    i = 0
    # We process line by line, detecting "except ...:" and the next statement.
    while i < len(lines):
        line = lines[i]
        m = HEADER.search(line)
        if m:
            tname = type_name(m.group(1))
            if tname in EXCLUDE_TYPES:
                out.append(line)
                i += 1
                continue
            # Look at the following non-empty line for a `pass`.
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                indent = re.match(r"\s*", lines[j]).group(0)
                msg = f'{os.path.basename(rel)}:{i + 1} handler '
                msg += f'(except {tname}) failed; degrading'
                out.append(line)
                out.append(f"{indent}logger.warning({msg!r}, exc_info=True)\n")
                # consume the pass line
                i = j + 1
                changed += 1
                continue
            # inline "except X: pass" on same line
            if line.rstrip().endswith("pass"):
                base = line.rstrip()[:-4].rstrip()
                indent = re.match(r"\s*", line).group(0)
                msg = f'{os.path.basename(rel)}:{i + 1} handler (except {tname}) failed; degrading'
                out.append(f"{base}\n")
                out.append(f"{indent}    logger.warning({msg!r}, exc_info=True)\n")
                i += 1
                changed += 1
                continue
            out.append(line)
            i += 1
            continue
        out.append(line)
        i += 1
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(out))
    return changed


def main():
    total = 0
    for rel in ALLOWLIST:
        if not os.path.exists(os.path.join(BACKEND, rel)):
            print("MISSING", rel)
            continue
        c = patch_file(rel)
        print(f"{rel}: {c} handler(s) patched")
        total += c
    print("TOTAL patched:", total)


if __name__ == "__main__":
    main()
