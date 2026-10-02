"""Agent performance + dispatch logger for the audit-compiler rebuild.

Append-only JSONL. One record per agent lifecycle event. Every dispatch must
have a matching `dispatch`, and every `complete` must carry verifiable
evidence counts. `verify_log.py` cross-checks the two.

Usage:
  python _audit/compiler/agent_log.py dispatch <agent_id> <scope> <expected>
  python _audit/compiler/agent_log.py complete <agent_id> <ok> <findings> <evidence> <notes>
  python _audit/compiler/agent_log.py reject <agent_id> <code> <detail>
  python _audit/compiler/agent_log.py heartbeat <agent_id> <step> <detail>
  python _audit/compiler/agent_log.py report
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(ROOT, "_audit", "compiler", "logs")
LOG = os.path.join(LOG_DIR, "agent_performance.jsonl")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit(rec: dict) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    rec["ts"] = now()
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read() -> list[dict]:
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def report() -> int:
    recs = read()
    disp = {r["agent_id"]: r for r in recs if r["event"] == "dispatch"}
    done = [r for r in recs if r["event"] == "complete"]
    rej = [r for r in recs if r["event"] == "reject"]
    beats = [r for r in recs if r["event"] == "heartbeat"]

    ok = [d for d in done if d.get("ok") is True]
    bad = [d for d in done if d.get("ok") is not True]

    print(f"{'agent_id':<34} {'scope':<26} {'exp':>5} {'got':>5} {'evid':>5}  status")
    print("-" * 92)
    for aid, d in sorted(disp.items()):
        mine = [c for c in done if c["agent_id"] == aid]
        rj = [r for r in rej if r["agent_id"] == aid]
        hb = len([b for b in beats if b["agent_id"] == aid])
        if rj:
            status = f"REJECTED({rj[0].get('code')})"
        elif mine and mine[-1].get("ok"):
            c = mine[-1]
            status = "OK"
        elif mine:
            status = "INCOMPLETE"
        else:
            status = "STALLED" if hb < 2 else "RUNNING"
        got = sum(m.get("findings", 0) for m in mine)
        ev = sum(m.get("evidence", 0) for m in mine)
        print(f"{aid:<34} {str(d.get('scope'))[:26]:<26} {d.get('expected',''):>5} "
              f"{got:>5} {ev:>5}  {status}")

    print("-" * 92)
    print(f"dispatched={len(disp)}  complete_ok={len(ok)}  complete_incomplete={len(bad)}  "
          f"rejected={len(rej)}  heartbeats={len(beats)}")
    exp = sum(d.get("expected", 0) or 0 for d in disp.values())
    got = sum(c.get("findings", 0) for c in done)
    ev = sum(c.get("evidence", 0) for c in done)
    print(f"expected_findings={exp}  reported_findings={got}  evidence_items={ev}")
    if exp:
        print(f"coverage={got / exp * 100:.1f}%")
    unreached = sorted(set(disp) - {c['agent_id'] for c in done})
    if unreached:
        print(f"UNREACHED: {unreached}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    action = argv[1]
    if action == "dispatch":
        emit({"event": "dispatch", "agent_id": argv[2], "scope": argv[3],
              "expected": int(argv[4]) if len(argv) > 4 else 0})
    elif action == "complete":
        emit({"event": "complete", "agent_id": argv[2],
              "ok": argv[3].lower() in {"1", "true", "yes"},
              "findings": int(argv[4]) if len(argv) > 4 else 0,
              "evidence": int(argv[5]) if len(argv) > 5 else 0,
              "notes": argv[6] if len(argv) > 6 else ""})
    elif action == "reject":
        emit({"event": "reject", "agent_id": argv[2], "code": argv[3],
              "detail": argv[4] if len(argv) > 4 else ""})
    elif action == "heartbeat":
        emit({"event": "heartbeat", "agent_id": argv[2], "step": argv[3],
              "detail": argv[4] if len(argv) > 4 else ""})
    elif action == "report":
        return report()
    else:
        print(f"unknown action: {action}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
