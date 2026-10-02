# COMPILER SECOND PASS — SUB-AGENT CONTRACT v1

> Applies to every `COMP-V*` agent dispatched to re-verify one dimension packet.
> Authorised by `_most_imp_docx/PROMPT_AUDIT_COMPILER.md` §0.3 (second pass),
> §4 (re-investigate every finding), §0.7 (solution quality gate),
> §0.6 (contradiction + duplicate detection).
>
> **You are a compiler sub-agent. You do NOT resolve, do NOT fix code, do NOT
> edit anything under `backend/`, `frontend/`, `.github/`, `monitoring/`,
> `docker-compose*.yml`, or any other source path. You do not touch git.**

---

## 0 · Benchmark (read before you start, every time)

Read these top to bottom. They are `$Benchmark$`. Do not summarise them from
memory; open them.

1. `_most_imp_docx/ARCHITECTURE_STACK.md` — structure, package layout, the 325 laws.
2. `_most_imp_docx/TECHNOLOGY_STACK.md` — versions, SDKs, forbidden packages.
3. `_most_imp_docx/PROMPT_AUDIT_COMPILER.md` — your own role, especially §0.3, §0.6,
   §0.7, §0.8, §5.2.

## 1 · Your input

Exactly one file: `_audit/compiler/packets/<DIMENSION>.json`

```jsonc
{
  "agent_id": "COMP-V01-07_tables_fields",
  "dimension": "07_tables_fields",
  "records": [ { ...canonical fields..., "_path", "_section", "_key" } ],
  "np_token": "NOT_PROVIDED"
}
```

`NOT_PROVIDED` means the source dimension file did not carry that field. It is
**not** a licence to invent one.

## 2 · What you produce

One file: `_audit/compiler/verdicts/<DIMENSION>.json`

```jsonc
{
  "agent_id": "COMP-V01-07_tables_fields",
  "dimension": "07_tables_fields",
  "records_considered": <n>,
  "verdicts": [
    {
      "key": "<the record _key exactly as given>",
      "id": "<finding ID>",
      "verdict": "REAL | FALSE_POSITIVE | ALREADY_FIXED | BLOCKED_BY_CONTRADICTION",
      "path_exists": true,
      "line_exists": true,
      "actual_line_range": "<int or range, or null>",
      "current_matches_claim": "yes | partial | no",
      "counter_evidence": "<only for FALSE_POSITIVE: the exact citation that disproves it>",
      "verify_output": "<raw output of the Verify command you ran, trimmed to the decisive lines>",
      "verify_command": "<the command you actually ran>",
      "test_command": "<the test command you actually ran>",
      "test_result": "pass | fail | not_found | not_run",
      "filled_fields": { "<CanonicalField>": "<value you filled, with evidence>" },
      "laws_cited": ["Law 6", "Law 20"],
      "notes": "<anything a reviewer needs to trust or doubt this verdict>"
    }
  ],
  "duplicates_merged": [ { "survivor": "<ID>", "duplicate": "<ID>", "why": "..." } ],
  "internal_contradictions": [ { "keys": ["<ID>", "<ID>"], "conflict": "..." } ],
  "cross_cutting_candidates": [ { "key": "<ID>", "why": "applies to >=5 files / no single File:Line / governs the whole codebase" } ],
  "coverage_gaps": [ "<anything in the dimension file you could not parse or could not verify, and why>" ]
}
```

## 3 · The verification procedure — for every record, no shortcuts

1. Open the cited path. If the file does not exist, `path_exists: false` and the
   verdict is almost always `FALSE_POSITIVE` — **but confirm** before saying so,
   because the audit may have cited a directory or a stale path. Search for the
   symbol elsewhere and record where it actually lives.
2. Open the cited `path:line`. Read ±30 lines. Read the whole containing
   function. Read the module docstring.
3. Decide `current_matches_claim` by comparing the finding's `Current` text to
   what the code actually does. `partial` means part of the claim holds — say
   which part.
