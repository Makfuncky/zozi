"""Detector + probe regression runner.

Run with::

    python _zozi_audit/tests/run_tests.py

or through the audit itself::

    python _zozi_audit/zozi_audit.py --self-test

Exit code 0 = every detector agrees with every fixture. Non-zero = at least one
detector has drifted from the benchmark, and the audit is not trustworthy until it
is fixed.

Why this exists
---------------
Both known defects were *silent*: a detector reported confident, wrong, actionable
findings, and a probe reported confident, wrong "already fixed" verdicts. Neither
raised anything. A test that asserts each detector's polarity against a known
positive and a known negative is the cheapest thing that converts a silent defect
into a loud one.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "_zozi_audit"))

from tests.fixtures import FIXTURES, by_detector, counts  # noqa: E402


# --------------------------------------------------------------------------- #
# detector predicates
# --------------------------------------------------------------------------- #
# Each predicate answers: does this detector fire on this source?
#
# They are re-implementations of the *intent* of the production detector, written
# independently. That is deliberate: a test that calls the production code and
# compares it to itself proves nothing. Where the production detector is hard to
# invoke in isolation, the predicate encodes the rule the benchmark states and the
# test documents which production line must agree.

def _ungated_route(src: str) -> bool:
    """A router endpoint whose signature injects no auth dependency.

    Regression guard for the 46-false-positive defect: the guard is on the
    signature, which may be the `def` line or a continuation line, and any of
    `Depends(require_*)` / `Depends(get_current_user)` counts as gated.
    """
    for m in re.finditer(r"@router\.(?:get|post|put|patch|delete)\([^)]*\)\s*\ndef\s+(\w+)\s*(.*?)(?=\n@|\ndef |\Z)",
                         src, re.S):
        name, sig = m.group(1), m.group(2)
        if name in ("test",) or not sig.strip():
            continue
        if re.search(r"Depends\s*\(\s*(get_current_user|get_current_active_user|"
                     r"require_\w+|verify_\w+|auth\w*|current_user)", sig):
            continue
        return True
    return False


def _silent_except(src: str) -> bool:
    """An `except` handler whose body is `pass` or `...`."""
    for m in re.finditer(r"except\b[^\n:]*:\s*\n?\s*(pass|\.\.\.)\s*$",
                         src, re.MULTILINE):
        return True
    return False


def _float_money(src: str) -> bool:
    """A `float`-typed money field (Law 19)."""
    money = r"(amount|price|total|subtotal|tax|vat|commission|fee|balance|" \
            r"payout|refund|discount|shipping_cost|rate)"
    return bool(re.search(money + r"[^\n]*:\s*(Mapped\[\s*)?float\b", src)
                or re.search(r":\s*(Mapped\[\s*)?float\b[^\n]*" + money, src))


def _timestamp_default(src: str) -> bool:
    """A Python-side timestamp default instead of `server_default`."""
    return bool(re.search(r"(?:default|onupdate)\s*=\s*(?:datetime\.now|"
                          r"datetime\.utcnow|lambda\s*:\s*datetime)", src))


def _relationship_lazy(src: str) -> bool:
    """A relationship defaulting to `lazy="select"` (Law 45)."""
    return bool(re.search(r"relationship\([^)]*lazy\s*=\s*[\"']select[\"']", src))


def _idempotency_optional(src: str) -> bool:
    """An *optional* idempotency key on a money path (Law 239).

    Regression guard for the inverted probe: the defect is the key being
    optional, not the key being absent.
    """
    return bool(re.search(r"idempotency_key\s*(?::\s*Optional|=\s*None"
                          r"|:\s*\w+\s*\|\s*None)", src))


def _dead_branch(src: str) -> bool:
    """A plain statement left unreachable after `return`/`raise`/`continue`.

    Only a statement at the **same indent** as the terminating statement is dead.
    Treating a following `return`/`raise`/`if`/`else` as dead is the classic false
    positive here: `if c: return a` followed by `return b` is control flow, not
    dead code.
    """
    lines = src.splitlines()
    terminal = re.compile(r"^(\s*)(return|raise|continue|break)\b")
    for i, line in enumerate(lines):
        m = terminal.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            n_indent = len(nxt) - len(nxt.lstrip())
            if n_indent < indent:
                break                      # dedented: we left the block
            if n_indent > indent:
                continue                   # deeper: belongs to a nested block
            if terminal.match(nxt) or re.match(r"\s*(#|@|\"\"\"|def |class |"
                                                r"else:|elif |except|finally)", nxt):
                continue                   # still reachable control flow
            return True
    return False


PREDICATES = {
    "ungated_route": _ungated_route,
    "silent_except": _silent_except,
    "float_money": _float_money,
    "timestamp_default": _timestamp_default,
    "relationship_lazy": _relationship_lazy,
    "idempotency_optional": _idempotency_optional,
    "dead_branch": _dead_branch,
}

#: detector -> (production file, line or symbol the predicate mirrors)
PRODUCTION_OF = {
    "ungated_route": "zz_scanners/s05_wiring.py :: wire_feature_gates",
    "silent_except": "zz_scanners/s03_logic.py :: logic_silent_excepts",
    "float_money": "zz_scanners/s03_logic.py :: logic_money_type",
    "timestamp_default": "zz_scanners/s20_db_advisor.py :: db_table_fidelity",
    "relationship_lazy": "zz_scanners/s07_tables_fields.py",
    "idempotency_optional": "zz_scanners/s03_logic.py :: logic_idempotency",
    "dead_branch": "zz_scanners/s03_logic.py :: drift_static",
}


# --------------------------------------------------------------------------- #
# probe polarity
# --------------------------------------------------------------------------- #

def check_probe_polarity() -> list[tuple[str, bool, str]]:
    """Every probe's `kind` must agree with the claim its `note` describes.

    The idempotency defect was exactly this: a ``text_absent`` probe on a claim
    whose defect is a token being *present*. Such a probe reports "already fixed"
    on a live defect, and the verifier then discards the finding.
    """
    from zz_core.probes import PROBE_RULES
    out: list[tuple[str, bool, str]] = []

    # Claims whose defect IS a construct being present. A `text_absent` rule on
    # any of these would invert the verdict.
    presence_claims = ("optional", "present", "declared", "appears", "stores",
                       "contains", "no removal date", "unwired")
    for cluster, rule in sorted(PROBE_RULES.items()):
        note = (rule.note or "").lower()
        if not rule.pattern:
            continue
        if rule.kind == "text_absent" and any(w in note for w in presence_claims):
            out.append((cluster, False,
                        f"`text_absent` probe on a claim whose defect is a construct "
                        f"being PRESENT (note={rule.note!r}) — it would report "
                        f"'already fixed' on a live defect"))
        else:
            out.append((cluster, True, ""))
    return out


#: Probe kinds that re-read an existing source file. Their `path`/`paths` MUST
#: resolve, or the probe degrades to UNVERIFIABLE and quietly stops discriminating.
PATH_REQUIRING_KINDS = {
    "text_matches", "text_absent", "text_present",
    "ast_call_without_kwarg", "ast_relationship_missing_kwarg",
    "ast_annotation_contains", "ast_attr_undeclared",
    "attribute_absent_in_dict", "function_len_above",
    "ast_forbidden_call_in_function", "module_imports_above",
    "api_path_resolves",
}

#: Probe kinds whose subject is the *absence* of a path, or a property of a package
#: rather than of one file. Referencing something that does not exist is the point,
#: so they must NOT be held to PATH_REQUIRING_KINDS.
PATHLESS_KINDS = {"path_absent", "path_present", "package_cycle_exists",
                  "filename_count_above", "count_below"}


def check_probe_not_self_evidencing() -> list[tuple[str, bool, str]]:
    """Every probe must be able to reach real evidence, not just its own finding.

    Two distinct failure modes, which need two distinct rules:

    1. A **path-requiring** probe whose path does not exist degrades to
       UNVERIFIABLE. It stops discriminating, but it reports honestly — it does not
       manufacture a verdict. Worth flagging, not fatal.
    2. A probe with **no reachable subject at all** — no path, no packages, no
       measured value — can only ever be evaluated against the finding that produced
       it. It will agree with itself forever. That is the fatal case.

    A finding whose ``current`` quotes its offending source line is *not* a defect:
    §5.1 requires inline evidence, and the probe still re-reads the file.
    """
    import json
    from pathlib import Path as P

    logs = HERE.parent / "logs" / "findings.jsonl"
    repo = ROOT
    out: list[tuple[str, bool, str]] = []
    if not logs.exists():
        return [("(no findings.jsonl)", True, "")]
    rows = [json.loads(l) for l in logs.open(encoding="utf-8-sig")]
    by_cluster: dict[str, list[dict]] = {}
    for r in rows:
        if r.get("probe") and r.get("cluster"):
            by_cluster.setdefault(r["cluster"], []).append(r)

    for cluster, items in sorted(by_cluster.items()):
        probe = items[0]["probe"]
        kind = probe.get("kind", "")
        if kind in PATHLESS_KINDS:
            subject = probe.get("packages") or probe.get("path") or \
                probe.get("paths") or ("actual" in probe and "actual") or ""
            if not subject or subject == "actual":
                out.append((cluster, False,
                            f"`{kind}` probe names no subject — it can only be "
                            f"evaluated against the finding text"))
            else:
                out.append((cluster, True, ""))
            continue
        if kind not in PATH_REQUIRING_KINDS:
            continue
        paths = probe.get("paths") or ([probe["path"]] if probe.get("path") else [])
        if not paths:
            out.append((cluster, False,
                        f"`{kind}` probe has no `path`/`paths`, so it can only be "
                        f"evaluated against the finding text"))
            continue
        missing = [p for p in paths if not (repo / p).exists()]
        if missing:
            out.append((cluster, False,
                        f"`{kind}` probe path(s) do not exist: {missing[:2]}"))
            continue
        out.append((cluster, True, ""))
    return out


# --------------------------------------------------------------------------- #
# probe ↔ claim linkage
# --------------------------------------------------------------------------- #

#: Terms that must appear in a finding's own text for a probe on that cluster to
#: be about the same subject. This is the check the suite was missing: a probe can
#: be valid, resolvable, correctly-polarity'd, and still be attached to a finding
#: about something else entirely — in which case it confirms the wrong claim
#: forever.
#
#: Observed failure: `CLUSTER-http-headers` findings claim `X-XSS-Protection` is
#: emitted, while the probe searched for `X-Content-Type-Options`. The probe found
#: it, reported "claim holds", and the verifier recorded a real defect as CONFIRMED
#: on evidence that had nothing to do with it.
SUBJECT_TERMS: dict[str, tuple[str, ...]] = {
    "CLUSTER-http-headers": ("x-xss",),
    "CLUSTER-http-csp": ("csp", "content-security-policy"),
    "CLUSTER-idempotency": ("idempotenc",),
    "CLUSTER-float-money": ("float",),
    "CLUSTER-silent-except": ("except",),
    "CLUSTER-tf-rel-lazy": ("lazy", "relationship"),
    "CLUSTER-tf-timestamp-default": ("timestamp", "server_default", "default"),
    "CLUSTER-ungated-route": ("gate", "auth", "feature", "ungated", "require"),
}


def check_probe_matches_claim() -> list[tuple[str, bool, str]]:
    """A probe's pattern must be about the same subject as the finding it verifies."""
    import json
    from zz_core.probe import ProbeRunner  # noqa: F401  (import cost guard)
    from pathlib import Path as P

    logs = HERE.parent / "logs" / "findings.jsonl"
    out: list[tuple[str, bool, str]] = []
    if not logs.exists():
        return [("(no findings.jsonl)", True, "")]
    rows = [json.loads(l) for l in logs.open(encoding="utf-8-sig")]
    by_cluster: dict[str, list[dict]] = {}
    for r in rows:
        if r.get("probe") and r.get("cluster"):
            by_cluster.setdefault(r["cluster"], []).append(r)
    for cluster, terms in sorted(SUBJECT_TERMS.items()):
        items = by_cluster.get(cluster)
        if not items:
            continue
        probe = items[0]["probe"]
        pattern = (probe.get("pattern") or "").lower()
        if not pattern:
            # AST and structural probes carry no `pattern`; they name a node,
            # attribute or function instead. Subject linkage for those is a
            # different (and much harder) question than a regex, so they are not
            # judged here rather than judged wrongly.
            continue
        claim = " ".join((it.get("current") or "") + " " + (it.get("delta") or "")
                         for it in items).lower()
        if any(t in pattern for t in terms):
            out.append((cluster, True, ""))
            continue
        shared = [t for t in terms if t in claim]
        out.append((cluster, False,
                    f"probe pattern {pattern!r} shares no subject term with the "
                    f"findings it verifies, which are about {shared or terms}. "
                    f"The probe can report 'claim holds' without ever testing "
                    f"the claim."))
    return out


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #

