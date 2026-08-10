"""Extract every SYSTEM_AUDIT_REPORT.md finding that belongs to the SECURITY domain.

Read-only helper. Writes a grouped inventory to _extra_files/security_findings.md
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "SYSTEM_AUDIT_REPORT.md"
OUT = ROOT / "_extra_files" / "security_findings.md"

# Security-domain file patterns (per AI File Placement Contract keyword routing:
# auth, authentication, authorization, biometric, blacklist, csrf, device_binding,
# dlp, fraud, ghost_watchdog, iam, incident, permission, permissions)
PATTERNS = [
    r"routers[\\/]admin_security_",
    r"routers[\\/]public_security_",
    r"routers[\\/]supplier_security",
    r"routers[\\/]system_security",
    r"routers[\\/]auth\.py",
    r"routers[\\/]_permission_primitives",
    r"routers[\\/]admin_permissions_",
    r"controllers[\\/]auth_controller",
    r"controllers[\\/]security[\\/]",
    r"controllers[\\/]iam_controller",
    r"controllers[\\/]permissions[\\/]",
    r"services[\\/]auth_service",
    r"services[\\/]auth_write_service",
    r"services[\\/]security[\\/]",
    r"services[\\/]fraud_",
    r"services[\\/]iam_service",
    r"services[\\/]triple_auth",
    r"services[\\/]ghost_watchdog",
    r"services[\\/]permission_service",
    r"services[\\/]effective_permissions",
    r"utils[\\/]auth\.py",
    r"utils[\\/]zero_trust_auth",
    r"utils[\\/]security_audit",
    r"models[\\/]fraud\.py",
    r"models[\\/]security[\\/]",
    r"models[\\/]incident\.py",
    r"middleware[\\/]csrf_middleware",
    r"middleware[\\/]impossible_travel",
    r"dependencies[\\/]fraud_events",
]
RX = re.compile("|".join(PATTERNS), re.IGNORECASE)

FINDING = re.compile(
    r"^- (?P<sev>[^\s*]+) \*\*(?P<code>[A-Z0-9]+)\*\*[: ]?(?P<loc>[^\u2014]*?)\u2014 (?P<msg>.*)$"
)


def main() -> None:
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    by_code: dict[str, list[str]] = defaultdict(list)
    by_file: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()

    current_file_section = ""
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("### `") and line.endswith(")"):
            current_file_section = line
        if not line.startswith("- "):
            continue
        m = FINDING.match(line)
        if not m:
            continue
        loc = m.group("loc").strip().strip("`")
        code = m.group("code")
        sev = m.group("sev")
        msg = m.group("msg")

        # Resolve the file this finding is about
        target = loc
        if not target or target.startswith(":"):
            # "Problems by File" style -> file comes from section header
            mm = re.search(r"### `([^`]+)`", current_file_section)
            target = (mm.group(1) if mm else "") + loc

        if not RX.search(target):
            continue
        key = f"{code}|{target}|{msg[:80]}"
        if key in seen:
            continue
        seen.add(key)
        entry = f"{sev} **{code}** `{target}` — {msg}"
        by_code[code].append(entry)
        fpath = target.split(":")[0]
        by_file[fpath].append(entry)

    out: list[str] = ["# SECURITY domain — audit findings inventory", ""]
    total = sum(len(v) for v in by_code.values())
    reds = sum(1 for v in by_code.values() for e in v if "🔴" in e)
    out.append(f"**Total:** {total} findings ({reds} RED) across {len(by_file)} files")
    out.append("")
    out.append("## By code")
    out.append("")
    for code in sorted(by_code, key=lambda c: -len(by_code[c])):
        out.append(f"### {code} ({len(by_code[code])})")
        out.append("")
        for e in sorted(set(by_code[code])):
            out.append(f"- {e}")
        out.append("")

    out.append("## By file")
    out.append("")
    for f in sorted(by_file, key=lambda k: -len(by_file[k])):
        r = sum(1 for e in by_file[f] if "🔴" in e)
        out.append(f"### `{f}` ({len(by_file[f])} findings, {r} RED)")
        out.append("")
        for e in sorted(set(by_file[f])):
            out.append(f"- {e}")
        out.append("")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUT} — {total} findings, {reds} RED, {len(by_file)} files")


if __name__ == "__main__":
    main()
