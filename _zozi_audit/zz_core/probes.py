"""Attach machine-checkable probes to findings that do not yet have one.

Why this exists
---------------
`probe.py` implements 14 predicate kinds, and the scanners that bother to emit one
use it well — probe coverage rose from 86/1629 (5.3%) to 565/1671 (33.8%) once
dimension 24/25/26 started reporting. But 1,106 findings still rest on prose, and
prose cannot be re-verified by a machine: it is re-read by a model that already
decided what it saw last time. That is precisely how a `FALSE_POSITIVE` becomes
`CONFIRMED` on the next run.

This module converts the remaining decidable claims into probes, in one auditable
place rather than by editing 22 scanners.

The governing rule
------------------
`probe.py` states it: *"A detector may not emit a probe it cannot itself run.
Otherwise the bug moves into the probe and the verdict becomes confidently
wrong."* So this module is deliberately narrow:

* only ``text_matches`` and ``text_absent`` are emitted — both are pure regex over
  source text and have no AST or filesystem edge cases;
* every pattern is an **explicit, hand-written rule**, never inferred from the
  finding's prose. A cluster with no rule stays unprobed and is reported;
* the expected ``count`` is measured from the file **at attach time**, inside the
  same window the probe will later use. The probe therefore asserts exactly what
  was observed — not an approximation of it;
* if the file cannot be read, or the pattern does not match anywhere in it, the
  finding is left unprobed. A probe that cannot hold is worse than no probe,
  because it manufactures a green verdict.

Semantics of the result
-----------------------
``text_matches`` with a measured count **holds while the code is unchanged** and
fails as soon as the region is edited. That is the correct meaning of "this claim
is still true in current source": the re-run loop reads a failure as evidence the
claim changed and re-checks it by hand rather than silently marking it resolved.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .constants import ROUTER_OK_INFRA
from .probe import _ALLOWED_IMPORTS, _layer_of

_ALL_LAYERS = set(_ALLOWED_IMPORTS)

#: Clusters whose claim is structural rather than textual, keyed to a builder that
#: returns a probe dict or ``None``. ``None`` leaves the finding honestly unprobed:
#: an invented probe manufactures confident wrong verdicts.
#: Law number -> independent re-derivation used to adjudicate the aggregate
#: finding that `laws_all` emits for it. A law absent from this map gets no
#: probe and is reported honestly as unprobed rather than given an invented one.
LAW_MEASURE_BY_LAW: dict[int, str] = {
    1: "law01_reverse_imports",
    3: "law03_event_spine",
    4: "law04_ungated_route",
    5: "law05_set_local_missing",
    7: "law07_undated_allowlist",
    12: "law12_extra_domains",
    13: "law13_extra_modules",
    19: "law19_float_money",
    21: "law21_python_timestamps",
    23: "law23_missing_audit_columns",
    27: "law27_temp_scripts",
    34: "law34_fstring_sql",
    37: "law37_rate_limiter",
    45: "law45_relationship_lazy",
    49: "law49_migration_heads",
    53: "law53_fk_without_index",
    54: "law54_missing_is_deleted",
    58: "law58_print_calls",
    59: "law59_silent_excepts",
    62: "law62_todo_hygiene",
    84: "law84_raw_getenv",
    123: "law123_provider_routing",
    129: "law129_provider_health",
    222: "law222_offset_pagination",
    248: "law248_runbooks",
    275: "law275_field_encryption",
}


def _codeowners_absent_probe(f, text: str) -> dict | None:
    """Law 240: required review is recorded nowhere.

    The defect IS the absence of the file, so the confirming probe is
    `path_absent` -- `path_present` would assert the opposite and refute a
    finding that is still true.
    """
    if "CODEOWNERS" not in ((f.current or "") + (f.fix or "")) \
            and "branch-protection" not in ((f.current or "") + (f.fix or "")):
        return None
    return {"kind": "path_absent", "path": ".github/CODEOWNERS",
            "note": "Law 240: the defect IS that no CODEOWNERS file exists"}


def _test_isolation_probe(f, text: str) -> dict | None:
    """Laws 74/214: a test mutates a process global with nothing to undo it."""
    if not f.file:
        return None
    return {"kind": "test_global_mutation_unguarded",
            "path": f.file.replace("\\", "/"), "line": int(f.line or 0),
            "note": "Laws 74/214: the enclosing test declares no cleanup"}


def _tsconfig_strict_probe(f, text: str) -> dict | None:
    """Law 170: TypeScript strict mode is on."""
    return {"kind": "tsconfig_strict_off",
            "path": (f.file or "frontend/shared/tsconfig.json").replace("\\", "/"),
            "note": "Law 170: compilerOptions.strict must be true"}


def _law_aggregate_probe(f, text: str) -> dict | None:
    """`LAW-nnn` aggregates in `09_laws`, which are phrased as counts.

    The claim is "the law is violated, and here is the magnitude". Token
    matching cannot test a magnitude, so these 26 findings were permanently
    UNVERIFIABLE. The probe names the independent measurement for that law; the
    runner re-derives the quantity and holds while it is still non-zero.
    """
    m = re.match(r"LAW-(\d+)$", (f.id or "").strip())
    if not m:
        return None
    measure = LAW_MEASURE_BY_LAW.get(int(m.group(1)))
    if not measure:
        return None
    return {"kind": "law_measure", "measure": measure,
            "note": f"Law {m.group(1)}: the violation count re-derived from source"}


#: Cluster -> independent re-derivation for the aggregate count claims. These
#: clusters all phrase their finding as "N <thing> exist", which no amount of
#: pattern-matching on the claim text can adjudicate -- the token fallback can
#: only ever answer UNVERIFIABLE, which is what kept 101 findings in 85 clusters
#: unresolved. Measurement bodies live in `zz_core.measurements`.
CLUSTER_MEASUREMENT: dict[str, str] = {
    # anti-patterns
    "CLUSTER-ap-stub-function-notimplementederror": "notimplementederror",
    "CLUSTER-ap-empty-handler-pass": "empty_handler_pass",
    "CLUSTER-ap-todo-only": "todo_only",
    "CLUSTER-ap-todo-only-implementation": "todo_only",
    "CLUSTER-ap-unimplemented-placeholder": "placeholder_marker",
    "CLUSTER-intent-stub": "intent_placeholder",
    # root / files
    "CLUSTER-root-discipline": "root_temp_scripts",
    "CLUSTER-package-manager": "noncanonical_lockfile",
    "CLUSTER-base-image": "base_image_drift",
    "CLUSTER-docs": "missing_setup_doc",
    # database
    "CLUSTER-select-star": "select_star",
    "CLUSTER-offset-pagination": "offset_pagination",
    "CLUSTER-count-queries": "count_queries",
    "CLUSTER-search-index": "leading_wildcard_ilike",
    "CLUSTER-n-plus-1": "relationship_without_lazy",
    "CLUSTER-table-relation": "relationship_without_lazy",
    "CLUSTER-db-pool": "db_pool_size",
    "CLUSTER-read-replica": "read_replica_unused",
    "CLUSTER-rls": "rls_policy_coverage",
    "CLUSTER-table-drift": "schema_drift",
    "CLUSTER-table-governance": "governance_columns_complete",
    "CLUSTER-migration-heads": "migration_heads",
    # providers / operations
    "CLUSTER-provider-health": "provider_health_check",
    "CLUSTER-provider-timeout": "provider_timeout",
    "CLUSTER-provider-resilience": "provider_circuit_breaker",
    "CLUSTER-provider-config": "provider_raw_getenv",
    "CLUSTER-provider-extra": "provider_extra_packages",
    "CLUSTER-orphan-provider": "provider_orphan",
    "CLUSTER-payment-webhook": "payment_webhook_signature",
    "CLUSTER-orphan-job": "orphan_job_module",
    "CLUSTER-raw-getenv": "raw_getenv",
    "CLUSTER-print-logging": "print_in_production",
    "CLUSTER-pii-logs": "pii_logs",
    # architecture / logic
    "CLUSTER-router-db-access": "router_db_access",
    "CLUSTER-public-by-design": "public_endpoint_undeclared",
    "CLUSTER-event-spine": "event_spine",
    "CLUSTER-deep-nesting": "deep_nesting",
    "CLUSTER-ssrf": "ssrf_unguarded",
    "CLUSTER-handover": "handover_unguarded",
    # features
    "CLUSTER-orphan-feature": "orphan_feature_atom",
    "CLUSTER-ghost-feature": "dead_feature_gate",
    # "feature-gate" carries FEAT-DEAD: declared-but-never-gated -- the OPPOSITE
    # direction to a ghost atom. Pointing it at `dead_feature_gate` made the
    # verifier disprove 146 real orphans with a measurement of the other set.
    "CLUSTER-feature-gate": "orphan_feature_atom",
    "CLUSTER-coverage-route": "orphaned_spec",
    # frontend design system
    "CLUSTER-color-drift": "raw_palette_classes",
    "CLUSTER-design-primitives": "no_variant_system",
    # frontend interaction
    "CLUSTER-interaction-button": "button_missing_type",
    "CLUSTER-interaction-form": "input_without_label",
    "CLUSTER-interaction-state": "swallowed_error",
    "CLUSTER-interaction-modal": "modal_no_escape",
    # performance
    "CLUSTER-cache-coverage": "cache_coverage",
    # declared laws
    "CLUSTER-law-test-isolation": "unguarded_global_mutation",
}


#: Several clusters carry DIFFERENT claims under one name, so a cluster-level
#: mapping silently gave `DS-hex-drift` the palette measurement and
#: `IX-modal-escape` the focus measurement -- three true findings verified as
#: one unrelated thing. Where the claims differ, the finding's own id selects the
#: measurement; this table takes precedence over `CLUSTER_MEASUREMENT`.
FINDING_MEASUREMENT: dict[str, str] = {
    # colour drift: three distinct vocabularies
    "DS-palette-drift": "raw_palette_classes",
    "DS-hex-drift": "hex_drift",
    "DS-inline-style": "inline_style",
    # design primitives: variant system, ref forwarding, duplicated markup
    "DS-no-variant-system": "no_variant_system",
    "DS-primitive-ref": "primitive_no_ref",
    "DS-duplicate-markup": "duplicate_primitive_markup",
    # engine factory: pool sizing and the asyncpg statement cache are separate
    "DB-005": "db_pool_size",
    "DB-006": "asyncpg_statement_cache",
    # modals: focus, Escape and destructive confirmation are three guarantees
    "IX-modal-focus": "modal_no_focus",
    "IX-modal-escape": "modal_no_escape",
    "IX-destructive-confirm": "destructive_without_confirm",
    # buttons: type, swallowed mutation failure, accessible name
    "IX-button-type": "button_missing_type",
    "IX-mutation-error-swallowed": "mutation_error_swallowed",
    "IX-icon-button-name": "icon_button_unnamed",
    # provider resilience: breaker, retry and timeout are different guarantees
    "OBS-001": "provider_circuit_breaker",
    "OBS-002": "provider_retry_policy",
    "OBS-003": "provider_timeout",
    # pipeline capabilities named individually
    "D2P-001": "ci_secret_scanning",
    "D2P-002": "ci_dependency_scanning",
    # a named capability with no implementation
    "FIN-manual-processes": "placeholder_capability",
    "QA-mechanisms-absent": "placeholder_capability",
}


def _measurement_probe(f, text: str) -> dict | None:
    """An aggregate count claim, re-derived from source by a measurement."""
    name = FINDING_MEASUREMENT.get(f.id or "")
    if not name:
        name = CLUSTER_MEASUREMENT.get(f.cluster or "")
    if not name:
        return None
    arg = ""
    m = re.search(r"no implementation found for:\s*([\w.]+)", f.current or "")
    if m:
        name, arg = "placeholder_capability", m.group(1)
    return {"kind": "measure", "measure": name, "arg": arg,
            "note": "the count is re-derived from source, independently of the scan"}


STRUCTURAL: dict[str, str] = {
    # Aggregate count claims: one builder, keyed by cluster.
    "_ANY_": "_measurement_probe",
    "CLUSTER-long-function": "_function_len_probe",
    "CLUSTER-router-business-logic": "_router_thinness_probe",
    "CLUSTER-file-too-long": "_file_size_probe",
    "CLUSTER-duplicate-definition": "_duplicate_symbol_probe",
    # The three below were previously served by regex `PROBE_RULES` whose pattern
    # described a NARROWER claim than the finding, so the probe matched nowhere
    # and the finding was dropped from coverage instead of being checked:
    #   rel-lazy      174 findings, 0 probed
    #   env-undeclared 41 findings, 0 probed
    #   silent-except 101 findings, 53 probed, 48 "matched nowhere"
    "CLUSTER-tf-rel-lazy": "_rel_lazy_probe",
    "CLUSTER-env-undeclared": "_env_undeclared_probe",
    "CLUSTER-silent-except": "_silent_except_probe",
}

#: Second batch, added after measuring what the compiler reported as "needs
#: triage". Each entry converts a claim that previously had NO way to be refuted
#: into one an instrument can check. 374 findings were unverifiable; every builder
#: below is responsible for a measurable slice of that.
STRUCTURAL.update({
    # Law 23 model-column gaps (35 findings across four clusters)
    "CLUSTER-tf-missing-country_code": "_missing_column_probe",
    "CLUSTER-tf-missing-created_at": "_missing_column_probe",
    "CLUSTER-tf-missing-updated_at": "_missing_column_probe",
    "CLUSTER-tf-missing-is_deleted": "_missing_column_probe",
    "CLUSTER-tf-schema-missing": "_missing_column_probe",
    # P20 renamed this cluster to `-symbol`; the mapping kept the old name, so 73
    # findings attached no probe.
    "CLUSTER-duplicate-symbol": "_duplicate_symbol_probe",
    # Law 21: the regex rule matched only a literal `datetime.now`, but the code
    # uses `default=_utcnow` (an alias), so 79 findings got nothing.
    "CLUSTER-tf-timestamp-default": "_timestamp_default_probe",
    # --- clusters that previously had NO rule, so nothing could re-decide them --
    # The `09_laws` aggregate per violated law. All 26 arrive with the same
    # shape ("N <thing>"), so one builder keyed on the LAW number serves them.
    "CLUSTER-law-architecture": "_law_aggregate_probe",
    "CLUSTER-law-structure": "_law_aggregate_probe",
    "CLUSTER-law-code-quality": "_law_aggregate_probe",
    "CLUSTER-law-security": "_law_aggregate_probe",
    "CLUSTER-law-database": "_law_aggregate_probe",
    "CLUSTER-law-config": "_law_aggregate_probe",
    "CLUSTER-law-migration": "_law_aggregate_probe",
    "CLUSTER-law-provider": "_law_aggregate_probe",
    "CLUSTER-law-docs": "_law_aggregate_probe",
    "CLUSTER-law-performance": "_law_aggregate_probe",
    "CLUSTER-law-testing": "_law_aggregate_probe",
    "CLUSTER-law-git-hygiene": "_law_aggregate_probe",
    "CLUSTER-law-frontend-contract": "_law_aggregate_probe",
    "CLUSTER-law-kernel-purity": "_law_aggregate_probe",
    "CLUSTER-law-test-isolation": "_test_isolation_probe",
    "CLUSTER-law-frontend-contract": "_tsconfig_strict_probe",
    # Law 240: branch protection is recorded nowhere in the repo. The ABSENCE
    # is the defect, so the confirming probe is `path_absent` on CODEOWNERS.
    "CLUSTER-law-git-hygiene": "_codeowners_absent_probe",
    "CLUSTER-law-gap-checkable": "_law_coverage_probe",
    "CLUSTER-law-not-statically-verifiable": "_law_coverage_probe",
    "CLUSTER-law-unattributed": "_law_coverage_probe",
    "CLUSTER-law-citation-drift": "_law_citation_drift_probe",
    "CLUSTER-settings-contract": "_settings_contract_probe",
    "CLUSTER-workflow-runtime": "_beat_schedule_probe",
    "CLUSTER-migration-downgrade": "_migration_downgrade_probe",
    "CLUSTER-migration-destructive": "_migration_destructive_probe",
    "CLUSTER-supply-chain": "_supply_chain_probe",
    "CLUSTER-router-empty": "_router_empty_probe",
    # Law 98 -- re-derivable from the real import graph
    "CLUSTER-circular-import": "_cycle_probe",
    # Law 1 / 97-106 -- these kinds existed and were never wired
    "CLUSTER-infra-imports-above": "_imports_above_probe",
    "CLUSTER-module-imports-infrastructure": "_imports_above_probe",
    # Law 248 -- the runbook's absence IS the claim, so probe presence
    "CLUSTER-runbooks": "_runbook_probe",
    # Law 67
    "CLUSTER-duplicate-file": "_duplicate_file_probe",
    # Law 298
    "CLUSTER-job-resilience": "_dlq_probe",
    # Law 227
    "CLUSTER-rls": "_rls_probe",
    # Law 3
    "CLUSTER-stub-subscriber": "_stub_subscriber_probe",
    # Law 12
    "CLUSTER-forbidden-package": "_forbidden_package_probe",
})


#: Repository root, published by :func:`attach`. Builders receive only
#: `(finding, text)`, so layout-dependent lookups read this instead of guessing.
_REPO_ROOT: Path | None = None

#: builders whose claim is about structure, so they need no source text
_FILELESS_BUILDERS = frozenset({"_cycle_probe"})

#: Probe kinds whose VERDICT depends on the file's text. `attach()` reads each
#: candidate's source to confirm a pattern is still present, and that check is
#: only meaningful for these kinds. A `path_present`, `path_absent` or AST kind
#: reads whatever it needs at RUN time, so gating attachment on a readable file
#: silently dropped probes that would have resolved fine -- `CLUSTER-runbooks` (3),
#: `CLUSTER-rls` (1) and `CLUSTER-http-headers` (1) attached nothing because the
#: cited path was absent, which is exactly the state those findings describe.
#:
#: So the gate is applied AFTER building, on the probe's own `kind`.
_TEXTUAL_PROBE_KINDS = frozenset({
    "text_matches", "text_absent", "text_present",
    "symbol_occurrences", "attribute_absent_in_dict", "filename_count_above",
})


def _table_of(f) -> str:
    m = re.search(r"table `([A-Za-z0-9_]+)`", f.current or "")
    return m.group(1) if m else ""


def _missing_column_probe(f, text: str) -> dict | None:
    """Law 23: `CLUSTER-tf-missing-*` -> `ast_model_missing_column`.

    The column name is the whole claim, so it comes from the cluster key rather
    than from parsing the sentence.
    """
    column = {
        "CLUSTER-tf-missing-country_code": "country_code",
        "CLUSTER-tf-missing-created_at": "created_at",
        "CLUSTER-tf-missing-updated_at": "updated_at",
        "CLUSTER-tf-missing-is_deleted": "is_deleted",
        "CLUSTER-tf-schema-missing": "country_code",
    }.get(f.cluster or "")
    if not column or not f.file:
        return None
    return {
        "kind": "ast_model_missing_column",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        "column": column,
        "table": _table_of(f),
        "note": f"Law 23: every model declares {column}",
    }


def _cycle_probe(f, text: str) -> dict | None:
    """Law 98: `package_cycle_exists`, re-derived from the AST import graph."""
    m = re.search(r"circular package dependency: (.+)$", f.current or "")
    if not m:
        return None
    chain = [x.strip() for x in m.group(1).split("->")]
    if len(chain) < 2:
        return None
    return {"kind": "package_cycle_exists", "packages": chain,
            "note": "Law 98: no circular imports between packages"}


def _imports_above_probe(f, text: str) -> dict | None:
    """Law 1 / 97-106: `module_imports_above`, which existed but was never wired.

    The runner reads `modules` (top-level names) and `layer`, so those are the
    keys emitted here.

    The direction is the whole point and it was inverted. The claim is that a
    LOWER layer reaches UP -- `infrastructure` importing `providers`. So the
    forbidden set must be the layers ABOVE the file's own layer. The previous
    build derived `modules` from the file's own layer, which made the probe ask
    "does infrastructure import infrastructure?" -- always false, so it refuted
    all 6 findings that were in fact true.

    `CLUSTER-infra-imports-above` -> forbid every layer above the file's own.
    `CLUSTER-module-imports-infrastructure` -> forbid the named target, which is
    what a router must reach only through a domain service.

    Two corrections kept this from over-refuting:

    * The forbidden set is now the DETECTOR's list, not a layer ordering. The
      ordering omitted `jobs` and `middleware`, so a genuine
      `infrastructure` -> `middleware` import (Law 1) had nothing to match and
      was refuted.
    * `modules/` may import `infrastructure/` only from a sanctioned subpackage
      (the RBAC gates, the SET-LOCAL helpers, the DTOs). Without
      `allow_prefixes` the probe consulted only `_ALLOWED_IMPORTS`, which lists
      `infrastructure` as allowed for `modules`, and so refuted every real hit.