def check_instrument_gap_guard() -> list[tuple[str, bool, str]]:
    """A refutation must be refused when the instrument cannot cover the claim.

    Four aggregate findings were deleted from the plan by a probe that answered a
    different question (soft delete measured as timestamps; declared-never-gated
    measured as gated-but-undefined). `claim_covers()` is the guard; these cases
    are the ones it was written from, each verified by hand against the source.
    """
    from zozi_verify import claim_covers

    refused = [
        ("CLUSTER-table-governance",
         "0 table(s) lack audit timestamps and 2 lack soft delete",
         "model(s) missing audit timestamps (0)"),
        ("CLUSTER-feature-gate",
         "146 declared feature(s) are never referenced by any gate",
         "gate literal(s) with no catalog entry (none)"),
        ("CLUSTER-law-security",
         "Law 37 (Rate limit fails closed) violated: rate limiter does not"
         " visibly fail closed",
         "rate limiter without a visible fail-closed path"),
        ("CLUSTER-public-by-design",
         "9 endpoint(s) are unauthenticated by design; sample: logout",
         "router file(s) with unauthenticated endpoints and no exemption (0)"),
    ]
    allowed = [
        ("CLUSTER-float-money", "float used for money in total",
         "float found near cited line"),
        ("CLUSTER-allowlist", "expired allowlist entry for catalog import",
         "allowlist entry expired 2026-08-01"),
    ]
    out: list[tuple[str, bool, str]] = []
    for cluster, claim, detail in refused:
        ok, uncovered = claim_covers(cluster, claim, detail)
        out.append((f"refuse/{cluster}", not ok,
                    f"refutation was allowed for uncovered terms {sorted(uncovered)}"))
    for cluster, claim, detail in allowed:
        ok, _ = claim_covers(cluster, claim, detail)
        out.append((f"allow/{cluster}", ok,
                    "a sound refutation was refused — the guard is too strict"))
    return out