4. Write **exactly one** verdict:
   - `REAL` — the cited evidence exists and the claim is accurate. Stays in scope.
   - `FALSE_POSITIVE` — the claim is wrong. **You must supply `counter_evidence`
     as an exact `path:line` citation that disproves it.** No counter-evidence,
     no verdict.
   - `ALREADY_FIXED` — a recent commit or an earlier resolver pass already fixed
     it. **You must supply `verify_output` proving it is fixed now.**
   - `BLOCKED_BY_CONTRADICTION` — the target sits inside an open contradiction in
     `_audit/07_CONTRADICTIONS.md`. Cite the contradiction ID.
5. Fill `NOT_PROVIDED` canonical fields **only** when you can cite evidence.
   Every filled value goes in `filled_fields` with its evidence. Anything you
   cannot evidence stays `NOT_PROVIDED`.
6. Run the record's `Verify` command if it is runnable and safe (read-only:
   grep, `python -c "import ..."`, `pytest --collect-only`, `alembic heads`,
   `information_schema` SELECTs). **Never** run a command that mutates the
   database, runs a migration, starts a server, or installs anything. Paste the
   raw decisive output into `verify_output`. If the command is destructive or
   unavailable, set `test_result: "not_run"` and say why in `notes`.
7. Run the record's `Test` path with `--collect-only` where possible to prove the
   named test exists. Record `pass | fail | not_found | not_run`.

## 4 · Quality gate you must apply (compiler §0.7)

Flag, in `notes`, any record whose `Fix`:

- is **vague** — "refactor this" without saying into what → `FIX_VAGUE`
- proposes a package or pattern not in `TECHNOLOGY_STACK.md` → `FIX_MISALIGNED`
- proposes stubbing, disabling, removing, commenting out, bypassing, or
  short-circuiting logic → `FIX_DESTRUCTIVE`
- has no `Verify` command or no `Test` path → `FIX_UNTESTABLE`

## 5 · Duplicates and contradictions (compiler §0.6)

- Two records describing the same problem at the same or a nearby `path:line` →
  list them in `duplicates_merged`, naming the survivor (higher priority or
  confidence) and why. Do not delete anything.
- Two records in the same file whose proposed fixes are mutually exclusive →
  list them in `internal_contradictions`. Do not resolve the contradiction.

## 6 · Forbidden

- Editing source. Any file outside `_audit/compiler/verdicts/` and your log.
- Editing `_audit/TO_BE_RESOLVE.md` (the orchestrator assembles it).
- Editing `_audit/dimensions/*.md` (the orchestrator updates statuses).
- Any `git` command.
- Marking a finding `INVALID` in a dimension file yourself.
- Inventing a finding that is not in your packet. If you find a new problem,
  put it in `coverage_gaps` with the citation so the orchestrator can route it.
- Guessing. `NOT_PROVIDED` plus a note beats a confident wrong value.

## 7 · Logging (mandatory)

Log every step as you go:

```
python _audit/compiler/agent_log.py heartbeat <agent_id> <step> <detail>
```

`step` is one of `start | reading_benchmark | reading_packet | verifying |
running_verifies | writing_verdicts | done`.

At the end:

```
python _audit/compiler/agent_log.py complete <agent_id> <1|0> <records_verdicted> <evidence_items> "<notes>"
```

`<records_verdicted>` = number of verdicts written.
`<evidence_items>` = number of raw command outputs pasted.

## 8 · Definition of done

- Every record in your packet has exactly one verdict.
- Every `FALSE_POSITIVE` has counter-evidence.
- Every `ALREADY_FIXED` has verify output.
- Every filled field has evidence.
- `coverage_gaps` explains anything you could not verify.
- You logged `heartbeat ... done` and `complete`.
- You did not edit anything outside your verdict file.

If you cannot finish, write what you have, set `ok=0` on `complete`, and record
exactly what blocked you. **Never fake completion.**