"""
    from .probe import _layer_of
    if not f.file:
        return None
    rel = f.file.replace("\\", "/")
    cluster = f.cluster or ""
    layer = _layer_of(rel)

    allow: list[str] = []
    if cluster == "CLUSTER-infra-imports-above":
        # the detector's exact per-layer forbidden set
        forbidden = {
            "infrastructure": ("domains", "modules", "rbac", "providers",
                               "jobs", "middleware"),
            "kernel": ("domains", "modules", "rbac", "providers", "jobs",
                       "middleware"),
            "providers": ("domains", "modules", "rbac", "jobs", "middleware"),
            "middleware": ("domains", "modules", "providers", "jobs"),
        }
        base = layer.split(".")[0]
        modules = list(forbidden.get(base, ()))
        note = f"Law 1: a {base} module must not import a higher layer"
    else:
        m = re.search(r"imports `([\w.]+)`", f.current or "")
        top = m.group(1).split(".")[0] if m else ""
        if not top:
            return None
        modules = [top]
        if top == "infrastructure":
            allow = list(ROUTER_OK_INFRA)
        note = "Law 1: arrows point down only -- reach the domain via a service"

    if not modules:
        return None
    probe = {"kind": "module_imports_above", "path": rel,
             "modules": modules, "layer": layer, "note": note}
    if allow:
        probe["allow_prefixes"] = allow
    return probe


def _runbook_probe(f, text: str) -> dict | None:
    """Law 248: the runbook's ABSENCE is the defect.

    So the confirming probe is `path_absent`. It was `path_present`, which
    asserts the opposite and therefore refuted all 3 true findings: a missing
    runbook is exactly what the finding says.
    """
    m = re.search(r"(docs/runbooks/[\w./-]+\.md)", (f.fix or "") + " " + (f.current or ""))
    if not m:
        return None
    return {"kind": "path_absent", "path": m.group(1),
            "note": "Law 248: no runbook exists here -- the defect IS the absence"}


def _duplicate_file_probe(f, text: str) -> dict | None:
    """Law 67: the claim is that the duplicate STILL EXISTS.

    The old build probed `path_absent` on the second path, which asserts the
    duplicate is gone -- the opposite of the finding, so it refuted all 5 true
    findings. The confirming predicate is that both files are still present.
    """
    paths = [p for p in re.findall(r"([\w./-]+\.py)", f.current or "") if p]
    paths = list(dict.fromkeys(paths))
    if len(paths) < 2:
        return None
    return {"kind": "duplicate_files_both_present", "paths": paths[:2],
            "note": "Law 67: byte-identical duplicates both still exist"}


def _dlq_probe(f, text: str) -> dict | None:
    """Law 298: the module must reference a dead-letter queue."""
    if not f.file:
        return None
    # the finding claims the module has NO DLQ reference, so absence is the
    # defect. `text_matches` asserted the opposite and refuted a true finding.
    return {"kind": "text_absent", "path": f.file.replace("\\", "/"),
            "line": int(f.line or 0), "within": 0, "whole_file": True,
            "pattern": r"(?i)\b(dlq|dead[_ -]?letter|deadletter)\b",
            "note": "Law 298: terminal failures route to a replayable DLQ"}


def _rls_probe(f, text: str) -> dict | None:
    """Law 227: `SET LOCAL app.country_code` must actually be executed."""
    if not f.file:
        return None
    # claim is "sets ContextVars only; no SET LOCAL executed" -> absence again
    return {"kind": "text_absent", "path": f.file.replace("\\", "/"),
            "line": int(f.line or 0), "within": 0, "whole_file": True,
            "pattern": r"(?i)SET\s+LOCAL\s+app\.country_code",
            "note": "Law 227: RLS context set with SET LOCAL, never session SET"}


def _stub_subscriber_probe(f, text: str) -> dict | None:
    """Law 3: a subscriber is still a stub while `# Future:` markers remain."""
    if not f.file:
        return None
    # claim is "stub: 3 handlers, 3 # Future: markers" -> the markers are
    # PRESENT, so presence is the defect and `text_absent` refuted it.
    return {"kind": "text_matches", "path": f.file.replace("\\", "/"),
            "line": int(f.line or 0), "within": 0, "whole_file": True,
            "pattern": r"#\s*Future\s*:",
            "note": "Law 3: handlers must be implemented, not deferred"}


def _forbidden_package_probe(f, text: str) -> dict | None:
    """Law 12: the forbidden dependency must still be declared."""
    m = re.search(r"`([A-Za-z0-9_.\-]+)`", f.current or "")
    if not m:
        return None
    name = m.group(1)
    base = _REPO_ROOT
    # Prefer the manifest the finding actually cites. The previous build always
    # read `requirements.txt`; the findings cite `requirements-compiled.txt`, so
    # the pattern was absent from the file it read and all 4 were refuted.
    cited = (f.file or "").strip()
    order = ([cited] if cited and cited != "_zozi_audit" else [])
    order += ["backend/requirements-compiled.txt", "backend/requirements.txt",
              "requirements.txt", "backend/pyproject.toml", "pyproject.toml",
              "frontend/package.json", "package.json"]
    for candidate in order:
        # An absent manifest makes the probe unresolvable rather than wrong, which
        # is the honest outcome: we cannot refute the claim without knowing where
        # the dependency is declared.
        if base is None or (base / candidate).exists():
            return {"kind": "text_present",
                    "path": candidate, "line": 0, "within": 0, "whole_file": True,
                    "pattern": re.escape(name),
                    "note": "Law 12: forbidden package must be removed"}
    return None


#: Unclustered findings still need probes. 135 of dimension 17's findings carry
#: no cluster at all, so a cluster-keyed table alone leaves the single largest
#: unprobed block untouched. Each entry is (regex over the finding text, builder);
#: they are explicit, not inferred, and the first match wins.
UNCLUSTERED_BUILDERS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"file has \d[\d,]* lines|exceeds? \d[\d,]* lines", re.I),
     "_file_size_probe"),
    (re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`\s+duplicates|duplicates\s+`", re.I),
     "_duplicate_symbol_probe"),
]


def _rel_lazy_probe(f, text: str) -> dict | None:
    """`CLUSTER-tf-rel-lazy` (Law 45) via the inheritance-aware AST probe.

    The old regex was ``relationship\\([^)]*lazy\\s*=\\s*["']select["']``, which
    only matches an EXPLICIT ``lazy="select"``. The overwhelming majority of the
    174 findings are the *omission* case -- ``relationship("user", ...)`` with no
    ``lazy`` at all, which SQLAlchemy defaults to ``"select"`` -- so the regex
    matched nothing and every one of them went unprobed.

    ``_ast_rel_missing_kwarg`` also resolves an inherited default from the
    declarative base, so a ``lazy`` supplied by a base class correctly counts as
    fixed instead of being reported forever.
    """
    m = re.search(r"relationship\s+`([A-Za-z_][A-Za-z0-9_]*)`", f.current or "")
    if not m:
        m = re.search(r"relationship\(\s*[\"'](\w+)[\"']", f.current or "")
    if not m or not f.file:
        return None
    return {
        "kind": "ast_relationship_missing_kwarg",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        # The finding's line is the TABLE (class) line, and the relationship sits
        # anywhere inside the class body. A window of 8 left 104 of 174
        # "no relationship bound to X — the code moved", i.e. UNVERIFIABLE rather
        # than checked. The class body is the search scope.
        "within": 400,
        "target_name": m.group(1),
        "require_absent_kwarg": "lazy",
        "note": "Law 45: relationship must declare lazy=selectin/joined",
    }


#: Law 59 requires a handler to log or raise. The old pattern
#: ``except\b[^\n:]*:\s*(?:pass|\.\.\.)`` only matched a body that is literally
#: `pass` on the following token, so `except (A, B, C):` with an assignment body,
#: or `except Exception:  # noqa: BLE001`, both failed to match and were reported
#: as "pattern matches nowhere in the file" even though they are the clearest
#: violations there are. The claim is an ABSENCE of logging/raising, so probe it
#: as an absence.
_SILENT_EXCEPT_GUARD = (
    r"(?:logger|logging|self\.log|_log|log)\s*\.\s*\w+\s*\("
    r"|\braise\b"
    r"|\bprint\s*\("
)


def _silent_except_probe(f, text: str) -> dict | None:
    if not f.file:
        return None
    return {
        "kind": "except_handler_silent",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        "note": "Law 59: the handler must log, raise, or act",
    }


#: The old pattern was ``\bsettings\.\w+`` but this code reads the environment
#: through ``os.environ`` / ``os.getenv`` / ``environ.get`` — the pattern described
#: a different mechanism from the one the finding is about, so all 41 findings
#: were unprobeable. The claim is "this file reads a raw env var".
_ENV_READ = r"os\s*\.\s*environ|os\s*\.\s*getenv|environ\s*\.\s*get|environ\s*\["


def _env_undeclared_probe(f, text: str) -> dict | None:
    if not f.file:
        return None
    return {
        "kind": "text_matches",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        "within": 6,
        "pattern": _ENV_READ,
        "note": "Law 46: the env var read here has no declaration site",
    }


# --------------------------------------------------------------------------- #
# builders for clusters that had no rule
# --------------------------------------------------------------------------- #
LAWMAP_REL = "zz_core/lawmap.json"


def _law_numbers(claim: str) -> list[int]:
    r"""Law numbers named by a claim, in every form the scanners emit.

    Three shapes occur and the first version only accepted the first, so the
    builder returned None and left 19 `law-gap-checkable` findings unprobed:
      "Law 315 (Operations) is not verifiable ..."   <- per-law findings
      "Law 14: Business logic -> domain"              <- unattributed rollup
      "... decidable from source: 108: SQLite in dev, 116: Email via SMTP"
                                                      <- the gap-checkable list,
                                                         which carries no "Law"
    The last form is the one that broke: matching only `Law\s+(\d+)` returned an
    empty list and every gap-checkable finding fell through to the token
    fallback, which can never resolve anything.
    """
    text = claim or ""
    nums = [int(x) for x in re.findall(r"Law\s+(\d{1,3})", text)]
    nums += [int(x) for x in re.findall(r"\b(\d{1,3}):\s", text)]
    seen: list[int] = []
    for n in nums:
        if n not in seen:
            seen.append(n)
    return seen


def _law_coverage_probe(f, text: str) -> dict | None:
    """Is this benchmark law STILL unenforced?

    These findings are about the audit's own coverage, so the thing that decides
    them is `zz_core/lawmap.json`: if the law is still absent from
    `enforced_by_check`, the finding still holds. Probing the claim text instead
    would be meaningless -- the sentence is generated by the scanner.
    """
    nums = _law_numbers(f.current or "")
    if not nums:
        return None
    return {"kind": "law_unenforced", "path": LAWMAP_REL, "laws": nums,
            "note": "the benchmark law is still not enforced by any check"}


def _law_citation_drift_probe(f, text: str) -> dict | None:
    return {"kind": "law_citation_drift", "path": LAWMAP_REL,
            "note": "a cited law number is absent from the benchmark table"}


def _settings_contract_probe(f, text: str) -> dict | None:
    """`settings.X` read but Settings declares no field X."""
    m = re.search(r"settings\.([A-Za-z_]\w*)", f.current or "")
    if not m or not f.file:
        return None
    return {"kind": "settings_field_absent", "path": f.file.replace("\\", "/"),
            "line": int(f.line or 0), "field": m.group(1),
            "note": "Law 221: Settings declares every attribute the code reads"}


def _dangling_import_probe(f, text: str) -> dict | None:
    """`WF-dangling-import` — is `mod.SYMBOL` really absent from `mod`?

    This finding used to receive the cluster's `celery_task_unregistered` probe,
    which asks whether a recurring task appears in `beat_schedule`. That is a
    different question, so 10 findings claiming a symbol was "not defined
    anywhere in the codebase" were CONFIRMED by an instrument that never looked
    for the symbol -- while `backend/domains/logistics/events.py:20` defines it.
    A probe may not be borrowed from the cluster when the finding's claim is
    specific; this one resolves the module the finding names and asserts the
    absence the finding asserts (`text_absent` holds while the symbol is absent).
    """
    m = re.search(r"imports\s+`([\w.]+)\.(\w+)`", f.current or "")
    if not m:
        return None
    mod, symbol = m.group(1), m.group(2)
    rel = "backend/" + mod.replace(".", "/")
    # Point at whichever file could define it: the module or its package.
    return {"kind": "text_absent", "path": rel + ".py", "pattern": rf"\b{symbol}\b",
            "note": f"{symbol} is not defined in {mod}; if it is, the finding is wrong"}


def _beat_schedule_probe(f, text: str) -> dict | None:
    """A Celery task that is defined but not registered in `beat_schedule`."""
    if not f.file:
        return None
    return {"kind": "celery_task_unregistered", "path": f.file.replace("\\", "/"),
            "note": "every recurring job appears in beat_schedule or is event-driven"}


def _migration_downgrade_probe(f, text: str) -> dict | None:
    """`downgrade()` empty or absent."""
    if not f.file or not f.file.endswith(".py"):
        return None
    return {"kind": "migration_downgrade_empty", "path": f.file.replace("\\", "/"),
            "note": "Law 57: migrations are reversible or explicitly irreversible"}


def _migration_destructive_probe(f, text: str) -> dict | None:
    """A destructive op with no expand-contract staging."""
    if not f.file:
        return None
    return {"kind": "destructive_op_unguarded", "path": f.file.replace("\\", "/"),
            "line": int(f.line or 0),
            "note": "Law 57: destructive migrations use expand-contract"}


def _supply_chain_probe(f, text: str) -> dict | None:
    """CI has no dependency-scanning step."""
    return {"kind": "ci_step_absent", "path": ".github/workflows",
            "step": r"dependabot|pip-audit|npm audit|trivy|safety|codeql|"
                    r"dependency.?review|sbom|cyclonedx",
            "note": "Law 44: supply-chain gates run in CI"}


def _router_empty_probe(f, text: str) -> dict | None:
    """A file under routers/ that declares no endpoint decorators."""
    if not f.file:
        return None
    return {"kind": "router_has_no_endpoints", "path": f.file.replace("\\", "/"),
            "note": "Law 8: routers declare HTTP endpoints"}


# Finding-id-specific builders. Checked BEFORE the cluster key, because a
# cluster-level instrument answers the cluster's question, and a finding that
# states a narrower claim needs an instrument that reads the claim.
FINDING_BUILDER: dict[str, str] = {
    "WF-dangling-import": "_dangling_import_probe",
    # Dimension 21 contradictions. These were emitted with an empty probe, so
    # no instrument could settle them and they were permanently UNVERIFIABLE --
    # including 4 hard completion blockers. Each claim below is re-derivable
    # from the tree; see the `m_*` measurements.
    "CONTRAD-001": "_extra_unit_probe",
    "CONTRAD-002": "_extra_unit_probe",
    "CONTRAD-003": "_extra_unit_probe",
    "CONTRAD-029": "_orphan_frontend_route_probe",
    "CONTRAD-034": "_router_shadow_probe",
}

STRUCTURAL.update({
    # Law 12/13: the canonical module/domain sets are fixed, so the existence
    # of this directory is the whole claim -- a `path_present` probe settles it
    # exactly, where the aggregate `law12_extra_domains` count would confirm
    # every finding in the cluster if any *other* extra directory survived.
    "CLUSTER-extra-module": "_extra_unit_probe",
    "CLUSTER-extra-domain": "_extra_unit_probe",
})

for _cid in ("001", "002", "003", "004", "005", "006", "007"):
    STRUCTURAL[f"CLUSTER-chain-chain-{_cid}"] = "_chain_event_probe"


def _extra_unit_probe(f, text: str) -> dict | None:
    """Law 12/13: does this non-canonical module/domain directory still exist?

    Deliberately per-path rather than the aggregate `law*_extra_*` measurement:
    the aggregate holds while ANY extra directory remains, so deleting the one
    this finding names would leave it CONFIRMED. The defect here is one
    directory, so the probe asks about one directory.
    """
    rel = (f.file or "").replace("\\", "/").rstrip("/")
    if not rel:
        return None
    law = 13 if "/modules/" in rel else 12
    return {"kind": "path_present", "path": rel,
            "note": f"Law {law}: the directory is still present outside the "
                    f"canonical set"}


def _orphan_frontend_route_probe(f, text: str) -> dict | None:
    """Law 13: a frontend rewrite targets a backend module that does not exist.

    Needs BOTH halves -- rewrite present, module absent -- so neither half can
    be probed alone without asserting something the finding never claimed.
    """
    cur = f.current or ""
    m = (re.search(r"/([A-Za-z0-9_-]+)/\*", cur)          # "/hr/* rewrite exists"
         or re.search(r"`/([A-Za-z0-9_-]+)/", cur)        # "`/hr/*`"
         or re.search(r"rewrites?\s+/([A-Za-z0-9_-]+)/", cur))
    if not m:
        return None
    return {"kind": "measure", "measure": "orphan_frontend_module_route",
            "arg": m.group(1),
            "note": "Law 13: the rewrite target has no backend module directory"}


def _router_shadow_probe(f, text: str) -> dict | None:
    """Law 18: a router file is shadowed by a same-named package beside it."""
    rel = (f.file or "").replace("\\", "/")
    if not rel:
        return None
    return {"kind": "measure", "measure": "router_shadowed_by_package",
            "arg": rel,
            "note": "the sibling package shadows the router file, so it never "
                    "imports"}


def _chain_event_probe(f, text: str) -> dict | None:
    """Chain completeness: the chain's event is declared in no events.py.

    The finding's `notes` carries `events=<name>,<name>`; the scanner recorded
    which of them it looked for, and re-deriving that from the tree is the
    independent instrument.
    """
    m = re.search(r"events=([A-Za-z0-9_.,-]+)", f.notes or "")
    if not m:
        return None
    names = [n for n in m.group(1).split(",") if n]
    if len(names) != 1:
        return None  # a multi-event chain needs a per-event claim to probe
    return {"kind": "measure", "measure": "chain_event_unwired",
            "arg": names[0],
            "note": "the chain's event is declared in no "
                    "backend/domains/*/events.py, so nothing can subscribe"}


def _builder_for(f) -> str | None:
    """Finding key, then cluster key, then the unclustered fallback table."""
    exact = FINDING_BUILDER.get(f.id or "")
    if exact:
        return exact
    named = STRUCTURAL.get(f.cluster or "")
    if named:
        return named
    # A cluster with a registered measurement gets the measurement builder even
    # if a more specific builder is added later: the measurement re-derives the
    # count the finding is actually about.
    if (f.cluster or "") in CLUSTER_MEASUREMENT or (f.id or "") in FINDING_MEASUREMENT:
        return "_measurement_probe"
    blob = f"{f.current or ''} {f.delta or ''}"
    for rx, builder in UNCLUSTERED_BUILDERS:
        if rx.search(blob):
            return builder
    return None


def _file_size_probe(f, text: str) -> dict | None:
    """`CLUSTER-file-too-long` — does the file still exceed the split threshold?

    The threshold comes from `target`/`fix`, **never** from `current`. `current`
    states the *observed* line count ("file has 4520 lines"); using that as the
    limit asks "is the file longer than itself", which is false for every file and
    would report the entire cluster as fixed on the first run.
    """
    if not f.file:
        return None
    limit = None
    for blob in (f.target or "", f.fix or "", f.current or ""):
        m = re.search(r"(?:under|below|at most|no more than|max(?:imum)?|limit)"
                      r"[^\d]{0,12}(\d[\d,]*)", blob, re.I)
        if m:
            limit = int(m.group(1).replace(",", ""))
            break
    if limit is None:
        m = re.search(r"(\d[\d,]*)\s*lines?\s*(?:threshold|limit)", f.fix or "", re.I)
        limit = int(m.group(1).replace(",", "")) if m else None
    if limit is None:
        # No stated threshold: fall back to the project's own guidance rather than
        # inventing one, and say so in the note.
        limit = 500
    return {"kind": "file_line_count_above", "path": f.file.replace("\\", "/"),
            "limit": limit,
            "note": f"file exceeds the {limit}-line split threshold"}


def _duplicate_symbol_probe(f, text: str) -> dict | None:
    """Law 67: does this file STILL share function bodies with the named file?

    `symbol_occurrences` counted one name and compared it to the number of
    duplicated functions: with 17 duplicates it read 1 and reported "fixed", so
    all 9 true findings were refuted. The claim is about shared *bodies*, so the
    probe compares normalised AST bodies between the two files.
    """
    m = re.search(r"duplicate `([\w./-]+\.py)`", f.current or "")
    other = m.group(1) if m else ""
    if not other or not f.file:
        return None
    names = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`",
                       (f.current or "").split(":", 1)[-1])
    return {"kind": "duplicated_bodies_present",
            "paths": [f.file.replace("\\", "/"), other],
            "names": names[:20],
            "note": f"Law 67: {names[:3]} still duplicated in {other}"}

#: cluster -> ProbeRule
#:
#: ``pattern``  regex that expresses the defect itself.
#: ``within``   lines of context around the cited line to search. ``0`` with
#:              ``whole_file`` searches the entire file, which is what a claim
#:              such as "this file declares timestamps in Python" actually means.
#: ``whole_file`` set means the claim is about the file, not a line.
#: ``negated``  use ``text_absent`` instead of ``text_matches`` — for a defect
#:              whose *absence* of a marker is the claim (an ungated route is
#:              ungated precisely because ``require_feature`` is not there).
PROBE_RULES: dict[str, "ProbeRule"] = {}


@dataclass(frozen=True)
class ProbeRule:
    kind: str = "text_matches"
    pattern: str = ""
    within: int = 2
    whole_file: bool = False
    note: str = ""
    fallback_whole_file: bool = True


def _rule(pattern: str, *, within: int = 2, whole_file: bool = False,
          kind: str = "text_matches", note: str = "",
          fallback_whole_file: bool = True) -> ProbeRule:
    return ProbeRule(kind=kind, pattern=pattern, within=within,
                     whole_file=whole_file, note=note,
                     fallback_whole_file=fallback_whole_file)


# Explicit rules. Each pattern is the minimal expression of the cited defect.
PROBE_RULES.update({
    # Law 19 — money is Decimal/Numeric. The defect is a `float` annotation on
    # the money declaration, so the pattern is the annotation itself.
    "CLUSTER-float-money": _rule(
        r"\bfloat\b", within=3,
        note="a float annotation in the cited money declaration"),

    # Law 59 — no silent except. The defect is a handler whose body is `pass`
    # or `...`, which is what makes it silent. No trailing `\b`: `...` ends in a
    # non-word character, so `\b` after it can never match.
    # `CLUSTER-silent-except` is served by `_silent_except_probe` in STRUCTURAL.
    # The former regex rule `except\b[^\n:]*:\s*(?:pass|\.\.\.)` described a
    # narrower claim than the finding and matched nowhere for 48 of 101 findings.

    # Law 3 — cross-domain writes go through events.py. The defect is an import
    # of another domain's package from inside a domain.
    "CLUSTER-cross-domain-direct": _rule(
        r"^\s*(?:from|import)\s+domains\.", whole_file=True,
        note="a direct import of another domain package"),

    # Law 21 — timestamps use server_default, not a Python-side default.
    "CLUSTER-tf-timestamp-default": _rule(
        r"(?:default|onupdate)\s*=\s*(?:datetime\.now|datetime\.utcnow|func\.now|"
        r"lambda\s*:\s*datetime)", whole_file=True,
        note="a Python-side timestamp default instead of server_default"),

    # Law 1 — modules import rbac/domains, never infrastructure directly.
    "CLUSTER-module-imports-infrastructure": _rule(
        r"^\s*(?:from|import)\s+infrastructure", whole_file=True,
        note="a module importing infrastructure directly"),

    "CLUSTER-infra-imports-above": _rule(
        r"^\s*(?:from|import)\s+(?:kernel|domains|modules)", whole_file=True,
        note="an infrastructure module importing upward"),

    # Law 88 — every protected endpoint is feature-gated. The claim is the
    # *absence* of a gate, so the probe is `text_absent`.
    "CLUSTER-ungated-route": _rule(
        r"require_feature", within=6, kind="text_absent",
        note="no require_feature gate on the cited endpoint"),

    # Law 46 / §11 — every env var read through typed settings.
    # `CLUSTER-env-undeclared` is served by `_env_undeclared_probe` in STRUCTURAL.
    # The former regex rule `\bsettings\.\w+` named a mechanism this code does not
    # use: the findings are about `os.environ` / `os.getenv` reads.
    "CLUSTER-env-raw": _rule(
        r"os\.environ|os\.getenv", within=3,
        note="a raw environment read bypassing typed settings"),

    # `CLUSTER-tf-rel-lazy` is served by `_rel_lazy_probe` in STRUCTURAL. The former
    # regex rule only matched an explicit `lazy="select"`, missing the omission
    # case that is the overwhelming majority of the cluster.
    # Law 23 — money columns are Numeric.
    "CLUSTER-float-money-column": _rule(
        r"\bFloat\b|\bfloat\b", within=3,
        note="a Float-typed monetary column"),

    # Test hygiene — a test with no assertion asserts nothing.
    "CLUSTER-test-no-assert": _rule(
        r"\bassert\b|\.assert[A-Z_]|\bexpect\(", kind="text_absent",
        within=0, whole_file=True,
        note="no assertion anywhere in the test file"),

    # -- structural claims that a text probe can still decide ----------------- #
    # Law 239 — the defect is that the key is OPTIONAL, not that it is absent.
    # `idempotency_key: Optional[str] = None` is the finding, so the probe must
    # assert the optional declaration. The first version of this rule was
    # `text_absent` over any idempotency token, which inverted the claim: the
    # token being present made the probe report "already fixed" and the verifier
    # then discarded 10 genuine P0 findings as false positives. A probe that
    # contradicts its own detector is worse than no probe.
    "CLUSTER-idempotency": _rule(
        r"idempotency_key\s*:\s*Optional|idempotency_key\s*:\s*\w+\s*\|\s*None"
        r"|idempotency_key\s*=\s*None",
        within=3,
        note="an optional idempotency key on a money path (Law 239)"),

    # `CLUSTER-settings-contract` was withdrawn. The pattern
    # `:\s*\w+\s*[:=]` matches almost any Python, so the probe reported
    # ALREADY_FIXED on 11 live defects. There is no sound text expression for
    # "this settings attribute has no declared field" — it needs a
    # `settings_declared_absent` AST probe, which is not implemented. Leaving the
    # rule out is correct; inventing a pattern is not.

    # A CSP header either exists in the middleware or it does not (Law 36).
    "CLUSTER-http-csp": _rule(
        r"Content-Security-Policy|content-security-policy", within=0,
        whole_file=True,
        note="no Content-Security-Policy header in this middleware module"),

    # The deprecated-header cluster, matched on the header it actually claims.
    #
    # This rule previously searched for `X-Content-Type-Options` while the
    # findings under `CLUSTER-http-headers` claim `X-XSS-Protection` is present.
    # The probe therefore "confirmed" the finding by finding an unrelated header
    # that is legitimately there — a green verdict for a claim it never tested.
    "CLUSTER-http-headers": _rule(
        r"x-xss-protection", within=0, kind="text_present", whole_file=True,
        note="the deprecated X-XSS-Protection header is still emitted"),

    # Missing-header claims are the mirror image and need their own rule: the
    # detector asserts a REQUIRED header is absent.
    "CLUSTER-http-header-missing": _rule(
        r"Strict-Transport-Security|strict-transport-security", within=0,
        kind="text_absent", whole_file=True,
        note="no Strict-Transport-Security header in this middleware module"),

    # Every FK needs an explicit ondelete; absence at the column is decidable.
    "CLUSTER-tf-fk-ondelete": _rule(
        r"ondelete\s*=", within=3, kind="text_absent",
        note="a ForeignKey with no explicit ondelete"),

    # A version pin is text; drift flips it.
    "CLUSTER-version-drift": _rule(
        r"[0-9]+\.[0-9]+", within=3,
        note="a version literal at the cited declaration"),

    # Law 12 — a domain may only shrink the allowlist. Each allowlist entry names
    # a domain, so its presence is the decidable claim.
    "CLUSTER-allowlist": _rule(
        r"^\s*-\s*\w+", within=0, whole_file=True,
        note="an entry present in DOMAIN_ALLOWLIST.yaml"),

    # Router thinness (Law 15) is not text-decidable, and job resilience needs
    # cross-callsite inspection. Both are listed explicitly so the coverage report
    # names them rather than letting them fall through as "unclustered".
    "CLUSTER-router-business-logic": _rule(
        "", fallback_whole_file=False, note="needs a call-graph probe"),
    "CLUSTER-job-resilience": _rule(
        "", fallback_whole_file=False, note="needs cross-callsite retry inspection"),
})


#: Clusters whose claims are structural rather than textual. Each entry receives the
#: finding and returns a probe dict, or ``None`` when it cannot build a sound one.
#: Returning ``None`` leaves the finding honestly unprobed — the alternative, a
#: guessed probe, is what manufactures confident wrong verdicts.
STRUCTURAL_BUILDERS = ("_function_len_probe", "_module_layer_probe",
                       "_router_thinness_probe")


def _function_len_probe(f, text: str) -> dict | None:
    """`CLUSTER-long-function` — does the named function still exceed the limit?

    The detector writes ``N function(s) >LIMIT lines; longest sample `name` = M
    lines``, so the name and the limit are both recoverable. Targeting that exact
    shape matters: a generic backtick grab would happily return an unrelated
    identifier, and a length probe pointed at the wrong function is a confidently
    wrong verdict rather than a visible failure.
    """
    src = f"{f.current or ''} {f.delta or ''}"
    m = re.search(r"longest sample\s+`([A-Za-z_][A-Za-z0-9_]*)`", src)
    if not m:
        m = re.search(r"function\s+`([A-Za-z_][A-Za-z0-9_]*)`", src)
    if not m:
        return None
    limit_m = re.search(r">\s*(\d{2,})\s*lines", src) or \
        re.search(r"exceeds?\s+(\d{2,})", src)
    if not limit_m:
        return None
    limit = int(limit_m.group(1))
    return {"kind": "function_len_above", "path": f.file.replace("\\", "/"),
            "function": m.group(1), "limit": limit, "line": int(f.line or 0),
            "note": f"function `{m.group(1)}` longer than {limit} lines"}


def _module_layer_probe(f, text: str) -> dict | None:
    """`CLUSTER-infra-imports-above` / module-layer findings — Law 1 direction.

    The layer is derived from the path by the probe itself, and the forbidden set
    comes from the architecture document, so neither is taken on trust from the
    detector that emitted the finding.
    """
    layer = _layer_of(f.file.replace("\\", "/"))
    if layer not in _ALLOWED_IMPORTS:
        return None
    above = sorted(_ALL_LAYERS - _ALLOWED_IMPORTS[layer])
    if not above:
        return None
    return {"kind": "module_imports_above", "path": f.file.replace("\\", "/"),
            "layer": layer, "modules": above,
            "note": f"a `{layer}` module importing a layer above it"}


def _router_thinness_probe(f, text: str) -> dict | None:
    """`CLUSTER-router-business-logic` — a router holding business branching.

    The claim is a *branch count* ("router contains 12 branch statements"), not a
    named function. It used to require a backticked handler name and returned
    None for all 10 findings, because the finding names no handler. So the probe
    now counts branch statements in the file and compares against the limit the
    claim itself states.
    """
    if not f.file:
        return None
    limit = _extract_int(f.current or "")
    probe = {
        # NOT `count_below`. The violation is having TOO MANY branches, so the
        # probe must hold while the count is at or above the reported number.
        # `count_below` asserts the opposite and refuted the six routers that
        # still violate the law.
        "kind": "count_at_or_above",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        "note": "Law 90: routers hold auth/gate/parse and one service call",
    }
    probe["at_least"] = limit if limit else 1
    probe["actual"] = _branch_count(text or "", probe["path"])
    return probe


def _branch_count(text: str, rel: str) -> int | None:
    r"""Branch statements, counted with the DETECTOR's own regex.

    The first version walked the AST for `If|For|AsyncFor|While|Match|Try|IfExp`
    and got 11 where the detector's `^\s+(if|for|while|try)\b` reported 12. The
    probe then concluded a live violation had been fixed. An off-by-one in a
    probe is a false "remediated", which is the most damaging kind of probe bug:
    it retires work that still needs doing. A probe must measure the same thing
    the claim was measured from, so this reuses the detector's expression rather
    than a "better" one.
    """
    if not text:
        return None
    return len(re.findall(r"^\s+(if|for|while|try)\b", text, re.MULTILINE))


def _timestamp_default_probe(f, text: str) -> dict | None:
    """Law 21: `created_at`/`updated_at` must use `server_default=func.now()`.

    The regex rule for this cluster matched only a literal `datetime.now`, so on
    code that writes `default=_utcnow` -- an alias of
    `infrastructure.utils.datetime_utils.utcnow` -- it matched nowhere and the
    finding received no probe. This reads the aliases out of the file and
    therefore asks the question the finding actually asks: is this timestamp
    stamped by Python or by the database?
    """
    if not f.file:
        return None
    aliases = _utcnow_aliases(text or "")
    return {
        "kind": "timestamp_default_is_python",
        "path": f.file.replace("\\", "/"),
        "line": int(f.line or 0),
        "aliases": sorted(aliases),
        "note": "Law 21: use server_default=func.now(), not a Python-side default",
    }


def _utcnow_aliases(text: str) -> set[str]:
    """Names in this module bound to a Python-side clock."""
    out: set[str] = set()
    for m in re.finditer(r"^from\s+[\w.]*\s*import\s+utcnow\s+as\s+(\w+)",
                         text, re.M):
        out.add(m.group(1))
    for m in re.finditer(r"^from\s+[\w.]*\s*import\s+(utcnow|datetime|now)\b",
                         text, re.M):
        out.add(m.group(1))
    for m in re.finditer(r"^\s*(utcnow|now)\s*=\s*(?:datetime\.)?(?:utc)?now",
                         text, re.M):
        out.add(m.group(1))
    return out


def _extract_int(text: str) -> int | None:
    m = re.search(r"(\d{2,})", text or "")
    return int(m.group(1)) if m else None


@dataclass
class AttachReport:
    total: int = 0
    already: int = 0
    attached: int = 0
    no_rule: int = 0
    unreadable: int = 0
    zero_match: int = 0
    by_cluster: dict[str, int] = field(default_factory=dict)
    #: builder exceptions, one per finding, never fatal
    builder_errors: list[str] = field(default_factory=list)
    unattached_examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "already_probed": self.already,
            "attached": self.attached,
            "no_rule": self.no_rule,
            "unreadable_file": self.unreadable,
            "pattern_matched_nowhere": self.zero_match,
            "by_cluster": dict(sorted(self.by_cluster.items(),
                                      key=lambda kv: -kv[1])),
            "unattached_examples": self.unattached_examples[:20],
            # Omitting this made `facts.json` report `builder_errors: 0` on a run
            # whose console had just printed 7 -- the one place a builder
            # failure is recorded was the one place it was not read.
            "builder_errors": self.builder_errors[:20],
            "builder_error_count": len(self.builder_errors),
        }


def attach(findings, root: Path, report: AttachReport | None = None) -> AttachReport:
    """Attach probes in place. Returns the coverage report."""
    rep = report or AttachReport()
    root = Path(root)
    # Builders only receive `(finding, text)`, so anything that must consult the
    # repository layout reads it from here. Without this, `_forbidden_package_probe`
    # raised `NameError: name 'ROOT' is not defined` on the first forbidden-package
    # finding, which aborted the whole pass -- `attach()` has no per-finding guard --
    # and left 770 findings with no probe while the run still reported success.
    global _REPO_ROOT
    _REPO_ROOT = root
    for f in findings:
        rep.total += 1
        if f.probe:
            rep.already += 1
            continue
        # Dispatch, in one place and in this order:
        #   1. a purpose-built structural builder -- it encodes the cluster's
        #      actual claim, whereas a legacy regex may not;
        #   2. a regex rule;
        #   3. nothing, reported honestly as `no_rule`.
        # The previous order let a stale pattern outrank a working builder, and a
        # nested variant of it ran the builder branch only when NO builder existed
        # -- which nulled `probe_coverage` entirely.
        rule = PROBE_RULES.get(f.cluster or "")
        builder = _builder_for(f)

        if builder:
            rel0 = f.file.replace("\\", "/") if f.file else ""
            if not rel0 and builder not in _FILELESS_BUILDERS:
                rep.no_rule += 1
                continue
            # Some builders reason about package structure, not source text, and
            # cite a package (`domains.accounts`) rather than a file. Requiring a
            # readable file skipped all 20 circular-import findings before the
            # builder could run.
            text0 = (_read(root, rel0) or "") if rel0 else ""
            try:
                made = globals()[builder](f, text0)
            except Exception as exc:
                # Isolate it. Unguarded, one builder raised out of the whole loop:
                # `zozi_audit.py` caught it once and the run reported success with
                # every remaining finding unprobed.
                made = None
                rep.builder_errors.append(
                    f"{builder} on {rel0}:{f.line} [{f.cluster or 'unclustered'}]"
                    f" -> {type(exc).__name__}: {exc}")
            if made and made.get("kind") in _TEXTUAL_PROBE_KINDS \
                    and not text0 and builder not in _FILELESS_BUILDERS:
                # A textual probe's verdict depends on the file's content, so a
                # file we cannot read means the probe cannot be answered. This is
                # decided on the probe's KIND, not the builder's name: gating on
                # the builder dropped `path_present` probes whose path is absent
                # -- the very condition they assert.
                rep.unreadable += 1
                continue
            if made:
                f.probe = made
                rep.attached += 1
                rep.by_cluster[f.cluster] = rep.by_cluster.get(f.cluster, 0) + 1
            else:
                rep.no_rule += 1
                if len(rep.unattached_examples) < 40:
                    rep.unattached_examples.append(
                        f"{f.id or '?'} [{f.cluster}] {rel0}:{f.line} — "
                        "structural builder refused (claim not recoverable)")
            continue

        if rule is None or not rule.pattern:
            rep.no_rule += 1
            if len(rep.unattached_examples) < 40:
                rep.unattached_examples.append(
                    f"{f.id or '?'} [{f.cluster or 'unclustered'}] "
                    f"{f.file or '(no file)'} — no rule")
            continue

        if not f.file:
            rep.no_rule += 1
            continue
        rel = f.file.replace("\\", "/")
        text = _read(root, rel)
        if text is None:
            rep.unreadable += 1
            continue

        window = _window(text, int(f.line or 0), rule)
        found = _count(rule.pattern, window)
        scope = "line"
        # The whole-file fallback escalates a *narrow* claim to a *broad* one. It
        # is only sound when the claim is "this pattern occurs N times here" and
        # the narrow window simply missed it.
        #
        # For `text_absent` it is actively destructive: the claim IS the absence,
        # so "not found in the window" is the expected result, not a reason to look
        # wider. Escalating found the token elsewhere in the file and turned 46
        # genuine `ungated-route` findings into "already fixed" — because a
        # require_admin-gated endpoint has no `require_feature` near its signature,
        # so the fallback searched the whole file, found 33 unrelated occurrences,
        # and reported the guard present. The verifier believed it.
        if (not found and rule.fallback_whole_file and not rule.whole_file
                and rule.kind != "text_absent"):
            whole = _count(rule.pattern, text)
            if whole:
                found, scope = whole, "file"
        if not found:
            if rule.kind == "text_absent":
                # Expected: the claimed absence holds inside the window. A
                # zero-match `text_absent` is a satisfied probe, so it still gets
                # one — with no `count`, because `ProbeRunner` evaluates presence
                # and a count would invert the meaning.
                probe = {"kind": rule.kind, "path": rel, "pattern": rule.pattern,
                         "scope": scope, "note": rule.note}
                if scope != "file":
                    probe["line"] = int(f.line or 0)
                    probe["within"] = rule.within
                f.probe = probe
                rep.attached += 1
                rep.by_cluster[f.cluster] = rep.by_cluster.get(f.cluster, 0) + 1
                continue
            rep.zero_match += 1
            if len(rep.unattached_examples) < 40:
                rep.unattached_examples.append(
                    f"{f.id or '?'} [{f.cluster or 'unclustered'}] {f.file or '(no file)'}"
                    f":{f.line} — pattern matches nowhere in the file")
            continue

        probe = {
            "kind": rule.kind,
            "path": rel,
            "pattern": rule.pattern,
            "scope": scope,
        }
        if scope == "file" or rule.whole_file:
            probe["count"] = found
        else:
            probe["line"] = int(f.line or 0)
            probe["within"] = rule.within
            probe["count"] = found
        probe["note"] = rule.note
        f.probe = probe
        rep.attached += 1
        rep.by_cluster[f.cluster] = rep.by_cluster.get(f.cluster, 0) + 1
    return rep


def _read(root: Path, rel: str) -> str | None:
    try:
        return (root / rel).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return None


def _count(pattern: str, text: str) -> int:
    """Count with the same flags `ProbeRunner._text_matches` uses.

    These two must agree exactly. If they disagree, every attached probe compares
    the re-run against a number that was never produced the same way, and the
    verdict is wrong for a reason no amount of reading the report would reveal.
    """
    if not pattern:
        return 0
    return len(re.findall(pattern, text, re.MULTILINE))


def _window(text: str, line: int, rule: ProbeRule) -> str:
    """Mirror `ProbeRunner._window` exactly, so the measured count is the count
    the probe will later see. Any divergence between these two would make every
    attached probe compare against the wrong number."""
    if rule.whole_file or not line:
        return text
    lines = text.splitlines()
    lo = max(0, line - 1 - rule.within)
    hi = min(len(lines), line + rule.within)
    return "\n".join(lines[lo:hi])


def coverage_pct(report: AttachReport) -> str:
    total = report.already + report.attached
    if not report.total:
        return "n/a"
    return f"{total}/{report.total} ({100.0 * total / report.total:.1f}%)"