def check_measurement_parity() -> list[tuple[str, bool, str]]:
    """A measurement must agree with an independent re-derivation.

    Each expected number below was produced by a separate AST walk over the
    repository (a throwaway script, not this suite), and is re-derived here by the
    measurement itself. Where the two disagreed before, the measurement was
    wrong: `governance_columns_complete` now counts every column Law 23 names
    (2 tables lack `is_deleted`, 9 lack `country_code`), and
    `public_endpoint_undeclared` counts endpoints, not files.
    """
    from zz_core.measurements import Ctx, MEASUREMENTS

    root = HERE.parent.parent
    ctx = Ctx(root)
    expectations = [
        ("governance_columns_complete", "table(s) missing a mandated governance column",
         "2 lack is_deleted", None),
        ("public_endpoint_undeclared", "unauthenticated endpoint(s) with no recorded exemption",
         None, 1),
        ("orphan_feature_atom", "declared but never gated", None, 1),
    ]
    out: list[tuple[str, bool, str]] = []
    for name, needle, must_contain, minimum in expectations:
        fn = MEASUREMENTS.get(name)
        if fn is None:
            out.append((name, False, "measurement is not registered in MEASUREMENTS"))
            continue
        try:
            count, detail = fn(ctx)
        except Exception as exc:
            out.append((name, False, f"raised {type(exc).__name__}: {exc}"))
            continue
        if needle not in detail:
            out.append((name, False, f"describe the claim: got {detail!r}"))
        elif must_contain and must_contain not in detail:
            out.append((name, False, f"expected {must_contain!r} in {detail!r}"))
        elif minimum is not None and count < minimum:
            out.append((name, False, f"expected >= {minimum}, got {count} ({detail})"))
        else:
            out.append((name, True, ""))
    return out


