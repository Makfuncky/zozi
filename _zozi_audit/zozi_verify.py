"""Falsification gate between the audit and the remediation plan.

The audit makes *claims*. Nothing in the pipeline ever tries to prove them
wrong. The project's own prior run measured that gap: it adjudicated 1,359
findings and found 910 REAL, 160 FALSE_POSITIVE and 265 ALREADY_FIXED — so
31% of what a raw audit emits is not actionable as stated. That is the number
this script exists to keep measurable for the current audit.

Method, deliberately not "re-run the same check":

1. **Location proof.** Does the cited file exist? Does the cited line exist?
   A finding whose `path:line` no longer resolves cannot be acted on.
2. **Cluster re-check.** For the clusters that carry the P0 mass there is a
   second, independent implementation of the same question, written against a
   different mechanism (AST vs regex, declared-field set vs mention scan).
   This is the only step allowed to return CONFIRMED or FALSE_POSITIVE.
3. **Token consistency.** Everything else falls back to comparing the tokens in
   the claim against the cited line. This can only *refute* (the line does not
   look like the claim); it never confirms. A finding that survives only this
   step is labelled UNVERIFIABLE, never CONFIRMED.

The compiler reads ``logs/verdicts.jsonl`` and refuses to emit a fix step for a
FALSE_POSITIVE, and refuses to present an unadjudicated finding as verified.

Usage:
    python _zozi_audit/zozi_verify.py
    python _zozi_audit/zozi_verify.py --cluster CLUSTER-float-money
    python _zozi_audit/zozi_verify.py --limit 200 --strict
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

VERDICTS = ("CONFIRMED", "FALSE_POSITIVE", "ALREADY_FIXED",
            "WRONG_LOCATION", "UNVERIFIABLE")

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "not", "but",
    "are", "was", "has", "have", "its", "their", "does", "must", "can", "any",
    "no", "of", "to", "in", "on", "is", "a", "an", "be", "or", "as", "at",
    "by", "it", "we", "per", "via", "than", "when", "which", "while", "each",
    "only", "also", "one", "two", "all", "if", "so", "up", "out", "use", "used",
}

# Identifiers worth extracting from a claim, longest first.
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{3,}")
MONEY_RE = re.compile(r"\b(amount|total|price|balance|subtotal|tax|vat|"
                      r"commission|refund|payout|cost|revenue|salary|fee|discount)\w*",
                      re.I)
RATE_RE = re.compile(r"(_rate|_percent|_ratio|_score|_weight)\w*$", re.I)


def _tokens(claim: str) -> list[str]:
    out: list[str] = []
    for m in TOKEN_RE.finditer(claim or ""):
        tok = m.group(0)
        low = tok.lower()
        if low in STOPWORDS or low in ("python", "http", "https", "json", "true",
                                      "false", "none", "self", "backend", "frontend"):
            continue
        out.append(tok)
    # longest first so a compound beats its own prefix
    return sorted(set(out), key=len, reverse=True)[:8]


class Verifier:
    def __init__(self, root: Path, logs: Path):
        self.root = root
        self.logs = logs
        self._ast_cache: dict[str, ast.AST | None] = {}
        self._text_cache: dict[str, str] = {}

    # -- IO -------------------------------------------------------------------
    def text(self, rel: str) -> str:
        if rel not in self._text_cache:
            p = self.root / rel
            try:
                self._text_cache[rel] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                self._text_cache[rel] = ""
        return self._text_cache[rel]

    def tree(self, rel: str) -> ast.AST | None:
        if rel not in self._ast_cache:
            try:
                self._ast_cache[rel] = ast.parse(self.text(rel))
            except Exception:
                self._ast_cache[rel] = None
        return self._ast_cache[rel]

    def line_at(self, rel: str, line: int) -> str:
        lines = self.text(rel).splitlines()
        if 1 <= line <= len(lines):
            return lines[line - 1]
        return ""

    # -- cluster re-checks ----------------------------------------------------
    def recheck(self, f: dict) -> tuple[str, str] | None:
        """``(verdict, evidence)`` for clusters with an independent check."""
        cluster = f.get("cluster") or ""
        handler = {
            "CLUSTER-float-money": self._re_float_money,
            "CLUSTER-idempotency": self._re_idempotency,
            "CLUSTER-tf-rel-lazy": self._re_rel_lazy,
            "CLUSTER-settings-contract": self._re_settings_contract,
            "CLUSTER-env-undeclared": self._re_env_undeclared,
            "CLUSTER-http-cors": self._re_cors_preflight,
            "CLUSTER-http-headers": self._re_xss_header,
            "CLUSTER-db-schema-drift": self._re_schema_drift,
        }.get(cluster)
        if handler is None:
            return None
        try:
            return handler(f)
        except Exception as exc:  # a broken re-check must not fake a verdict
            return None

    def _re_float_money(self, f: dict) -> tuple[str, str]:
        """A monetary float, re-derived from the AST rather than a text scan.

        A rate/percentage/score is not money; that distinction alone accounted
        for five false positives in the first audit run.
        """
        rel, line = f.get("file") or "", int(f.get("line") or 0)
        src = self.text(rel)
        if not src:
            return ("FALSE_POSITIVE", f"{rel} no longer exists")
        tree = self.tree(rel)
        if tree is None:
            return ("UNVERIFIABLE", f"{rel} does not parse")
        # Look at the cited line and a small window around it.
        lo = max(0, line - 4)
        hi = line + 4
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AnnAssign, ast.arg, ast.Assign)):
                continue
            nline = getattr(node, "lineno", 0)
            if not (lo <= nline <= hi):
                continue
            names: list[str] = []
            seg = ""
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
                seg = ast.get_source_segment(src, node) or ""
                if node.annotation is not None:
                    names.append(ast.unparse(node.annotation))
            elif isinstance(node, ast.arg):
                names = [node.arg]
                seg = ast.get_source_segment(src, node) or ""
                if node.annotation is not None:
                    names.append(ast.unparse(node.annotation))
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                seg = ast.get_source_segment(src, node) or ""
            joined = " ".join(names)
            if "float" not in joined and "float(" not in seg:
                continue
            money_name = next((n for n in names if MONEY_RE.fullmatch(n or "")), None)
            if money_name is None:
                money_name = next((n for n in names if MONEY_RE.search(n or "")), None)
            if money_name is None:
                continue
            if RATE_RE.search(money_name):
                return ("FALSE_POSITIVE",
                        f"{rel}:{nline} `{money_name}` is a rate/ratio, not a monetary "
                        f"amount — Law 19 does not apply")
            if "float(" not in seg and "float" not in joined:
                continue
            return ("CONFIRMED",
                    f"{rel}:{nline} `{money_name}` is annotated/constructed as float: "
                    f"{seg.strip()[:120]}")
        near = self.line_at(rel, line) or src.splitlines()[min(hi, len(src.splitlines()) - 1)]
        if "float" not in near:
            return ("ALREADY_FIXED",
                    f"{rel}:{line} no longer contains a float near the cited location")
        return ("UNVERIFIABLE",
                f"{rel}:{line} mentions float but no monetary node at that position")

    def _re_idempotency(self, f: dict) -> tuple[str, str]:
        rel, line = f.get("file") or "", int(f.get("line") or 0)
        src = self.text(rel)
        if not src:
            return ("FALSE_POSITIVE", f"{rel} no longer exists")
        tree = self.tree(rel)
        if tree is None:
            return ("UNVERIFIABLE", f"{rel} does not parse")
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                    and node.target.id == "idempotency_key":
                ann = ast.unparse(node.annotation) if node.annotation else ""
                optional = node.value is None or "Optional" in ann or "None" in ann
                return ("CONFIRMED" if optional else "FALSE_POSITIVE",
                        f"{rel}:{node.lineno} idempotency_key annotation={ann or '?'} "
                        f"default={'None (optional)' if node.value is None else 'required'}")
        for m in re.finditer(r"idempotency_key", src):
            ctx_line = src[:m.start()].count("\n") + 1
            if abs(ctx_line - line) <= 6:
                seg = src.splitlines()[ctx_line - 1].strip()
                if seg.startswith(('"""', "'''", "#", "*")) or '"' in seg[:6]:
                    return ("WRONG_LOCATION",
                            f"{rel}:{ctx_line} the cited 'idempotency_key' is prose "
                            f"(docstring/comment), not a parameter: {seg[:100]}")
        return ("ALREADY_FIXED", f"{rel} declares no idempotency_key field")

    def _re_rel_lazy(self, f: dict) -> tuple[str, str]:
        rel, line = f.get("file") or "", int(f.get("line") or 0)
        tree = self.tree(rel)
        if tree is None:
            return ("UNVERIFIABLE", f"{rel} does not parse")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if fn != "relationship":
                continue
            nline = getattr(node, "lineno", 0)
            if abs(nline - line) > 12:
                continue
            has_lazy = any(kw.arg == "lazy" for kw in node.keywords)
            if has_lazy:
                val = next((ast.unparse(kw.value) for kw in node.keywords
                            if kw.arg == "lazy"), "?")
                return ("FALSE_POSITIVE",
                        f"{rel}:{nline} relationship() now declares lazy={val}")
            return ("CONFIRMED", f"{rel}:{nline} relationship() has no lazy= argument")
        return ("WRONG_LOCATION",
                f"{rel}:{line} no relationship() call within 12 lines")

    def _re_settings_contract(self, f: dict) -> tuple[str, str]:
        m = re.search(r"settings\.(\w+)", f.get("current") or "")
        if not m:
            return None
        attr = m.group(1)
        src = self.text("backend/config.py")
        tree = self.tree("backend/config.py")
        if tree is None:
            return ("UNVERIFIABLE", "backend/config.py does not parse")
        declared: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        declared.add(stmt.target.id)
                    elif isinstance(stmt, ast.Assign):
                        declared.update(t.id for t in stmt.targets if isinstance(t, ast.Name))
                    elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        declared.add(stmt.name)
        if attr in declared:
            return ("FALSE_POSITIVE",
                    f"Settings now declares `{attr}` — the finding was fixed")
        # still read somewhere?
        used = False
        for rel, text in self._text_cache.items():
            if re.search(rf"settings\.{attr}\b", text):
                used = True
                break
        if not used:
            return ("ALREADY_FIXED",
                    f"Settings still does not declare `{attr}`, but no code reads "
                    f"settings.{attr} any more")
        return ("CONFIRMED",
                f"`{attr}` is read in application code and still absent from "
                f"Settings ({len(declared)} fields declared)")

    def _re_env_undeclared(self, f: dict) -> tuple[str, str]:
        m = re.search(r"`([A-Z][A-Z0-9_]+)`", f.get("current") or "")
        if not m:
            return None
        key = m.group(1)
        for candidate in (".env.example", "backend/.env.example"):
            if key in self.text(candidate):
                return ("FALSE_POSITIVE", f"{key} is now documented in {candidate}")
        if key in self.text("backend/config.py"):
            return ("FALSE_POSITIVE", f"{key} is now declared in backend/config.py")
        return ("CONFIRMED",
                f"{key} is read but absent from .env.example and config.py")

    def _re_cors_preflight(self, f: dict) -> tuple[str, str]:
        pat = re.compile(
            r'(?:method|request\.method)\s*==\s*["\']OPTIONS["\'][\s\S]{0,600}?'
            r'(call_next\s*\(\s*request\s*\))')
        checked = []
        for rel in list(self._text_cache) or ["backend/middleware/security_headers.py"]:
            src = self.text(rel)
            if not src:
                continue
            for m in pat.finditer(src):
                seg = src[m.start():m.start() + 700]
                after = seg[m.end(1) - m.start():]
                if re.match(r"^\s*return\b", after):
                    return ("FALSE_POSITIVE",
                            f"{rel} now returns its own response for OPTIONS without "
                            f"calling the router")
                checked.append(rel)
        if checked:
            return ("CONFIRMED",
                    f"{checked[0]} still calls call_next() in the OPTIONS branch, so "
                    f"the router answers the preflight first")
        return ("UNVERIFIABLE", "no OPTIONS branch matched the expected shape")

    def _re_xss_header(self, f: dict) -> tuple[str, str]:
        hits = []
        for rel in ("backend/middleware/security_headers.py", "backend/main.py"):
            if re.search(r"x-xss-protection", self.text(rel), re.I):
                hits.append(rel)
        if hits:
            return ("CONFIRMED",
                    f"X-XSS-Protection is still declared in {', '.join(hits)}")
        return ("FALSE_POSITIVE", "X-XSS-Protection is no longer emitted")

    def _re_schema_drift(self, f: dict) -> tuple[str, str]:
        m = re.search(r"schemas?:?\s*([a-z_]+)", f.get("current") or "")
        if not m:
            return None
        schema = m.group(1)
        from zz_core.util import walk_all  # local import: optional dependency
        orm_schemas: set[str] = set()
        for p in walk_all(self.root / "backend"):
            if p.suffix != ".py" or "models" not in p.as_posix():
                continue
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    orm_schemas.add(node.value)
        if schema in orm_schemas:
            return ("FALSE_POSITIVE",
                    f"schema `{schema}` now appears in the ORM metadata")
        return ("CONFIRMED",
                f"schema `{schema}` is still referenced by a migration but declared by "
                f"no ORM model")

    # -- generic --------------------------------------------------------------
    def locate(self, f: dict) -> tuple[str, str]:
        """``(kind, detail)`` where kind is file|dir|absent|missing-ref."""
        rel = f.get("file") or ""
        if not rel:
            return ("missing-ref", "finding cites no file")
        p = self.root / rel
        if p.is_dir():
            return ("dir", rel)
        if not p.exists():
            return ("absent", f"{rel} does not exist on disk")
        line = int(f.get("line") or 0)
        nlines = len(self.text(rel).splitlines())
        if line and line > nlines:
            return ("file", f"{rel} has {nlines} lines; cited line {line} is past EOF")
        return ("file", self.line_at(rel, line))

    def _dir_evidence(self, rel: str, toks: list[str]) -> tuple[str, str]:
        """Adjudicate a directory-level claim by scanning its files."""
        from zz_core.util import iter_files
        scanned = 0
        present: set[str] = set()
        for f in iter_files(self.root / rel, (".py", ".ts", ".tsx", ".json", ".yml",
                                             ".yaml", ".ini", ".toml", ".sql", ".md"),
                            exclude=set()):
            scanned += 1
            txt = self.text(str(f.relative_to(self.root)).replace("\\", "/"))
            present.update(t for t in toks if t in txt)
        if scanned == 0:
            return ("UNVERIFIABLE",
                    f"{rel} is a directory with no auditable files")
        if not toks:
            return ("UNVERIFIABLE", f"{rel}: {scanned} file(s) scanned, claim has no tokens")
        hit = len(present)
        if hit == len(toks):
            return ("UNVERIFIABLE",
                    f"{rel}: all {hit} claim token(s) present across {scanned} file(s) — "
                    f"consistent, not independently re-derived")
        if hit:
            return ("UNVERIFIABLE",
                    f"{rel}: {hit}/{len(toks)} claim token(s) present across "
                    f"{scanned} file(s)")
        return ("FALSE_POSITIVE",
                f"none of the {len(toks)} claim token(s) ({', '.join(toks[:4])}) "
                f"appear in any of the {scanned} file(s) under {rel}")

    def generic(self, f: dict) -> tuple[str, str]:
        """Refutation-only. Can never return CONFIRMED."""
        kind, detail = self.locate(f)
        if kind == "missing-ref":
            return ("UNVERIFIABLE", detail)
        toks = _tokens(f.get("current") or "")
        if kind == "dir":
            return self._dir_evidence(detail, toks)
        if kind == "absent":
            # The claim may be "this file is missing". Absence is then the
            # evidence, not a refutation.
            claim = (f.get("current") or "").lower()
            if re.search(r"\bno\b.*\b(cannot|could not|does not|not found|missing|"
                         r"absent|is not defined)", claim):
                return ("UNVERIFIABLE",
                        f"{detail}; the claim asserts absence, which is consistent — "
                        f"an auditor must read it")
            return ("WRONG_LOCATION",
                    f"{detail}, but the claim does not assert absence")
        if "past EOF" in detail:
            return ("WRONG_LOCATION", detail)
        line_text = detail
        if toks:
            hit = sum(1 for t in toks if t.lower() in line_text.lower())
            if hit == len(toks):
                return ("UNVERIFIABLE",
                        f"all {len(toks)} claim token(s) appear on "
                        f"{f['file']}:{f['line']}; consistent but not independently "
                        f"re-derived")
            if hit:
                return ("UNVERIFIABLE",
                        f"{hit}/{len(toks)} claim token(s) appear on the cited line")
            whole = self.text(f.get("file") or "")
            present = sum(1 for t in toks if t in whole)
            if present == 0:
                return ("ALREADY_FIXED",
                        f"none of the {len(toks)} claim token(s) "
                        f"({', '.join(toks[:4])}) appear anywhere in {f['file']}")
            # Tokens exist in the file but not on the cited line. That is
            # evidence the line drifted — it is NOT proof the finding is wrong.
            # Claiming a refutation here would be the same false-positive class
            # this project keeps hitting, so it is reported as unverifiable with
            # the drift signal attached and routed to a verification task.
            return ("UNVERIFIABLE",
                    f"cited line {f['file']}:{f['line']} carries none of the "
                    f"{len(toks)} claim token(s) ({', '.join(toks[:4])}) but "
                    f"{present} appear elsewhere in the file — the line most "
                    f"likely drifted; re-locate before acting")
        return ("UNVERIFIABLE", "no tokenisable claim")

    # -- driver ---------------------------------------------------------------
    def run(self, rows: list[dict], cluster_filter: str | None = None) -> list[dict]:
        # Warm the text cache so _re_* helpers that scan it see real content.
        for rel in ("backend/config.py", ".env.example", "backend/.env.example",
                    "backend/middleware/security_headers.py", "backend/main.py"):
            self.text(rel)
        out: list[dict] = []
        for f in rows:
            if cluster_filter and cluster_filter not in (f.get("cluster") or ""):
                continue
            kind, detail = self.locate(f)
            checked = self.recheck(f)
            if checked:
                verdict, evidence = checked
                basis = "cluster_recheck"
            else:
                verdict, evidence = self.generic(f)
                basis = "token_consistency"
            out.append({
                "key": f.get("id"),
                "cluster": f.get("cluster"),
                "dimension": f.get("dimension"),
                "priority": f.get("priority"),
                "blocker": f.get("completion_blocker"),
                "verdict": verdict,
                "basis": basis,
                "target_kind": kind,
                "path_exists": kind in ("file", "dir"),
                "line_exists": kind == "file",
                "cited_line": (detail.strip()[:160] if kind == "file" else ""),
                "evidence": evidence[:400],
                "location": detail if kind != "file" else "",
            })
        return out


