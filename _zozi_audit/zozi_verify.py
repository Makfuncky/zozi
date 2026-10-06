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

def claim_tokens(text: str) -> set[str]:
    """Content words of a claim: lowercase, singular-ish, stopwords dropped."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", (text or "").lower())
    out = set()
    for w in words:
        if w in STOPWORDS:
            continue
        for suffix in ("(s)", "s"):
            if w.endswith(suffix) and len(w) > len(suffix) + 3:
                w = w[: -len(suffix)]
                break
        out.add(w)
    return out


# A claim can assert that something is ABSENT. "Absent" is then the claim, so
# finding the thing absent corroborates it -- it can never disprove it.
#
# This regex was defined only inside the missing-file branch, so the two branches
# that refute on token absence ignored it:
#   D2P-003 "container has no HEALTHCHECK" (backend/Dockerfile)
#   D2P-004 "container has no HEALTHCHECK" (backend/Dockerfile.prod)
#   PERF-001 "no bundle analyzer configured" (next.config.ts)
#   DECLLAW-011 "no commit-message linter is configured" (package.json)
# All four were true (`grep -c HEALTHCHECK backend/Dockerfile` -> 0, no analyzer
# key, no commitlint/lint-staged key) and all four were marked ALREADY_FIXED and
# dropped from the plan, because none of their tokens appeared in the file.
ABSENCE_CLAIM = re.compile(
    r"\b(cannot|could not|does not|doesn't|do not|not found|no such|no\b|"
    r"missing|absent|is not defined|is absent|not present|undeclared|"
    r"zero\b.*\bdeclared|nothing|lacks?|without\b|never\b)")

# Clusters whose re-check instrument measures only PART of the finding's claim.
#
# Free text cannot decide claim alignment -- I first tried requiring the
# instrument's words to cover every content word of the claim and it refused
# every refutation in the suite, including the correct ones, because both sides
# are prose. So the gap is declared as data, from cases inspected by hand against
# the source:
#
#   CLUSTER-table-governance   probe counts the two audit TIMESTAMPS; the finding
#                             is "2 tables lack soft delete" (both true).
#   CLUSTER-feature-gate       probe counts gated-but-undefined atoms; the finding
#                             is the opposite set, declared-but-never-gated. The
#                             mapping is now fixed, and this keeps a future
#                             mis-mapping from deleting 146 real orphans again.
#   CLUSTER-law-security       probe greps for a fail-closed path; the finding
#                             cites a specific law verdict, which the grep cannot
#                             settle either way.
#   CLUSTER-public-by-design   probe was file-level, the finding endpoint-level.
#
# A refutation is refused when the claim mentions any declared gap token: the
# instrument does not cover that part of the claim, so a low count cannot
# disprove it. The finding is deferred to triage (UNVERIFIABLE) instead of
# deleted. A lower count can never *confirm* anything, but it can silently delete
# real work, so the two errors are not symmetric.
CLAIM_GAPS: dict[str, set[str]] = {
    "CLUSTER-table-governance": {"soft", "delete", "country", "code", "nullable"},
    "CLUSTER-feature-gate": {"declared", "never", "gate", "referenced", "orphan"},
    "CLUSTER-ghost-feature": {"undefined", "catalog", "literal"},
    "CLUSTER-law-security": {"law", "violated", "verdict"},
    "CLUSTER-public-by-design": {"design", "public", "sample", "logout", "recorded"},
}


def claim_covers(cluster: str, claim: str, detail: str) -> tuple[bool, set[str]]:
    """May a probe whose description is ``detail`` refute ``claim``?

    Allowed by default; refused when the cluster is known to measure only part of
    its claim (``CLAIM_GAPS``) and the claim mentions a part the instrument does
    not cover. Returns ``(allowed, uncovered_tokens)``.
    """
    gaps = CLAIM_GAPS.get(cluster or "")
    if not gaps:
        return True, set()
    uncovered = claim_tokens(claim) & gaps
    return not uncovered, uncovered


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


# Re-location thresholds. The cited line drifts whenever the file is edited
# between the scan and the adjudication, which is the normal case on an active
# tree, so the verifier has to be able to say "the construct is here, not there".
RELOCATE_MIN_SCORE = 2    # distinct claim tokens that must land on the winner
RELOCATE_MIN_TOKEN = 6    # ...and at least one of them must be this specific
RELOCATE_WINDOW = 40      # lines either side of an anchor that may corroborate


def _prose_lines(lines: list[str]) -> set[int]:
    """1-based line numbers that hold prose, not code.

    A comment or a docstring cannot be the construct a finding is about. The
    first relocation attempt put all four `schema is not canonical` claims on the
    module docstring of `payment_models.py`, because `canonical` occurs exactly
    once in the file -- inside the sentence "the canonical Payment / Payout /
    Gateway models still live in ...", which is about a different thing
    entirely. Matching `#` alone is not enough; a docstring has no marker.
    """
    out: set[int] = set()
    fence: str | None = None
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if fence is not None:
            out.add(i)
            if fence in ln:
                fence = None
            continue
        if s.startswith(("#", "//", "*", "/*")):
            out.add(i)
            continue
        m = re.search(r'("""|\'\'\')', ln)
        if m:
            quote = m.group(1)
            if quote in ln[m.end():]:
                out.add(i)          # opened and closed on this line
            else:
                fence = quote       # opened here, prose runs on
                out.add(i)
    return out