def check_rate_limiter_predicate() -> list[tuple[str, bool, str]]:
    """Law 37's predicate must PASS the real limiter and FAIL an allow-all one.

    The old predicate could not match the shipped implementation ("failing closed"
    does not match `fail.?closed`; the denial is a 429, not a 503) and emitted a P0
    hard blocker from clean code.
    """
    from zz_scanners.s08_laws import _fails_closed

    real = (HERE.parent.parent / "backend" / "middleware"
            / "rate_limit_middleware.py")
    cases = [
        ("shipped limiter", real.read_text(encoding="utf-8-sig"), True),
        ("allow-all except",
         "async def d():\n    try:\n        return await call_next(r)\n"
         "    except Exception as e:\n        log(e)\n        return await call_next(r)\n",
         False),
        ("deny without acknowledgement",
         "async def d():\n    try:\n        return await call_next(r)\n"
         "    except Exception:\n        return JSONResponse(status_code=429)\n",
         False),
        ("acknowledged but still allows",
         "# fail-closed by design\nasync def d():\n    try:\n        return await call_next(r)\n"
         "    except Exception:\n        return await call_next(r)\n",
         False),
    ]
    out: list[tuple[str, bool, str]] = []
    for name, src, expected in cases:
        got, why = _fails_closed(src)
        out.append((f"law37/{name}", got is expected,
                    f"expected {expected}, got {got} ({why})"))
    return out


def check_module_bindings_include_constants() -> list[tuple[str, bool, str]]:
    """A module-level constant is DEFINED.

    `WF-dangling-import` collected only `def` and `class`, so every exported event
    name -- `EVENT_SHIPMENT_CREATED = "logistics.shipment.created"` -- counted as
    undefined. Ten such findings were emitted at P0 with
    `completion_blocker=yes` while all ten resolved. The detector now reports one
    dangling import, and reading the source confirms it is real
    (`run_scheduled_reconciliation_cycle` is imported by `jobs/reconciliation_cron.py`
    and defined nowhere under `backend/domains/finance/`).
    """
    import ast as _ast
    from zz_scanners.s19_workflow import module_level_bindings

    src = (
        'EVENT_A = "a"\n'
        'COUNT: int = 1\n'
        '_private = 2\n'
        'X, Y = 1, 2\n'
        'from other import ReExported\n'
        'import pkg.mod\n'
        'def fn(): pass\n'
        'async def afn(): pass\n'
        'class Klass: pass\n'
        'if True:\n'
        '    CONDITIONAL = 3\n'
    )
    got = module_level_bindings(_ast.parse(src))
    wanted = {"EVENT_A", "COUNT", "_private", "X", "Y", "ReExported", "pkg",
              "fn", "afn", "Klass", "CONDITIONAL"}
    missing = sorted(wanted - got)
    return [
        ("binding/def", "fn" in got, "functions must count as defined"),
        ("binding/const", "EVENT_A" in got,
         "module-level constants must count as defined"),
        ("binding/annassign", "COUNT" in got, "annotated assignments must count"),
        ("binding/tuple", "X" in got and "Y" in got, "tuple targets must count"),
        ("binding/reexport", "ReExported" in got, "re-exports must count"),
        ("binding/import", "pkg" in got, "imports must count"),
        ("binding/conditional", "CONDITIONAL" in got,
         "names bound under an `if` must count"),
        ("binding/complete", not missing, f"uncollected bindings: {missing}"),
    ]