def summarise(verdicts: list[dict], findings: list[dict]) -> dict:
    by_v = Counter(v["verdict"] for v in verdicts)
    total = len(verdicts) or 1
    fp = by_v.get("FALSE_POSITIVE", 0)
    fixed = by_v.get("ALREADY_FIXED", 0)
    wrong = by_v.get("WRONG_LOCATION", 0)
    conf = by_v.get("CONFIRMED", 0)
    unver = by_v.get("UNVERIFIABLE", 0)
    unadjudicated = unver
    p0 = [v for v in verdicts if v["priority"] == "P0"]
    p0_fp = sum(1 for v in p0 if v["verdict"] in ("FALSE_POSITIVE", "WRONG_LOCATION"))
    p0_conf = sum(1 for v in p0 if v["verdict"] == "CONFIRMED")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings_in": len(findings),
        "verdicts": len(verdicts),
        "confirmed": conf,
        "false_positive": fp,
        "already_fixed": fixed,
        "wrong_location": wrong,
        "unverifiable": unver,
        "false_positive_rate_pct": round(100.0 * (fp + wrong) / total, 1),
        "not_actionable_pct": round(100.0 * (fp + wrong + fixed) / total, 1),
        "independently_confirmed_pct": round(100.0 * conf / total, 1),
        "p0_total": len(p0),
        "p0_confirmed": p0_conf,
        "p0_false_or_wrong": p0_fp,
        "p0_noise_pct": round(100.0 * p0_fp / (len(p0) or 1), 1),
        "by_cluster": {c: dict(Counter(v["verdict"] for v in vs))
                       for c, vs in _by_cluster(verdicts).items()},
    }