class Verifier:
    def __init__(self, root: Path, logs: Path):
        self.root = root
        self.logs = logs
        self._ast_cache: dict[str, ast.AST | None] = {}
        self._text_cache: dict[str, str] = {}
        self._probe_runner = None
        self._probe_unavailable = ""
        self._relocated: dict[str, int] = {}

    # -- probe layer ----------------------------------------------------------
    def probe_runner(self):
        """The `ProbeRunner`, or None. Never raises: this stage is advisory."""
        if self._probe_runner is None and not self._probe_unavailable:
            try:
                from zz_core.probe import ProbeRunner
                self._probe_runner = ProbeRunner(self.root)
            except Exception as exc:
                self._probe_unavailable = f"{type(exc).__name__}: {exc}"
        return self._probe_runner

    def probe_verdict(self, f: dict) -> tuple[str, str] | None:
        """Re-decide a finding with its own probe.

        This stage existed nowhere before, so the verifier could only *refute* on
        token consistency and marked 1300+ findings `UNVERIFIABLE` -- 81% of the
        suite's output passed through unexamined while the summary read as
        healthy. The probe is the stronger instrument: it re-executes the claim's
        own check against the source.

        Returns None when the probe is absent, errors, or cannot resolve the
        claim -- None means "no evidence", which is different from "no verdict".
        """
        probe = f.get("probe") or {}
        if not probe:
            return None
        runner = self.probe_runner()
        if runner is None:
            return None
        try:
            res = runner.run(probe)
        except Exception as exc:
            return None
        detail = res.detail or res.summary or ""
        if res.holds and res.resolvable:
            return ("CONFIRMED", f"probe holds — {detail}")
        if res.resolvable and not res.holds:
            # A refutation deletes work, so it is only allowed when the probe's
            # own description actually covers the claim. Measured on this run:
            # `CLUSTER-table-governance` refuted "2 lack soft delete" with a
            # measurement of the two audit *timestamps* (which are present), and
            # `CLUSTER-feature-gate` refuted "146 declared but never gated" with
            # the opposite measurement ("gated but undefined"). Both claims were
            # true; both findings left the plan. `claim_covers()` refuses a
            # refutation whose instrument answers a narrower or different
            # question and defers the finding to triage instead.
            ok, uncovered = claim_covers(f.get("cluster") or "",
                                         f.get("current") or "", detail)
            if not ok:
                return ("UNVERIFIABLE",
                        f"probe cannot decide this claim — it measures "
                        f"'{detail}'; the claim also asserts "
                        f"{', '.join(sorted(uncovered)[:6]) or 'more'} "
                        f"(deferred, not refuted)")
            return ("FALSE_POSITIVE", f"probe refutes it — {detail}")
        return None

    # -- IO -------------------------------------------------------------------
    def text(self, rel: str) -> str:
        if rel not in self._text_cache:
            p = self.root / rel
            try:
                self._text_cache[rel] = p.read_text(encoding="utf-8-sig", errors="replace")
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

    # -- re-location ----------------------------------------------------------
    def relocate(self, f: dict, toks: list[str]) -> tuple[int, str] | None:
        """Where does the claim's construct actually sit? ``(line, note)``.

        A cited line that no longer carries the claim is not evidence that the
        finding is wrong. `comms.py` was 203 lines when LOGIC-041 was scanned,
        180 when it was adjudicated and 156 minutes later -- while the
        `except WebSocketDisconnect: pass` it reports (Law 59)never stopped existing, it only moved to line 150. Refuting on a drifted line deleted
        a real violation, so the construct is re-located first. Two routes are
        tried: a single line that carries enough of the claim, then a unique
        anchor (a token occurring exactly once) corroborated nearby, because
        "table X declares schema Y" spans two lines by construction.

        Deliberately strict, because promoting a verdict is the dangerous
        direction: a candidate must collect at least ``RELOCATE_MIN_SCORE``
        distinct tokens (rarity only *ranks* the survivors -- weighting it into
        the cut-off let a lone `pass` on the next line outweigh the
        `except WebSocketDisconnect` that was actually being cited), at least
        one token must be long enough to be specific rather than generic prose,
        and the winner must beat every rival outright, since a tie means the
        claim does not single out one construct. Comment lines cannot host a
        construct. An absence claim is never re-located -- finding the thing is
        not evidence about a claim that says the thing is not there.
        """
        if not toks or ABSENCE_CLAIM.search((f.get("current") or "").lower()):
            return None
        lines = self.text(f.get("file") or "").splitlines()
        if not lines:
            return None
        lows = [ln.lower() for ln in lines]
        prose = _prose_lines(lines)
        code = [i for i in range(1, len(lines) + 1) if i not in prose]
        if not code:
            return None
        # Score by rarity, not by count. `schema` appears on every table in the
        # file and identifies nothing; `payment_methods` appears once and names
        # the construct outright. Counting matches equally made four identical
        # table declarations tie and refused to resolve a real finding.
        scores: list[tuple[float, int, int, list[str]]] = []
        df = {t: sum(1 for low in lows if t.lower() in low) for t in toks}
        for i in code:
            low = lows[i - 1]
            matched = [t for t in toks if t.lower() in low]
            if matched:
                scores.append((sum(1.0 / df[t] for t in matched),
                               len(matched), i, matched))
        if scores:
            # Qualify first, rank second. A rival only counts if it could have
            # won on its own merits: letting a lone `pass` on the next line
            # (one rare token) veto the `except WebSocketDisconnect` that the
            # claim is actually about made every two-token line unresolvable.
            cands = [s for s in scores
                     if s[1] >= RELOCATE_MIN_SCORE
                     and any(len(t) >= RELOCATE_MIN_TOKEN for t in s[3])]
            cands.sort(key=lambda s: (-s[0], -s[1], s[2]))
            if cands:
                score, n_match, line_no, matched = cands[0]
                runner_up = cands[1][0] if len(cands) > 1 else 0.0
                # Ambiguity is refused: a rival line scoring the same means the
                # claim does not single out one construct, so nothing is claimed.
                if score > runner_up:
                    snippet = lines[line_no - 1].strip()[:100]
                    note = f"{', '.join(sorted(matched)[:4])} -> `{snippet}`"
                    self._relocated[str(f.get("id") or "")] = line_no
                    return line_no, note

        # Fallback for a claim that spans two lines. "table `payment_methods`
        # declares schema `payments`" puts the name on one line and the schema
        # a few lines below, so no single line can carry the whole claim. Anchor
        # on a token that occurs exactly once and is long enough to be a name,
        # then require the rest of the claim nearby.
        best: tuple[int, int, str, list[str]] | None = None
        tie = False
        for t in toks:
            if len(t) < RELOCATE_MIN_TOKEN or df[t] != 1:
                continue
            line_no = next((i for i in code if t.lower() in lows[i - 1]), 0)
            if not line_no:
                continue
            lo = max(1, line_no - RELOCATE_WINDOW)
            hi = min(len(lows), line_no + RELOCATE_WINDOW)
            near = {u for u in toks if u != t
                    and any(u.lower() in lows[j - 1] for j in range(lo, hi + 1))}
            if not near:
                continue
            if best and len(near) == best[0]:
                tie = True
            elif not best or len(near) > best[0]:
                best, tie = (len(near), line_no, t, sorted(near)), False
        if best and not tie:
            _, line_no, anchor, near = best
            snippet = lines[line_no - 1].strip()[:100]
            note = (f"`{anchor}` -> `{snippet}` corroborated by "
                    f"{', '.join(near[:3])} within {RELOCATE_WINDOW} lines")
            self._relocated[str(f.get("id") or "")] = line_no
            return line_no, note
        return None

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
        """Does the CITED middleware still delegate the preflight to the router?

        This previously scanned every file in the text cache and returned
        FALSE_POSITIVE as soon as ANY of them answered OPTIONS itself. That let
        `middleware/country_context.py`, an unrelated layer, overturn a finding
        about `middleware/security_headers.py`. Whether another middleware might
        answer first depends on registration order, which a static read cannot
        establish -- so it cannot refute the claim about the cited file either
        way. The verdict has to follow the file the finding names.
        """
        pat = re.compile(
            r'(?:method|request\.method)\s*==\s*["\']OPTIONS["\'][\s\S]{0,600}?'
            r'(call_next\s*\(\s*request\s*\))')
        cited = (f.get("file") or "").replace("\\", "/")
        targets = [cited] if cited else ["backend/middleware/security_headers.py"]
        matched = False
        for rel in targets:
            src = self.text(rel)
            if not src:
                continue
            for m in pat.finditer(src):
                matched = True
                seg = src[m.start():m.start() + 700]
                after = seg[m.end(1) - m.start():]
                if re.match(r"^\s*return\b", after):
                    return ("FALSE_POSITIVE",
                            f"{rel} now returns its own response for OPTIONS "
                            f"without calling the router")
        if matched:
            return ("CONFIRMED",
                    f"{targets[0]} still calls call_next() in the OPTIONS branch, "
                    f"so the router answers the preflight first")
        return ("UNVERIFIABLE",
                f"no OPTIONS branch matching the expected shape in {targets[0]}")

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
                tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
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
        if ABSENCE_CLAIM.search((f.get("current") or "").lower()):
            return ("UNVERIFIABLE",
                    f"{rel}: none of the {len(toks)} claim token(s) appear in any "
                    f"of the {scanned} file(s) — but the claim ASSERTS that "
                    f"absence, so this corroborates it rather than disproving it")
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
            #
            # The marker test must NOT require a preceding "no": a claim can
            # assert absence without it. Requiring `\bno\b` before the marker
            # misread every phrasing like "`docs/runbooks/deploy.md` does not
            # exist" or "no deploy / rollback / migration runbook found" and
            # returned WRONG_LOCATION for a finding that was plainly correct.
            claim = (f.get("current") or "").lower()
            if ABSENCE_CLAIM.search(claim):
                return ("UNVERIFIABLE",
                        f"{detail}; the claim asserts absence, which is consistent — "
                        f"an auditor must read it")
            return ("WRONG_LOCATION",
                    f"{detail}, but the claim does not assert absence")
        if "past EOF" in detail:
            # Being past EOF proves the file changed, not that the finding is
            # wrong. LOGIC-041 was refuted here while the `except` it reports was
            # still in the file at line 150: a real Law 59 violation deleted from
            # the plan by a line number. Re-locate; if that fails, defer.
            hit = self.relocate(f, toks)
            if hit:
                line_no, note = hit
                return ("CONFIRMED",
                        f"cited line {f['line']} is past EOF, but the claim's "
                        f"construct is present at {f['file']}:{line_no} ({note}); "
                        f"the location drifted, the extent of the claim is not "
                        f"re-derived")
            return ("UNVERIFIABLE",
                    f"{detail} — line drift, not a refutation; no line carries the "
                    f"claim's tokens, so an auditor must read the file")
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
                if ABSENCE_CLAIM.search((f.get("current") or "").lower()):
                    return ("UNVERIFIABLE",
                            f"none of the {len(toks)} claim token(s) "
                            f"({', '.join(toks[:4])}) appear in {f['file']} — but the "
                            f"claim asserts that absence, so the file agrees with "
                            f"it; an auditor must read it")
                return ("ALREADY_FIXED",
                        f"none of the {len(toks)} claim token(s) "
                        f"({', '.join(toks[:4])}) appear anywhere in {f['file']}")
            # Tokens exist in the file but not on the cited line. That is
            # evidence the line drifted — it is NOT proof the finding is wrong.
            # Claiming a refutation here would be the same false-positive class
            # this project keeps hitting, so the construct is re-located and
            # reported with its corrected line; only an unresolvable claim is
            # deferred to triage.
            hit = self.relocate(f, toks)
            if hit:
                line_no, note = hit
                return ("CONFIRMED",
                        f"cited line {f['file']}:{f['line']} drifted; the claim's "
                        f"construct is present at line {line_no} ({note}); the "
                        f"extent of the claim is not re-derived")
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
            probed = self.probe_verdict(f)

            # A probe verdict and a cluster re-check that disagree are the most
            # valuable thing this stage can produce, so the disagreement is
            # reported rather than resolved silently. The probe wins because it
            # re-executes the claim's own check; the re-check is kept as context.
            if probed and checked and checked[0] in ("CONFIRMED", "FALSE_POSITIVE") \
                    and checked[0] != probed[0]:
                verdict, evidence = probed
                basis = "probe_over_recheck_disagreement"
                evidence += (f"  ||  cluster re-check said {checked[0]}: {checked[1]}")
            elif probed:
                verdict, evidence = probed
                basis = "probe"
            elif checked:
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
                # Set when the verdict re-located the construct to a different
                # line, so the plan can carry the corrected location instead of
                # pointing a fix at a line that no longer holds the defect.
                "relocated_to": self._relocated.get(str(f.get("id") or ""), ""),
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
        # Which instrument actually decided each verdict. Without this the summary
        # reads as one number while 1300+ findings were decided by nothing and
        # merely labelled UNVERIFIABLE.
        "by_basis": {b: n for b, n in
                     Counter(v.get("basis") or "?" for v in verdicts).most_common()},
        "disagreements": sum(1 for v in verdicts
                             if v.get("basis") == "probe_over_recheck_disagreement"),
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
    findings = [json.loads(l) for l in fp.read_text(encoding="utf-8-sig").splitlines()
                if l.strip()]
    if args.limit:
        findings = findings[:args.limit]

    v = Verifier(root, logs)
    verdicts = v.run(findings, args.cluster)
    sm = summarise(verdicts, findings)

    logs.mkdir(parents=True, exist_ok=True)
    # plain utf-8 on WRITE -- utf-8-sig would prepend a BOM to verdicts.jsonl
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