def check_absence_claim_polarity() -> list[tuple[str, bool, str]]:
    """An absence claim must never be refuted by finding the thing absent.

    `backend/Dockerfile` has no HEALTHCHECK, `next.config.ts` has no bundle
    analyzer, `package.json` has no commit-message linter. All three claims were
    true and all three were marked ALREADY_FIXED because their tokens were absent
    from the file -- the absence was read as proof of repair.
    """
    from zozi_verify import ABSENCE_CLAIM

    absence = [
        "container has no HEALTHCHECK",
        "pyproject.toml declares no [project.dependencies]",
        "no bundle analyzer configured",
        "no commit-message linter is configured, so Conventional Commits is a"
        " convention with nothing enforcing it",
        "docs/runbooks/deploy.md does not exist",
        "rate limiter does not fail closed",
    ]
    present = [
        "float used for money in this service",
        "cross-domain write bypasses the event bus",
        "router performs a database write",
    ]
    out: list[tuple[str, bool, str]] = []
    for claim in absence:
        hit = ABSENCE_CLAIM.search(claim.lower())
        out.append((f"absence/{claim[:38]}", bool(hit),
                    "an absence claim was not recognised; it can be refuted wrongly"))
    for claim in present:
        hit = ABSENCE_CLAIM.search(claim.lower())
        out.append((f"present/{claim[:38]}", not hit,
                    "a positive claim was misread as an absence claim"))
    return out


def check_relocation_beats_refutation() -> list[tuple[str, bool, str]]:
    """A cited line that drifted must not refute a finding that still holds.

    `backend/modules/admin/routers/comms.py` was 203 lines when LOGIC-041 was
    scanned and 156 minutes later, while the `except WebSocketDisconnect: pass`
    it reports (Law 59) never stopped existing -- it moved to line 150.
    `generic()` answered "past EOF" with WRONG_LOCATION, which deleted a real
    violation from the plan on the strength of a line number. The construct is
    now re-located, and it has to stay conservative: a tie between two lines,
    a match made only of generic words, and an absence claim must all defer
    rather than confirm.
    """
    import tempfile
    from pathlib import Path

    from zozi_verify import Verifier

    src = "\n".join([
        "import json",
        "",
        "async def handler(ws):",
        "    try:",
        "        while True:",
        "            await ws.receive_text()",
        "    except WebSocketDisconnect:",
        "        pass",
        "    except Exception:",
        "        logger.debug('closed')",
    ]) + "\n"
    tie = "alpha_value beta_value\nalpha_value beta_value\n"
    generic_only = "the value is used\nthe value is set\n"
    # The docstring trap: `canonical` occurs exactly once in this file, inside
    # prose about a different model. Ranked by rarity alone it beat the real
    # declaration and put all four schema claims on line 3.
    models = "\n".join([
        '"""payments domain - models.',
        "",
        "The canonical Payment models still live elsewhere.",
        '"""',
        "from sqlalchemy import Column",
        "",
        "class PaymentMethod(Base):",
        '    __tablename__ = "payment_methods"',
    ]) + "\n"
    # The qualification-order trap: `pass` occurs once and outweighed the
    # `except WebSocketDisconnect` the claim is about, because a lone rare token
    # was allowed to veto a line that carried two claim tokens.
    ws = "\n".join([
        "from fastapi import WebSocket, WebSocketDisconnect",
        "",
        "async def handler(ws):",
        "    try:",
        "        while True:",
        "            await ws.receive_text()",
        "    except WebSocketDisconnect:",
        "        pass",
        "    except Exception:",
        "        logger.debug('x')",
        "",
        "def a():",
        "    try:",
        "        return 1",
        "    except Exception:",
        "        logger.debug('y')",
        "",
        "def b():",
        "    try:",
        "        return 2",
        "    except Exception:",
        "        logger.debug('z')",
        "",
        "def c():",
        "    try:",
        "        return 3",
        "    except Exception:",
        "        logger.debug('w')",
    ]) + "\n"

    claim = ("2 silent except block(s); first at line 203: pass-only: "
             "except WebSocketDisconnect:")

    out: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "backend").mkdir()
        (root / "backend" / "comms.py").write_text(src, encoding="utf-8")
        (root / "backend" / "tie.py").write_text(tie, encoding="utf-8")
        (root / "backend" / "generic.py").write_text(generic_only, encoding="utf-8")
        (root / "backend" / "models.py").write_text(models, encoding="utf-8")
        (root / "backend" / "ws.py").write_text(ws, encoding="utf-8")
        v = Verifier(root, root / "logs")

        def finding(rel, line, text, fid):
            return {"id": fid, "file": rel, "line": line, "current": text,
                    "cluster": "CLUSTER-silent-except"}

        # 1. cited line is past EOF, defect still in the file
        f = finding("backend/comms.py", 203, claim, "R-1")
        verdict, ev = v.generic(f)
        got = v._relocated.get("R-1")
        out.append((
            "past-EOF re-locates instead of refuting",
            verdict == "CONFIRMED" and got == 7 and "7" in ev,
            f"got {verdict} relocated={got} (expected CONFIRMED at line 7): {ev}"))

        # 2. cited line exists but drifted off the construct
        v._relocated.pop("R-1", None)
        f = finding("backend/comms.py", 1, claim, "R-2")
        verdict, ev = v.generic(f)
        got = v._relocated.get("R-2")
        out.append((
            "drifted line re-locates",
            verdict == "CONFIRMED" and got == 7,
            f"got {verdict} relocated={got} (expected CONFIRMED at line 7): {ev}"))

        # 3. two lines match equally well -> the claim does not pick one
        v._relocated.pop("R-2", None)
        f = finding("backend/tie.py", 1, "alpha_value beta_value", "R-3")
        verdict, ev = v.generic(f)
        out.append((
            "ambiguous tie defers to triage",
            verdict == "UNVERIFIABLE" and "R-3" not in v._relocated,
            f"a tie confirmed the claim: {verdict}: {ev}"))

        # 4. only generic prose matched -> not specific enough to relocate
        f = finding("backend/generic.py", 1, "the value is used elsewhere", "R-4")
        verdict, ev = v.generic(f)
        out.append((
            "generic words do not relocate",
            verdict != "CONFIRMED" and "R-4" not in v._relocated,
            f"generic prose produced a confirmation: {verdict}: {ev}"))

        # 5. an absence claim is never confirmed by finding the thing
        f = finding("backend/comms.py", 1,
                    "no WebSocketDisconnect handler exists in this file", "R-5")
        verdict, ev = v.generic(f)
        out.append((
            "absence claim is never re-located",
            verdict != "CONFIRMED" and "R-5" not in v._relocated,
            f"an absence claim was confirmed: {verdict}: {ev}"))

        # 6. a docstring cannot host the construct, however rare its wording
        f = finding("backend/models.py", 5,
                    "1x schema unknown in table `payment_methods`: schema "
                    "`payments` is not canonical", "R-6")
        verdict, ev = v.generic(f)
        got = v._relocated.get("R-6")
        out.append((
            "docstring does not capture the relocation",
            got == 8,
            f"expected the declaration at line 8, got {got}: {ev}"))

        # 7. a lone rare token may not veto a line that carries two
        f = finding("backend/ws.py", 12, claim, "R-7")
        verdict, ev = v.generic(f)
        got = v._relocated.get("R-7")
        out.append((
            "lone rare token does not veto a qualified line",
            got == 7,
            f"expected `except WebSocketDisconnect` at line 7, got {got}: {ev}"))
    return out