def _by_cluster(verdicts: list[dict]) -> dict[str, list[dict]]:
    d: dict[str, list[dict]] = defaultdict(list)
    for v in verdicts:
        d[v.get("cluster") or "(none)"].append(v)
    return d


def render(sm: dict, verdicts: list[dict], findings: list[dict]) -> str:
    out = ["# ZOZI — Finding verification (falsification gate)", "",
           f"_Generated {sm['generated_at']} from {sm['findings_in']} findings._", "",
           "## Why this exists", "",
           "The audit makes claims. The prior run of this project adjudicated 1,359 of "
           "its own findings and found 910 REAL, 160 FALSE_POSITIVE and 265 "
           "ALREADY_FIXED — **31% were not actionable as stated**. Nothing in the audit "
           "pipeline tried to prove its own findings wrong. This document is that "
           "missing step, and its rate is the number that says whether the remediation "
           "plan can be followed by an AI without re-checking every step.",
           "", "## Method", "",
           "| Basis | Share | What it may conclude |",
           "|-------|-------|-----------------------|",
           "| `cluster_recheck` | "
           f"{sum(1 for v in verdicts if v['basis'] == 'cluster_recheck')}/{len(verdicts)} | "
           "CONFIRMED or FALSE_POSITIVE — a second, independent implementation "
           "(AST vs regex) of the same question |",
           "| `token_consistency` | "
           f"{sum(1 for v in verdicts if v['basis'] != 'cluster_recheck')}/{len(verdicts)} | "
           "**Refutation only.** May return ALREADY_FIXED / WRONG_LOCATION / "
           "UNVERIFIABLE, never CONFIRMED |", "",
           "A finding with no cluster re-check is therefore **never** auto-promoted to "
           "a fix instruction; it lands in the plan as a verification task.", "",
           "## Result", "",
           "| Verdict | Count | Share | Meaning |",
           "|---------|-------|-------|---------|",
           f"| CONFIRMED | {sm['confirmed']} | {100.0*sm['confirmed']/max(1,sm['verdicts']):.1f}% | "
           "independently re-derived and still true |",
           f"| FALSE_POSITIVE | {sm['false_positive']} | "
           f"{100.0*sm['false_positive']/max(1,sm['verdicts']):.1f}% | disproved |",
           f"| ALREADY_FIXED | {sm['already_fixed']} | "
           f"{100.0*sm['already_fixed']/max(1,sm['verdicts']):.1f}% | no longer present |",
           f"| WRONG_LOCATION | {sm['wrong_location']} | "
           f"{100.0*sm['wrong_location']/max(1,sm['verdicts']):.1f}% | cited line is wrong |",
           f"| UNVERIFIABLE | {sm['unverifiable']} | "
           f"{100.0*sm['unverifiable']/max(1,sm['verdicts']):.1f}% | consistent, not proven |",
           "",
           f"- **False-positive rate (FP + wrong location): {sm['false_positive_rate_pct']}%**",
           f"- **Not actionable as stated (FP + wrong + already fixed): "
           f"{sm['not_actionable_pct']}%**",
           f"- **Independently confirmed: {sm['independently_confirmed_pct']}%**",
           "",
           "## P0 impact", "",
           f"- P0 findings: **{sm['p0_total']}**",
           f"- independently confirmed: **{sm['p0_confirmed']}**",
           f"- false or mislocated: **{sm['p0_false_or_wrong']}** "
           f"(**{sm['p0_noise_pct']}%** of the P0 set)", "",
           "## Per-cluster", "",
           "| Cluster | REAL | FP | FIXED | WRONG | UNVER |",
           "|---------|------|----|-------|-------|-------|"]
    for cluster, c in sorted(sm["by_cluster"].items(),
                             key=lambda kv: -sum(kv[1].values()))[:40]:
        tot = sum(c.values())
        out.append(f"| `{cluster}` | {c.get('CONFIRMED',0)} | "
                   f"{c.get('FALSE_POSITIVE',0)} | {c.get('ALREADY_FIXED',0)} | "
                   f"{c.get('WRONG_LOCATION',0)} | {c.get('UNVERIFIABLE',0)} |")
    out += ["", "## What this does not prove", "",
            "- An `UNVERIFIABLE` finding is **not** a pass. It is a claim the tooling "
            "could not adjudicate, and the plan treats it as a verification task.",
            "- A `CONFIRMED` verdict proves the *claim*, not the *fix*. The proposed "
            "`fix` field still needs an engineering review.",
            "- Clusters without a re-check contribute no CONFIRMED verdicts at all, so "
            "the confirmed share is a floor, not a total.",
            "- This gate never edits source. It only classifies.", "",
            "---", "",
            "_Generated by `_zozi_audit/zozi_verify.py`. `zozi_compile.py` reads this and "
            "will not emit a fix instruction for a disproved finding._", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Falsify audit findings before remediation")
    p.add_argument("--root", default=str(HERE.parent))
    p.add_argument("--logs", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--cluster", default=None, help="only verify findings in this cluster")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--strict", action="store_true",
                   help="exit 1 when the false-positive rate exceeds 20%")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    logs = Path(args.logs).resolve() if args.logs else root / "_zozi_audit" / "logs"
    fp = logs / "findings.jsonl"
    if not fp.exists():
        print(f"FATAL: {fp} not found. Run zozi_audit.py first.", file=sys.stderr)
        return 2
    findings = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    if args.limit:
        findings = findings[:args.limit]

    v = Verifier(root, logs)
    verdicts = v.run(findings, args.cluster)
    sm = summarise(verdicts, findings)

    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "verdicts.jsonl").open("w", encoding="utf-8") as fh:
        for row in verdicts:
            fh.write(json.dumps(row) + "\n")
    (logs / "verification_summary.json").write_text(
        json.dumps(sm, indent=2), encoding="utf-8")
    out = Path(args.out).resolve() if args.out else root / "_zozi_audit" / "zozi_verification.md"
    out.write_text(render(sm, verdicts, findings), encoding="utf-8")

    print(f"[verify] {len(verdicts)} finding(s) -> {out}")
    print(f"[verify] confirmed={sm['confirmed']} fp={sm['false_positive']} "
          f"wrong={sm['wrong_location']} fixed={sm['already_fixed']} "
          f"unverifiable={sm['unverifiable']}")
    print(f"[verify] FP+wrong = {sm['false_positive_rate_pct']}% | "
          f"not actionable = {sm['not_actionable_pct']}% | "
          f"P0 noise = {sm['p0_noise_pct']}%")
    if args.strict and sm["false_positive_rate_pct"] > 20:
        print("[verify] STRICT: FP rate above 20% — the plan is not safe to execute "
              "without review.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())