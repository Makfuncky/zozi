"""Compiles the forensic audit into an ordered, executable remediation plan.

The audit answers *what is wrong*. This answers *what to do, in what order, and
how to prove each step*. It is deliberately a separate artifact so the audit
output stays a statement of fact and the plan stays a statement of intent.

Design rules:

* **Only verified evidence becomes a blocking step.** A finding whose
  ``claim_state`` is UNKNOWN/INFERRED at L0 is a *verification task*, not a fix
  task — the plan must never tell an implementer to change code on a hunch.
* **Dependency order is derived, not assumed.** A wave may only be started when
  its prerequisites are satisfied. Boot, migration and test-collection problems
  are preconditions for trusting any other verification, so they land first.
* **Every step carries its own verification command.** A step that cannot be
  verified is a wish, not a plan.
* **Recommendations are a separate track.** They never gate release, and they
  are ordered after the blockers unless they unlock a blocker.

Usage:
    python _zozi_audit/zozi_compile.py
    python _zozi_audit/zozi_compile.py --wave 1
    python _zozi_audit/zozi_compile.py --list
    python _zozi_audit/zozi_compile.py --check feature
    python _zozi_audit/zozi_compile.py --status BLOCK-006=in_progress
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

EFFORT_HOURS = {"S": 1.0, "M": 2.5, "L": 6.0, "XL": 20.0}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
TRUSTED_TRUTH = {"L0"}
UNTRUSTED_CLAIM = {"UNKNOWN", "INFERRED", "CONTRADICTED"}

# A step can only be *executed* once the project can build, boot, and be tested.
# Everything else in a wave is either a prerequisite or parallel work.
GATE_CLUSTERS = {
    "CLUSTER-boot-preflight": "boot",
    "CLUSTER-test-broken": "test-collection",
    "CLUSTER-migration-import": "migrations",
    "CLUSTER-lockfile": "migrations",
}

PHASE_TITLES = {
    "0": "Restore the ability to verify anything (build · boot · test · migrate)",
    "1": "Fix the hard blockers that prevent correct behaviour",
    "2": "Close correctness and security defects",
    "3": "Close coverage, quality and performance defects",
    "4": "Verification tasks for untrusted claims",
    "5": "Improvement track — recommendations (not release-gating)",
}


@dataclass
class Step:
    id: str
    kind: str                     # fix | verify | gate | improve
    wave: int
    title: str
    detail: str
    files: list[str] = field(default_factory=list)
    fix: str = ""
    verify: str = ""
    rollback: str = ""
    effort: str = "M"
    priority: str = "P1"
    cluster: str = ""
    dimension: str = ""
    blockers: str = "no"
    depends_on: list[str] = field(default_factory=list)
    truth_level: str = ""
    claim_state: str = ""
    source: str = "finding"       # finding | recommendation | preflight

    def to_dict(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "wave": self.wave,
            "title": self.title, "detail": self.detail, "files": self.files,
            "fix": self.fix, "verify": self.verify, "rollback": self.rollback,
            "effort": self.effort, "effort_hours": EFFORT_HOURS.get(self.effort, 2.5),
            "priority": self.priority, "cluster": self.cluster,
            "dimension": self.dimension, "completion_blocker": self.blockers,
            "depends_on": self.depends_on, "truth_level": self.truth_level,
            "claim_state": self.claim_state, "source": self.source,
        }


class Compiler:
    # A finding that has been adjudicated FALSE_POSITIVE or ALREADY_FIXED is not
    # a work item. A finding nobody could adjudicate is not an instruction to
    # change code. Both rules exist because the prior run measured 31% of its own
    # findings as not actionable, and a plan that inherits that noise cannot be
    # followed by an AI without re-checking every step.
    REJECTED = {"FALSE_POSITIVE", "ALREADY_FIXED"}

    def __init__(self, root: Path, logs: Path):
        self.root = root
        self.logs = logs
        # `warnings` must exist before any loader runs: the loaders report
        # missing inputs through it, and a missing verdicts.jsonl is the
        # expected input for the no-gate path, not an exceptional case.
        self.warnings: list[str] = []
        self.rejected: list[dict] = []
        self.steps: list[Step] = []
        self.findings: list[dict] = self._load_jsonl("findings.jsonl")
        self.observations: list[dict] = self._load_jsonl("observations.jsonl")
        self.recommendations: list[dict] = self._load_jsonl("recommendations.jsonl")
        self.verdicts: dict[str, dict] = {
            v.get("key") or "": v
            for v in self._load_jsonl("verdicts.jsonl")
        }
        self.verification: dict = self._load_json("verification_summary.json")
        self.facts: dict = self._load_json("facts.json")
        self.run: dict = self._load_json("run.json")
        if not self.verdicts:
            self.warnings.append(
                "no logs/verdicts.jsonl — run `python _zozi_audit/zozi_verify.py` "
                "first. Without it every finding is treated as UNVERIFIABLE and "
                "no fix instruction is emitted.")

    def verdict_of(self, finding_id: str) -> str:
        """Adjudicated verdict, defaulting to UNVERIFIABLE (never CONFIRMED)."""
        v = self.verdicts.get(finding_id)
        return v.get("verdict", "UNVERIFIABLE") if v else "UNVERIFIABLE"

    # -- input ----------------------------------------------------------------
    def _load_jsonl(self, name: str) -> list[dict]:
        path = self.logs / name
        if not path.exists():
            self.warnings.append(f"missing input: {name}")
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    self.warnings.append(f"{name}: bad line ({exc.msg})")
        return rows

    def _load_json(self, name: str) -> dict:
        path = self.logs / name
        if not path.exists():
            self.warnings.append(f"missing input: {name}")
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.warnings.append(f"{name}: invalid JSON")
            return {}

    # -- classification -------------------------------------------------------
    def _is_trusted(self, f: dict) -> bool:
        return (f.get("truth_level") in TRUSTED_TRUTH
                and f.get("claim_state") not in UNTRUSTED_CLAIM)

    def _wave_for(self, f: dict) -> int:
        cluster = f.get("cluster") or ""
        if cluster in GATE_CLUSTERS:
            return 0
        # Verification state overrides the finding's own confidence: a P0 nobody
        # could adjudicate is a verification task, not an instruction.
        if self.verdict_of(f.get("id") or "") != "CONFIRMED":
            return 4
        if f.get("completion_blocker") == "yes" or f.get("priority") == "P0":
            return 1
        if f.get("priority") == "P1":
            return 2
        return 3

    def _kind_for(self, f: dict) -> str:
        cluster = f.get("cluster") or ""
        if cluster in GATE_CLUSTERS:
            return "gate"
        return "fix" if self.verdict_of(f.get("id") or "") == "CONFIRMED" else "verify"

    # -- build ----------------------------------------------------------------
    def build(self) -> None:
        # 1. Pre-flight rows are the ground truth about the toolchain itself.
        for row in self.facts.get("preflight", []) or []:
            if not isinstance(row, dict):
                continue
            status = str(row.get("status", "")).upper()
            if status in ("PASS", "SKIPPED", "ADAPTED"):
                continue
            check_name = str(row.get("check", "pre-flight check"))
            # PYTHONHASHSEED changes `hash()` between runs, so a hash-derived id
            # would not survive a re-run and progress tracking would break.
            slug = re.sub(r"[^A-Za-z0-9]+", "-", check_name).strip("-").upper()[:28]
            self.steps.append(Step(
                id=f"PRE-{slug}",
                kind="gate", wave=0,
                title=f"{check_name} -> {status}",
                detail=str(row.get("evidence", ""))[:600],
                fix="Resolve the pre-flight failure before trusting any other "
                    "verification step; nothing downstream can be proven while it fails.",
                verify="python _zozi_audit/zozi_audit.py --full   # this row must become PASS",
                rollback="Revert the specific change; this step is diagnostic-first.",
                effort="M", priority="P0",
                cluster="CLUSTER-preflight", dimension="27_project_completion_blockers",
                blockers="yes", source="preflight",
                truth_level="L0", claim_state="VERIFIED",
            ))

        # 2. Findings — adjudicated claims only become steps.
        for f in self.findings:
            fid = f.get("id") or "FIND-?"
            verdict = self.verdict_of(fid)
            if verdict in self.REJECTED:
                v = self.verdicts.get(fid, {})
                self.rejected.append({
                    "id": fid, "verdict": verdict, "cluster": f.get("cluster"),
                    "priority": f.get("priority"),
                    "claim": (f.get("current") or "")[:180],
                    "evidence": v.get("evidence", ""),
                })
                continue
            self.steps.append(Step(
                id=fid,
                kind=self._kind_for(f),
                wave=self._wave_for(f),
                title=(f.get("current") or "")[:180],
                detail=(f.get("delta") or "")[:400],
                files=[f["file"]] if f.get("file") else [],
                fix=f.get("fix", ""),
                verify=f.get("verify", ""),
                rollback=f.get("rollback", ""),
                effort=f.get("effort") or "M",
                priority=f.get("priority") or "P1",
                cluster=f.get("cluster", ""),
                dimension=f.get("dimension", ""),
                blockers=f.get("completion_blocker", "no"),
                depends_on=[d for d in (f.get("depends_on") or "").split(",") if d.strip()],
                truth_level=f.get("truth_level", ""),
                claim_state=f.get("claim_state", ""),
            ))

        # 3. Recommendations — improvement track, never gating.
        for r in self.recommendations:
            self.steps.append(Step(
                id=r.get("id") or "REC-?",
                kind="improve", wave=5,
                title=r.get("title", ""),
                detail=r.get("rationale", ""),
                files=[p for p in (r.get("evidence") or "").split("; ") if "/" in p][:4],
                fix=r.get("proposal", ""),
                verify=f"python _zozi_audit/zozi_audit.py --full   # "
                       f"re-measure the metric this recommendation cites",
                rollback="Feature-flag or stage behind a config default so it can be "
                         "switched off without a code revert.",
                effort=r.get("effort") or "M",
                priority="P3",
                cluster=f"CLUSTER-rec-{r.get('area', '')}",
                dimension=r.get("dimension", ""),
                blockers="no",
                depends_on=list(r.get("prerequisites") or []),
                truth_level="L1",
                claim_state="INFERRED",
                source="recommendation",
            ))

        # 4. Cross-step dependency inference: a fix in a file that a gate step
        #    reports on cannot start until the gate is green.
        gate_ids = {s.id for s in self.steps if s.kind == "gate"}
        rec_ids = {s.id for s in self.steps if s.source == "recommendation"}
        for s in self.steps:
            deps = set(s.depends_on)
            if s.kind in ("fix", "verify") and gate_ids and s.wave > 0:
                deps.update(sorted(gate_ids)[:1])
            for d in list(deps):
                if d in rec_ids:
                    deps.discard(d)  # recommendations never block a fix
            s.depends_on = sorted(deps)

        self.steps.sort(key=lambda s: (s.wave, PRIORITY_ORDER.get(s.priority, 9),
                                       -EFFORT_HOURS.get(s.effort, 2.5), s.id))

    # -- reporting ------------------------------------------------------------
    def summary(self) -> dict:
        by_wave: dict[int, dict] = {}
        for s in self.steps:
            slot = by_wave.setdefault(s.wave, {
                "count": 0, "hours": 0.0, "blockers": 0,
                "gates": 0, "verifications": 0, "improvements": 0})
            slot["count"] += 1
            slot["hours"] += EFFORT_HOURS.get(s.effort, 2.5)
            if s.blockers == "yes":
                slot["blockers"] += 1
            if s.kind == "gate":
                slot["gates"] += 1
            elif s.kind == "verify":
                slot["verifications"] += 1
            elif s.kind == "improve":
                slot["improvements"] += 1
        for slot in by_wave.values():
            slot["hours"] = round(slot["hours"], 1)
        conf = self.verification or {}
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_run": self.run.get("run_id", ""),
            "source_commit": self.run.get("commit", ""),
            "findings_in": len(self.findings),
            "findings_rejected": len(self.rejected),
            "recommendations_in": len(self.recommendations),
            "steps_out": len(self.steps),
            "release_gating_steps": sum(1 for s in self.steps if s.kind != "improve"),
            "improvement_steps": sum(1 for s in self.steps if s.kind == "improve"),
            "untrusted_claims": sum(1 for s in self.steps if s.kind == "verify"),
            "confirmed_steps": sum(1 for s in self.steps if s.kind == "fix"),
            "verification_present": bool(self.verdicts),
            "confirmed_pct": conf.get("independently_confirmed_pct"),
            "false_positive_pct": conf.get("false_positive_rate_pct"),
            "not_actionable_pct": conf.get("not_actionable_pct"),
            "p0_noise_pct": conf.get("p0_noise_pct"),
            "by_wave": {str(k): v for k, v in sorted(by_wave.items())},
            "total_hours": round(sum(EFFORT_HOURS.get(s.effort, 2.5)
                                     for s in self.steps if s.kind != "improve"), 1),
            "warnings": self.warnings,
        }

    # -- work packages --------------------------------------------------------
    # A flat list of 1800 steps is not a plan. Grouping by cluster (and, for a
    # large cluster, by the file that dominates it) produces units one person or
    # one agent can actually finish and verify.
    PACKAGE_SPLIT_THRESHOLD = 25

    def work_packages(self) -> list[dict]:
        groups: dict[tuple, list[Step]] = {}
        cluster_size: dict[str, int] = {}
        for s in self.steps:
            cluster_size[s.cluster or ""] = cluster_size.get(s.cluster or "", 0) + 1
        for s in self.steps:
            if s.kind == "improve":
                # Recommendations are grouped by their subject area. Deriving an
                # id from their `evidence` prose produced ids like
                # "RECOMMENDATIONS-finance (missing:" — useless as a handle.
                key = (s.wave, "recommendations", _rec_area(s))
            else:
                key = (s.wave, s.cluster or "CLUSTER-uncategorised",
                       _dominant_file(s)
                       if cluster_size.get(s.cluster or "", 0) > self.PACKAGE_SPLIT_THRESHOLD
                       else "")
            groups.setdefault(key, []).append(s)
        packages: list[dict] = []
        for (wave, cluster, sub), items in sorted(groups.items()):
            items.sort(key=lambda s: (PRIORITY_ORDER.get(s.priority, 9), s.id))
            files: list[str] = []
            for s in items:
                for f in s.files:
                    if f and f not in files:
                        files.append(f)
            dominant = {}
            for s in items:
                for f in s.files:
                    dominant[f] = dominant.get(f, 0) + 1
            top_file = max(dominant.items(), key=lambda t: t[1])[0] if dominant else ""
            slug = re.sub(r"[^A-Za-z0-9]+", "-", cluster.replace("CLUSTER-", "")).strip("-")
            suffix = ""
            if sub:
                safe = re.sub(r"[^A-Za-z0-9]+", "-", sub).strip("-")
                suffix = f"-{safe[:20].upper()}" if safe else ""
            pkg_id = f"WP{wave}-{slug[:34].upper()}{suffix}"
            packages.append({
                "id": pkg_id,
                "wave": wave,
                "cluster": cluster,
                "title": items[0].title[:140],
                "steps": items,
                "step_count": len(items),
                "files": files[:12],
                "file_count": len(files),
                "dominant_file": top_file,
                "hours": round(sum(EFFORT_HOURS.get(s.effort, 2.5) for s in items), 1),
                "blockers": sum(1 for s in items if s.blockers == "yes"),
                "verifications": sum(1 for s in items if s.kind == "verify"),
                "gates": sum(1 for s in items if s.kind == "gate"),
            })
        return packages

    def render_packages(self, packages: list[dict], wave: int, status: dict,
                        per_package: int = 8) -> str:
        out: list[str] = []
        pkgs = [p for p in packages if p["wave"] == wave]
        if not pkgs:
            return ""
        out += [f"#### Work packages in wave {wave} ({len(pkgs)})", "",
                "| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |",
                "|---------|-------|-------|---------|---------------|--------|-------|"]
        for p in sorted(pkgs, key=lambda x: (-x["blockers"], -x["step_count"])):
            out.append(f"| `{p['id']}` | {p['step_count']} | {p['file_count']} | "
                       f"{p['blockers']} | {p['verifications']} | {p['hours']} | "
                       f"{_one_line(p['title'])} |")
        out.append("")
        for p in sorted(pkgs, key=lambda x: (-x["blockers"], -x["step_count"])):
            done = sum(1 for s in p["steps"]
                       if status.get(s.id, {}).get("state") in ("done", "dismissed"))
            out += [f"##### `{p['id']}` — {p['title']}", "",
                    f"- **cluster:** `{p['cluster']}` · **steps:** {p['step_count']} "
                    f"({done} closed) · **files:** {p['file_count']} · "
                    f"**est.:** {p['hours']}h"]
            if p["files"]:
                out.append(f"- **files:** {', '.join(f'`{f}`' for f in p['files'][:8])}")
            out.append("")
            for s in p["steps"][:per_package]:
                st = status.get(s.id, {}).get("state", "pending")
                mark = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]",
                        "dismissed": "[-]"}.get(st, "[ ]")
                out += [f"{mark} `{s.id}` — {_one_line(s.title)}"]
                if s.kind == "verify":
                    # Never tell an implementer to change code on an unconfirmed
                    # claim. Confirm it first; the fix is conditional.
                    out.append(f"    - confirm: the audit could not establish this "
                               f"statically ({s.truth_level}/{s.claim_state}). "
                               f"Read the cited location and decide.")
                elif s.fix:
                    out.append(f"    - do: {_one_line(s.fix, 240)}")
                if s.verify:
                    out.append(f"    - verify: `{_one_line(s.verify, 200)}`")
            if len(p["steps"]) > per_package:
                out.append(f"    - … and {len(p['steps']) - per_package} more step(s) "
                           f"in this package; full list in "
                           f"`_zozi_audit/logs/plan.json` "
                           f"(filter by cluster `{p['cluster']}`)")
            out.append("")
        return "\n".join(out)

    def render(self) -> str:
        sm = self.summary()
        packages = self.work_packages()
        sm["work_packages"] = len(packages)
        out: list[str] = []
        out += [
            "# ZOZI — Remediation Plan (compiled from the forensic audit)",
            "",
            f"_Generated {sm['generated_at']} from audit run `{sm['source_run']}` "
            f"at commit `{sm['source_commit']}`._",
            "",
            "This is the **solution half** of the audit. The audit states what is "
            "wrong; this states what to do, in what order, and how to prove each "
            "step is finished.",
            "",
            "## How to use this plan",
            "",
            "1. Work **wave by wave**. A wave may only start when the previous wave "
            "is green — this is what makes the result trustworthy rather than "
            "merely different.",
            f"2. Wave 0 is the gate: until it passes, no other verification means "
            f"anything.",
            "3. Each step carries its own `verify` command. Run it. A step whose "
            "verification does not change is not done.",
            "4. Steps marked **verify** are *not* instructions to change code. They "
            "are claims the audit could not confirm statically; confirm or dismiss "
            "them first.",
            "5. Steps marked **improve** are recommendations. They never gate a "
            "release.",
            "6. Mark progress with `--status`; the compiler round-trips it.",
            "",
            "## Verification gate",
            "",
            *_gate_block(sm),
            "",
            "### How this plan may be followed",
            "",
            "1. **Every `fix` step was independently re-derived** before it reached "
            "this document. Nothing else is presented as a fix.",
            "2. **A `verify` step is not an instruction to change code.** It is a claim "
            "the tooling could not adjudicate; confirm or dismiss it first.",
            f"3. **{sm['findings_rejected']} finding(s) were rejected outright** "
            "(false positive or already fixed) and are listed in the Rejected "
            "appendix with counter-evidence. They are not work.",
            "4. **A CONFIRMED verdict proves the claim, not the fix.** The `fix` text "
            "still needs engineering review — most of all for law, schema and "
            "security changes.",
            "",
            "## Totals",
            "",
            f"- Findings consumed: **{sm['findings_in']}**",
            f"- Findings rejected (false positive / already fixed): "
            f"**{sm['findings_rejected']}**",
            f"- Confirmed fix steps: **{sm['confirmed_steps']}**",
            f"- Recommendations consumed: **{sm['recommendations_in']}**",
            f"- Release-gating steps: **{sm['release_gating_steps']}** "
            f"(~{sm['total_hours']}h at S=1h M=2.5h L=6h XL=20h)",
            f"- Improvement steps: **{sm['improvement_steps']}** (not gating)",
            f"- Untrusted claims needing verification first: **{sm['untrusted_claims']}**",
            f"- Work packages (the unit of work): **{len(packages)}**",
            "",
            "## Work package index",
            "",
            "Finish a whole package, not a single line. A package is one cluster "
            "touched by one person or one agent, with a single coherent outcome.",
            "",
            "| Wave | Package | Steps | Files | Est. h | Focus |",
            "|------|---------|-------|-------|--------|-------|",
        ]
        for p in sorted(packages, key=lambda x: (x["wave"], -x["blockers"],
                                                 -x["step_count"])):
            out.append(f"| {p['wave']} | `{p['id']}` | {p['step_count']} | "
                       f"{p['file_count']} | {p['hours']} | {_one_line(p['title'], 70)} |")
        out += [
            "",
            "## Wave plan",
            "",
            "| Wave | Title | Steps | Blockers | Gates | Verifications | Est. hours |",
            "|------|-------|-------|----------|-------|---------------|------------|",
        ]
        for w, slot in sm["by_wave"].items():
            out.append(f"| {w} | {PHASE_TITLES.get(w, 'Other')} | {slot['count']} | "
                       f"{slot['blockers']} | {slot['gates']} | "
                       f"{slot['verifications']} | {slot['hours']} |")
        out.append("")

        status = self._load_status()
        for w in sorted(sm["by_wave"], key=int):
            steps = [s for s in self.steps if str(s.wave) == w]
            if not steps:
                continue
            out += ["---", f"## Wave {w} · {PHASE_TITLES.get(w, 'Other')}", ""]
            if w == "0":
                out += ["> **Nothing else can be verified until this wave is green.** "
                        "A static audit run on a project that does not boot, does not "
                        "migrate, or does not collect its tests produces numbers "
                        "without meaning.", ""]
            if w == "5":
                out += ["> Improvement track. These do not gate a release. Prioritise "
                        "by the workload they remove, not by severity.", ""]
            out.append(self.render_packages(packages, int(w), status))
            if len(steps) <= 40:
                for s in steps:
                    st = status.get(s.id, {}).get("state", "pending")
                    mark = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]",
                            "dismissed": "[-]"}.get(st, "[ ]")
                    out += [f"{mark} `{s.id}` — {_one_line(s.title, 200)}"]
            else:
                out += [f"_This wave has {len(steps)} steps. Work them by package "
                        f"above; the complete step list is in "
                        f"`_zozi_audit/logs/plan.json`._", ""]

        out += [
            "---",
            "## Rejected findings (not work)",
            "",
        ]
        if not self.rejected:
            out += ["_Nothing was rejected in this run._", ""]
        else:
            out += [
                f"{len(self.rejected)} finding(s) were disproved or found already "
                f"fixed by `zozi_verify.py`. They are excluded from every wave above "
                f"and are recorded here so the exclusion is auditable.",
                "",
                "| ID | Verdict | Cluster | Priority | Counter-evidence |",
                "|----|---------|---------|----------|------------------|",
            ]
            for r in self.rejected[:120]:
                out.append(f"| `{r['id']}` | {r['verdict']} | "
                           f"`{_one_line(r['cluster'], 30)}` | {r['priority']} | "
                           f"{_one_line(r['evidence'], 110)} |")
            if len(self.rejected) > 120:
                out.append(f"| … | | | | {len(self.rejected)-120} more in "
                           f"`_zozi_audit/logs/verdicts.jsonl` |")
            out.append("")
        out += [
            "---",
            "",
            "## Measurement gaps this plan cannot close",
            "",
            "The following were measured but cannot be asserted statically. They are "
            "listed so nobody mistakes silence for a pass.",
            "",
        ]
        gaps = [
            "Runtime behaviour: no live boot, HTTP journey, or browser run is part "
            "of this plan beyond the pre-flight gate.",
            "Load and p95 latency: needs `zozi_audit.py --load` against a running "
            "stack.",
            "Third-party gateway behaviour (Stripe/Tap/PayTabs/Thawani/PayPal): "
            "needs sandbox credentials and real webhook delivery.",
            "Mobile (Expo) runtime: no emulator/simulator run is performed.",
            "LLM-intent agreement: advisory only (L2), never a gate.",
        ]
        out += [f"- {g}" for g in gaps]
        out += ["", "---", "",
                f"_Compiled by `_zozi_audit/zozi_compile.py`. Re-run after every "
                f"audit to refresh this plan._", ""]
        return "\n".join(out)

    # -- status round-trip ----------------------------------------------------
    def _status_path(self) -> Path:
        return self.logs / "plan_status.json"

    def _load_status(self) -> dict:
        path = self._status_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("steps", {})
        except json.JSONDecodeError:
            return {}

    def apply_status(self, assignment: str) -> None:
        step_id, _, state = assignment.partition("=")
        step_id = step_id.strip()
        state = state.strip() or "in_progress"
        if state not in ("pending", "in_progress", "done", "dismissed"):
            raise SystemExit(f"unknown state: {state}")
        if not any(s.id == step_id for s in self.steps):
            raise SystemExit(f"unknown step id: {step_id} "
                             f"(run without --status to list the plan)")
        path = self._status_path()
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"steps": {}}
        data.setdefault("steps", {})[step_id] = {
            "state": state, "at": datetime.now(timezone.utc).isoformat()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[compile] {step_id} -> {state}")


def _dominant_file(steps) -> str:
    """The file that most of these steps touch — the natural package name.

    Accepts a Step or a list of Steps so a package id can be derived from a
    group before it is constructed.
    """
    if isinstance(steps, Step):
        steps = [steps]
    counts: dict[str, int] = {}
    for s in steps:
        for f in s.files:
            if f:
                counts[f] = counts.get(f, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda t: t[1])[0]


def _rec_area(s: "Step") -> str:
    """The subject area of an improvement step, from its id (REC-<AREA>-NNN)."""
    m = re.match(r"REC-([A-Z]+)-\d+", s.id or "")
    if m:
        return f"rec-{m.group(1).lower()}"
    return "rec-general"


def _gate_block(sm: dict) -> list[str]:
    """The verification numbers, or an honest warning that they are missing."""
    if not sm.get("verification_present"):
        return [
            "> **NO VERIFICATION GATE.** `logs/verdicts.jsonl` is absent, so **no "
            "finding in this plan has been adjudicated.** Every step is a claim, "
            "and the default verdict is UNVERIFIABLE — which is why the step counts "
            "below contain no fix instructions.",
            ">",
            "> Run `python _zozi_audit/zozi_verify.py` and re-compile before anyone "
            "acts on this plan.",
        ]
    return [
        f"- Findings adjudicated: **{sm.get('confirmed_pct')}% independently "
        f"confirmed**",
        f"- False positives + wrong locations: **{sm.get('false_positive_pct')}%**",
        f"- Not actionable as stated (incl. already fixed): "
        f"**{sm.get('not_actionable_pct')}%**",
        f"- P0 noise (false or mislocated): **{sm.get('p0_noise_pct')}%**",
        "",
        "A low *confirmed* share is expected and is not a defect: a claim with no "
        "independent re-check cannot honestly be called confirmed. It is routed to a "
        "verification task instead of being silently trusted.",
    ]


def _one_line(text: str, limit: int = 120) -> str:
    """Collapse to a single line and clip — a table cell must not break layout."""
    flat = " ".join(str(text or "").split())
    if len(flat) <= limit:
        return flat
    return flat[:limit - 1].rstrip() + "…"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compile the audit into a remediation plan")
    p.add_argument("--root", default=str(HERE.parent))
    p.add_argument("--logs", default=None,
                   help="audit logs directory (default <root>/_zozi_audit/logs)")
    p.add_argument("--out", default=None,
                   help="output markdown (default <root>/_zozi_audit/zozi_remediation_plan.md)")
    p.add_argument("--json", default=None, help="also write the machine-readable plan")
    p.add_argument("--wave", type=int, default=None, help="print only one wave")
    p.add_argument("--status", action="append", default=[],
                   metavar="ID=STATE",
                   help="record progress, e.g. --status BLOCK-006=in_progress")
    p.add_argument("--list", action="store_true", help="print step ids and exit")
    p.add_argument("--check", default=None,
                   help="print the steps belonging to a cluster prefix, e.g. feature")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    logs = Path(args.logs).resolve() if args.logs else root / "_zozi_audit" / "logs"
    if not logs.exists():
        print(f"FATAL: audit logs not found at {logs}. Run zozi_audit.py first.",
              file=sys.stderr)
        return 2

    comp = Compiler(root, logs)
    comp.build()
    for assignment in args.status:
        comp.apply_status(assignment)

    if args.list:
        for s in comp.steps:
            print(f"{s.wave}\t{s.kind:9s}\t{s.priority}\t{s.effort}\t{s.id}\t{s.title[:90]}")
        return 0
    if args.check:
        needle = args.check.lower()
        hits = [s for s in comp.steps
                if needle in (s.cluster or "").lower() or needle in s.id.lower()]
        for s in hits:
            print(f"[wave {s.wave}/{s.kind}] {s.id} {s.title}\n  do: {s.fix}\n"
                  f"  verify: {s.verify}\n")
        print(f"{len(hits)} step(s) match {args.check!r}")
        return 0

    text = comp.render()
    if args.wave is not None:
        head, _, tail = text.partition(f"## Wave {args.wave} ·")
        if not tail:
            print(f"no wave {args.wave}")
            return 1
        rest = tail.partition("\n---\n")[0]
        print(head.split("## Wave plan")[0] + f"## Wave {args.wave} ·" + rest)
        return 0

    out = Path(args.out).resolve() if args.out else root / "_zozi_audit" / "zozi_remediation_plan.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    sm = comp.summary()
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "plan.json").write_text(
        json.dumps({"summary": sm, "steps": [s.to_dict() for s in comp.steps]},
                   indent=2), encoding="utf-8")
    print(f"[compile] {sm['steps_out']} step(s) -> {out}")
    print(f"[compile] release-gating: {sm['release_gating_steps']} "
          f"(~{sm['total_hours']}h) | improvement: {sm['improvement_steps']} | "
          f"untrusted claims: {sm['untrusted_claims']}")
    if sm["warnings"]:
        for wmsg in sm["warnings"]:
            print(f"[compile] WARNING: {wmsg}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