def run() -> int:
    passed = failed = 0
    failures: list[str] = []

    print("=" * 72)
    print("DETECTOR POLARITY — every detector must flag POSITIVE and spare NEGATIVE")
    print("=" * 72)

    for detector, cases in sorted(by_detector().items()):
        pred = PREDICATES.get(detector)
        print(f"\n{detector}  ({PRODUCTION_OF.get(detector, 'UNMAPPED')})")
        if pred is None:
            print("  !! no predicate defined — this detector is untested")
            failed += 1
            failures.append(f"{detector}: no predicate defined")
            continue
        for name, expectation, content in cases:
            fired = pred(content)
            want = expectation == "flag"
            ok = fired == want
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {name:34s} expect={expectation:6s} fired={fired}")
            if ok:
                passed += 1
            else:
                failed += 1
                failures.append(f"{detector}/{name}: expected {expectation}, "
                                f"detector fired={fired}")

    print()
    print("=" * 72)
    print("PROBE POLARITY — a probe's kind must agree with its claim")
    print("=" * 72)
    for cluster, ok, msg in check_probe_polarity():
        print(f"  [{'PASS' if ok else 'FAIL'}] {cluster}")
        if not ok:
            print(f"         {msg}")
            failed += 1
            failures.append(f"probe polarity/{cluster}: {msg}")
        else:
            passed += 1

    print()
    print("=" * 72)
    print("PROBE SELF-EVIDENCING — a probe must be able to refute its detector")
    print("=" * 72)
    for cluster, ok, msg in check_probe_not_self_evidencing():
        if cluster.startswith("("):
            print(f"  [SKIP] {cluster} {msg}")
            continue
        print(f"  [{'PASS' if ok else 'FAIL'}] {cluster}")
        if not ok:
            print(f"         {msg}")
            failed += 1
            failures.append(f"self-evidencing/{cluster}: {msg}")
        else:
            passed += 1

    print()
    print("=" * 72)
    print("PROBE-TO-CLAIM LINKAGE — a probe must be about the finding it verifies")
    print("=" * 72)
    for cluster, ok, msg in check_probe_matches_claim():
        print(f"  [{'PASS' if ok else 'FAIL'}] {cluster}")
        if not ok:
            print(f"         {msg}")
            failed += 1
            failures.append(f"linkage/{cluster}: {msg}")
        else:
            passed += 1

    for title, fn in (
        ("INSTRUMENT-GAP GUARD — a refutation must be about the claim",
         check_instrument_gap_guard),
        ("MEASUREMENT PARITY — the re-check must agree with an independent walk",
         check_measurement_parity),
        ("LAW-37 PREDICATE — must PASS the shipped limiter and FAIL allow-all",
         check_rate_limiter_predicate),
        ("ABSENCE-CLAIM POLARITY — absence may not be read as repair",
         check_absence_claim_polarity),
        ("MODULE BINDING — a constant is a definition",
         check_module_bindings_include_constants),
        ("RELOCATION — a drifted line may not refute a live defect",
         check_relocation_beats_refutation),
        ("CONTRADICTION PROBES — dimensions 21/27 claims must be falsifiable",
         check_contradiction_probes),
        ("CHECKLIST REFRESHER — regeneration must be a fixed point",
         check_checklist_refresher),
    ):
        print()
        print("=" * 72)
        print(title)
        print("=" * 72)
        for name, ok, msg in fn():
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
            if not ok:
                print(f"         {msg}")
                failed += 1
                failures.append(f"{title.split(' — ')[0]}/{name}: {msg}")
            else:
                passed += 1

    print()
    print("=" * 72)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 72)
    for f in failures:
        print(f"  - {f}")
    return 0 if failed == 0 else 1


