# PRECONDITION FAILURE — Resolver run 8

- Date: 2026-10-02
- Source commit: `6666d435`
- Spec: `_most_imp_docx/PROMPT_RESOLUTION_ORCHESTRATOR.md` v4
- Rule invoked: **§0.2.3 — "Stop on unmet preconditions. Never improvise."**
- Status: `RESOLUTION HALTED` at Step 1 (tracker build)

---

## 1 · What passed

| Precondition (§2) | Result |
|---|---|
| Benchmark `ARCHITECTURE_STACK.md` (916 lines, 325 laws) | PASS |
| Benchmark `TECHNOLOGY_STACK.md` (577 lines) | PASS |
| Worklist `_audit/TO_BE_RESOLVE.md` exists | PASS |
| Audit rollups + 35 dimension files | PASS |
| `_audit/10_CHAINS.md` | PASS |
| `_browser_test/` | PASS |
| Boot smoke `from backend.main import app` | **PASS — 84 routes** |
| Valkey unreachable → graceful degradation (Law 110) | PASS |

## 2 · What failed — worklist schema regression

`_audit/TO_BE_RESOLVE.md` **no longer carries the file-block schema** that the
resolver dispatches on.

| Field the resolver requires | §0.0 declares invariant | Present in worklist |
|---|---|---|
| `## FILE <n>: <path>` header | yes | **NO** |
| `Phase` | yes | **NO** |
| `Depends on` | yes | **NO** |
| `Blast radius` | yes | **NO** |
| 11 subsections (Architectural … Feature Relation) | yes | **NO** |
| `Resolution status` column | yes | **NO** |
| Finding IDs | yes | YES (447) |

### 2.1 · Evidence

- Working tree: **155** `## <path>` groups, **458** findings, **447** unique finding IDs,
  each group carrying a rollup line `**Status:** n VALID, n INVALID, n RESOLVED, …`.
- `git show HEAD:_audit/TO_BE_RESOLVE.md` (schema A): **174** `## FILE <order>: <path>`
  headers + 174 `Resolution status` lines, but only **16** unique finding IDs —
  a truncated-reconstruction skeleton with no finding bodies.
- Prior resolver annotations (86 `RESOLVED` blocks) are therefore **not recoverable**
  from the current worklist.

### 2.2 · Consequence

§6 defines the dispatch unit as *"the file block in `_audit/TO_BE_RESOLVE.md`"* and
§0.4 rule 19 repeats it. With no file blocks there is nothing to freeze a contract
against (§7), nothing to compute `behaviors_frozen` from (§31), and no honest
`allowed_functions` list (§1). Dispatching now would require me to **invent** the
phase order, the dependency graph, and the 11-subsection breakdown — that is
**compiler work**, which §"What this resolver does" explicitly assigns to
`PROMPT_AUDIT_COMPILER.md`, not to the resolver.

## 3 · Scale of the real remaining work

From the current worklist: **127 path groups carry ≥1 open `VALID` finding**
(380 open findings total). Open findings by dimension prefix:

| Prefix | Count | Prefix | Count |
|---|---|---|---|
| TF (tables/fields) | 240 refs | DRIFT (ai) | 9 |
| FEAT (features) | 42 | ARCHTEST | 9 |
| TECH | 31 | CONTRAD | 8 |
| CFG (config/env) | 19 | OBS | 7 |
| ARCH | 14 | BLOCKER | 7 |
| OPS | 9 | D2P (dev→prod) | 7 |
| MOB | 9 | BROWSER | 6 |
| PERF | 9 | SUP / LOGIC / COLLECT / DB / CFM / WIR | 14 |

## 4 · Escalation

Per §0.7 / §21 this is a **process-level halt requiring a user decision**, because the
unblocking action is to change the compiler's output contract — which the resolver is
forbidden to do (§0.2.1 read-only on the audit; §20 "❌ Document instead of resolve").

Three routes, in my order of preference:

1. **Re-run the compiler with the file-block contract enforced** (`PROMPT_AUDIT_COMPILER.md`
   emits `## FILE <n>`, `Phase`, `Depends on`, 11 subsections, `Resolution status`).
   Cleanest: preserves the invariant, keeps role separation, keeps every `RESOLVED`
   mark honest.
2. **Authorize the resolver to normalize schema B → schema A** as an explicitly logged
   exception, deriving `Phase` from finding-dimension prefix + `11_PRODUCTION_READINESS.md`
   priority, `Depends on` from observed import edges, and the 11 subsections from the
   dimension files the findings came from.
3. **Dispatch directly on the 127 open path groups** without file-block normalization.
   Fastest, but `Phase`/`Depends on`/§7 contract sections `behaviors_frozen` and
   `allowed_functions` would be derived at investigation time rather than frozen up front,
   weakening drift detection (`D-SCOPE`, `D-CASCADE`).