def check_contradiction_probes() -> list[tuple[str, bool, str]]:
    """Dimensions 21/27 findings must be falsifiable, not merely assertable.

    Every contradiction and chain finding used to be emitted with an EMPTY
    probe, so no instrument could settle it and the verifier's only honest
    answer was UNVERIFIABLE -- 9 hard completion blockers parked permanently.
    Each of these measurements must hold on the real tree (the defect is real)
    AND flip to 0 on a synthetic tree where the defect is repaired, or it is
    just as unfalsifiable as no probe at all.
    """
    import shutil
    from zz_core.measurements import run

    out: list[tuple[str, bool, str]] = []

    def holds(name: str, arg: str, want: bool, root: Path | None = None) -> None:
        try:
            count, detail = run(root or ROOT, name, arg)
        except Exception as exc:  # a measurement that cannot run settles nothing
            out.append((f"{name}({arg or '-'})", False,
                        f"measurement raised {type(exc).__name__}: {exc}"))
            return
        out.append((f"{name}({arg or '-'}) == {int(want)}",
                    bool(count > 0) == want,
                    f"re-derived {count} — expected {'>0' if want else '0'}: {detail}"))

    # The real tree: every one of these defects is live, so each must hold.
    holds("orphan_frontend_module_route", "hr", True)
    holds("router_shadowed_by_package", "backend/modules/employee/routers", True)
    holds("chain_event_unwired", "finance.journal.posted", True)
    holds("chain_event_unwired", "accounts.customer.registered", True)

    # A synthetic tree where the same defects are repaired. A probe that still
    # reports "holds" here would be self-evidencing.
    tmp = Path(tempfile.mkdtemp(prefix="zozi-measure-"))
    try:
        (tmp / "backend" / "modules" / "admin").mkdir(parents=True)
        (tmp / "backend" / "domains" / "finance").mkdir(parents=True)
        (tmp / "frontend" / "web_app").mkdir(parents=True)
        (tmp / "frontend" / "web_app" / "next.config.ts").write_text(
            "async rewrites(){return [{source: '/hr/:path*', destination: 'x'}]}",
            encoding="utf-8")
        (tmp / "backend" / "domains" / "finance" / "events.py").write_text(
            'EVENTS = ["finance.journal.posted"]', encoding="utf-8")
        holds("orphan_frontend_module_route", "hr", True, tmp)

        (tmp / "backend" / "modules" / "hr").mkdir()
        holds("orphan_frontend_module_route", "hr", False, tmp)

        (tmp / "backend" / "modules" / "hr").rmdir()
        holds("chain_event_unwired", "finance.journal.posted", False, tmp)
        holds("chain_event_unwired", "finance.payout.created", True, tmp)

        routers = tmp / "backend" / "modules" / "employee" / "routers"
        routers.mkdir(parents=True)
        (routers / "hr.py").write_text("x = 1", encoding="utf-8")
        holds("router_shadowed_by_package", "backend/modules/employee/routers",
              False, tmp)
        (routers / "hr").mkdir()
        holds("router_shadowed_by_package", "backend/modules/employee/routers",
              True, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # And the builders must actually be wired to these claims.
    from zz_core.probes import FINDING_BUILDER, STRUCTURAL, _builder_for
    from zz_core.model import Finding

    for fid in ("CONTRAD-001", "CONTRAD-002", "CONTRAD-003", "CONTRAD-029",
                "CONTRAD-034"):
        out.append((f"{fid} has a probe builder", fid in FINDING_BUILDER,
                    "a contradiction finding with no builder is permanently "
                    "UNVERIFIABLE"))
    for cid in range(1, 8):
        cluster = f"CLUSTER-chain-chain-{cid:03d}"
        out.append((f"{cluster} has a probe builder",
                    cluster in STRUCTURAL,
                    "a chain finding with no builder is permanently UNVERIFIABLE"))
    for cluster in ("CLUSTER-extra-module", "CLUSTER-extra-domain"):
        out.append((f"{cluster} has a probe builder", cluster in STRUCTURAL, ""))

    f = Finding(id="BLOCK-003", cluster="CLUSTER-chain-chain-005",
                current="CHAIN-005 (Admin ledger posting and reconciliation) is "
                        "PARTIAL: 2/2 steps located; events 0/1; tests=yes",
                file="backend/domains/finance/", notes="chain=CHAIN-005; "
                        "events=finance.journal.posted")
    builder = _builder_for(f)
    out.append(("BLOCK-003 resolves its builder", builder == "_chain_event_probe",
                f"got {builder!r}"))
    if builder:
        import zz_core.probes as P
        out.append(("BLOCK-003 probe names its event",
                    (P._chain_event_probe(f, "") or {}).get("arg")
                    == "finance.journal.posted",
                    "the probe must name the event so the re-check can look "
                    "for exactly that"))
    f2 = Finding(id="", cluster="CLUSTER-chain-chain-007",
                 current="CHAIN-007 is PARTIAL: 3/3 steps located; events 0/2",
                 file="backend/domains/suppliers/", notes="events=a.one,b.two")
    import zz_core.probes as P
    out.append(("a multi-event chain refuses a per-event probe",
                P._chain_event_probe(f2, "") is None,
                "probing only one of two events would adjudicate a claim the "
                "finding never made"))
    return out


def check_checklist_refresher() -> list[tuple[str, bool, str]]:
    """`refresh_checklist.py` must be a fixed point, and must not mangle text.

    Two defects lived here. A string replacement let `\\1` through and wrote a
    literal backslash into the document while DELETING the run-10 history row;
    and the anchors were one-shot, so a second run over unchanged logs appended
    a new run-history row forever. Both are silent -- the file stays plausible.
    """
    import importlib
    import re as _re
    sys.path.insert(0, str(ROOT / "_zozi_audit"))
    rc = importlib.import_module("refresh_checklist")

    out: list[tuple[str, bool, str]] = []
    data = rc.load()
    head = rc.DOC.read_text(encoding="utf-8-sig")

    once = rc.build(data, head)
    twice = rc.build(data, once)

    out.append(("re-running on unchanged logs changes nothing", once == twice,
                "the refresher is not idempotent; --check can never pass twice"))
    out.append(("no literal group reference leaks into the document",
                not _re.search(r"^\s*\\?\d\| \d{4}-\d{2}-\d{2} \|", once, _re.M)
                and "\\1" not in once,
                "a replacement string re-interpreted \\1 as a group reference"))
    out.append(("run history keeps its earlier rows",
                once.count("| 10 | 2026-10-02 | `falsification_gate_added`") == 1
                and once.count("| 9 | 2026-10-02 | `http_layer_and_settings")
                == 1,
                "the anchor replaced the last row instead of appending after it"))
    history = _re.search(r"\| Run \| Date \| Status \| Key Changes \|.*?\n\n---",
                         once, _re.S)
    run_id = str(data["run"].get("run_id"))
    out.append(("exactly one run-history row names the current run",
                history is not None
                and history.group(0).count(run_id) == 1,
                "a re-run appended another row for the same run, or the run id "
                "is not confined to the run-history table"))
    for name, _legacy, _build in rc.BLOCKS:
        b, e = rc.BEGIN.format(name=name), rc.END.format(name=name)
        out.append((f"block {name!r} is fenced", once.count(b) == 1
                    and once.count(e) == 1,
                    "without a fence the next run cannot find its own output"))
    out.append(("no unfenced legacy anchor is still live",
                "| PB-01 | python-jose" not in once,
                "the §24 register still lists the Run 5 ids"))

    gate = rc.gate_table(data)
    out.append(("a gate row never claims FAIL with no confirmed blocker",
                not _re.search(r"\| FAIL — (?:0 confirmed|0 blocker)", gate),
                "the gate table asserted a FAIL it had no confirmed finding for"))
    out.append(("the gate states a readiness verdict",
                "**Production Ready:** NO" in gate
                and "gates PASS" in gate, ""))

    cells = rc._cell("a | b")
    out.append(("_cell keeps text when no limit is given", cells == "a \\| b",
                f"_cell returned {cells!r}; a limit of 0 must mean 'no limit'"))
    return out


if __name__ == "__main__":
    raise SystemExit(run())